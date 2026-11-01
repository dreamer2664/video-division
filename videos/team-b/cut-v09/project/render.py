#!/usr/bin/env python3
"""Deterministic, code-drawn four-second-forward CCTV short. Requires Pillow, NumPy, FFmpeg."""
from __future__ import annotations
import csv, math, os, pathlib, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
FPS, SECONDS = 30, 60
START_MS = (2*3600 + 13*60 + 8)*1000
BG=(7,12,22); PANEL=(12,22,34); BLUE=(24,43,63); GRID=(43,67,86)
TEXT=(231,235,229); MUTED=(121,149,163); AMBER=(238,185,75); GREEN=(131,222,169); RED=(223,70,62)
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONTS={}
def font(sz,bold=True):
    key=(sz,bold)
    if key not in FONTS: FONTS[key]=ImageFont.truetype(BOLD if bold else REG,sz)
    return FONTS[key]

def ts(ms):
    ms=(START_MS+ms)%(24*3600*1000)
    h=ms//3600000; m=(ms//60000)%60; s=(ms//1000)%60; milli=ms%1000
    return f'{h:02d}:{m:02d}:{s:02d}.{milli:03d}'

def bg_image(w,h):
    y,x=np.mgrid[0:h,0:w].astype(np.float32)
    r=np.sqrt(((x-w*.48)/(w*.75))**2+((y-h*.42)/(h*.82))**2)
    glow=np.exp(-r*r*2)
    a=np.zeros((h,w,3),np.uint8)
    for c,base,amp in [(0,7,8),(1,12,15),(2,22,21)]: a[:,:,c]=np.clip(base+amp*glow,0,255)
    vign=np.clip(1-.52*np.maximum(0,r-.32),.44,1)
    a=(a*vign[:,:,None]).astype(np.uint8)
    return Image.fromarray(a,'RGB')

CAP_EVENTS=[]
RED_CAPS={"HIS HAND ISN'T OPEN YET",'NOW. EXACTLY.','FEED FIVE: ONLINE','WHO IS BEHIND HIM?','CAM FIVE HAS NO KEY'}
def caption_at(t):
    value='02:13:08.000'
    for onset,caption in CAP_EVENTS:
        if onset>t: break
        value=caption
    return value

# Camera scene cards are generated from the same integer-frame clock as their burn-ins.
def corridor(d,b,t):
    x0,y0,x1,y1=b; w=x1-x0; h=y1-y0
    d.rectangle(b,fill=(9,17,27))
    vanx=x0+w*.53; vany=y0+h*.35
    d.line((x0,y0,x1,y0),fill=GRID,width=2)
    d.polygon([(x0,y0+h*.1),(vanx,vany),(x1,y0+h*.1),(x1,y0+h*.82),(x0,y0+h*.82)],fill=(13,27,42),outline=GRID)
    d.line((x0,y0+h*.82,vanx,vany),fill=GRID,width=2); d.line((x1,y0+h*.82,vanx,vany),fill=GRID,width=2)
    # Door event begins at timeline 16.8s and unfolds over 2.4s.
    p=max(0,min(1,(t-16.8)/2.4)); doorx=x0+w*.39; dw=w*.27; top=y0+h*.22; bot=y0+h*.78
    d.rectangle((doorx,top,doorx+dw,bot),fill=(26,42,57),outline=(83,111,129),width=2)
    if p>0:
        # Hinged panel opens by the same amount on feed and real-room displays.
        dx=int(dw*.8*p); d.polygon([(doorx,top),(doorx+dw-dx,top+int(h*.04*p)),(doorx+dw-dx,bot-int(h*.04*p)),(doorx,bot)],fill=(18,31,43),outline=(98,123,133))
    d.ellipse((doorx+dw-10, y0+h*.49, doorx+dw-5,y0+h*.52),fill=AMBER if p>0 else MUTED)
    # A single small relay lamp pulses after the latch begins moving.
    if p>0 and int(t*3)%2: d.ellipse((x0+8,y0+8,x0+13,y0+13),fill=RED)

