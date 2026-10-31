from pathlib import Path
import subprocess,numpy as np,json,re,csv
from scipy import signal
root=Path('/home/user/wave2-review/reviews/wave2')
def dec(p):
 b=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-vn','-ar','48000','-ac','2','-f','f32le','-']);return np.frombuffer(b,dtype='<f4').reshape(-1,2).astype(np.float64)
for w,v,stem in [('reel','v07','assets/narration.flac'),('cut','v08','assets/narration.wav')]:
 p=next(Path('/home/user/wave2-'+w).glob('videos/*/'+w+'-'+v));d=root/(w+'-'+v)
 x=dec(p/stem);y=dec(p/'video.mp4');n=min(len(x),len(y));x=x[:n];y=y[:n]
 corr=signal.correlate(y[:480000,0],x[:480000,0],mode='full',method='fft'); mid=480000-1;lag=np.argmax(corr[mid-480:mid+481])-480
 if lag>0:yy=y[lag:];xx=x[:len(yy)]
 elif lag<0:xx=x[-lag:];yy=y[:len(xx)]
 else:xx=x;yy=y
 nn=min(len(xx),len(yy));xx=xx[:nn];yy=yy[:nn]
 rows=[]
 for st in range(0,nn,48000):
  a=xx[st:st+48000];b=yy[st:st+48000]
  if len(a)<24000:continue
  power=np.mean(a*a)
  if power<1e-8:continue
  g=float(np.sum(a*b)/np.sum(a*a));res=b-g*a
  rows.append({'time':st/48000,'gain':g,'correlation':float(np.sum(a*b)/np.sqrt(np.sum(a*a)*np.sum(b*b))),'speech_power':float(np.mean((g*a)**2)),'residual_power':float(np.mean(res**2))})
 windows=[]
 for st in range(0,60,10):
  r=[z for z in rows if st<=z['time']<st+10];seg=x[st*48000:(st+10)*48000];rms=np.sqrt(np.mean(seg*seg,axis=1));
  # 20ms RMS to define numerically active voice, not subjective intelligibility.
  vals=[np.sqrt(np.mean(seg[i:i+960]**2)) for i in range(0,len(seg),960)]
  windows.append({'start':st,'voice_active_fraction_above_minus40dBFS_20ms':float(np.mean(np.array(vals)>.01)),'voice_rms_dbfs':float(20*np.log10(np.sqrt(np.mean(seg*seg))+1e-20)),'fitted_voice_to_residual_db':float(10*np.log10(sum(z['speech_power'] for z in r)/sum(z['residual_power'] for z in r)))})
 spans=[]
 if w=='reel':
  words=json.loads((p/'assets/word_timings.json').read_text())['words']
  cues=[]
  def sec(s):
   h,m,s=s.replace(',','.').split(':');return float(h)*3600+float(m)*60+float(s)
  for block in (p/'captions.srt').read_text().strip().split('\n\n'):
   l=block.splitlines();a,b=l[1].split(' --> ');cues.append((sec(a),sec(b),' '.join(l[2:])))
  over=[]
  for word in words:
   cs=[c for c in cues if c[0]<=word['start']+.03334 and c[1]>=word['end']-.03334];over.append(bool(cs))
  timing={'word_count':len(words),'caption_count':len(cues),'words_covered_within_1frame':sum(over),'first_word':words[0],'last_word':words[-1]}
 else:
  rs=list(csv.DictReader((p/'project/voice_cues.csv').open()));timing={'cues':len(rs),'outside_caption_shot_windows':[]}
  for r in rs:
   i=int(r['shot']);a=float(r['voice_start_s']);b=float(r['voice_end_s']);
   if a<(i-1)*2.4 or b>i*2.4+1/30:timing['outside_caption_shot_windows'].append({'shot':i,'voice_start':a,'voice_end':b,'caption_end':i*2.4})
 out={'stem':stem,'stem_samples_48000':n,'stem_duration_s':n/48000,'crosscorrelation_lag_samples':int(lag),'crosscorrelation_lag_seconds':lag/48000,'windows':windows,'per_second_fits':rows,'timing':timing,'method':'Least-squares scaled actual committed voice versus delivered AAC, per 1-second block. Residual includes all nonvoice plus codec/nonlinear errors, not a separately delivered music stem. Voice dominance relative to residual is a conservative empirical proxy for voice-above-bed, not an isolated music LUFS measurement or perceptual guarantee. No human listened; no speech recognition performed. Zero-lag waveform correlation ties committed speech source to the delivered mix; timing metadata is not independent word recognition.'}
 (d/'speech-analysis.json').write_text(json.dumps(out,indent=2));print(w,'lag',lag,'windows',windows,'timing',timing,flush=True)
