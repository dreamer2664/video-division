#!/usr/bin/env python3
"""Original WARD TEN screen furniture and perspective compositions; no external images."""
import argparse,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont

HERE=Path(__file__).resolve().parent
FONT=HERE/'assets'/'Anton-Regular.ttf'; W,H=1080,1920
PALE=(199,220,213); DIM=(110,148,143); TEAL=(112,215,179)
AMBER=(245,209,78); RED=(226,69,60); NIGHT=(9,18,28)
_fonts={}
def font(n):
    if n not in _fonts:_fonts[n]=ImageFont.truetype(str(FONT),n)
    return _fonts[n]
def text(d,xy,s,size=50,fill=PALE,anchor=None): d.text(xy,str(s),font=font(size),fill=fill,anchor=anchor)
def center(d,x,y,s,size=50,fill=PALE):text(d,(x,y),s,size,fill,'mm')
def rr(d,b,r,fill,outline=None,width=1):d.rounded_rectangle(b,radius=r,fill=fill,outline=outline,width=width)
def glow(im,x,y,r,c,alpha=85):
    r=int(r);layer=Image.new('RGBA',(2*r+1,2*r+1));d=ImageDraw.Draw(layer)
    d.ellipse((r*.38,r*.38,r*1.62,r*1.62),fill=(*c,alpha));layer=layer.filter(ImageFilter.GaussianBlur(r*.26));im.paste(layer,(int(x-r),int(y-r)),layer)
def base():
    x=np.linspace(-1,1,W,dtype=np.float32)[None,:];y=np.linspace(-1,1,H,dtype=np.float32)[:,None]
    light=np.exp(-((x*.93)**2+(y*.83+.05)**2)*2.1);vig=1-.55*np.clip((x*x+(y*.9)**2)**.65,0,1)
    a=np.empty((H,W,3),np.uint8)
    for k,(v,inc) in enumerate(zip(NIGHT,(19,29,31))):a[:,:,k]=np.clip((v+inc*light)*vig,0,255).astype(np.uint8)
    return Image.fromarray(a,'RGB')
BASE=base()
def header(im,num,section):
    d=ImageDraw.Draw(im,'RGBA')
    text(d,(76,164),'02:17 A.M.  /  NIGHT SHIFT',42,(*PALE,240))
    text(d,(815,164),'LIVE',42,(*AMBER,245))
    d.line((76,221,1004,221),fill=(94,140,128,130),width=2)
    text(d,(76,238),section,42,(*DIM,245));text(d,(915,238),f'{num:02}',42,(*DIM,210))
    d.line((76,303,1004,303),fill=(94,140,128,75),width=2)
    # The moving scan cursor is drawn by ffmpeg over this static rail.
    d.line((140,1318,940,1318),fill=(96,165,139,110),width=3)
    for x in range(140,941,100):d.line((x,1310,x,1326),fill=(96,165,139,100),width=2)
    for i in range(180):
        a=int(56*math.sin(math.pi*i/180)**2);d.line((65,1360+2*i,1015,1360+2*i),fill=(2,8,13,a),width=2)
    return d

def shell(im,title,accent=TEAL):
    glow(im,540,820,330,accent,34);d=ImageDraw.Draw(im,'RGBA')
    rr(d,(135,355,945,1260),23,(15,30,37,255),(75,112,105,255),7)
    rr(d,(170,390,910,1225),8,(11,23,29,255),(47,80,72,255),3)
    text(d,(205,422),title,59,(*PALE,255));d.line((205,508,875,508),fill=(87,132,116,170),width=3)
    return d

