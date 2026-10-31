#!/usr/bin/env python3
"""Synthesize original drone and dry foley, no samples or reference audio."""
import argparse,wave
from pathlib import Path
import numpy as np
SR=48000; DURATION=60; N=SR*DURATION

def write_wav(path,stereo):
    pcm=np.clip(stereo*32767,-32768,32767).astype('<i2')
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    t=np.arange(N,dtype=np.float32)/SR
    slow=.65+.20*np.sin(2*np.pi*t/21)+.12*np.sin(2*np.pi*t/39)
    rise=1+.22*np.clip((t-26)/20,0,1)
    fadein=np.minimum(1,.35+t/1.1);fadeout=np.minimum(1,np.maximum(.18,(60-t)/1.4))
    drone=(.075*np.sin(2*np.pi*55*t+.16*np.sin(2*np.pi*t/18))+
           .028*np.sin(2*np.pi*82.407*t)+.016*np.sin(2*np.pi*110*t+.3*np.sin(t*.08)))
    side=.012*np.sin(2*np.pi*55.23*t+.2)
    bed=(slow*rise*fadein*fadeout).astype(np.float32)
    music=np.stack([(drone+side)*bed,(drone-side)*bed],axis=1).astype(np.float32)
    # All foley is synthesized from elementary oscillators/noise, with a fixed seed.
    sfx=np.zeros(N,dtype=np.float32);rng=np.random.default_rng(71213)
    def add(at,signal):
        i=round(at*SR);n=min(len(signal),N-i)
        if i>=0 and n>0:sfx[i:i+n]+=signal[:n].astype(np.float32)
    # Dry clock tick, deliberately sparse (one every 2.4 seconds).
    for tick in np.arange(.72,59.5,2.4):
        q=np.arange(int(.04*SR),dtype=np.float32)/SR
        sample=.036*np.sin(2*np.pi*1800*q)*np.exp(-q*110)
        sample+=.008*rng.standard_normal(len(q))*np.exp(-q*130)
        add(float(tick),sample)
    # Original low mechanical impacts / heartbeat at narrative changes.
    for moment in [4.8,16.85,24.05,29.75,40.8,42.25,43.45,45.6,51.4,57.6]:
        q=np.arange(int(.24*SR),dtype=np.float32)/SR
        phase=2*np.pi*(64*q-35*q*q); add(moment,.095*np.sin(phase)*np.exp(-q*18))
    # Short lift-relay clicks and soft pen marks; no source audio.
    for moment in [3.05,17.10,24.35,30.1,51.45]:
        q=np.arange(int(.16*SR),dtype=np.float32)/SR
        add(moment,.023*np.sin(2*np.pi*(750*q+400*q*q))*np.exp(-q*35))
    for moment in [21.9,28.75,31.65,32.05]:
        q=np.arange(int(.12*SR),dtype=np.float32)/SR
        raw=rng.standard_normal(len(q)).astype(np.float32);crisp=np.r_[0,np.diff(raw)]
        add(moment,.006*crisp*np.exp(-q*24))
    foley=np.stack([sfx,sfx],axis=1)
    write_wav(args.out/'music.wav',music);write_wav(args.out/'sfx.wav',foley)
    print('Original 60-second music and dry foley synthesized from sinusoids and seeded noise.')
if __name__=='__main__':main()
