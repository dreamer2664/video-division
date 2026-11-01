#!/usr/bin/env python3
"""Original PERFECT TIME drone, queue beeps, headset clicks and relay effects."""
import argparse,wave
from pathlib import Path
import numpy as np
SR=48000;N=60*SR

def write(path,a):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
        w.writeframes(np.clip(a*32767,-32768,32767).astype('<i2').tobytes())

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    t=np.arange(N,dtype=np.float32)/SR
    env=(.64+.14*np.sin(2*np.pi*t/19)+.11*np.sin(2*np.pi*t/37))*np.minimum(1,.25+t/1.6)*np.minimum(1,np.maximum(.2,(60-t)/1.8))
    tension=1+.22*np.clip((t-27)/20,0,1)
    core=(.060*np.sin(2*np.pi*55*t+.14*np.sin(2*np.pi*t/17))+
          .023*np.sin(2*np.pi*82.41*t)+.014*np.sin(2*np.pi*110*t+.22*np.sin(t*.07)))
    side=.009*np.sin(2*np.pi*55.32*t+.7)
    music=np.stack([(core+side)*env*tension,(core-side)*env*tension],axis=1)
    sfx=np.zeros(N,dtype=np.float32);rng=np.random.default_rng(20261109)
    def add(at,s):
        i=round(at*SR);n=min(len(s),N-i)
        if i>=0 and n>0:sfx[i:i+n]+=np.asarray(s[:n],dtype=np.float32)
    # Sparse low electronic ticks mark the queue; all effects are procedural.
    for at in np.arange(.95,59.3,2.0):
        q=np.arange(int(.035*SR),dtype=np.float32)/SR
        add(float(at),.024*np.sin(2*np.pi*1350*q)*np.exp(-q*125)+.004*rng.standard_normal(len(q))*np.exp(-q*150))
    # Short dry dual-frequency call-routing tones, not a sampled telephone.
    for at in [3.75,7.03,9.15,18.02,24.52,27.05,42.31,51.48,54.20,57.84]:
        q=np.arange(int(.18*SR),dtype=np.float32)/SR
        add(at,(.035*np.sin(2*np.pi*697*q)+.025*np.sin(2*np.pi*1209*q))*np.minimum(1,q*120)*np.exp(-q*18))
    # Headset switch/relay clicks, plus muted low impacts around status changes.
    for at in [20.2,22.52,26.46,34.20,39.1,47.1,50.64,53.3,55.6]:
        q=np.arange(int(.11*SR),dtype=np.float32)/SR
        noise=rng.standard_normal(len(q)).astype(np.float32)
        add(at,.007*np.r_[0,np.diff(noise)]*np.exp(-q*45))
    for at in [4.0,9.8,14.8,19.8,24.5,30.0,34.0,39.6,42.2,47.1,49.5,53.3,57.8]:
        q=np.arange(int(.23*SR),dtype=np.float32)/SR
        add(at,.080*np.sin(2*np.pi*(62*q-32*q*q))*np.exp(-q*18))
    write(a.out/'music.wav',music);write(a.out/'sfx.wav',np.stack([sfx,sfx],axis=1))
    print('Original 60-second call-centre drone, routing tones and relay Foley synthesized.')
if __name__=='__main__':main()