def stair(d,b,t):
    x0,y0,x1,y1=b; w=x1-x0; h=y1-y0
    d.rectangle(b,fill=(10,19,29))
    for i in range(6):
        x=x0+w*.18+i*w*.105; y=y0+h*.72-i*h*.085
        d.line((x,y,x+w*.34,y),fill=(76,96,110),width=2)
        d.line((x+w*.34,y,x+w*.34,y-h*.085),fill=(76,96,110),width=2)
    d.line((x0+w*.2,y0+h*.2,x1-w*.12,y0+h*.2),fill=GRID,width=2)
    d.ellipse((x1-w*.2,y0+h*.12,x1-w*.15,y0+h*.18),fill=GREEN if int(t*2)%2 else MUTED)

def lobby(d,b,t):
    x0,y0,x1,y1=b; w=x1-x0; h=y1-y0
    d.rectangle(b,fill=(10,19,29)); d.rectangle((x0+w*.17,y0+h*.12,x0+w*.83,y0+h*.88),fill=(15,29,42),outline=GRID,width=2)
    d.rectangle((x0+w*.26,y0+h*.2,x0+w*.45,y0+h*.78),fill=(20,37,51),outline=(74,97,114),width=2)
    d.rectangle((x0+w*.55,y0+h*.2,x0+w*.74,y0+h*.78),fill=(17,31,45),outline=(74,97,114),width=2)
    d.line((x0+w*.5,y0+h*.2,x0+w*.5,y0+h*.8),fill=GRID,width=2)
    d.ellipse((x0+w*.47,y0+h*.48,x0+w*.49,y0+h*.51),fill=AMBER if int(t*2)%2 else MUTED)

def control_scene(d,b,t,scale=1.0,detail=False):
    x0,y0,x1,y1=b; w=x1-x0; h=y1-y0
    d.rectangle(b,fill=(9,18,28))
    d.line((x0+w*.08,y0+h*.69,x1-w*.08,y0+h*.69),fill=(60,78,91),width=max(1,int(w*.008)))
    # chair and desk are intentionally strict, diagrammatic shapes.
    cx=x0+w*.53; cy=y0+h*.51
    d.rounded_rectangle((cx-w*.13,cy-h*.10,cx+w*.13,cy+h*.16),radius=max(2,int(w*.03)),fill=(17,29,41),outline=(65,82,96),width=max(1,int(w*.01)))
    d.rectangle((x0+w*.22,y0+h*.62,x0+w*.83,y0+h*.70),fill=(56,70,80))
    d.rectangle((x0+w*.27,y0+h*.70,x0+w*.30,y0+h*.91),fill=(54,69,80)); d.rectangle((x0+w*.75,y0+h*.70,x0+w*.78,y0+h*.91),fill=(54,69,80))
    # seated guard silhouette, same figure in current room and CAM 04 preview.
    head=(cx-w*.055,cy-h*.34,cx+w*.055,cy-h*.17)
    d.ellipse(head,fill=(137,149,148))
    d.polygon([(cx-w*.11,cy-h*.17),(cx+w*.11,cy-h*.17),(cx+w*.16,cy+h*.08),(cx-w*.15,cy+h*.08)],fill=(44,59,68))
    d.line((cx-w*.06,cy-h*.02,x0+w*.37,y0+h*.63),fill=(160,169,164),width=max(2,int(w*.025)))
    # The forecast gesture: closed at t<49.6, open palm at 49.6, against lens at 53.6.
    state='closed' if t<49.6 else ('open' if t<53.6 else 'lens')
    hx=x0+w*.37; hy=y0+h*.63
    if state=='closed':
        d.ellipse((hx-w*.025,hy-h*.035,hx+w*.025,hy+h*.015),fill=(189,151,125))
    elif state=='open':
        # open palm with separated fingers, uncluttered silhouette.
        d.ellipse((hx-w*.045,hy-h*.045,hx+w*.045,hy+h*.025),fill=(200,163,137))
        for j in range(4):
            fx=hx-w*.035+j*w*.023
            d.rounded_rectangle((fx,hy-h*.12-(j%2)*h*.008,fx+w*.014,hy-h*.025),radius=max(1,int(w*.006)),fill=(200,163,137))
        d.line((hx-w*.035,hy,x0+w*.34,y0+h*.57),fill=(200,163,137),width=max(2,int(w*.012)))
    else:
        # Palm meets lens: simple flat oval foreground shape.
        d.ellipse((x0+w*.70,y0+h*.25,x0+w*.86,y0+h*.53),fill=(200,163,137),outline=(236,185,145),width=max(1,int(w*.007)))
        for j in range(4):
            fx=x0+w*(.715+j*.032)
            d.rounded_rectangle((fx,y0+h*.16,fx+w*.019,y0+h*.36),radius=max(1,int(w*.007)),fill=(200,163,137))
    if detail and t>=57.6:
        # A second seated silhouette appears only in the forecast, beyond the known room.
        sx=x0+w*.78; sy=y0+h*.40
        d.ellipse((sx-w*.032,sy-h*.18,sx+w*.032,sy-h*.08),fill=(5,9,15))
        d.polygon([(sx-w*.07,sy-h*.08),(sx+w*.07,sy-h*.08),(sx+w*.09,sy+h*.08),(sx-w*.09,sy+h*.08)],fill=(5,9,15))

