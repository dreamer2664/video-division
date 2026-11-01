from pathlib import Path
import json,subprocess,numpy as np
from scipy import signal
p=Path('/home/user/q-grade-v06/videos/team-b/grade-v06');o=Path('/home/user/queue-review/reviews/queue-2026-11-01/grade-v06')
a=json.loads((p/'timing/timeline_locked.json').read_text());cues=json.loads((p/'timing/captions_locked.json').read_text());turns=a['turns'];words=[w for t in turns for w in t['words']]
b=subprocess.check_output(['ffmpeg','-v','error','-i',str(p/'video.mp4'),'-vn','-ar','16000','-ac','2','-f','f32le','-']);mix=np.frombuffer(b,dtype='<f4').reshape(-1,2).astype(np.float64)
f=signal.sosfilt(signal.butter(4,[350,3400],fs=16000,btype='bandpass',output='sos'),mix,axis=0)
rows=[]
for t in turns:
 z=f[round(t['start']*16000):round(t['end']*16000)];l,r=np.mean(z*z,axis=0);rows.append({'turn':t['turn'],'speaker':t['speaker'],'start':t['start'],'end':t['end'],'mix_speechband_L_minus_R_dB':float(10*np.log10(l/r))})
drift=[]
for c in cues:
 ws=[w for w in words if w['turn']==c['turn'] and w['start']>=c['start']-.001 and w['end']<=c['end']+.001]
 drift.append(max(abs(c['start']-ws[0]['start']),abs(c['end']-ws[-1]['end'])) if ws else None)
r={'actual_mixed_audio_turn_pan':rows,'metadata_turn_count':len(turns),'metadata_alternates_A_B':all(t['speaker']==('A' if i%2==0 else 'B') for i,t in enumerate(turns)),'metadata_overlap_s':sum(max(0,turns[i]['end']-turns[i+1]['start']) for i in range(len(turns)-1)),'gaps_s':[round(turns[i+1]['start']-turns[i]['end'],3) for i in range(len(turns)-1)],'cue_count':len(cues),'max_structural_word_cue_endpoint_drift_s':max(x for x in drift if x is not None),'cues_without_word_span':sum(x is None for x in drift),'stem_files_present':[],'limitations':'Actual mix speech-band pan reversals can corroborate speaker-turn timing, but absent A/B source stems prevent independent stem silencedetect, source-versus-bed/mix comparison, immutable acoustic F0 claims (105.5/206Hz) and actual zero-overlap proof. Metadata overlap=0 is not measured waveform source overlap. No human listened.'}
(o/'two-voice-audit.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
