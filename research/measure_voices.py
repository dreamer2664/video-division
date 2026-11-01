#!/usr/bin/env python3
"""Measure committed TTS evidence on one common signal path. No perceptual MOS."""
import csv,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
import parselmouth,webrtcvad
from scipy import signal
R=Path(__file__).resolve().parent;SR=16000
TEXT=(R/'ab-reel/benchmark.txt').read_text().strip();WORDS=len(re.findall(r"\b[\w']+\b",TEXT))

def analyze(path):
    data=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ac','1','-ar',str(SR),'-f','f32le','-'])
    y=np.frombuffer(data,dtype='<f4').astype(np.float64);peak=float(np.max(np.abs(y)));rms=float(np.sqrt(np.mean(y*y)))
    # Same gain convention for VAD; preserve original relative within-clip dynamics.
    scale=min(.89/max(peak,1e-9),.1/max(rms,1e-9));y=y*scale
    pcm=np.round(np.clip(y,-1,1)*32767).astype('<i2');n=480;vad=webrtcvad.Vad(2)
    flags=np.array([vad.is_speech(pcm[i:i+n].tobytes(),SR) for i in range(0,len(pcm)-n+1,n)],bool)
    active=np.flatnonzero(flags)
    if not len(active):raise ValueError(f'No VAD activity in {path}')
    first,last=int(active[0]),int(active[-1]);utterance=(last-first+1)*.03
    pauses=[];i=first
    while i<=last:
        if not flags[i]:
            j=i
            while j<=last and not flags[j]:j+=1
            dur=(j-i)*.03
            if dur>=.15-1e-9:pauses.append(round(dur,3))
            i=j
        else:i+=1
    pitch=parselmouth.Sound(y,SR).to_pitch_ac(time_step=.01,pitch_floor=60,pitch_ceiling=350)
    f0=pitch.selected_array['frequency'];f0=f0[f0>0]
    if not len(f0):raise ValueError(f'No voiced pitch in {path}')
    f,t,z=signal.stft(y,fs=SR,window='hann',nperseg=512,noverlap=352,nfft=512,boundary=None,padded=False)
    mag=np.abs(z);valid=flags[np.minimum((t/.03).astype(int),len(flags)-1)]
    mag=mag[:,valid];mass=mag.sum(axis=0);ok=mass>1e-10;mag=mag[:,ok];mass=mass[ok]
    centroid=(f[:,None]*mag).sum(axis=0)/mass
    roll_idx=(np.cumsum(mag,axis=0)>=.85*mass).argmax(axis=0);roll=f[roll_idx]
    return {'duration_s':round(len(y)/SR,4),'vad_utterance_s':round(utterance,3),'words':WORDS,
      'wpm_vad_span':round(WORDS/utterance*60,2),'f0_mean_hz':round(float(f0.mean()),2),'f0_sd_hz':round(float(f0.std()),2),
      'f0_sd_semitones':round(float((12*np.log2(f0/100)).std()),2),'f0_p05_hz':round(float(np.percentile(f0,5)),2),'f0_p95_hz':round(float(np.percentile(f0,95)),2),
      'f0_voiced_frame_fraction':round(float(len(f0)/len(pitch.selected_array['frequency'])),4),
      'pause_count_150ms':len(pauses),'pause_median_s':round(float(np.median(pauses)),3) if pauses else 0.0,
      'pause_p90_s':round(float(np.percentile(pauses,90)),3) if pauses else 0.0,'pause_max_s':max(pauses) if pauses else 0.0,'pause_durations_s':pauses,
      'centroid_mean_hz':round(float(centroid.mean()),1),'rolloff85_mean_hz':round(float(roll.mean()),1),
      'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    entries=[]
    for p in sorted((R/'voice-matrix/edge').glob('*.mp3')):
        m=json.loads(p.with_suffix('.json').read_text());entries.append((p,{'engine':'edge-tts','voice':m['voice'],'setting':m['condition'],'rate':m['rate'],'pitch':m['pitch']}))
    for p in sorted((R/'voice-matrix/piper').glob('*.flac')):
        setting=p.stem.split('--')[-1];entries.append((p,{'engine':'piper','voice':'en_US-joe-medium','setting':setting,'rate':'length_scale=1.0' if setting=='neutral' else 'length_scale=1.12','pitch':'native (not tunable)'}))
    for p in sorted((R/'voice-matrix/eleven').glob('*.mp3')):
        m=json.loads(p.with_suffix('.json').read_text());entries.append((p,{'engine':'ElevenLabs','voice':m['voice']['name'],'setting':'reference','rate':'speed=1.0','pitch':'native (not tunable)','model':m['model_id']}))
    rows=[]
    for path,meta in entries:
        d={'file':str(path.relative_to(R)),**meta,**analyze(path)};rows.append(d)
        print(meta['engine'],meta['voice'],meta['setting'],'f0',d['f0_mean_hz'],d['f0_sd_hz'],'wpm',d['wpm_vad_span'],'pauses',d['pause_count_150ms'],flush=True)
    (R/'voice-metrics.json').write_text(json.dumps({'method':{'sample_rate':SR,'f0':'Praat autocorrelation; 10ms, 60–350Hz; unvoiced excluded','vad':'WebRTC mode 2, 30ms frames, peak-capped RMS normalization','speech_rate':f'{WORDS} written tokens / first-to-last VAD time * 60, not ASR','pause':'non-voiced interior VAD spans >=150ms','spectral':'STFT Hann 32ms, 10ms hop, speech frames; amplitude-weighted centroid and 85% rolloff; common 0–8kHz bandwidth'},'rows':rows},indent=2)+'\n')
    cols=['engine','voice','setting','rate','pitch','duration_s','vad_utterance_s','wpm_vad_span','f0_mean_hz','f0_sd_hz','f0_sd_semitones','f0_voiced_frame_fraction','pause_count_150ms','pause_median_s','pause_p90_s','pause_max_s','centroid_mean_hz','rolloff85_mean_hz','file','sha256']
    with (R/'voice-metrics.csv').open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(rows)
    print('MEASURED ROWS',len(rows),flush=True)
if __name__=='__main__':main()