def unknown_scene(d,b,t):
    x0,y0,x1,y1=b; w=x1-x0; h=y1-y0
    d.rectangle(b,fill=(5,10,17))
    # View is behind the guard; foreground silhouette and an impossible seated shape.
    d.polygon([(x0+w*.12,y1),(x0+w*.32,y0+h*.48),(x0+w*.46,y1)],fill=(27,38,46))
    d.ellipse((x0+w*.64,y0+h*.26,x0+w*.76,y0+h*.48),fill=(5,8,13))
    d.polygon([(x0+w*.59,y0+h*.47),(x0+w*.8,y0+h*.47),(x0+w*.88,y1),(x0+w*.53,y1)],fill=(5,8,13))
    d.line((x0+w*.05,y0+h*.88,x1-w*.05,y0+h*.88),fill=GRID,width=1)


def camera_card(d,box,cam,frame_ms,prog_t,panel_font,large=False):
    x0,y0,x1,y1=map(int,box); w=x1-x0; h=y1-y0
    d.rounded_rectangle((x0,y0,x1,y1),radius=max(3,int(w*.025)),fill=PANEL,outline=(53,78,91),width=max(1,int(w*.006)))
    label=f'CAM {cam:02d}' if cam<5 else 'CAM 05 / NEW'
    d.text((x0+w*.04,y0+h*.03),label,font=font(panel_font,True),fill=AMBER if cam!=5 else RED)
    stamp=ts(frame_ms+4000)
    d.text((x1-w*.04,y0+h*.03),stamp,font=font(max(9,panel_font-3),False),fill=GREEN,anchor='ra')
    ix0=x0+w*.045; iy0=y0+h*(.22 if h<100 else .17); ix1=x1-w*.045; iy1=y1-h*.15
    if cam==1: corridor(d,(ix0,iy0,ix1,iy1),prog_t)
    elif cam==2: stair(d,(ix0,iy0,ix1,iy1),prog_t)
    elif cam==3: lobby(d,(ix0,iy0,ix1,iy1),prog_t)
    elif cam==4: control_scene(d,(ix0,iy0,ix1,iy1),prog_t,detail=True)
    else: unknown_scene(d,(ix0,iy0,ix1,iy1),prog_t)
    # burn-in status line reinforces the measurable invariant.
    d.text((x0+w*.04,y1-h*.045),'LIVE  +00:04.000',font=font(max(8,panel_font-4),True),fill=GREEN,anchor='ls')

