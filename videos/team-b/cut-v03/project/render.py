#!/usr/bin/env python3
"""Generate The Quiet Signal: procedural city-light imagery, 1080p30 raw frames."""
import math, os, subprocess, sys
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
W,H,FPS,SECONDS=1920,1080,30,60
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
scenes=[(0,5,'SOMEWHERE, A SIGNAL.',55),(5,12,'ONE LIGHT.',58),(12,20,'THEN ANOTHER.',58),(20,30,'DISTANCE BECOMES A PATTERN.',47),(30,40,'A PAUSE IS NOT AN END.',50),(40,51,'WE ANSWER BY NOTICING.',52),(51,56,'KEEP THE SIGNAL MOVING.',48),(56,60,'THE QUIET SIGNAL  ·  CUT V03',40)]
# Timestamp narration is intentionally absent; captions are the original on-screen copy.
cmd=[sys.argv[1] if len(sys.argv)>1 else 'ffmpeg','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','ultrafast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart','-an','picture.mp4']
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
font_cache={}
def font(sz):
 if sz not in font_cache: font_cache[sz]=ImageFont.truetype(BOLD,sz)
 return font_cache[sz]
# Precomputed urban grid, viewed through a slow, shifting crop with pulse-driven light.
y,x=np.mgrid[0:H,0:W].astype(np.float32)
for n in range(FPS*SECONDS):
 t=n/FPS
 # Deep navy atmospheric base, gently shifting aurora gradient.
 glow=np.exp(-((x-(960+260*math.sin(t*.11)))**2/(2*700**2)+(y-480)**2/(2*420**2)))
 frame=np.zeros((H,W,3),np.uint8); frame[:,:,0]=np.clip(27+43*glow,0,255); frame[:,:,1]=np.clip(13+24*glow,0,255); frame[:,:,2]=np.clip(10+14*glow,0,255)
 # Perspective-like city blocks, sparse hairline grid, moving scan line.
 shift=int((t*14)%120)
 for xx in range(-120+shift,W,120): cv2.line(frame,(xx,0),(xx,H),(30,47,66),1,cv2.LINE_AA)
 for yy in range(40,H,100): cv2.line(frame,(0,yy),(W,yy),(30,47,66),1,cv2.LINE_AA)
 # Windows pulse across block faces; deterministic layout and time-varying intensity.
 for row in range(1,10):
  yy=row*100+25
  for col in range(16):
   xx=col*120+24
   dist=abs((col*0.8+row*0.32)-(t*1.7%20))
   phase=math.sin(t*1.7-col*.37-row*.61)
   active=(phase>.22) or dist<1.4
   if active:
    c=(min(255,int(190+60*max(0,phase))),min(255,int(145+65*max(0,phase))),min(255,int(115+80*max(0,phase))))
    cv2.rectangle(frame,(xx,yy),(xx+9,yy+22),c,-1,cv2.LINE_AA)
 # Signal pulse sweeps; warm orange core and soft glow.
 px=int(160+((t*180)%1600)); py=int(260+240*math.sin(t*.31))
 if 30<=t<40: px=int(850+26*math.sin(t*2.2))
 cv2.circle(frame,(px,py),38,(20,90,185),-1,cv2.LINE_AA)
 cv2.circle(frame,(px,py),19,(35,145,245),-1,cv2.LINE_AA)
 cv2.circle(frame,(px,py),7,(80,225,255),-1,cv2.LINE_AA)
 # Connecting trajectory becomes visible in development and opening up to wide.
 if t>=12:
  pts=np.array([[130,py+120],[460,py+20],[800,py+85],[1160,py-40],[1770,py+50]],np.int32)
  cv2.polylines(frame,[pts],False,(90,118,130),2,cv2.LINE_AA)
 # Text overlays, fading only by alpha, 40+ px actual glyph sizing.
 title=next((s for a,b,s,z in scenes if a<=t<b), '')
 size=next((z for a,b,s,z in scenes if a<=t<b), 48)
 im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)); d=ImageDraw.Draw(im)
 box=d.textbbox((0,0),title,font=font(size)); tw=box[2]-box[0]
 start=next(a for a,b,s,z in scenes if a<=t<b); end=next(b for a,b,s,z in scenes if a<=t<b)
 alpha=min(1,(t-start)/.25,(end-t)/.25)
 # Dark translucent backing keeps typography readable without masking the composition.
 top=H-152
 d.rounded_rectangle((115,top-17,132+tw,top+size+21),radius=12,fill=(4,10,21,215))
 # Composite for alpha support.
 overlay=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(overlay)
 od.text((132,top),title,font=font(size),fill=(245,248,252,int(255*max(.0,min(1,alpha)))))
 im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB')
 p.stdin.write(cv2.cvtColor(np.asarray(im),cv2.COLOR_RGB2BGR).tobytes())
 if n%300==0: print(f'frames {n}/{FPS*SECONDS}',flush=True)
p.stdin.close(); rc=p.wait()
if rc: raise SystemExit(rc)
