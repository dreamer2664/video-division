#!/usr/bin/env python3
"""Deterministic, cue-sheet-driven 1080x1920 proof renderer (Pillow + FFmpeg).

No reference pixels/assets are read here. The screenshot is an original schematic UI.
"""
from __future__ import annotations
import argparse, json, math, re, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W,H=1080,1920; FPS=30
INK=(25,35,57); CREAM=(250,242,220); JADE=(39,143,130); JADE_D=(19,87,87)
ORANGE=(235,129,75); GOLD=(252,204,85); LILAC=(185,177,229); SKIN=(224,159,119)
ROOT=Path(__file__).resolve().parent
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def font(sz,bold=True):
    p=FONT if bold else FONT_REG
    return ImageFont.truetype(p,sz)
def rr(d,box,r,fill,outline=None,width=1): d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)
def cubic(p0,p1,p2,p3,n=24):
    out=[]
    for i in range(n+1):
        t=i/n; u=1-t
        out.append((u**3*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t**3*p3[0],u**3*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t**3*p3[1]))
    return out

def background():
    im=Image.new('RGB',(W,H)); px=im.load()
    top=(244,206,177); mid=(178,198,221); bottom=(35,48,72)
    for y in range(H):
        q=y/(H-1)
        if q<.67:
            t=q/.67; c=tuple(round(top[k]*(1-t)+mid[k]*t) for k in range(3))
        else:
            t=(q-.67)/.33; c=tuple(round(mid[k]*(1-t)+bottom[k]*t) for k in range(3))
        for x in range(W): px[x,y]=c
    d=ImageDraw.Draw(im,'RGBA')
    d.rounded_rectangle((54,330,1026,1040),radius=270,fill=(242,231,214,90),outline=(255,255,255,120),width=9)
    d.line((540,370,540,1030),fill=(255,255,255,105),width=8)
    d.line((90,790,990,790),fill=(255,255,255,85),width=7)
    for x,y,r,a in [(118,440,14,100),(935,430,10,105),(150,700,8,90),(920,670,13,80),(290,385,7,90),(770,970,10,60),(380,760,7,65)]:
        d.ellipse((x-r,y-r,x+r,y+r),fill=(255,255,255,a))
    d.ellipse((730,320,1010,600),fill=(255,232,176,35)); d.ellipse((775,365,965,555),outline=(255,255,255,45),width=4)
    d.polygon([(0,1250),(1080,1190),(1080,1920),(0,1920)],fill=(22,33,54,125))
    d.line((0,1246,1080,1186),fill=(255,255,255,55),width=5)
    for y in range(1360,1920,110): d.line((0,y,1080,y-60),fill=(255,255,255,18),width=2)
    for x in range(-800,1700,220): d.line((540,1260,x,1920),fill=(255,255,255,13),width=2)
    return im

def draw_ambient(im,t):
    """Slow reflected practical-light sweep and drifting frost keep holds alive."""
    d=ImageDraw.Draw(im,'RGBA')
    x=int((t*220)%1450)-180
    # A broad low-opacity window reflection has enough visible travel to read as moving light,
    # not a frozen slide, while staying behind the characters and type.
    d.polygon([(x,365),(x+120,365),(x+385,982),(x+210,982)],fill=(255,219,174,22))
    d.line((x+65,382,x+185,960),fill=(255,231,196,28),width=18)
    for i in range(18):
        xx=(97+i*53+int(t*(18+i%4)*(-1 if i%2 else 1)))%1030
        yy=380+(i*79+int(t*(16+i%5)*12))%650
        r=3+(i%3)
        d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=(255,255,255,35+(i%4)*8))

def make_screen():
    im=Image.new('RGBA',(650,610),(0,0,0,0)); d=ImageDraw.Draw(im)
    rr(d,(8,8,642,602),38,(249,247,239,255),outline=(35,48,72,255),width=8)
    rr(d,(28,28,622,106),22,(31,46,67,255))
    d.ellipse((50,54,74,78),fill=(240,145,93,255)); d.text((94,43),'FIELD LAB  /  POWER',font=font(27),fill=(255,255,255))
    d.text((46,132),'COLD-WEATHER BATTERY',font=font(27),fill=(41,55,77))
    d.text((46,176),'Illustrative interface · not test data',font=font(20,False),fill=(94,105,121))
    for y,title,sub,color,level in [(237,'OUTDOORS','cold conditions',ORANGE,0.38),(374,'AFTER WARMING','room temperature',JADE,0.72)]:
        rr(d,(38,y,612,y+112),18,(235,239,237,255),outline=(215,222,222,255),width=2)
        d.text((62,y+18),title,font=font(22),fill=(39,53,74)); d.text((62,y+53),sub,font=font(18,False),fill=(85,98,116))
        rr(d,(340,y+47,570,y+77),14,(215,221,220,255)); rr(d,(340,y+47,340+230*level,y+77),14,color)
    d.text((46,520),'A phone may report less usable charge in the cold.',font=font(18,False),fill=(49,62,82))
    rr(d,(44,558,606,588),12,(255,232,177,255)); d.text((57,560),'Allow it to return to normal temperature.',font=font(16),fill=(75,56,38))
    return im