def board(im,variant=0):
    d=shell(im,'HANDOVER BOARD')
    text(d,(210,530),'CAPACITY',48,(*DIM,255));text(d,(605,519),'10 BEDS',70,(*AMBER,255))
    for i in range(10):
        row=i//2;col=i%2;x=208+col*335;y=632+row*82
        rr(d,(x,y,x+312,y+65),6,(26,50,47,255),(69,118,96,210),2)
        text(d,(x+18,y+4),f'{i+1:02}',43,(160,199,175,255));text(d,(x+110,y+5),'OCCUPIED',41,(143,186,159,235))
        d.ellipse((x+278,y+22,x+294,y+38),fill=(*TEAL,230))
    rr(d,(208,1068,872,1180),8,(59,30,33,255),(*RED,200),3)
    text(d,(232,1088),'BED 11',58,(*RED,255));text(d,(492,1093),'NO ADMISSION',47,(222,165,148,255))
    if variant:
        d.rectangle((201,621,879,1054),outline=(120,212,158,70),width=3)

def chart(im,variant=0):
    d=shell(im,'OBSERVATION CHART')
    text(d,(210,530),'PATIENTS',47,(*DIM,255));text(d,(708,515),'10',87,(*AMBER,255))
    for i in range(10):
        row=i//2;col=i%2;x=215+col*335;y=635+row*76
        d.line((x,y+64,x+302,y+64),fill=(76,121,105,105),width=2)
        text(d,(x,y+5),f'PAT {i+1:02}',42,(163,193,176,255))
        d.line((x+176,y+38,x+288,y+38),fill=(79,144,112,170),width=3)
        if i==variant%10:d.ellipse((x+283,y+30,x+298,y+45),fill=(*TEAL,220))
    text(d,(215,1080),'CURRENT TOTAL',45,(*DIM,220));text(d,(650,1064),'10 / 10',60,(164,198,173,255))

def bells(im,mode='total'):
    d=shell(im,'CALL-BELL LOG',RED)
    text(d,(210,531),'RECORDED CALLS',47,(*DIM,255));text(d,(740,513),'11',88,(*RED,255))
    rows=[('01–05','ACKNOWLEDGED'),('06','BED 06'),('07','BED 07'),('08','BED 08'),('09','BED 09'),('10','BED 10'),('11','BED 11')]
    for i,(a,b) in enumerate(rows):
        y=632+i*73;last=i==6
        if last:rr(d,(205,y-3,874,y+62),5,(60,30,34,255),(*RED,190),2)
        text(d,(230,y),a,43,(*RED,255) if last else (*DIM,255));text(d,(420,y),b,44,(*PALE,255))
        text(d,(747,y),('WAIT' if last else 'ACK'),41,(*RED,255) if last else (108,172,137,255))
    if mode=='next':
        d.rectangle((205,1080,875,1185),fill=(54,30,34,255));center(d,540,1130,'NEXT NURSE',66,RED)
    else:
        text(d,(230,1160),'11  /  NO ADMISSION',42,(205,140,129,255))

def admission(im):
    d=shell(im,'ADMISSION SEARCH',RED)
    text(d,(215,552),'QUERY  /  BED 11',55,(*PALE,255))
    rr(d,(210,680,870,983),15,(29,39,40,255),(106,126,113,255),4)
    d.line((276,750,350,824),fill=(*RED,235),width=9);d.line((350,750,276,824),fill=(*RED,235),width=9)
    text(d,(395,744),'NO MATCH',75,(*RED,255));text(d,(395,855),'ADMITTED  /  0',48,(183,177,158,255))
    text(d,(220,1068),'BED 11  ·  NO ADMISSION',47,(190,147,133,255))

def protocol(im):
    d=shell(im,'HANDOVER RULE')
    rr(d,(210,595,870,1040),15,(25,45,44,255),(99,152,123,255),4)
    text(d,(255,642),'01',80,(*TEAL,255));text(d,(370,649),'ANSWER',69,(*PALE,255));text(d,(370,735),'EVERY BELL',69,(*AMBER,255))
    d.line((258,865,820,865),fill=(99,151,125,150),width=3)
    text(d,(260,910),'BEFORE SIGNING',60,(178,204,185,255))