def room_panel(d,box,frame_ms,elapsed,large=False):
    x0,y0,x1,y1=map(int,box); w=x1-x0; h=y1-y0
    d.rounded_rectangle((x0,y0,x1,y1),radius=5,fill=(9,17,27),outline=(66,85,97),width=2)
    d.text((x0+w*.04,y0+h*.04),'CONTROL ROOM / WALL CLOCK',font=font(max(12,int(w*.035)),True),fill=MUTED)
    d.text((x1-w*.04,y0+h*.04),ts(frame_ms),font=font(max(13,int(w*.038)),True),fill=AMBER,anchor='ra')
    control_scene(d,(x0+w*.06,y0+h*.17,x1-w*.06,y1-h*.07),elapsed,detail=False)

def fitted_text(d,xy,text,sz,maxw,fill=TEXT,bold=True,anchor='mm'):
    f=font(sz,bold)
    while d.textbbox((0,0),text,font=f)[2] > maxw and sz>10:
        sz-=1; f=font(sz,bold)
    d.text(xy,text,font=f,fill=fill,anchor=anchor)

def compose(frame,orientation,bg):
    vertical=orientation=='v'
    W,H=bg.size
    im=bg.copy(); d=ImageDraw.Draw(im)
    frame_ms=(frame*1000)//FPS; elapsed=frame/FPS
    idx=min(24,frame//72); local=(frame%72)/71
    # Eased push-in, subtle enough not to corrupt the geometric timing read.
    ease=local*local*(3-2*local); zoom=1.0+0.06*ease
    # shot header and UTC-like wall clock (explicitly the room clock, not feed time)
    if vertical:
        d.text((W*.05,H*.026),'NORTH / NIGHT CONTROL',font=font(19,True),fill=MUTED)
        d.text((W*.95,H*.026),'REC  ●',font=font(15,True),fill=RED,anchor='ra')
        fitted_text(d,(W*.5,H*.075),f'WALL  {ts(frame_ms)}',26,W*.91,AMBER,True)
        if idx==19:
            # Deliberately designed hero: large future feed above, present room below.
            camera_card(d,(22,112,W-22,574),4,frame_ms,elapsed+4,19,True)
            room_panel(d,(32,592,W-32,792),frame_ms,elapsed,True)
            # Three synchronized witness timecodes remain legible in a narrow inset strip.
            for j,cam in enumerate((1,2,3)):
                xx=28+j*(W-56)/3
                d.text((xx,805),f'CAM {cam:02d}  {ts(frame_ms+4000)}',font=font(12,True),fill=GREEN)
        else:
            # Four simultaneous synchronized feeds.
            gap=12; x0=20; x1=W-20; cardw=(x1-x0-gap)/2; cardh=195
            y0=122
            cams=(1,2,3,4)
            for k,cam in enumerate(cams):
                row=k//2; col=k%2; xx=x0+col*(cardw+gap); yy=y0+row*(cardh+10)
                camera_card(d,(xx,yy,xx+cardw,yy+cardh),cam,frame_ms,elapsed+4,15)
            room_panel(d,(25,535,W-25,774),frame_ms,elapsed)
            if elapsed>=53.6:
                # CAM 05 is an unconfigured, fifth view, first visible at its live appearance.
                camera_card(d,(30,775,W-30,855),5,frame_ms,elapsed+4,13)
        # caption system sits below picture; one current word is amber-karaoke highlighted.
        cap=caption_at(elapsed)
        color=RED if cap in RED_CAPS else TEXT
        fitted_text(d,(W*.5,H*.914),cap,24,W*.91,color,True)
        d.text((W*.5,H*.964),'FRAME TIME BASE  30/1   ·   NO DROPPED FRAMES',font=font(12,True),fill=(96,119,132),anchor='mm')
    else:
        d.text((W*.035,H*.045),'NORTH / NIGHT CONTROL',font=font(22,True),fill=MUTED)
        d.text((W*.965,H*.045),f'WALL  {ts(frame_ms)}',font=font(24,True),fill=AMBER,anchor='ra')
        if idx==19:
            camera_card(d,(25,95,600,410),4,frame_ms,elapsed+4,20,True)
            room_panel(d,(622,95,935,410),frame_ms,elapsed,True)
            for j,cam in enumerate((1,2,3)):
                d.text((34+j*190,424),f'CAM {cam:02d}  {ts(frame_ms+4000)}',font=font(15,True),fill=GREEN)
        else:
            gx,gy=25,92; gap=12; cw=270; ch=153
            for k,cam in enumerate((1,2,3,4)):
                row=k//2; col=k%2; xx=gx+col*(cw+gap); yy=gy+row*(ch+10)
                camera_card(d,(xx,yy,xx+cw,yy+ch),cam,frame_ms,elapsed+4,16)
            room_panel(d,(590,92,935,422),frame_ms,elapsed)
            if elapsed>=53.6: camera_card(d,(690,318,928,415),5,frame_ms,elapsed+4,11)
        cap=caption_at(elapsed); color=RED if cap in RED_CAPS else TEXT
        fitted_text(d,(W*.5,H*.89),cap,32,W*.9,color,True)
        d.text((W*.5,H*.955),'LIVE WALL CLOCK  /  FOUR-SECOND FORECAST',font=font(17,True),fill=(96,119,132),anchor='mm')
    # eased 1.00→1.025 push for the full shot; output crops symmetrically.
    if zoom>1.0001:
        nw,nh=round(W*zoom),round(H*zoom)
        im=im.resize((nw,nh),Image.Resampling.LANCZOS)
        left=(nw-W)//2; top=(nh-H)//2
        im=im.crop((left,top,left+W,top+H))
    return im

def render_one(orientation,outfile,still_dir,ffmpeg):
    if orientation=='v': base=(540,960); out=(1080,1920)
    else: base=(960,540); out=(1920,1080)
    bg=bg_image(*base); total=FPS*SECONDS
    outfile.parent.mkdir(parents=True,exist_ok=True); still_dir.mkdir(parents=True,exist_ok=True)
    mix=ROOT/'assets'/'final_mix.wav'
    cmd=[ffmpeg,'-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{out[0]}x{out[1]}','-r',str(FPS),'-i','-','-i',str(mix),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-t',str(SECONDS),'-movflags','+faststart',str(outfile)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    if proc.stdin is None: raise RuntimeError('failed to open FFmpeg stdin')
    for n in range(total):
        im=compose(n,orientation,bg).resize(out,Image.Resampling.LANCZOS)
        if orientation=='v' and n in (180,576,1368,1656):
            name={180:'01-synchronized-feeds.png',576:'02-door-offset.png',1368:'HERO-01-open-palm.png',1656:'03-cam-five.png'}[n]
            im.save(still_dir/name,optimize=True)
        proc.stdin.write(im.tobytes())
        if n%300==0: print(f'{orientation}: {n}/{total}',flush=True)
    proc.stdin.close(); code=proc.wait()
    if code: raise SystemExit(f'FFmpeg encode returned {code}')

def main():
    global CAP_EVENTS
    with open(ROOT/'project'/'caption_cues.csv',newline='') as f:
        CAP_EVENTS=[(float(r['caption_start_s']),r['caption']) for r in csv.DictReader(f)]
    ffmpeg=os.environ.get('FFMPEG','ffmpeg')
    render_one('v',ROOT/'video.mp4',ROOT/'stills',ffmpeg)
    render_one('h',ROOT/'video-landscape.mp4',ROOT/'stills',ffmpeg)
if __name__=='__main__': main()