def active(items,t): return next((x for x in items if x['start']<=t<x['end']),None)
def smooth01(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)
def event_intensity(events,actor,action,t):
    for e in events:
        if e.get('actor')==actor and e.get('action')==action and e['start']<=t<e['end']:
            q=(t-e['start'])/max(.01,e['end']-e['start']); return math.sin(math.pi*max(0,min(1,q)))
    return 0.0

def draw_presenter(im,t,cues,mouth):
    d=ImageDraw.Draw(im,'RGBA'); ev=cues['motion']
    breathe=math.sin(2*math.pi*t/3.6)*7; sway=math.sin(2*math.pi*t/6.2)*0.07
    screen_cue=cues['screenshot'][0]
    move=smooth01((t-(screen_cue['start']-.35))/.55)*(1-smooth01((t-(screen_cue['end']-.05))/.55))
    cx=397-int(100*move)+int(24*math.sin(t*2.4)); cy=1000+int(breathe)
    point=event_intensity(ev,'presenter','point_screen',t); palm=event_intensity(ev,'presenter','open_palm',t); shrug=event_intensity(ev,'presenter','shrug',t)
    d.polygon([(cx-285,cy+335),(cx-230,cy+255),(cx-120,cy+210),(cx+115,cy+210),(cx+235,cy+260),(cx+290,cy+690),(cx-290,cy+690)],fill=(18,42,58,255),outline=(18,35,51,255))
    d.polygon([(cx-242,cy+315),(cx-140,cy+248),(cx+128,cy+248),(cx+246,cy+320),(cx+268,cy+690),(cx-264,cy+690)],fill=(38,148,133,255))
    d.polygon([(cx-240,cy+320),(cx-140,cy+250),(cx-40,cy+248),(cx-110,cy+690),(cx-264,cy+690)],fill=(26,111,112,255))
    d.polygon([(cx-83,cy+230),(cx+70,cy+235),(cx+121,cy+455),(cx+3,cy+405),(cx-115,cy+448)],fill=(224,120,77,255))
    d.ellipse((cx+168,cy+385,cx+215,cy+432),fill=(252,205,96,255),outline=(22,43,59,255),width=5); d.ellipse((cx+180,cy+397,cx+203,cy+420),fill=(22,43,59,255))
    arm_y=cy+390
    if point>0:
        d.line((cx+170,arm_y,cx+280,cy+195),fill=(26,111,112,255),width=92); d.line((cx+185,arm_y,cx+280,cy+195),fill=(38,148,133,255),width=62)
        d.ellipse((cx+248,cy+140,cx+310,cy+216),fill=SKIN,outline=INK,width=5); d.line((cx+278,cy+164,cx+323,cy+98),fill=SKIN,width=24)
    elif palm>0:
        d.line((cx+135,arm_y,cx+260,cy+315),fill=(26,111,112,255),width=90); d.line((cx+155,arm_y,cx+255,cy+315),fill=(38,148,133,255),width=58)
        d.ellipse((cx+226,cy+275,cx+299,cy+349),fill=SKIN,outline=INK,width=5)
        for dx in (0,17,34): d.line((cx+248+dx,cy+300,cx+258+dx,cy+255),fill=SKIN,width=10)
    elif shrug>0:
        for s in (-1,1):
            d.line((cx+s*145,arm_y,cx+s*275,cy+345),fill=(26,111,112,255),width=88); d.line((cx+s*155,arm_y,cx+s*270,cy+345),fill=(38,148,133,255),width=55)
            d.ellipse((cx+s*295-34,cy+305,cx+s*295+34,cy+370),fill=SKIN,outline=INK,width=5)
    else:
        d.line((cx-140,arm_y,cx-220,cy+510),fill=(26,111,112,255),width=88); d.line((cx-140,arm_y,cx-220,cy+510),fill=(38,148,133,255),width=56)
        d.line((cx+145,arm_y,cx+224,cy+500),fill=(26,111,112,255),width=88); d.line((cx+145,arm_y,cx+224,cy+500),fill=(38,148,133,255),width=56)
        d.ellipse((cx-255,cy+477,cx-186,cy+545),fill=SKIN,outline=INK,width=5); d.ellipse((cx+190,cy+472,cx+260,cy+540),fill=SKIN,outline=INK,width=5)
    d.rectangle((cx-77,cy+143,cx+80,cy+310),fill=(188,113,85,255))
    d.ellipse((cx-220,cy-260,cx+220,cy+230),fill=SKIN,outline=(32,39,56,255),width=9)
    d.polygon([(cx-214,cy+20),(cx-168,cy+155),(cx-45,cy+214),(cx-83,cy+72)],fill=(198,126,95,255))
    d.ellipse((cx-245,cy-35,cx-185,cy+50),fill=SKIN,outline=INK,width=6); d.ellipse((cx+185,cy-35,cx+245,cy+50),fill=SKIN,outline=INK,width=6)
    d.polygon([(cx-220,cy-102),(cx-206,cy-220),(cx-112,cy-283),(cx+38,cy-292),(cx+170,cy-244),(cx+218,cy-130),(cx+154,cy-93),(cx+84,cy-156),(cx+12,cy-113),(cx-67,cy-176),(cx-112,cy-99)],fill=(41,42,66,255),outline=(20,29,48,255))
    d.polygon([(cx-195,cy-160),(cx-95,cy-237),(cx+58,cy-240),(cx+132,cy-206),(cx+62,cy-194),(cx+8,cy-146),(cx-45,cy-172),(cx-112,cy-124)],fill=(70,63,93,255))
    rr(d,(cx+107,cy-205,cx+154,cy-185),8,(250,207,105,255))
    phase=t%5.15; blink=math.exp(-((phase-4.62)/.095)**2); blink=max(blink,.8*math.exp(-((phase-4.82)/.065)**2)); eye_h=max(3,int(37*(1-blink))); glance=int(10*math.sin(t*.8))
    for ex in (-93,88):
        d.ellipse((cx+ex-38,cy-62-eye_h//2,cx+ex+38,cy-62+eye_h//2),fill=(255,249,232,255),outline=(38,39,58,255),width=5)
        if eye_h>9: d.ellipse((cx+ex+glance-10,cy-76,cx+ex+glance+12,cy-29),fill=(43,60,73,255))
    browlift=12*palm+7*point+4*math.sin(t*1.3)
    d.line([(cx-137,cy-112-browlift),(cx-88,cy-128-browlift-15*sway),(cx-48,cy-113-browlift)],fill=(35,34,54,255),width=15)
    d.line([(cx+44,cy-117+browlift),(cx+92,cy-135+browlift+15*sway),(cx+139,cy-108+browlift)],fill=(35,34,54,255),width=15)
    d.polygon([(cx+2,cy-35),(cx-15,cy+42),(cx+20,cy+45)],fill=(180,103,84,255))
    for dx,dy in [(-148,14),(-129,28),(-112,17),(129,17),(146,28),(163,12)]: d.ellipse((cx+dx,cy+dy,cx+dx+7,cy+dy+7),fill=(154,83,72,210))
    open_amt=max(0,min(1,(mouth-.08)/.55))
    if open_amt>.12:
        mw=40+int(35*open_amt); mh=8+int(52*open_amt); d.ellipse((cx-mw,cy+98-mh//2,cx+mw,cy+98+mh//2),fill=(60,31,44,255),outline=(70,42,49,255),width=5)
        if mh>27: d.rounded_rectangle((cx-mw+8,cy+98-mh//2+5,cx+mw-8,cy+98-mh//2+18),radius=5,fill=(255,240,225,255))
    else: d.arc((cx-55,cy+71,cx+58,cy+135),5,172,fill=(95,48,57,255),width=8)

def draw_sidekick(im,t,cues):
    d=ImageDraw.Draw(im,'RGBA'); ev=cues['motion']; shiver=event_intensity(ev,'sidekick','shiver',t); recoil=event_intensity(ev,'sidekick','comic_recoil',t); squint=event_intensity(ev,'sidekick','squint',t)
    bob=17*math.sin(t*2.4)+int(10*shiver*math.sin(t*24)); cx=875+int(7*math.sin(t*1.7))-int(60*recoil); cy=1170+int(bob)
    d.line(cubic((cx+66,cy+22),(cx+155,cy-10),(cx+138,cy-112),(cx+215,cy-95),20),fill=(239,143,83,255),width=18); d.ellipse((cx+204,cy-106,cx+230,cy-80),fill=(252,204,85,255),outline=INK,width=4)
    rr(d,(cx-122,cy-140,cx+122,cy+112),78,(21,59,78,255),outline=(15,32,52,255),width=9); rr(d,(cx-101,cy-121,cx+101,cy+94),62,(77,183,169,255),outline=(188,245,221,255),width=5)
    d.polygon([(cx-92,cy-52),(cx-73,cy-104),(cx+21,cy-116),(cx-5,cy-48)],fill=(111,211,192,255)); rr(d,(cx-73,cy-48,cx+73,cy+35),27,(23,42,60,255))
    eh=8 if squint>.2 else 20
    for ex in (-35,35): d.ellipse((cx+ex-9,cy-19-eh//2,cx+ex+9,cy-19+eh//2),fill=(255,227,130,255))
    for ex in (-62,62):
        d.line((cx+ex,cy+105,cx+ex+(12 if ex>0 else -12),cy+144),fill=(235,142,84,255),width=15); d.ellipse((cx+ex-17,cy+135,cx+ex+20,cy+153),fill=(235,142,84,255))
    if shiver>.15: d.text((cx-22,cy-192),'❄',font=font(44),fill=(223,246,255,255),stroke_width=2,stroke_fill=(40,64,92,255))
    elif recoil>.15: d.text((cx-27,cy-196),'!',font=font(50),fill=(255,204,87,255),stroke_width=3,stroke_fill=INK)

def draw_status(im,cues,t):
    d=ImageDraw.Draw(im,'RGBA'); s=active(cues['status'],t) or cues['status'][-1]
    rr(d,(42,56,1038,243),30,(17,31,50,224),outline=(255,255,255,120),width=3); rr(d,(70,79,222,132),15,(252,204,85,255))
    d.text((84,87),'STATUS',font=font(27),fill=(33,42,54)); step=s.get('step',1); d.text((245,87),f'STEP {step}',font=font(30),fill=(252,204,85))
    text=s['text']; f=font(40)
    while d.textbbox((0,0),text,font=f)[2]>900 and f.size>30: f=font(f.size-1)
    d.text((70,158),text,font=f,fill=(255,255,255),stroke_width=1,stroke_fill=(17,31,50)); d.text((775,103),'ROOK  /  NIB',font=font(20),fill=(184,207,218))
def draw_label(im,cues,t):
    item=active(cues['labels'],t)
    if not item:return
    d=ImageDraw.Draw(im,'RGBA'); text=item['text']; f=font(29); box=d.textbbox((0,0),text,font=f); w=box[2]-box[0]+44; x=1038-w; y=278
    color=(252,204,85,255) if item.get('kind') in ('step','joke','context') else (117,229,211,255)
    rr(d,(x,y,1038,y+58),16,color,outline=(25,35,57,255),width=3); d.text((x+22,y+10),text,font=f,fill=(25,35,57,255))
def text_lines(words,draw,f,maxw):
    lines=[]; cur=[]
    for word in words:
        trial=' '.join(cur+[word])
        if cur and draw.textbbox((0,0),trial,font=f,stroke_width=0)[2]>maxw: lines.append(cur); cur=[word]
        else: cur.append(word)
    if cur:lines.append(cur)
    return lines
def draw_caption(im,cues,t):
    beat=active(cues['captions'],t)
    if not beat:return
    d=ImageDraw.Draw(im,'RGBA'); x0,x1=66,1014; y0,y1=1435,1690; rr(d,(x0,y0,x1,y1),32,(14,24,41,232),outline=(255,255,255,115),width=4)
    words=beat['word_times']; texts=[w['text'] for w in words]; f=font(83); lines=text_lines(texts,d,f,850)
    while len(lines)>2 and f.size>64: f=font(f.size-4); lines=text_lines(texts,d,f,850)
    current=max(0,next((i for i,w in enumerate(words) if w['start']<=t<w['end']),len(words)-1)); line_h=f.size+20; total_h=len(lines)*line_h; yy=y0+(y1-y0-total_h)//2; offset=0
    for line in lines:
        widths=[d.textbbox((0,0),word,font=f,stroke_width=0)[2] for word in line]; spaces=22; total=sum(widths)+spaces*(len(line)-1); xx=(W-total)//2
        for j,(word,ww) in enumerate(zip(line,widths)):
            idx=offset+j; col=(252,205,93,255) if idx==current else (255,255,255,255)
            d.text((xx,yy),word,font=f,fill=col,stroke_width=5,stroke_fill=(4,9,18,255)); xx+=ww+spaces
        offset+=len(line); yy+=line_h
def draw_footer(im,cues):
    d=ImageDraw.Draw(im,'RGBA'); d.text((57,1818),'Cold performance is temporary; do not force-heat a device.',font=font(19,False),fill=(238,240,247,230)); d.text((57,1852),'Source: Apple Support · support.apple.com/en-us/118431',font=font(16,False),fill=(207,218,228,220))
def load_audio_envelope(path,frames):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ac','1','-ar','3000','-f','f32le','pipe:1']); a=np.frombuffer(raw,dtype='<f4'); vals=[]
    for i in range(frames):
        lo=round(i*len(a)/frames); hi=round((i+1)*len(a)/frames); vals.append(float(np.sqrt(np.mean(a[lo:max(lo+1,hi)]**2))) if hi>lo else 0.0)
    arr=np.asarray(vals); scale=max(float(np.percentile(arr,88)),1e-5); return np.clip(arr/scale,0,1.15)
def render(cues_path,audio_path,out_path,preview_dir=None):
    cues=json.loads(Path(cues_path).read_text()); w,h=cues['resolution']; fps=cues['frame_rate']; dur=cues['duration_seconds']
    if (w,h)!=(W,H) or fps!=FPS: raise ValueError('This proof renderer targets 1080x1920 at 30 fps.')
    frames=round(dur*fps); envelope=load_audio_envelope(audio_path,frames); base=background(); screen=make_screen(); out_path=Path(out_path); out_path.parent.mkdir(parents=True,exist_ok=True)
    proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{w}x{h}','-framerate',str(fps),'-i','-','-an','-c:v','libx264','-preset','ultrafast','-crf','19','-pix_fmt','yuv420p',str(out_path)],stdin=subprocess.PIPE)
    if preview_dir: Path(preview_dir).mkdir(parents=True,exist_ok=True)
    screenshot=cues['screenshot'][0]; asset_path=Path(cues_path).parent/screenshot['asset']; asset_path.parent.mkdir(parents=True,exist_ok=True); screen.save(asset_path); screen=screen.resize((535,502),Image.Resampling.LANCZOS); sw,sh=screen.size
    preview_frames={0,round(4*fps),round(8*fps),round(12*fps),round(16.5*fps),round(19*fps),round(21.5*fps),frames-1}
    for i in range(frames):
        t=i/fps; im=base.copy(); draw_ambient(im,t)
        if screenshot['start']<=t<screenshot['end']:
            q=smooth01((t-screenshot['start'])/.24); cw=int(sw*(.89+.11*q)); ch=int(sh*(.89+.11*q)); card=screen.resize((cw,ch),Image.Resampling.LANCZOS); im.paste(card,(W-cw-35,395),card)
        draw_presenter(im,t,cues,float(envelope[i])); draw_sidekick(im,t,cues); draw_status(im,cues,t); draw_label(im,cues,t); draw_caption(im,cues,t); draw_footer(im,cues)
        if preview_dir and i in preview_frames: im.save(Path(preview_dir)/f'frame_{i:04d}_{t:05.2f}s.jpg',quality=92)
        proc.stdin.write(im.tobytes())
        if i%90==0: print(f'frame {i}/{frames}',flush=True)
    proc.stdin.close(); rc=proc.wait()
    if rc: raise SystemExit(f'ffmpeg video encode failed: {rc}')
    print(f'video-only render: {out_path} ({frames} frames)')
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--cues',default=str(ROOT/'proof/cues.json')); ap.add_argument('--audio',default=str(ROOT/'proof/voice.mp3')); ap.add_argument('--out',default=str(ROOT/'proof/video-silent.mp4')); ap.add_argument('--preview-dir',default=str(ROOT/'proof/stills'))
    a=ap.parse_args(); render(a.cues,a.audio,a.out,a.preview_dir)
