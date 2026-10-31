import pathlib,subprocess,concurrent.futures,json,struct
root=pathlib.Path('/home/user/video-division/reviews/2026-10-31-final')
def run(w):
 p=next(pathlib.Path('/home/user/audit-'+w).glob('videos/*/*/video.mp4')); d=root/w;d.mkdir(exist_ok=True)
 cmds={'probe':'ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 video.mp4','loudness-spec':'ffmpeg -v error -i video.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | tail -12','loudness':'ffmpeg -hide_banner -nostats -i video.mp4 -vn -af loudnorm=print_format=summary -f null -','scan':'ffmpeg -hide_banner -nostats -threads 1 -i video.mp4 -vf blackdetect=d=0.5:pix_th=0.02,freezedetect=n=-60dB:d=0.5 -an -f null -','details':'ffprobe -v error -show_streams -show_format -of json video.mp4'}
 for name,cmd in cmds.items():
  r=subprocess.run(['bash','-o','pipefail','-c',cmd],cwd=p.parent,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(d/(name+'.txt')).write_text('$ '+cmd+'\n'+r.stdout+'\nexit_status='+str(r.returncode)+'\n')
 # inspection sheet: entire piece each 5s plus boundaries
 subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(p),'-vf','fps=1/5,scale=480:270,tile=3x4','-frames:v','1','-y',str(d/'overview.jpg')],check=True)
 for t in [0,0.5,59,59.9]:
  subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(p),'-frames:v','1','-y',str(d/f'boundary-{t}.png')],check=True)
 with p.open('rb') as f:
  atoms=[]
  while True:
   off=f.tell(); h=f.read(8)
   if len(h)<8:break
   n,k=struct.unpack('>I4s',h)
   if n==1:n=struct.unpack('>Q',f.read(8))[0]
   atoms.append((k.decode(),off,n))
   if n==0:break
   f.seek(off+n)
 (d/'inventory.txt').write_text('video bytes: '+str(p.stat().st_size)+'\natoms: '+str(atoms)+'\nstills: '+str([x.name for x in (p.parent/'stills').glob('*')])+'\n')
 return w
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
 for w in ex.map(run,['reel','cut','grade','pixel']):print(w+' complete',flush=True)
