#!/usr/bin/env python3
"""Original synthesized ambient pulse; no sampled or licensed source audio."""
import math, wave
import numpy as np
sr=48000; duration=60; block=48000
with wave.open('../assets/original-score.wav','wb') as w:
 w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
 for start in range(0,sr*duration,block):
  ix=np.arange(start,min(start+block,sr*duration),dtype=np.float64); t=ix/sr
  fade=np.minimum(1,t/1.8)*np.minimum(1,(duration-t)/2.2)
  beat=np.maximum(0,np.sin(2*np.pi*1.5*t))**12
  pulse=np.sin(2*np.pi*(55+4*np.sin(t*.19))*t)*(.07+.09*beat)
  pad=(np.sin(2*np.pi*110*t)+.45*np.sin(2*np.pi*164.81*t)+.25*np.sin(2*np.pi*220*t))*.035
  ticks=np.maximum(0,np.sin(2*np.pi*3*t))**36*.055
  # Drop out at the narrative pause, then resolve into a sustained final chord.
  drop=np.where((t>30)&(t<34),.12,1.0)
  swell=np.where(t>40,1.14,1.0)
  mono=(pulse+pad+ticks)*fade*drop*swell
  l=mono*(.96+.04*np.sin(t*.25)); r=mono*(.96-.04*np.sin(t*.25))
  out=np.column_stack((l,r)); w.writeframes(np.clip(out*32767,-32768,32767).astype('<i2').tobytes())