def corridor(im,close=False):
    glow(im,540,715,330,AMBER,42);d=ImageDraw.Draw(im,'RGBA')
    # Explicit one-point perspective: walls, ceiling and floor converge at the doorway.
    d.polygon([(100,352),(980,352),(655,566),(425,566)],fill=(38,54,57,255))
    d.polygon([(100,352),(425,566),(425,890),(100,1260)],fill=(28,42,47,255))
    d.polygon([(980,352),(655,566),(655,890),(980,1260)],fill=(25,39,44,255))
    d.polygon([(100,1260),(980,1260),(655,890),(425,890)],fill=(35,46,46,255))
    d.rectangle((425,566,655,890),fill=(20,32,36,255),outline=(96,120,109,255),width=4)
    for x in [150,300,450,630,780,930]:d.line((x,1260,540,739),fill=(95,114,101,125),width=3)
    for y,l,r in [(1190,155,925),(1115,220,860),(1045,280,800),(980,338,742)]:d.line((l,y,r,y),fill=(102,124,108,100),width=3)
    d.polygon([(149,510),(270,563),(270,1055),(149,1168)],fill=(12,24,29,255),outline=(83,110,101,255))
    d.polygon([(310,590),(375,620),(375,931),(310,994)],fill=(13,25,29,255),outline=(79,108,98,255))
    d.polygon([(931,510),(810,563),(810,1055),(931,1168)],fill=(12,24,29,255),outline=(83,110,101,255))
    d.polygon([(770,590),(705,620),(705,931),(770,994)],fill=(13,25,29,255),outline=(79,108,98,255))
    d.polygon([(278,382),(802,382),(754,421),(326,421)],fill=(153,184,160,180))
    d.polygon([(365,452),(715,452),(683,475),(397,475)],fill=(133,176,146,145))
    d.polygon([(431,514),(649,514),(633,528),(447,528)],fill=(139,184,151,160))
    rr(d,(465,575,615,895),3,(9,17,19,255),(179,156,91,255),4)
    d.polygon([(586,583),(615,575),(615,895),(586,881)],fill=(197,157,66,145))
    d.polygon([(465,895),(615,895),(720,1040),(360,1040)],fill=(204,164,76,45))
    if close:
        d.line((425,566,425,890),fill=(153,179,145,160),width=7)
        d.line((655,566,655,890),fill=(153,179,145,160),width=7)
    text(d,(156,442),'WARD 10',44,(143,173,150,210))

def bed(im,close=False):
    glow(im,540,800,330,TEAL,25);d=ImageDraw.Draw(im,'RGBA')
    rr(d,(130,355,950,1260),20,(18,30,35,255),(80,111,102,255),6)
    d.rectangle((194,402,886,1190),fill=(27,42,43,255),outline=(79,108,97,255),width=3)
    # A trapezoid mattress and converging edges show depth from the doorway.
    d.polygon([(220,443),(860,443),(754,573),(326,573)],fill=(38,57,55,255))
    d.polygon([(194,1187),(886,1187),(754,910),(326,910)],fill=(34,45,43,255))
    d.rectangle((455,590,755,756),fill=(32,54,53,255),outline=(102,132,113,255),width=5)
    d.polygon([(299,987),(475,702),(735,702),(785,987)],fill=(128,158,141,255),outline=(193,207,181,255))
    d.polygon([(299,987),(785,987),(785,1074),(299,1074)],fill=(70,98,88,255),outline=(148,175,149,255))
    d.polygon([(472,750),(687,750),(665,812),(435,812)],fill=(182,202,181,255),outline=(113,148,126,255))
    d.line((352,1080,352,1110),fill=(148,176,154,255),width=13);d.line((728,1080,728,1110),fill=(148,176,154,255),width=13)
    d.line((284,986,800,986),fill=(190,208,182,255),width=8)
    text(d,(230,1135),'BED 11  /  EMPTY',47,(173,193,170,255))
    if close:d.line((385,892,690,892),fill=(210,224,194,150),width=4)

