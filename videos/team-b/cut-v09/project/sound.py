#!/usr/bin/env python3
"""Generate the original drone/relay score, mix with narration and loudness-normalize."""
import math, os, pathlib, subprocess, wave
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
SR=48000; DUR=60

def write_wav(path,x):
    x=np.clip(x,-1,1)
    pcm=(x*32767).astype('<i2')
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

def main():
    t=np.arange(SR*DUR,dtype=np.float64)/SR
    # Original synthesized low drone, slow beating partials, subtle filtered pulse.
    sweep=38+1.4*np.sin(2*np.pi*t/17.0)
    phase=2*np.pi*np.cumsum(sweep)/SR
    left=.040*np.sin(phase)+.018*np.sin(2*np.pi*52.0*t+.35*np.sin(2*np.pi*t/23))
    right=.040*np.sin(phase+.12)+.018*np.sin(2*np.pi*50.7*t+.35*np.sin(2*np.pi*t/23))
    # soft dissonant upper partial, kept restrained; small low-frequency swell every 12 s.
    swell=.70+.30*(.5+.5*np.sin(2*np.pi*t/12.0))
    left=(left+.010*np.sin(2*np.pi*73.4*t))*swell
    right=(right+.009*np.sin(2*np.pi*71.8*t))*swell
    score=np.column_stack([left,right])
    # Six self-generated relay clicks. No sampled or licensed audio is used.
    for sec in (9.6,16.8,24.0,45.6,49.6,53.6,55.2):
        n0=int(sec*SR); n=min(int(.055*SR),len(t)-n0)
        if n>0:
            z=np.arange(n)/SR; click=.055*np.sin(2*np.pi*1150*z)*np.exp(-z*95)
            score[n0:n0+n,0]+=click; score[n0:n0+n,1]+=click*.9
    score_path=ROOT/'assets'/'score.wav'; write_wav(score_path,score)
    ffmpeg=os.environ.get('FFMPEG','ffmpeg')
    narration=ROOT/'assets'/'narration.wav'; output=ROOT/'assets'/'final_mix.wav'
    cmd=[ffmpeg,'-y','-hide_banner','-i',str(narration),'-i',str(score_path),'-filter_complex','[0:a]aresample=48000,aformat=channel_layouts=stereo[v];[1:a]aformat=channel_layouts=stereo[m];[v][m]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-16:TP=-1:LRA=11:linear=true:print_format=summary[out]','-map','[out]','-c:a','pcm_s16le','-ar','48000',str(output)]
    subprocess.run(cmd,check=True)
    print(f'Wrote original procedural drone {score_path} and normalized mix {output}')
if __name__=='__main__': main()
