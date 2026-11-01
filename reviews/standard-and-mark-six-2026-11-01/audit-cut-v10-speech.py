from pathlib import Path
import subprocess,json,hashlib,re,numpy as np
from scipy import signal
p=Path('/home/user/cinematic-cut/videos/team-b/cut-v10');d=Path('/home/user/standard-review/reviews/standard-and-mark-six-2026-11-01/cut-v10')
def dec(f,sr=48000):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(f),'-vn','-ar',str(sr),'-ac','2','-f','f32le','-']),dtype='<f4').reshape(-1,2).astype(np.float64)
v=dec(p/'audio/narration_stem_48k.flac');bed=dec(p/'audio/bed_stem_48k.flac');mix=dec(p/'video.mp4')[:len(v)];raw=dec(p/'audio/narration_source.mp3',16000);words=json.loads((p/'timing/word_telemetry.json').read_text());cues=json.loads((p/'timing/captions_locked.json').read_text());assert len(v)==len(bed)==len(mix)==2880000;hashes={}
for typ,key in [('source_text','source_text_sha256'),('source_mp3','source_mp3_sha256')]:
 h=hashlib.sha256((p/words[typ]).read_bytes()).hexdigest();assert h==words[key];hashes[typ]=h
stem16=signal.resample_poly(v[:480000].mean(axis=1),1,3);ra=raw[:160000].mean(axis=1);cc=signal.correlate(stem16,ra,method='fft');mid=len(ra)-1;source_lag=int(np.argmax(cc[mid:mid+16001]));vu=signal.resample_poly(v[:480000].mean(axis=1),1,3);mu=signal.resample_poly(mix[:480000].mean(axis=1),1,3);cc=signal.correlate(mu,vu,method='fft');mid=len(vu)-1;lag16=int(np.argmax(cc[mid-1600:mid+1601])-1600)
mask=np.zeros(len(v),bool);dr=[];inds=[]
for c in cues:
 ids=c['source_event_indices'];inds+=ids;ws=[words['words'][i] for i in ids];dr.extend([abs(c['start']-(ws[0]['start_s']+.3)),abs(c['end']-(ws[-1]['end_s']+.3))]);
for w in words['words']:mask[round((w['start_s']+.3)*48000):round((w['end_s']+.3)*48000)]=True
assert inds==list(range(len(words['words'])))
wins=[]
for t in range(0,60,10):
 a=t*48000;b=(t+10)*48000;z=v[a:b];bb=bed[a:b];yy=mix[a:b];active=np.sqrt(np.mean(z.reshape(-1,960,2)**2,axis=(1,2)))>.01;corr=[];vo=[];rs=[]
 for k in range(10):
  zz=z[k*48000:(k+1)*48000];ym=yy[k*48000:(k+1)*48000];den=np.sum(zz*zz)
  if den<1e-10:continue
  gain=float(np.sum(zz*ym)/den);pr=gain*zz;res=ym-pr;vo.append(np.sum(pr*pr));rs.append(np.sum(res*res));corr.append(float(np.sum(zz*ym)/np.sqrt(den*np.sum(ym*ym))))
 m=mask[a:b];wins.append({'start':t,'speech_active_fraction_20ms_minus40dBFS':float(active.mean()),'source_voice_over_bed_on_word_intervals_db':float(10*np.log10(np.mean(z[m]**2)/np.mean(bb[m]**2))) if m.any() else None,'fitted_voice_above_mix_residual_db':float(10*np.log10(sum(vo)/sum(rs))),'median_source_mix_1s_correlation':float(np.median(corr))})
for name in ['narration_stem_48k.flac','bed_stem_48k.flac']:
 for typ,cmd in [('probe',['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p/'audio'/name)]),('silence',['ffmpeg','-hide_banner','-nostats','-i',str(p/'audio'/name),'-af','silencedetect=n=-40dB:d=0.3','-f','null','-'])]:
  res=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True);(d/(name+'-'+typ+'.txt')).write_text(' '.join(cmd)+'\n'+res.stdout+'\nexit_status=0\n')
out={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip(),'stem_duration_s':len(v)/48000,'verified_source_hashes':hashes,'original_MP3_to_stem_lag_s':source_lag/16000,'stem_to_actual_final_mix_lag_s':lag16/16000,'word_count':len(words['words']),'cue_count':len(cues),'cue_word_endpoint_drift_max_s':max(dr),'all_word_indices_covered_once_in_order':True,'first_word_s':words['words'][0]['start_s']+.3,'last_word_end_s':words['words'][-1]['end_s']+.3,'actual_source_voice_over_bed_word_spans_db':float(10*np.log10(np.mean(v[mask]**2)/np.mean(bed[mask]**2))),'body_windows':wins,'note':'No human listened; independent source/mix method includes codec/gain errors in residual, not isolated music LUFS or ASR. Silent6.29s ending assessed separately from body coverage.'};(d/'speech-source-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
