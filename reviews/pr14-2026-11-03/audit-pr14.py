from pathlib import Path
import subprocess,json,hashlib,struct,numpy as np
from scipy import signal
from PIL import Image,ImageDraw
p=Path('/tmp/lux-pr14/videos/team-a/reel-v09-cinematic');d=Path('/home/user/video-division/reviews/pr14-2026-11-03')
def run(name,args):
 r=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(d/name).write_text('$ '+' '.join(args)+'\n'+r.stdout+'\nexit_status='+str(r.returncode)+'\n');assert r.returncode==0;return r.stdout
f=p/'video.mp4';probe=json.loads(run('ffprobe.txt',['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(f)]));run('loudnorm.txt',['ffmpeg','-hide_banner','-nostats','-i',str(f),'-vn','-af','loudnorm=print_format=json','-f','null','-']);run('full-scan.txt',['ffmpeg','-hide_banner','-nostats','-threads','1','-i',str(f),'-vf','blackdetect=d=0.5:pix_th=0.02,freezedetect=n=-60dB:d=0.5','-an','-f','null','-']);run('decode.txt',['ffmpeg','-v','error','-i',str(f),'-f','null','-'])
manifest=[]
for fp in sorted(p.rglob('*')):
 if fp.is_file():manifest.append({'path':str(fp.relative_to(p)),'bytes':fp.stat().st_size,'sha256':hashlib.sha256(fp.read_bytes()).hexdigest()})
atoms=[]
with f.open('rb') as ff:
 while h:=ff.read(8):
  off=ff.tell()-8;n,k=struct.unpack('>I4s',h)
  if n==1:n=struct.unpack('>Q',ff.read(8))[0]
  if n==0:n=f.stat().st_size-off
  atoms.append({'type':k.decode(),'offset':off,'size':n});ff.seek(off+n)
(d/'manifest.json').write_text(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip(),'files':manifest,'mp4_atoms':atoms},indent=2))
def dec(fp):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(fp),'-ar','48000','-ac','2','-f','f32le','-']),dtype='<f4').reshape(-1,2).astype(np.float64)
v=dec(p/'audio/narration_stem_48k.flac');bed=dec(p/'audio/bed_ducked_48k.flac');mix=dec(f)[:2880000];nv=len(v);v=np.pad(v,((0,2880000-nv),(0,0)))[:2880000];mapping=json.loads((p/'audio/gain_mapping.json').read_text());tm=json.loads((p/'timing/word_timings.json').read_text());words=tm['words'];cues=json.loads((p/'timing/captions_locked.json').read_text())['cues'];mask=np.zeros(len(v),bool)
for w in words:mask[round(w['start']*48000):round(w['end']*48000)]=True
for fn,h in mapping['stems_sha256'].items():assert hashlib.sha256((p/'audio'/fn).read_bytes()).hexdigest()==h
sm=json.loads((p/'timing/tts_source_manifest.json').read_text())
for fn,h in sm['raw'].items():assert hashlib.sha256((p/fn).read_bytes()).hexdigest()==h
assert hashlib.sha256((p/'audio/narration_stem_48k.flac').read_bytes()).hexdigest()==sm['processed_stem_sha256'];assert hashlib.sha256((p/'timing/word_timings.json').read_bytes()).hexdigest()==sm['processed_word_timings_sha256']
run('stem-probe.txt',['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p/'audio/narration_stem_48k.flac')]);run('stem-silence.txt',['ffmpeg','-hide_banner','-nostats','-i',str(p/'audio/narration_stem_48k.flac'),'-af','silencedetect=n=-40dB:d=0.3','-f','null','-'])
a=signal.resample_poly(v[:480000].mean(axis=1),1,6);b=signal.resample_poly(mix[:480000].mean(axis=1),1,6);cc=signal.correlate(b,a,method='fft');mid=len(a)-1;lag=int(np.argmax(cc[mid-800:mid+801])-800)*6
# Same source-based margin mask used for cut/v10, not a different active-gate to force a pass.
windows=[]
for t in range(0,60,10):
 lo=t*48000;hi=(t+10)*48000;z=v[lo:hi];bb=bed[lo:hi];act=np.sqrt(np.mean(z.reshape(-1,960,2)**2,axis=(1,2)))>.01;m=mask[lo:hi];windows.append({'start_s':t,'20ms_activity_fraction_above_minus40dBFS':float(act.mean()),'source_voice_minus_bed_word_spans_dB':float(10*np.log10(np.mean(z[m]**2)/np.mean(bb[m]**2))) if m.any() else None})
vv=v;bb=bed;yy=mix;g=np.linalg.solve([[np.sum(vv*vv),np.sum(vv*bb)],[np.sum(vv*bb),np.sum(bb*bb)]],[np.sum(vv*yy),np.sum(bb*yy)]);pred=g[0]*vv+g[1]*bb;corr=float(np.sum(pred*yy)/np.sqrt(np.sum(pred*pred)*np.sum(yy*yy)))
flatten=[w for c in cues for w in c['words']];assert len(flatten)==len(words);dr=[];delay=[]
for w,cw in zip(words,flatten):
 assert w['word']==cw['text'];dr.extend([abs(w['start']-cw['start_s']),abs(w['end']-cw['end_s'])]);fr=cw['first_eligible_frame'];assert fr==int(np.ceil(w['start']*30-1e-8));delay.append(fr/30-w['start'])
(d/'speech.json').write_text(json.dumps({'stem_duration_s':nv/48000,'source_and_processed_hashes_verified':True,'mix_lag_samples_48k':lag,'word_count':len(words),'cue_count':len(cues),'cue_word_span_translation_max_drift_s':max(dr),'max_first_eligible_frame_delay_s':max(delay),'word_count_range_per_cue':[min(len(c['words']) for c in cues),max(len(c['words']) for c in cues)],'source_voice_over_bed_word_spans_dB':float(10*np.log10(np.mean(v[mask]**2)/np.mean(bed[mask]**2))),'windows':windows,'joint_source_and_bed_mix_fit_gains':g.tolist(),'joint_source_and_bed_mix_fit_correlation':corr,'first_word_s':words[0]['start'],'last_word_end_s':words[-1]['end'],'note':'No human listened. Source-to-mix numeric/telemetry test, not lexical ASR or subjective intelligibility; silence tail assessed separately.'},indent=2))
# Decoded actual frames; only contact sheets, not full resolution intermediates, persist.
frames=[]
for i,t in enumerate([.5,7,13,19,24.5,29.5,36.5,42,48,59]):
 q=Path('/tmp')/f'lux-hotel-frame-{i}.jpg';subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(f),'-frames:v','1','-update','1',str(q)],check=True);im=Image.open(q).convert('RGB');im.thumbnail((480,270));frames.append(im)
sheet=Image.new('RGB',(1440,1200),'#151515');drw=ImageDraw.Draw(sheet)
for i,im in enumerate(frames):x=i%3*480;y=i//3*300+20;sheet.paste(im,(x,y));drw.text((x+2,y-16),str([.5,7,13,19,24.5,29.5,36.5,42,48,59][i])+'s',fill='white')
sheet.save(d/'chronological-pictures.jpg')
print('Full media, immutable source, numeric speech and frame audit complete')
