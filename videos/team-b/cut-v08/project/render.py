#!/usr/bin/env python3
"""Procedural nursery-horror illustration, karaoke captions and 1080x1920 H.264."""
import argparse, csv, math, os, pathlib, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W,H,FPS,SECONDS=1080,1920,30,60
SLOT=SECONDS/25
NAVY=(11,16,32); BLUE=(14,21,38); AMBER=(245,197,66); CAP_AMBER=(245,209,78)
WHITE=(245,244,238); RED=(226,69,60); GREEN=(124,242,156); SKIN=(226,163,138)
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
CAPTIONS=[
 '2:13 A.M. NURSERY','PARENT CHECKS MONITOR','BABY SLEEPS','YOU COUNT WHAT YOU HEAR',
 'ONE: RADIATOR TICKS','PARENT HEARS IT','TWO: CRIB GROANS','HEARD THAT, TOO',
 'TWO SOUNDS HAPPENED','MONITOR REPORTS THREE','THREE: LATCH TURNS','DOOR STAYS SHUT',
 "BABY'S HAND OPENS",'ONE FINGER CURLS','SHE TURNS TO LENS','NOW IT NAMES THE PARENT',
 'THEIR THUMB COVERS GLASS','PARENT STANDS OUTSIDE','LENS FACES THE CHILD',"VOICE ISN'T INSIDE",
 'BESIDE THE REFLECTION','ON THIS SIDE OF GLASS',"NOT THE CHILD'S SIDE",'REACH FOR THE PLUG',
 'THE MONITOR GOES QUIET']
SCENES=['wide','monitor','crib','rule','radiator','meter','crib','meter2','counter','monitor3','latch','door','hand','finger','turn','lens','thumb','split','lenschild','reveal','reflection','boundary','childside','plug','quiet']

def read_cues(path):
 rows=[]
 with open(path,newline='') as f:
  for r in csv.DictReader(f): rows.append((float(r['voice_start_s']),float(r['voice_end_s']),r['text']))
 if len(rows)!=25: raise ValueError(f'expected 25 voice cues, got {len(rows)}')
 return rows

def make_bg():
 y,x=np.mgrid[0:H,0:W].astype(np.float32)
 rad=np.sqrt(((x-530)/760)**2+((y-690)/1150)**2)
 glow=np.exp(-rad*rad*2.1)
 lamp=np.exp(-(((x-520)/390)**2+((y-700)/500)**2)*2.0)
 a=np.zeros((H,W,3),np.uint8)
 a[:,:,0]=np.clip(NAVY[0]+12*glow+15*lamp,0,255)
 a[:,:,1]=np.clip(NAVY[1]+22*glow+17*lamp,0,255)
 a[:,:,2]=np.clip(NAVY[2]+38*glow+9*lamp,0,255)
 vign=np.clip(1-.48*np.maximum(0,rad-.25),.44,1)
 a=(a*vign[:,:,None]).astype(np.uint8)
 return Image.fromarray(a,'RGB')

FONT_CACHE={}
def font(size,bold=True):
 k=(size,bold)
 if k not in FONT_CACHE: FONT_CACHE[k]=ImageFont.truetype(BOLD if bold else REG,size)
 return FONT_CACHE[k]

def roundrect(d,box,fill,outline=None,width=1,r=24):
 d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)

def draw_room(d,glow=0.0):
 # Preserve the underlying radial gradient; add only a darker ceiling band.
 d.polygon([(0,0),(W,0),(W,250),(0,250)],fill=(12,18,35))
 # Moon window: a warm, softly glowing rectangle with blue panes.
 d.rectangle((120,235,450,580),fill=(34,50,79),outline=(85,98,125),width=8)
 d.line((285,240,285,575),fill=(78,91,116),width=6); d.line((125,410,445,410),fill=(78,91,116),width=6)
 d.ellipse((160,275,235,350),fill=(239,207,144))
 for sx,sy in [(525,310),(730,430),(850,270),(650,205)]: d.ellipse((sx,sy,sx+5,sy+5),fill=(104,126,159))
 # Floor and skirting.
 d.rectangle((0,1510,W,H),fill=(9,13,26)); d.polygon([(0,1510),(W,1510),(W,1585),(0,1585)],fill=(19,25,42))
 # The base image already contains a smooth radial amber lamp glow and dark vignette.

