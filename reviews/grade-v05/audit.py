from pathlib import Path
import subprocess,struct,json,hashlib
p=Path('/home/user/audit-grade-v05/videos/team-b/grade-v05');o=Path('/home/user/lux-v05-review/reviews/grade-v05')
cmds={'probe':'ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 video.mp4','details':'ffprobe -v error -show_streams -show_format -of json video.mp4','loudness-spec':'ffmpeg -v error -i video.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | tail -12','loudness':'ffmpeg -hide_banner -nostats -i video.mp4 -vn -af loudnorm=print_format=json -f null -','scan':'ffmpeg -hide_banner -nostats -threads 1 -i video.mp4 -vf blackdetect=d=0.5:pix_th=0.02,freezedetect=n=-60dB:d=0.5 -an -f null -','mix-silence':'ffmpeg -hide_banner -nostats -i video.mp4 -vn -af silencedetect=n=-40dB:d=1 -f null -','speech-band':'ffmpeg -hide_banner -nostats -i video.mp4 -vn -af highpass=f=300,lowpass=f=4000,asetnsamples=n=480000:p=0,astats=metadata=1:reset=1,ametadata=print:file=- -f null -'}
for n,c in cmds.items():
 r=subprocess.run(['bash','-o','pipefail','-c',c],cwd=p,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(o/(n+'.txt')).write_text('$ '+c+'\n'+r.stdout+'\nexit_status='+str(r.returncode))
with (p/'video.mp4').open('rb') as f:
 atoms=[]
 while h:=f.read(8):
  off=f.tell()-8;n,k=struct.unpack('>I4s',h)
  if n==1:n=struct.unpack('>Q',f.read(8))[0]
  atoms.append((k.decode(),off,n))
  if not n:break
  f.seek(off+n)
(o/'identity.txt').write_text('head=047e32219512984ada13356e5a2dcaf77fde49b1\nbytes='+str((p/'video.mp4').stat().st_size)+'\nsha256='+hashlib.sha256((p/'video.mp4').read_bytes()).hexdigest()+'\natoms='+repr(atoms)+'\n')
for t in [0,0.5,8.9,16,28,39,45.5,53,57.8,59,59.9]:
 subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(p/'video.mp4'),'-frames:v','1','-y',str(o/f'frame-{t}.jpg')],check=True)
cues=json.loads((p/'timing/captions_locked.json').read_text());tl=json.loads((p/'timing/timeline_locked.json').read_text());lines=[]
shots=tl['shots']; words=[x for s in shots for x in s['words']]
for c in cues:
 w=[w for w in words if w['line']==c['line'] and w['start']>=c['start']-.001 and w['end']<=c['end']+.001]
 lines.append(dict(cue=c['cue'],start=c['start'],end=c['end'],word_span=[w[0]['start'],w[-1]['end']] if w else None,plain=c['plain'],words=' '.join(x['text'] for x in w)))
(o/'caption-structural.json').write_text(json.dumps(lines,indent=2))
(o/'stem-inventory.txt').write_text('Tracked v05 WAV/MP3/FLAC stems: '+repr([str(x.relative_to(p)) for x in p.rglob('*') if x.suffix.lower() in ['.wav','.mp3','.flac']])+'\nQA cited /tmp/grade_v05_build/narration/narration_stem_48k.wav: absent on independent checkout/sandbox\nNo isolated narration or bed available: stem probe, stem silencedetect and actual stem-to-delivered-mix comparison cannot be run. No TTS regeneration or video rerender performed.\n')