def printer(im):
    glow(im,540,790,300,AMBER,38);d=ImageDraw.Draw(im,'RGBA')
    rr(d,(150,478,930,1180),22,(30,43,43,255),(101,124,111,255),6)
    rr(d,(205,775,875,1120),16,(49,64,59,255),(126,143,124,255),4)
    d.rectangle((246,705,834,790),fill=(8,18,22,255),outline=(100,125,110,255),width=3)
    d.rectangle((290,400,790,735),fill=(148,164,142,255),outline=(211,215,189,255),width=4)
    text(d,(332,445),'DISCHARGE',62,(48,60,51,255));text(d,(332,542),'BED  /  11',58,(53,68,57,255))
    d.line((332,630,735,630),fill=(69,88,69,200),width=4)
    text(d,(278,862),'WARD PRINTER',63,(*PALE,255));text(d,(278,970),'STATUS  /  PRINTING',44,(155,189,160,255))
    d.ellipse((782,876,810,904),fill=(*AMBER,235))

def form(im,mode='hidden'):
    d=shell(im,'DISCHARGE RECORD',RED)
    rr(d,(215,555,865,1150),9,(37,51,48,255),(119,143,119,255),4)
    text(d,(255,605),'BED',46,(*DIM,255));text(d,(640,585),'11',84,(*AMBER,255))
    d.line((255,700,822,700),fill=(100,140,119,150),width=3)
    text(d,(255,755),'PATIENT',46,(*DIM,255))
    if mode=='hidden':
        for j in range(5):d.rectangle((472+j*60,758,515+j*60,804),fill=(96,121,106,190))
        text(d,(255,930),'IDENTITY PENDING',51,(164,186,164,255))
    elif mode=='you':
        text(d,(500,722),'YOU',101,(*RED,255));text(d,(255,935),'DISCHARGE PENDING',49,(198,161,141,255))
    else:
        center(d,540,874,'DISCHARGED',84,RED);text(d,(255,1012),'PATIENT  /  YOU',50,(192,181,156,255))

def badge(im):
    glow(im,540,800,300,TEAL,24);d=ImageDraw.Draw(im,'RGBA')
    rr(d,(180,390,900,1215),24,(27,43,45,255),(97,125,112,255),6)
    text(d,(244,456),'STAFF BADGE',62,(*PALE,255));text(d,(244,548),'WARD TEN  /  NIGHT',47,(*DIM,255))
    d.ellipse((260,675,410,825),fill=(68,94,83,255),outline=(120,156,130,255),width=4)
    d.polygon([(235,868),(435,868),(465,1025),(205,1025)],fill=(68,94,83,255))
    d.rectangle((502,688,830,757),fill=(15,25,29,255),outline=(100,126,111,255),width=3)
    text(d,(516,795),'NAME  /  —',53,(*RED,255));text(d,(516,905),'STATUS  /  OFF',47,(174,179,157,255))

def handover(im,mode='start'):
    d=shell(im,'WARD TEN  /  HANDOVER')
    if mode=='start':
        text(d,(220,560),'NIGHT SHIFT',65,(*PALE,255));text(d,(220,658),'02:17 A.M.',85,(*AMBER,255))
        d.line((220,797,860,797),fill=(97,150,121,170),width=3)
        text(d,(220,870),'BEDS  /  10',60,(163,204,174,255));text(d,(220,969),'PATIENTS  /  10',60,(163,204,174,255))
    elif mode=='shift':
        text(d,(220,560),'SHIFT CHANGE',72,(*PALE,255));text(d,(220,678),'HANDOVER',61,(*DIM,255))
        rr(d,(220,820,860,1050),9,(36,53,49,255),(114,158,127,255),3)
        center(d,540,885,'NEXT SHIFT',68,AMBER);center(d,540,990,'1 CALL WAITING',59,RED)
    else:
        text(d,(215,570),'NEXT SHIFT',69,(*PALE,255));text(d,(215,690),'ONE CALL WAITING',58,(*AMBER,255))
        rr(d,(220,850,860,1055),9,(62,30,35,255),(*RED,220),3)
        center(d,540,948,'NEXT NURSE',80,RED)