def draw_crib(d,phase=0.0,turned=False):
 # Bed frame, blanket, mattress and simple geometric sleeping infant.
 d.rectangle((235,1020,875,1455),fill=(18,25,42),outline=(102,119,146),width=12)
 d.rectangle((255,1070,855,1370),fill=(92,113,151))
 bshift=int(10*math.sin(phase*math.tau))
 d.rounded_rectangle((272,1165+bshift,840,1374+bshift),radius=48,fill=(41,57,90))
 d.ellipse((365,935,660,1225),fill=(238,199,174))
 # Ear and cap silhouette; minimal face, no realistic hands.
 d.pieslice((350,915,675,1210),180,360,fill=(33,35,49))
 eyex=505+(-28 if turned else 0)
 d.ellipse((eyex-40,1055,eyex-21,1074),fill=(39,37,42)); d.ellipse((eyex+28,1055,eyex+47,1074),fill=(39,37,42))
 d.arc((eyex-28,1080,eyex+38,1125),5,170,fill=(123,77,69),width=5)
 # Neat crib slats, strong vector construction.
 for xx in range(275,850,72): d.rounded_rectangle((xx,1000,xx+11,1440),radius=5,fill=(124,139,164))
 d.rectangle((220,980,890,1015),fill=(136,152,177)); d.rectangle((220,1438,890,1470),fill=(136,152,177))

def draw_monitor(d,phase=0.0,mode=0):
 roundrect(d,(290,395,790,1120),(4,9,20),outline=(84,103,133),width=10,r=42)
 roundrect(d,(325,445,755,1042),(8,19,31),outline=(29,54,71),width=4,r=20)
 d.ellipse((520,412,560,452),fill=(22,35,50),outline=(115,135,155),width=3)
 # Tiny camera view window.
 d.rectangle((350,470,730,780),fill=(17,29,46))
 d.rectangle((350,695,730,780),fill=(22,31,44))
 d.rectangle((390,620,690,720),fill=(31,49,75))
 d.ellipse((465,570,565,670),fill=(225,179,151)); d.arc((454,560,575,660),180,360,fill=(39,38,47),width=15)
 # Green waveform is one intentionally moving detail.
 d.line((380,840,700,840),fill=(44,89,88),width=3)
 for j in range(35):
  xx=390+j*8; amp=8+int(30*abs(math.sin(j*.73+phase*math.tau)))
  d.line((xx,840-amp,xx,840+amp),fill=(85,197,148),width=3)
 if mode>=2:
  d.text((380,910),'SOUNDS  2 / 3',font=font(31),fill=(216,223,214))
 # Receiver LED.
 d.ellipse((680,450,700,470),fill=GREEN if math.sin(phase*math.tau)>0 else (24,74,58))

def draw_door(d,phase=0.0,open_door=False):
 d.rectangle((330,330,795,1520),fill=(5,9,20),outline=(77,90,116),width=18)
 d.rectangle((365,365,760,1485),fill=(23,32,51))
 if open_door:
  d.polygon([(368,370),(565,420),(565,1410),(368,1485)],fill=(41,37,54),outline=(127,108,93))
  d.polygon([(570,415),(755,365),(755,1480),(570,1410)],fill=(92,73,49))
 else:
  d.rectangle((385,390,740,1460),fill=(21,31,51),outline=(49,63,86),width=5)
 d.ellipse((690,915,726,951),fill=(218,177,93))
 # Latch tongue subtly shifts; door remains shut for the false report.
 off=int(9*math.sin(phase*math.tau))
 d.rectangle((713+off,885,753+off,912),fill=(156,161,165))

def draw_parent(d,alpha=220,side='right'):
 # Abstract, faceless parent silhouette; all shapes are vector-drawn.
 x0=710 if side=='right' else 80
 d.ellipse((x0+60,520,x0+270,750),fill=(42,36,48))
 d.rounded_rectangle((x0,700,x0+370,1580),radius=140,fill=(17,22,38))
 d.ellipse((x0+105,545,x0+235,690),fill=(102,76,80))
 d.ellipse((x0+143,600,x0+153,610),fill=(180,146,130)); d.ellipse((x0+190,600,x0+200,610),fill=(180,146,130))

