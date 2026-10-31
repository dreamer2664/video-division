#!/usr/bin/env python3
"""Original Ward Ten drone, call bells, printer ticks and sub hits. No reference samples."""
import argparse,wave
from pathlib import Path
import numpy as np
SR=48000; N=60*SR

def write(path,a):
    pcm=np.clip(a*32767,-32768,32767).astype('<i2')
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    t=np.arange(N,dtype=np.float32)/SR
    env=(.67+.19*np.sin(2*np.pi*t/23)+.09*np.sin(2*np.pi*t/41))*np.minimum(1,.32+t/1.3)*np.minimum(1,np.maximum(.18,(60-t)/1.4))
    rise=1+.20*np.clip((t-28)/18,0,1)
    drone=(.070*np.sin(2*np.pi*49*t+.11*np.sin(2*np.pi*t/21))+
           .025*np.sin(2*np.pi*73.416*t)+.015*np.sin(2*np.pi*98*t+.35*np.sin(t*.06)))
    side=.010*np.sin(2*np.pi*49.27*t+.3)
    music=np.stack([(drone+side)*env*rise,(drone-side)*env*rise],axis=1)
    f=np.zeros(N,dtype=np.float32);rng=np.random.default_rng(20261008)
    def add(at,signal):
        i=round(at*SR);n=min(len(signal),N-i)
        if i>=0 and n>0:f[i:i+n]+=signal[:n].astype(np.float32)
    # Quiet clock rhythm is independent from the sparse bedside call bell.
    for at in np.arange(.82,59.5,2.0):
        q=np.arange(int(.04*SR),dtype=np.float32)/SR
        add(float(at),.025*np.sin(2*np.pi*1800*q)*np.exp(-q*115)+.006*rng.standard_normal(len(q))*np.exp(-q*135))
    # A short dry two-part electronic call bell, composed for this film.
    for at in [11.26,13.30,24.91,54.20,56.25]:
        q=np.arange(int(.30*SR),dtype=np.float32)/SR
        bell=(.048*np.sin(2*np.pi*660*q)+.027*np.sin(2*np.pi*990*q))*np.exp(-q*15)
        add(at,bell)
    # Soft printer/relay mechanisms and sparse low impacts.
    for at in [35.25,36.12,37.35,37.75]:
        q=np.arange(int(.16*SR),dtype=np.float32)/SR
        noise=rng.standard_normal(len(q)).astype(np.float32)
        add(at,.007*np.r_[0,np.diff(noise)]*np.exp(-q*25))
    for at in [4.0,9.8,15.2,25.0,34.9,39.7,41.4,42.1,46.8,54.2,57.3]:
        q=np.arange(int(.25*SR),dtype=np.float32)/SR
        add(at,.090*np.sin(2*np.pi*(58*q-28*q*q))*np.exp(-q*18))
    write(a.out/'music.wav',music);write(a.out/'sfx.wav',np.stack([f,f],axis=1))
    print('Original 60-second drone and hospital call/printer foley synthesized.')
if __name__=='__main__':main()