def draw_scene(i):
    im=BASE.copy()
    labels=['WARD TEN / HANDOVER','WARD BOARD / 10','WARD BOARD / 10','OBSERVATION / 10','PATIENT CHART / 10','CALL LOG / 11','BELL / BED 11','ADMISSIONS / SEARCH','ADMISSIONS / NO MATCH','HANDOVER / RULE','BED BOARD / OCCUPIED','CHART / TEN NAMES','CALL LOG / BED 11','CORRIDOR / WARD 10','UNMARKED / DOOR','BED 11 / ROOM','BED 11 / EMPTY','CHART / STILL 10','DISCHARGE / PRINTER','DISCHARGE / BED 11','DISCHARGE / HOLD','PATIENT / PENDING','PATIENT / YOU','STATUS / DISCHARGE','STAFF / BADGE','CHART / TEN','HANDOVER / NEXT','CALL LOG / AGAIN','NEXT SHIFT / WAITING','CALL TO / NEXT NURSE']
    header(im,i,labels[i-1])
    if i==1:handover(im)
    elif i in (2,3,11):board(im,i==11)
    elif i in (4,5,12,18,26):chart(im,i)
    elif i in (6,7,13,28):bells(im)
    elif i in (8,9):admission(im)
    elif i==10:protocol(im)
    elif i in (14,15):corridor(im,i==15)
    elif i in (16,17):bed(im,i==17)
    elif i==19:printer(im)
    elif i in (20,21,22):form(im,'hidden')
    elif i==23:form(im,'you')
    elif i==24:form(im,'discharged')
    elif i==25:badge(im)
    elif i==27:handover(im,'shift')
    elif i in (29,30):handover(im,'next')
    return im

def landscape_bg(path):
    w,h=1920,1080;x=np.linspace(-1,1,w,dtype=np.float32)[None,:];y=np.linspace(-1,1,h,dtype=np.float32)[:,None]; light=np.exp(-((x*.7)**2+y*y)*2.1)
    a=np.empty((h,w,3),np.uint8)
    for k,(v,c) in enumerate(zip((7,13,21),(14,24,26))):a[:,:,k]=np.clip(v+c*light,0,255).astype(np.uint8)
    im=Image.fromarray(a,'RGB');d=ImageDraw.Draw(im,'RGBA')
    d.line((64,130,370,130),fill=(89,137,120,160),width=2);d.line((1540,130,1850,130),fill=(89,137,120,160),width=2)
    text(d,(76,185),'NIGHT SHIFT',48,(*DIM,255));text(d,(76,300),'WARD',92,(*PALE,255));text(d,(76,410),'TEN',92,(*PALE,255))
    d.rectangle((76,548,340,555),fill=(*AMBER,190));text(d,(76,602),'02:17 A.M.',48,(145,181,159,255))
    text(d,(1530,185),'HANDOVER',50,(*DIM,255))
    for i in range(4):
        y0=340+i*130;d.rectangle((1530,y0,1554,y0+24),outline=(106,150,125,200),width=3);d.line((1590,y0+18,1850,y0+18),fill=(81,123,104,130),width=3)
    text(d,(1530,905),'WARD  /  10',46,(151,175,151,255));im.save(path,optimize=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    lens=[54,60,66]*10
    for i in range(1,31):
        draw_scene(i).save(args.out/f'shot{i:02}.png',optimize=True);print(f'art {i}/30',flush=True)
    landscape_bg(args.out/'landscape-bg.png')
    with (args.out/'shots.ffconcat').open('w') as f:
        f.write('ffconcat version 1.0\n')
        for i,n in enumerate(lens,1):f.write(f"file '{(args.out/f'shot{i:02}.png').resolve()}'\nduration {n/30:.6f}\n")
        f.write(f"file '{(args.out/'shot30.png').resolve()}'\n")
if __name__=='__main__':main()
