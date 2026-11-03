#!/usr/bin/env python3
"""Deterministic, original 60-second hotel weather, bed and close Foley. No samples."""
import argparse,wave
from pathlib import Path
import numpy as np
from scipy import signal
SR=48000;N=60*SR

def wav(path,data):
    a=np.clip(data,-.999,.999)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(np.rint(a*32767).astype('<i2').tobytes())

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(2026110109);t=np.arange(N,dtype=np.float32)/SR
    # Low, slow D/Phrygian oscillators; nothing sampled from grade/reference films.
    env=(.65+.13*np.sin(2*np.pi*t/27)+.08*np.sin(2*np.pi*t/13))*np.minimum(1,.24+t/2.2)
    tension=1+.22*np.clip((t-28)/18,0,1)
    drone=(.065*np.sin(2*np.pi*36.708*t+.18*np.sin(t*.08))+.027*np.sin(2*np.pi*55*t)+
           .018*np.sin(2*np.pi*73.416*t+.2*np.sin(t*.11))+.007*np.sin(2*np.pi*77.782*t))
    side=.009*np.sin(2*np.pi*36.93*t+.5)
    music=np.stack([(drone+side)*env*tension,(drone-side)*env*tension],axis=1).astype(np.float32)
    # Textured rain in stereo, filtered and gusted as if falling on an awning outside glass.
    wn=rng.standard_normal((N,2)).astype(np.float32)
    sos=signal.butter(3,[440,7500],btype='bandpass',fs=SR,output='sos')
    rain=signal.sosfilt(sos,wn,axis=0).astype(np.float32)
    gust=(.70+.16*np.sin(2*np.pi*t/8.7)+.08*np.sin(2*np.pi*t/3.1))[:,None]
    fx=.030*rain*gust
    def add(at,s,left=1.0,right=1.0):
        i=round(at*SR);n=min(len(s),N-i)
        if i>=0 and n>0:
            fx[i:i+n,0]+=np.asarray(s[:n],np.float32)*left;fx[i:i+n,1]+=np.asarray(s[:n],np.float32)*right
    # Dry switch and receiver clicks; brief resonances, not electronic UI beeps.
    for at in (15.1,21.78,22.02,23.0,45.95,51.65):
        q=np.arange(int(.11*SR),dtype=np.float32)/SR
        n=rng.standard_normal(len(q)).astype(np.float32)
        click=(.055*n+.055*np.sin(2*np.pi*310*q))*np.exp(-q*48)
        add(at,click,.95,.82)
    # Twin metal bell partials and interrupted mechanical trill from the desk telephone.
    for at in (23.55,24.30,46.55,47.32,48.09,53.25,54.02):
        q=np.arange(int(.50*SR),dtype=np.float32)/SR
        envelope=np.minimum(1,q*90)*np.minimum(1,(.50-q)*35)
        trem=(.6+.4*np.cos(2*np.pi*19*q))
        ring=.032*(np.sin(2*np.pi*880*q)+.62*np.sin(2*np.pi*1318*q))*envelope*trem
        add(at,ring,.9,.72)
    # Lift motor enters quietly before its bell; an inharmonic metal creak persists into the pre-reveal pause.
    q=np.arange(int(6.3*SR),dtype=np.float32)/SR
    motor=.024*np.sin(2*np.pi*(82*q+2.0*np.sin(q*.55)))*np.sin(np.pi*q/6.3)**2
    add(25.05,motor,.7,1.0)
    for at in (29.25,36.75):
        q=np.arange(int(.85*SR),dtype=np.float32)/SR
        bell=.045*(np.sin(2*np.pi*704*q)+.34*np.sin(2*np.pi*1408*q))*np.exp(-q*4.7)
        add(at,bell,.73,1.0)
    q=np.arange(int(2.6*SR),dtype=np.float32)/SR
    creak=.021*np.sin(2*np.pi*(113*q+32*q*q/2)+.3*np.sin(2*np.pi*3*q))*np.sin(np.pi*q/2.6)**2
    add(36.45,creak,.8,.55)
    # Wet footfalls; filtered impacts and a short splash cluster, with long, low filmic sub hits.
    for at in (7.56,8.34,32.22,33.03,41.13):
        q=np.arange(int(.32*SR),dtype=np.float32)/SR
        wet=rng.standard_normal(len(q)).astype(np.float32)
        sos=signal.butter(2,[150,2400],btype='bandpass',fs=SR,output='sos')
        wet=signal.sosfilt(sos,wet).astype(np.float32)
        add(at,.050*wet*np.exp(-q*17)+.07*np.sin(2*np.pi*66*q)*np.exp(-q*23),.9,1.0)
    for at in (9.66,23.02,25.12,32.04,34.65,39.0,45.5):
        q=np.arange(int(1.0*SR),dtype=np.float32)/SR
        sub=.10*np.sin(2*np.pi*(53*q-12*q*q))*np.exp(-q*5.2)
        add(at,sub,1.0,1.0)
    # Long filtered thunder roll lives under the wordless reveal, not a sampled boom.
    q=np.arange(int(3.5*SR),dtype=np.float32)/SR
    thunder=signal.sosfilt(signal.butter(3,140,btype='lowpass',fs=SR,output='sos'),rng.standard_normal(len(q))).astype(np.float32)
    add(36.4,.16*thunder*np.sin(np.pi*q/3.5)**2,1.0,.85)
    wav(args.out/'music.wav',music);wav(args.out/'foley.wav',fx)
    print('Original hotel bed, awning rain, lift, telephone, switch, wet footfall and thunder synthesized.')
if __name__=='__main__':main()
