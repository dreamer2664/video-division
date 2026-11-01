from pathlib import Path
import subprocess,json,hashlib,struct,concurrent.futures
out=Path('/home/user/queue-review/reviews/queue-2026-11-01');out.mkdir(parents=True,exist_ok=True)
items=[('pixel','v06'),('reel','v08'),('grade','v06'),('pixel','v07')]
def audit(item):
 w,v=item;p=next(Path('/home/user/q-'+w+'-'+v).glob('videos/*/'+w+'-'+v));d=out/(w+'-'+v);d.mkdir(exist_ok=True)
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip(); inv={'head':head,'files':{}}
 for f in sorted(p.glob('video*.mp4')):
  pre=f.stem
  cmds={'probe':f'ffprobe -v error -show_streams -show_format -of json {f.name}','spec-probe':f'ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 {f.name}','loudness':f'ffmpeg -hide_banner -nostats -i {f.name} -vn -af loudnorm=print_format=json -f null -','scan':f'ffmpeg -hide_banner -nostats -threads 1 -i {f.name} -vf blackdetect=d=0.5:pix_th=0.02,freezedetect=n=-60dB:d=0.5 -an -f null -','silence':f'ffmpeg -hide_banner -nostats -i {f.name} -vn -af silencedetect=n=-40dB:d=1 -f null -'}
  for n,c in cmds.items():
   r=subprocess.run(['bash','-o','pipefail','-c',c],cwd=p,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(d/(pre+'-'+n+'.txt')).write_text('$ '+c+'\n'+r.stdout+'\nexit_status='+str(r.returncode))
  atoms=[]
  with f.open('rb') as ff:
   while h:=ff.read(8):
    off=ff.tell()-8;n,k=struct.unpack('>I4s',h)
    if n==1:n=struct.unpack('>Q',ff.read(8))[0]
    atoms.append((k.decode(),off,n))
    if n==0:break
    ff.seek(off+n)
  inv['files'][f.name]={'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'atoms':atoms}
  subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(f),'-vf','fps=1/5,scale=270:270:force_original_aspect_ratio=decrease,pad=270:270:(ow-iw)/2:(oh-ih)/2,tile=4x3','-frames:v','1','-y',str(d/(pre+'-overview.jpg'))],check=True)
  for t in [0.5,59]:subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(f),'-frames:v','1','-y',str(d/f'{pre}-{t}.jpg')],check=True)
 stems=[f for f in (p/'assets').glob('*') if f.suffix in ['.flac','.wav','.mp3']] if (p/'assets').exists() else []
 inv['audio_assets']=[str(s.relative_to(p)) for s in stems]
 for s in stems:
  for n,c in [('probe',f'ffprobe -v error -show_format -show_streams -of json "{s}"'),('silence',f'ffmpeg -hide_banner -nostats -i "{s}" -af silencedetect=n=-40dB:d=0.3 -f null -')]:
   r=subprocess.run(c,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(d/('stem-'+n+'.txt')).write_text('$ '+c+'\n'+r.stdout+'\nexit_status='+str(r.returncode))
 (d/'identity.json').write_text(json.dumps(inv,indent=2));return w
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as e:
 for w in e.map(audit,items):print(w+' verified',flush=True)