def base_scene(i,phase):
 im=BASE.copy(); dr=ImageDraw.Draw(im); draw_room(dr,phase)
 scene=SCENES[i]
 if scene in ('wide','crib','rule','radiator','meter','meter2','counter','monitor3','hand','finger','turn','lenschild','childside'):
  draw_crib(dr,phase,turned=scene in ('turn','lenschild'))
 if scene in ('monitor','rule','meter','meter2','counter','monitor3','lens','thumb','split','reveal','reflection','boundary','plug','quiet'):
  draw_monitor(dr,phase,mode=2 if scene in ('counter','monitor3','reveal') else 0)
 if scene in ('latch','door','wide'): draw_door(dr,phase,open_door=False)
 if scene=='radiator':
  roundrect(dr,(650,700,920,1010),(23,34,49),outline=(89,102,119),width=8,r=20)
  for xx in range(690,900,35): dr.rounded_rectangle((xx,735,xx+14,975),radius=6,fill=(121,134,151))
 if scene in ('meter','meter2','counter','monitor3'):
  roundrect(dr,(120,790,560,930),(4,9,18),outline=(52,75,93),width=4,r=18)
  dr.line((150,860,530,860),fill=(43,86,87),width=3)
  for k in range(3):
   xx=205+k*105; amp=33 if k<2 or phase>.78 else 7
   dr.line((xx,860-amp,xx,860+amp),fill=GREEN if k<2 else AMBER,width=7)
 if scene in ('door','latch'):
  draw_door(dr,phase,open_door=False)
 if scene in ('hand','finger'):
  # Tiny, deliberately abstract mitten-like infant silhouette; no anatomical hand rendering.
  dr.ellipse((705,1110,820,1215),fill=(229,183,159),outline=(249,214,185),width=5)
  if scene=='finger': dr.line((770,1150,826,1105),fill=(239,205,180),width=20)
 if scene in ('thumb','split','reflection','boundary','reveal','plug'):
  draw_parent(dr,alpha=150 if scene=='thumb' else 220,side='right')
 if scene=='split':
  dr.rectangle((535,300,545,1510),fill=(245,209,78));
 if scene in ('lens','lenschild'):
  dr.ellipse((480,305,600,425),outline=(119,228,169),width=7)
  dr.ellipse((515,340,565,390),fill=(17,31,45),outline=(177,226,196),width=5)
 if scene=='reveal':
  dr.ellipse((474,300,606,432),outline=RED,width=9)
 if scene=='boundary':
  dr.rectangle((520,300,545,1510),fill=(224,69,60))
 if scene=='plug':
  dr.line((430,1050,710,1050),fill=(117,130,150),width=14)
  roundrect(dr,(350,1028,435,1073),(210,214,220),r=18)
 if scene=='quiet':
  dr.rectangle((390,875,690,884),fill=(26,47,58))
 # Permanent tiny clock and recorder tag anchor the format without overwhelming the art.
 dr.text((74,95),'NIGHT NURSERY  /  CAM 01',font=font(28,False),fill=(151,171,194))
 if i < 19: dr.text((818,96),'2:13',font=font(35,True),fill=(225,206,166))
 return im

BASE=make_bg()

def draw_dynamic(im,i,local):
 d=ImageDraw.Draw(im)
 pulse=(math.sin(local*math.tau/1.2)+1)/2
 # One small motion cue per shot; never add an unreported diegetic sound.
 x,y= [(775,1010),(690,452),(865,1250),(700,1000),(882,855),(530,860),(875,1390),(520,860),(520,860),(520,860),(725,898),(720,900),(760,1160),(780,1150),(510,1020),(540,430),(780,710),(880,1250),(540,370),(540,370),(800,680),(540,540),(750,1120),(392,1050),(540,860)][i]
 r=5+int(5*pulse)
 if i in (0,1,3,5,8,9,15,19,24):
  col=RED if i==19 else (GREEN if i in (1,5,8,9,15) else AMBER)
  d.ellipse((x-r,y-r,x+r,y+r),fill=col)
 elif i==2:
  d.line((365,1300+int(7*pulse),655,1300+int(7*pulse)),fill=(150,170,202),width=5)
 elif i==4:
  d.ellipse((850-r,840-r,850+r,840+r),fill=AMBER)
 elif i==6:
  d.line((290,1010,290+int(35*pulse),1010),fill=(235,206,152),width=5)
 elif i==10:
  d.ellipse((710-r,898-r,710+r,898+r),fill=(226,207,158))
 elif i==11:
  d.line((368,1070,368+int(10*pulse),1070),fill=(123,150,189),width=5)
 elif i==12:
  d.ellipse((790-r,1150-r,790+r,1150+r),fill=(230,185,157))
 elif i==13:
  d.line((777,1150,777+int(16*pulse),1142),fill=(246,206,179),width=8)
 elif i==14:
  d.ellipse((535-r,1045-r,535+r,1045+r),fill=GREEN)
 elif i==16:
  # Reflected silhouette blooms, not an anatomical hand.
  d.ellipse((827-r,750-r,827+r,750+r),fill=(93,92,104))
 elif i==17:
  d.ellipse((827-r,690-r,827+r,690+r),fill=(132,99,89))
 elif i==18:
  d.ellipse((540-r,380-r,540+r,380+r),outline=(172,228,193),width=4)
 elif i==20:
  d.ellipse((822-r,745-r,822+r,745+r),outline=(245,209,78),width=5)
 elif i==21:
  d.line((540,320,540,900+int(50*pulse)),fill=(239,99,79),width=6)
 elif i==22:
  d.ellipse((500-r,1020-r,500+r,1020+r),outline=(93,153,171),width=4)
 elif i==23:
  d.ellipse((425-r,1050-r,425+r,1050+r),fill=(245,209,78))


