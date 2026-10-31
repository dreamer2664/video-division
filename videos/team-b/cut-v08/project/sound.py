#!/usr/bin/env python3
"""Generate original 48 kHz stereo drone and the two real nursery sounds."""
import argparse, pathlib, wave
import numpy as np
SR=48000; D=60; BLOCK=48000

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out',default='/tmp/cut-v08-build/score.wav'); a=ap.parse_args()
 out=pathlib.Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
 with wave.open(str(out),'wb') as w:
  w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
  for st in range(0,SR*D,BLOCK):
   ix=np.arange(st,min(st+BLOCK,SR*D),dtype=np.float64); t=ix/SR
   # Low, slow, original score bed. Soft modulation changes color without introducing extra diegetic ticks.
   mod=.78+.22*np.sin(2*np.pi*.035*t)
   drone=.025*np.sin(2*np.pi*42.0*t)+.018*np.sin(2*np.pi*(55+1.4*np.sin(2*np.pi*.022*t))*t)+.009*np.sin(2*np.pi*82*t)
   shimmer=.004*np.sin(2*np.pi*(173+5*np.sin(2*np.pi*.08*t))*t)
   bed=(drone*mod+shimmer)
   # Sparse cinematic sub swells under transitions, not diegetic report sounds.
   for when in (7.2,19.2,21.6,36.0,43.2,45.6,55.2):
    q=t-when; hit=(q>=0)&(q<.48); bed+=hit*.035*np.sin(2*np.pi*(48-16*np.maximum(q,0))*np.maximum(q,0))*np.exp(-7*np.maximum(q,0))
   # Two verifiable diegetic sounds only: radiator tick (shot 5), crib wood groan (shot 7).
   q=t-9.60; hit=(q>=0)&(q<.16); bed+=hit*.105*np.sin(2*np.pi*780*np.maximum(q,0))*np.exp(-31*np.maximum(q,0))
   q=t-14.40; hit=(q>=0)&(q<.42); freq=155-100*np.clip(q,0,.42)/.42
   bed+=hit*.075*np.sin(2*np.pi*freq*np.maximum(q,0))*np.exp(-9*np.maximum(q,0))
   # A light breath of generated noise, panned gently, gives the nursery a physical floor.
   rng=np.random.default_rng(st//BLOCK+731)
   noise=rng.standard_normal(len(t))*0.0008
   fade=np.minimum(1,t/1.2)*np.minimum(1,(D-t)/1.0)
   mono=np.clip((bed+noise)*fade,-.35,.35)
   pan=.025*np.sin(2*np.pi*.04*t)
   left=mono*(1-pan); right=mono*(1+pan)
   pcm=np.column_stack((left,right))
   w.writeframes(np.clip(pcm*32767,-32768,32767).astype('<i2').tobytes())
 print(f'Wrote original score/SFX {out}: {D}s, {SR} Hz stereo PCM')
if __name__=='__main__': main()
