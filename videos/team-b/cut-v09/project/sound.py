#!/usr/bin/env python3
"""Synthesize an original drone, duck it under narration, and normalize the master."""
import os, pathlib, subprocess, wave
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
SR=48000; DUR=60

def write_wav(path,x):
    pcm=(np.clip(x,-1,1)*32767).astype('<i2')
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

def main():
    t=np.arange(SR*DUR,dtype=np.float64)/SR
    sweep=38+1.4*np.sin(2*np.pi*t/17.0)
    phase=2*np.pi*np.cumsum(sweep)/SR
    left=.040*np.sin(phase)+.018*np.sin(2*np.pi*52.0*t+.35*np.sin(2*np.pi*t/23))
    right=.040*np.sin(phase+.12)+.018*np.sin(2*np.pi*50.7*t+.35*np.sin(2*np.pi*t/23))
    swell=.70+.30*(.5+.5*np.sin(2*np.pi*t/12.0))
    left=(left+.010*np.sin(2*np.pi*73.4*t))*swell
    right=(right+.009*np.sin(2*np.pi*71.8*t))*swell
    score=np.column_stack([left,right])
    for sec in (9.6,16.8,24.0,45.6,49.6,53.6,55.2):
        n0=int(sec*SR); n=min(int(.055*SR),len(t)-n0)
        if n>0:
            z=np.arange(n)/SR; click=.055*np.sin(2*np.pi*1150*z)*np.exp(-z*95)
            score[n0:n0+n,0]+=click; score[n0:n0+n,1]+=click*.9
    # Side-chain the synthesized bed to a 10 dB RMS margin in 100ms voiced blocks.
    with wave.open(str(ROOT/'assets'/'narration.wav'),'rb') as w:
        speech=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float64)/32768
        speech=np.repeat(speech,2)
    block=SR//10; centers=[]; gains=[]
    for start in range(0,len(speech),block):
        end=min(start+block,len(speech))
        vr=float(np.sqrt(np.mean(speech[start:end]**2)))
        mr=float(np.sqrt(np.mean(np.mean(score[start:end]**2,axis=1))))
        gains.append(min(1.0,vr/(mr*10**.5)) if vr>.008 and mr>0 else 1.0)
        centers.append((start+end-1)/2)
    env=np.interp(np.arange(len(t)),centers,gains,left=gains[0],right=gains[-1])
    env=np.convolve(env,np.ones(3)/3,mode='same')
    score*=env[:,None]
    score_path=ROOT/'assets'/'score.wav'; write_wav(score_path,score)
    ffmpeg=os.environ.get('FFMPEG','ffmpeg')
    output=ROOT/'assets'/'final_mix.wav'
    filtergraph='[0:a]aresample=48000,aformat=channel_layouts=stereo[v];[1:a]aformat=channel_layouts=stereo[m];[v][m]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:print_format=summary[out]'
    cmd=[ffmpeg,'-y','-hide_banner','-i',str(ROOT/'assets'/'narration.wav'),'-i',str(score_path),'-filter_complex',filtergraph,'-map','[out]','-c:a','pcm_s16le','-ar','48000',str(output)]
    subprocess.run(cmd,check=True)
    print(f'Wrote generated drone {score_path}; 10dB active-voice duck target; normalized mix {output}')
if __name__=='__main__': main()