def draw_caption(im,i,t,cues):
 caption=CAPTIONS[i]
 voice_start,voice_end,spoken=cues[i]
 # Use spoken word count to advance karaoke tint through the corresponding caption phrase.
 words=caption.split(); elapsed=max(0,t-voice_start); dur=max(.05,voice_end-voice_start)
 active=min(len(words)-1,int(elapsed/dur*len(words)))
 col=RED if i==19 else CAP_AMBER
 d=ImageDraw.Draw(im)
 # first shot has separate time stamp at upper third
 if i==0:
  d.text((85,250),'2:13 A.M.',font=font(78,True),fill=AMBER,stroke_width=2,stroke_fill=(43,32,22))
 # Draw at 82 px, then compress horizontally into the central 84% safe width.
 # This keeps tall caption glyphs while giving the sans face a condensed treatment.
 size=82; f=font(size,True); widths=[f.getlength(w) for w in words]
 gap=int(size*.22); total=sum(widths)+gap*(len(words)-1)
 line=Image.new('RGBA',(int(total)+8,112),(0,0,0,0)); ld=ImageDraw.Draw(line); x=4
 for j,w in enumerate(words):
  color=col if j==active else WHITE
  ld.text((int(x),0),w,font=f,fill=color,stroke_width=1,stroke_fill=(4,7,12))
  x+=widths[j]+gap
 scale=min(1.0,860/line.width)
 if scale<1: line=line.resize((860,112),Image.Resampling.LANCZOS)
 box=(86,1430,994,1585)
 d.rounded_rectangle(box,radius=28,fill=(3,7,16),outline=(53,67,86),width=2)
 im.paste(line,((W-line.width)//2,1452),line)
 # The sequel hook is a tiny visual-only indicator after the last spoken phrase.
 if i==24 and t>59.54:
  d.text((W-355,1620),'HALL MIC: LIVE',font=font(26,True),fill=GREEN)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--ffmpeg',default='ffmpeg'); ap.add_argument('--out',default='/tmp/cut-v08-build/picture.mp4'); ap.add_argument('--cues',default='project/voice_cues.csv'); args=ap.parse_args()
 cues=read_cues(args.cues); pathlib.Path(args.out).parent.mkdir(parents=True,exist_ok=True)
 cmd=[args.ffmpeg,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','ultrafast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',args.out]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for n in range(FPS*SECONDS):
  t=n/FPS; i=min(24,int(t/SLOT)); local=(t-i*SLOT)/SLOT
  base=base_scene(i,local); draw_dynamic(base,i,local)
  ease=(1-math.cos(math.pi*local))/2; zoom=1+0.06*ease
  cw,ch=int(W/zoom),int(H/zoom); left=(W-cw)//2; top=(H-ch)//2
  frame=base.crop((left,top,left+cw,top+ch)).resize((W,H),Image.Resampling.LANCZOS)
  draw_caption(frame,i,t,cues)
  # Fine, restrained deterministic night-vision sensor noise, never a static/noisy stock texture.
  if n%2==0:
   d=ImageDraw.Draw(frame); seed=(n*2654435761)&0xffffffff
   rng=np.random.default_rng(seed)
   for _ in range(18):
    xx=int(rng.integers(20,W-20)); yy=int(rng.integers(20,H-20)); d.point((xx,yy),fill=(35,50,63))
  p.stdin.write(frame.tobytes())
  if n%300==0: print(f'picture frames {n}/{FPS*SECONDS}',flush=True)
 p.stdin.close(); rc=p.wait()
 if rc: raise SystemExit(rc)
 print(f'Wrote {args.out}: {FPS*SECONDS} frames, {W}x{H}, {FPS} fps')

if __name__=='__main__': main()
