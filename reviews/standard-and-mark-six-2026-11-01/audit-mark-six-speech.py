from pathlib import Path
import subprocess,json,hashlib,numpy as np
from scipy import signal
p=Path('/home/user/mark-six/videos/team-b/grade-v07');d=Path('/home/user/standard-review/reviews/standard-and-mark-six-2026-11-01/grade-v07')
def dec(f,sr=48000):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(f),'-vn','-ar',str(sr),'-ac','2','-f','f32le','-']),dtype='<f4').reshape(-1,2).astype(np.float64)
gm=json.loads((p/'audio/gain_mapping.json').read_text());hashes={};stems={}
for name,want in gm['stems_sha256'].items():
 f=p/'audio'/name;h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==want;hashes[name]=h;stems[name]=dec(f)
 for typ,cmd in [('probe',['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(f)]),('silence',['ffmpeg','-hide_banner','-nostats','-i',str(f),'-af','silencedetect=n=-40dB:d=0.3','-f','null','-'])]:
  r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);assert r.returncode==0;(d/(f.stem+'-'+typ+'.txt')).write_text(' '.join(cmd)+'\n'+r.stdout+'\nexit_status=0\n')
a,b,c,v,bed=[stems[k] for k in ['voice_A_reel_48k.flac','voice_B_line_48k.flac','voice_C_horn_48k.flac','dialogue_stem_48k.flac','bed_ducked_48k.flac']];assert all(len(z)==2880000 for z in stems.values());mix=dec(p/'video.mp4')[:len(v)];av=np.max(np.abs(a),axis=1)>1/32768;bv=np.max(np.abs(b),axis=1)>1/32768
# Source-based lag, search +/-100ms over the first10s.
vm=signal.resample_poly(v[:480000].mean(axis=1),1,6);ym=signal.resample_poly(mix[:480000].mean(axis=1),1,6);cc=signal.correlate(ym,vm,method='fft');mid=len(vm)-1;lag8=int(np.argmax(cc[mid-800:mid+801])-800);lag=lag8*6
if lag>=0:xv=v[:len(v)-lag] if lag else v;xb=bed[:len(v)-lag] if lag else bed;y=mix[lag:]
else:xv=v[-lag:];xb=bed[-lag:];y=mix[:lag]
g=np.linalg.solve([[np.sum(xv*xv),np.sum(xv*xb)],[np.sum(xv*xb),np.sum(xb*xb)]],[np.sum(xv*y),np.sum(xb*y)]);pred=g[0]*xv+g[1]*xb;res=y-pred
wins=[]
for t in range(0,60,10):
 z=v[t*48000:(t+10)*48000];bb=bed[t*48000:(t+10)*48000];active=np.sqrt(np.mean(z.reshape(-1,960,2)**2,axis=(1,2)))>.01;mask=np.repeat(active,960)
 wins.append({'start_s':t,'speech_active_fraction_20ms_minus40dBFS':float(active.mean()),'active_dialogue_over_bed_rms_db':float(10*np.log10(np.mean(z[mask]**2)/np.mean(bb[mask]**2)))})
def acoustic(z):
 mono=signal.resample_poly(z.mean(axis=1),1,6);lp=signal.sosfilt(signal.butter(3,450,fs=8000,output='sos'),mono);f=[]
 for i in range(0,len(lp)-480,320):
  zz=lp[i:i+480];orig=mono[i:i+480]
  if np.sqrt(np.mean(orig**2))<.01:continue
  zz=(zz-zz.mean())*np.hanning(480);ac=signal.correlate(zz,zz,mode='full',method='fft')[479:];peaks,_=signal.find_peaks(ac[23:115]);
  if len(peaks):
   pk=int(peaks[np.argmax(ac[23:115][peaks])]+23)
   if ac[pk]/max(ac[0],1e-16)>.3:f.append(8000/pk)
 return {'autocorrelation_f0_median_hz':float(np.median(f)),'voiced_windows':len(f),'L_minus_R_RMS_db':float(10*np.log10(np.mean(z[:,0]**2)/np.mean(z[:,1]**2)))}
manifest=json.loads((p/'timing/tts_source_manifest.json').read_text());tl=json.loads((p/'timing/timeline_locked.json').read_text());drift=[];mp3=[]
for line,turn in zip(manifest['turns'],tl['turns']):
 f=p/line['rel_mp3'];h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==line['sha256'];mp3.append({'path':line['rel_mp3'],'sha256':h});assert len(line['words_raw'])==len(turn['words'])
 for raw,w in zip(line['words_raw'],turn['words']):
  for k in ['start','end']:drift.append(abs(w[k]-(line['timeline_start_s']+raw[k]-line['first_word_offset_s'])))
js={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip(),'verified_source_hashes':hashes,'source_durations_s':{k:len(z)/48000 for k,z in stems.items()},'verified_raw_turn_mp3s':mp3,'isolated_A_B_overlap_samples_above_one_LSB':int(np.sum(av&bv)),'dialogue_minus_A_plus_B_plus_C_max_abs':float(np.max(np.abs(v-a-b-c))), 'isolated_AC_overlap_samples':int(np.sum(av & (np.max(np.abs(c),axis=1)>1/32768))), 'isolated_BC_overlap_samples':int(np.sum(bv & (np.max(np.abs(c),axis=1)>1/32768))),'A_acoustic':acoustic(a),'B_acoustic':acoustic(b),'C_acoustic':acoustic(c),'mix_to_dialogue_lag_samples_48k':lag,'mix_to_dialogue_lag_s':lag/48000,'joint_source_mix_fit_gains':g.tolist(),'joint_source_mix_correlation':float(np.sum(pred*y)/np.sqrt(np.sum(pred*pred)*np.sum(y*y))),'joint_fit_residual_dbfs':float(20*np.log10(np.sqrt(np.mean(res*res)))),'body_windows':wins,'max_original_word_telemetry_to_locked_timeline_drift_s':max(drift),'limitations':'No human listened. RMS margins and autocorrelation pitch are numeric estimates, not subjective intelligibility. Lag search6-sample granularity. No production rebuild or TTS.'}
turnmask=np.zeros(len(v),dtype=bool)
for turn in tl['turns']:turnmask[round(turn['start']*48000):round(turn['end']*48000)]=True
js['declared_turn_dialogue_over_committed_bed_rms_db']=float(10*np.log10(np.mean(v[turnmask]**2)/np.mean(bed[turnmask]**2)))
js['declared_turn_coverage_fraction']=float(turnmask.mean())
(d/'speech-source-audit.json').write_text(json.dumps(js,indent=2));print(json.dumps(js,indent=2))
