from pathlib import Path
import json,subprocess,numpy as np,hashlib,re
from scipy import signal
p=Path('/home/user/q-grade-v05/videos/team-b/grade-v05');d=Path('/home/user/queue-review/reviews/queue-2026-11-01/grade-v05')
def run(c,out):
 r=subprocess.run(c,cwd=p,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(d/out).write_text('$ '+c+'\n'+r.stdout+'\nexit_status='+str(r.returncode))
for name in ['narration_stem_48k','bed_ducked_48k']:
 run('ffprobe -v error -show_format -show_streams -of json audio/'+name+'.flac',name+'-probe.txt')
 run('ffmpeg -hide_banner -nostats -i audio/'+name+'.flac -af silencedetect=n=-40dB:d=0.3 -f null -',name+'-silence.txt')
def dec(path):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-vn','-ar','48000','-ac','2','-f','f32le','-']),dtype='<f4').reshape(-1,2).astype(np.float64)
v=dec(p/'audio/narration_stem_48k.flac');b=dec(p/'audio/bed_ducked_48k.flac');y=dec(p/'video.mp4')[:len(v)];n=len(v)
assert len(v)==len(b)==2880000
lagcorr=signal.correlate(y[:480000,0],v[:480000,0],mode='full',method='fft');mid=480000-1;lag=int(np.argmax(lagcorr[mid-480:mid+481])-480)
vv=float(np.sum(v*v));bb=float(np.sum(b*b));vb=float(np.sum(v*b));vy=float(np.sum(v*y));by=float(np.sum(b*y));g=np.linalg.solve(np.array([[vv,vb],[vb,bb]]),np.array([vy,by]));pred=g[0]*v+g[1]*b;res=y-pred;corr=float(np.sum(pred*y)/np.sqrt(np.sum(pred*pred)*np.sum(y*y)))
windows=[]
for st in range(0,60,10):
 z=v[st*48000:(st+10)*48000];zbed=b[st*48000:(st+10)*48000];blocks=np.sqrt(np.mean(z.reshape(-1,960,2)**2,axis=(1,2)));act=blocks>.01;mask=np.repeat(act,960)
 windows.append({'start':st,'voice_active_fraction_20ms_above_minus40dBFS':float(act.mean()),'voice_over_bed_db_whole_window':float(10*np.log10(np.mean(z*z)/np.mean(zbed*zbed))),'voice_over_bed_db_active_blocks':float(10*np.log10(np.mean(z[mask]**2)/np.mean(zbed[mask]**2)))})
m=json.loads((p/'timing/tts_source_manifest.json').read_text());tl=json.loads((p/'timing/timeline_locked.json').read_text());words=[w for s in tl['shots'] for w in s['words']];cues=json.loads((p/'timing/captions_locked.json').read_text());drift=[];hashes=[];mdrift=[]
for line in m['lines']:
 f=p/line['rel_mp3'];h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==line['sha256'];hashes.append({'path':line['rel_mp3'],'sha256':h,'verified':True})
 ws=[w for w in words if w['line']==line['id']]
 assert len(ws)==len(line['words_raw'])
 for w,raw in zip(ws,line['words_raw']):mdrift.extend([abs(w['start']-(line['timeline_clip_start_s']+raw['start']-line['trim_in_s'])),abs(w['end']-(line['timeline_clip_start_s']+raw['end']-line['trim_in_s']))])
for c in cues:
 ws=[w for w in words if w['line']==c['line'] and w['start']>=c['start']-.001 and w['end']<=c['end']+.001];assert ws;drift.extend([abs(c['start']-ws[0]['start']),abs(c['end']-ws[-1]['end'])])
stems={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'audio').glob('*.flac')};gmap=json.loads((p/'audio/gain_mapping.json').read_text());assert stems['narration_stem_48k.flac']==gmap['narration_stem_sha256'];assert stems['bed_ducked_48k.flac']==gmap['bed_ducked_sha256']
a=json.loads((d/'identity.json').read_text());a['audio_assets']=[str(x.relative_to(p)) for x in (p/'audio').rglob('*') if x.suffix in ['.flac','.wav','.mp3']];(d/'identity.json').write_text(json.dumps(a,indent=2))
sil=(d/'narration_stem_48k-silence.txt').read_text();events=re.findall(r'silence_end: ([\d.]+) \| silence_duration: ([\d.]+)',sil)
out={'audited_head':a['head'],'stem_duration_s':60,'stems_sha256_verified':stems,'body_windows':windows,'voice_to_actual_mix_lag_samples':lag,'joint_voice_bed_to_final_mix_fit_gains':g.tolist(),'joint_prediction_correlation_to_final_AAC':corr,'joint_fit_residual_dbfs':float(20*np.log10(np.sqrt(np.mean(res*res)))),'longest_source_gap_s':max(float(b) for a,b in events),'cue_count':len(cues),'word_count':len(words),'maximum_cue_word_endpoint_drift_s':max(drift),'maximum_original_telemetry_to_timeline_translation_drift_s':max(mdrift),'original_mp3_hashes_verified':hashes,'note':'Immutable sources compared to actual final AAC; no production rebuild, no new TTS. Global linear least-squares reconstruction is an analysis-only model, not a claim of byte-identical AAC or subjective intelligibility. No human listened.'}
(d/'speech-source-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
