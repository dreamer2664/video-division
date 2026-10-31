#!/usr/bin/env python3
"""Draw all original vector-like flat artwork to a temporary build directory."""
import argparse, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE=Path(__file__).resolve().parent
FONT=HERE/'assets'/'Anton-Regular.ttf'
W,H=1080,1920
NAVY=(11,16,32); PALE=(202,211,210); DIM=(107,126,133)
AMBER=(245,197,66); GOLD=(245,209,78); RED=(226,69,60); GREEN=(124,242,156)
_f={}
def font(size):
    if size not in _f: _f[size]=ImageFont.truetype(str(FONT),size)
    return _f[size]
def txt(d,xy,text,size=50,fill=PALE,anchor=None,spacing=4):
    d.text(xy,str(text),font=font(size),fill=fill,anchor=anchor,spacing=spacing)
def ctext(d,x,y,text,size=50,fill=PALE): txt(d,(x,y),text,size,fill,'mm')
def glow(im,x,y,r,color,alpha=80):
    r=int(r);sz=2*r+1
    layer=Image.new('RGBA',(sz,sz));ld=ImageDraw.Draw(layer)
    ld.ellipse((r*.45,r*.45,r*1.55,r*1.55),fill=(*color,alpha))
    layer=layer.filter(ImageFilter.GaussianBlur(r*.30))
    im.paste(layer,(int(x-r),int(y-r)),layer)
def rounded(d,box,r,fill,outline=None,width=1):d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)
def base():
    x=np.linspace(-1,1,W,dtype=np.float32)[None,:];y=np.linspace(-1,1,H,dtype=np.float32)[:,None]
    light=np.exp(-((x*.95)**2+(y*.85+.08)**2)*2.1)
    vignette=1-.53*np.clip((x*x+(y*.9)**2)**.65,0,1)
    arr=np.empty((H,W,3),np.uint8)
    for k,(v,add) in enumerate(zip(NAVY,(20,26,38))):arr[:,:,k]=np.clip((v+add*light)*vignette,0,255).astype(np.uint8)
    return Image.fromarray(arr,'RGB')
BASE=base()
def header(im,number,section):
    d=ImageDraw.Draw(im,'RGBA')
    txt(d,(88,166),'02:41 A.M.  /  NIGHT SHIFT',42,(*PALE,235))
    txt(d,(88,235),section,42,(*DIM,240))
    txt(d,(802,166),'LIVE',42,(*AMBER,235))
    d.line((88,220,992,220),fill=(98,118,128,105),width=2)
    d.line((88,301,992,301),fill=(98,118,128,75),width=2)
    txt(d,(882,235),f'{number:02}',42,(120,137,145,190))
    # Very subtle dark caption shelf; captions themselves are rendered afterwards.
    for i in range(180):
        a=int(54*math.sin(math.pi*i/180)**2)
        d.line((65,1340+i*2,1015,1340+i*2),fill=(3,7,14,a),width=2)
    return d

def elevator(im,open_door=False,red=True):
    d=ImageDraw.Draw(im,'RGBA'); glow(im,540,790,340,AMBER,58); d=ImageDraw.Draw(im,'RGBA')
    rounded(d,(160,355,920,1245),24,(14,22,35,255),(72,83,92,255),8)
    rounded(d,(213,418,867,1205),8,(18,25,36,255),(88,96,100,255),5)
    if open_door:
        d.rectangle((221,425,859,1199),fill=(5,10,17,255))
        d.rectangle((221,425,330,1199),fill=(47,56,62,255))
        d.rectangle((750,425,859,1199),fill=(47,56,62,255))
        d.polygon([(342,1196),(738,1196),(870,1300),(210,1300)],fill=(193,143,55,70))
        d.line((328,428,328,1197),fill=(123,120,94,150),width=5)
        d.line((752,428,752,1197),fill=(123,120,94,150),width=5)
    else:
        d.rectangle((223,427,538,1197),fill=(42,50,56,255))
        d.rectangle((542,427,857,1197),fill=(35,43,50,255))
        d.line((540,430,540,1196),fill=(7,12,19,255),width=8)
        d.line((236,442,236,1185),fill=(91,101,102,120),width=3)
    rounded(d,(448,373,632,433),8,(9,12,17,255),(89,87,74,255),2)
    ctext(d,540,398,'13',50,RED if red else AMBER)
    return d

def people(d,count,base_y=1148,scale=1.0):
    step=145 if count<=3 else 125; xs=[540+(i-(count-1)/2)*step for i in range(count)]
    for x in xs:
        r=int(34*scale); top=int(base_y-230*scale)
        d.ellipse((x-r,top-r,x+r,top+r),fill=(7,12,19,255),outline=(53,67,68,255),width=3)
        d.polygon([(x-43*scale,top+42*scale),(x+43*scale,top+42*scale),
                   (x+58*scale,base_y),(x-58*scale,base_y)],fill=(8,14,21,255),outline=(53,67,68,255))
        d.line((x-40*scale,base_y,x-52*scale,base_y+38*scale),fill=(8,14,21,255),width=int(24*scale))
        d.line((x+40*scale,base_y,x+52*scale,base_y+38*scale),fill=(8,14,21,255),width=int(24*scale))

def ledger(im,count=0,next_shift=False):
    d=ImageDraw.Draw(im,'RGBA');glow(im,540,820,330,AMBER,38);d=ImageDraw.Draw(im,'RGBA')
    rounded(d,(165,362,915,1275),18,(18,27,37,255),(84,99,102,255),6)
    rounded(d,(204,400,876,1235),4,(48,56,57,255),(115,122,105,255),3)
    d.rectangle((222,417,858,1219),fill=(35,45,49,255))
    txt(d,(258,461),'NEXT SHIFT' if next_shift else 'EXIT LOG',60,(*PALE,255))
    txt(d,(260,543),'FLOOR  /  COUNT',42,(159,172,156,255))
    d.line((254,611,828,611),fill=(167,175,151,180),width=3)
    if next_shift:
        txt(d,(260,665),'SHIFT STARTED',64,(*AMBER,255))
        txt(d,(260,795),'GUARD',46,(150,162,150,255))
        d.line((260,880,795,880),fill=(159,172,156,190),width=4)
        d.rectangle((260,969,800,1032),fill=(24,33,37,255))
    else:
        for i in range(4):
            y=662+i*122;d.line((255,y+83,824,y+83),fill=(142,157,145,90),width=2)
            txt(d,(270,y),f'0{i+1}',52,(121,143,135,255))
            if i<count:
                txt(d,(665,y-7),str(i+1),72,(*(AMBER if i<2 else RED),255))
        txt(d,(260,1134),'ARRIVALS  /  13',42,(135,149,139,220))
    return d

def camera(im,alt=False):
    glow(im,540,790,320,GREEN,38);d=ImageDraw.Draw(im,'RGBA')
    rounded(d,(148,373,932,1230),25,(15,26,31,255),(74,111,94,255),7)
    rounded(d,(189,414,891,1188),8,(9,23,25,255),(56,100,75,255),3)
    txt(d,(230,460),'CAM 04  /  ARRIVAL',48,(140,208,154,255));txt(d,(733,460),'LIVE',42,(*RED,240))
    for y in range(520,1070,44):d.line((224,y,858,y),fill=(89,145,105,17),width=2)
    d.rectangle((326,552,754,1050),outline=(115,179,130,200),width=5)
    d.rectangle((368,596,712,1018),outline=(72,125,89,190),width=4)
    d.line((540,600,540,1014),fill=(74,130,90,180),width=3)
    d.line((362,1049,718,1049),fill=(110,169,122,160),width=3)
    ctext(d,540,1122,'EMPTY',55,(151,211,157,220))
    for x,y in [(238,550),(842,550),(238,1034),(842,1034)]:
        d.line((x-18,y,x+18,y),fill=(118,200,140,170),width=2);d.line((x,y-18,x,y+18),fill=(118,200,140,170),width=2)
    return d

def desk(im,reveal=False):
    d=ImageDraw.Draw(im,'RGBA')
    if reveal:
        elevator(im,False); d=ImageDraw.Draw(im,'RGBA')
        # Re-open central panel visually: desk and monitor are inside the car frame.
        d.rectangle((283,495,796,1045),fill=(22,31,37,255),outline=(88,101,94,255),width=3)
    else:
        glow(im,540,710,300,AMBER,30);d=ImageDraw.Draw(im,'RGBA')
        d.rectangle((152,362,928,1160),fill=(20,29,39,230),outline=(68,81,89,200),width=5)
    rounded(d,(322,527,720,792),10,(12,21,25,255),(70,114,91,255),5)
    d.rectangle((349,553,692,760),fill=(14,38,35,255));txt(d,(382,612),'CAM 04',52,(118,192,139,255))
    d.line((522,794,522,836),fill=(86,99,95,255),width=10)
    d.polygon([(206,893),(874,893),(936,1012),(144,1012)],fill=(77,78,66,255),outline=(143,136,99,255),width=4)
    d.rectangle((159,1012,919,1185),fill=(32,40,41,255),outline=(94,101,91,255),width=4)
    rounded(d,(586,907,787,984),5,(168,154,113,255),(70,65,53,255),3)
    d.line((612,928,756,928),fill=(74,77,65,200),width=2);d.line((612,953,756,953),fill=(74,77,65,200),width=2)
    d.line((347,971,490,922),fill=(185,173,134,255),width=9)
    ctext(d,540,1097,'SECURITY',64,(137,150,142,255))
    return d

def directory(im):
    d=ImageDraw.Draw(im,'RGBA');rounded(d,(168,370,912,1270),18,(21,31,42,255),(74,92,100,255),6)
    ctext(d,540,456,'FLOOR DIRECTORY',60,PALE)
    for i in range(12):
        row=i//3;col=i%3;x=250+col*220;y=560+row*125
        rounded(d,(x,y,x+170,y+90),6,(34,47,55,255),(81,103,104,255),2);ctext(d,x+85,y+44,f'{i+1:02}',53,(172,187,178))
    rounded(d,(250,1110,830,1205),6,(53,31,36,255),(*RED,210),3)
    ctext(d,540,1158,'13  /  NO FLOOR',57,RED)

def plan(im,close=False):
    glow(im,540,800,300,GREEN,22);d=ImageDraw.Draw(im,'RGBA')
    rounded(d,(140,365,940,1260),12,(13,34,42,255),(74,119,124,255),6)
    txt(d,(202,420),'BUILDING PLAN',62,(161,205,201,255))
    if not close:
        for j in range(3):
            for i in range(4):
                x=230+i*153;y=550+j*150
                d.rectangle((x,y,x+118,y+105),outline=(91,155,151,220),width=4)
                txt(d,(x+24,y+22),f'{j*4+i+1:02}',48,(102,166,154,255))
        d.line((225,1042,856,1042),fill=(101,166,158,180),width=3)
        ctext(d,540,1117,'GUARD BOOTH  /  —',49,(194,175,124,255))
    else:
        d.rectangle((218,568,862,980),outline=(93,162,152,220),width=4)
        for x in range(250,850,100):d.line((x,580,x,969),fill=(64,114,111,70),width=2)
        for y in range(600,970,90):d.line((230,y,850,y),fill=(64,114,111,70),width=2)
        ctext(d,540,730,'BOOTH',90,(173,204,190));ctext(d,540,858,'NO MATCH',83,RED)
        txt(d,(230,1060),'SEARCH COMPLETE',44,(110,162,149,255))

def protocol(im):
    d=ImageDraw.Draw(im,'RGBA');rounded(d,(145,385,935,1250),20,(25,34,43,255),(86,104,107,255),6)
    txt(d,(215,458),'LIFT  /  PROTOCOL',60,(*PALE,255))
    d.line((215,553,865,553),fill=(113,129,130,170),width=3)
    rounded(d,(215,604,865,835),8,(31,45,46,255),(112,144,119,255),3)
    txt(d,(260,650),'01',70,(*GREEN,255));txt(d,(380,648),'COUNT EXITS',65,(*AMBER,255))
    d.polygon([(277,753),(340,753),(340,733),(390,779),(340,823),(340,802),(277,802)],fill=(115,183,132,255))
    rounded(d,(215,881,865,1113),8,(40,38,43,255),(115,85,84,255),3)
    txt(d,(260,930),'02',70,(*RED,255));txt(d,(380,932),'IGNORE ENTRY',61,(178,185,177,255))
    d.line((265,1055,345,976),fill=(*RED,220),width=9)

def tower(im):
    d=ImageDraw.Draw(im,'RGBA');glow(im,830,415,120,(190,210,220),35);d=ImageDraw.Draw(im,'RGBA')
    d.ellipse((807,389,855,437),fill=(174,192,203,230))
    for x,y in [(145,430),(325,356),(920,510),(720,344),(178,632),(905,703)]:d.ellipse((x,y,x+5,y+5),fill=(117,146,157,155))
    glow(im,545,900,330,AMBER,34);d=ImageDraw.Draw(im,'RGBA')
    d.polygon([(260,1255),(260,488),(540,374),(820,488),(820,1255)],fill=(25,34,45,255),outline=(76,91,99,255),width=5)
    d.rectangle((305,506,775,1216),fill=(20,29,40,255),outline=(68,81,89,255),width=3)
    for r in range(12):
        for c in range(5):
            x=330+c*90;y=530+r*53
            lit=((r*7+c*3)%9 in (0,2,5))
            d.rectangle((x,y,x+49,y+26),fill=((*AMBER,135) if lit else (34,48,58,255)))
    d.rectangle((475,1160,605,1255),fill=(9,15,23,255),outline=(90,96,88,255),width=3)
    d.line((540,1160,540,1255),fill=(75,79,74,200),width=3)
    d.line((150,1256,930,1256),fill=(90,104,108,140),width=3)

def pen(im):
    d=ImageDraw.Draw(im,'RGBA');glow(im,540,820,300,AMBER,35);d=ImageDraw.Draw(im,'RGBA')
    rounded(d,(155,480,925,1150),25,(37,43,45,255),(78,90,90,255),5)
    d.polygon([(239,940),(720,640),(777,674),(296,974)],fill=(151,159,143,255),outline=(31,36,34,255),width=4)
    d.polygon([(204,983),(239,940),(296,974)],fill=(198,170,98,255),outline=(37,39,34,255),width=3)
    d.line((325,924,739,665),fill=(213,210,175,180),width=5)
    txt(d,(215,1058),'PEN  /  STILL HERE',51,(165,176,160,255))

def camera_turn(im):
    glow(im,540,795,300,RED,30);d=ImageDraw.Draw(im,'RGBA')
    rounded(d,(155,390,925,1220),18,(24,31,39,255),(80,91,98,255),5)
    d.ellipse((300,524,780,1004),fill=(42,49,51,255),outline=(118,130,119,255),width=7)
    d.ellipse((382,606,698,922),fill=(10,18,22,255),outline=(96,133,112,255),width=8)
    d.ellipse((451,675,629,853),fill=(27,57,48,255),outline=(135,206,151,255),width=4)
    d.ellipse((502,714,555,767),fill=(152,219,174,150))
    d.arc((260,470,820,1060),200,322,fill=(*AMBER,200),width=10)
    d.polygon([(794,798),(846,833),(776,855)],fill=(*AMBER,210))
    ctext(d,540,1119,'CAMERA  /  TURN',55,PALE)

def guard(im):
    elevator(im,False);d=ImageDraw.Draw(im,'RGBA')
    d.rectangle((258,499,822,1009),fill=(30,38,42,255))
    # Faceless seated guard, no hands or photographic elements.
    d.ellipse((470,605,610,745),fill=(8,14,20,255),outline=(90,101,91,255),width=4)
    rounded(d,(427,751,653,1008),34,(8,14,20,255),(75,87,81,255),3)
    d.rectangle((290,963,790,1114),fill=(63,70,63,255),outline=(122,127,105,255),width=4)
    d.rectangle((588,817,762,941),fill=(10,23,23,255),outline=(83,141,102,255),width=4)
    ctext(d,540,1052,'SECURITY',53,(149,162,143))

def floor_display(im,last=False):
    glow(im,540,780,320,RED if last else AMBER,65);d=ImageDraw.Draw(im,'RGBA')
    rounded(d,(182,398,898,1226),35,(28,32,37,255),(102,104,94,255),7)
    rounded(d,(248,478,832,1100),20,(9,13,18,255),(84,81,71,255),5)
    txt(d,(318,540),'FLOOR',60,(144,157,146,255))
    ctext(d,540,820,'13',300,RED if last else AMBER)
    d.line((318,1035,762,1035),fill=(93,109,98,190),width=3)
    ctext(d,540,1167,'ARRIVAL',52,(169,171,146))

def draw_scene(i):
    im=BASE.copy(); sections=['TOWER / EXTERIOR','LIFT / FLOOR','DIRECTORY / 12','SECURITY / DESK','PROTOCOL / EXITS','THRESHOLD / OUT','LOG / OPEN','ARRIVAL / 01','CAMERA / EMPTY','LOG / 01','ARRIVAL / 02','CAMERA / EMPTY','LOG / 02','ARRIVAL / 03','LOG / 03','DESK / PEN','BUILDING / PLAN','BOOTH / SEARCH','CAMERA / TURN','LIFT / INTERIOR','GUARD / INSIDE','ARRIVAL / 04','SHIFT / NEXT','DISPLAY / READ','FLOOR / 13']
    header(im,i,sections[i-1])
    if i==1:tower(im)
    elif i==2:elevator(im)
    elif i==3:directory(im)
    elif i==4:desk(im)
    elif i==5:protocol(im)
    elif i==6:elevator(im,True)
    elif i==7:ledger(im,0)
    elif i in (8,11,22):
        elevator(im,True);d=ImageDraw.Draw(im,'RGBA');people(d,{8:1,11:2,22:4}[i]);ctext(d,540,1120,f'{ {8:1,11:2,22:4}[i]:02}  /  EXITS',43,AMBER)
    elif i in (9,12):camera(im,i==12)
    elif i==10:ledger(im,1)
    elif i==13:ledger(im,2)
    elif i==14:
        desk(im);d=ImageDraw.Draw(im,'RGBA')
        for k in range(3):
            x=300+k*220;d.polygon([(x,925),(x+53,925),(x+164,1190),(x+77,1190)],fill=(4,9,15,215))
        ctext(d,540,760,'03  /  EXITS',64,RED)
    elif i==15:ledger(im,3)
    elif i==16:pen(im)
    elif i==17:plan(im)
    elif i==18:plan(im,True)
    elif i==19:camera_turn(im)
    elif i==20:desk(im,True)
    elif i==21:guard(im)
    elif i==23:ledger(im,0,True)
    elif i==24:floor_display(im)
    elif i==25:floor_display(im,True)
    return im

def landscape_bg(path):
    w,h=1920,1080;x=np.linspace(-1,1,w,dtype=np.float32)[None,:];y=np.linspace(-1,1,h,dtype=np.float32)[:,None]
    light=np.exp(-((x*.7)**2+y*y)*2.0);a=np.empty((h,w,3),np.uint8)
    for k,(v,c) in enumerate(zip((8,12,23),(13,19,28))):a[:,:,k]=np.clip(v+c*light,0,255).astype(np.uint8)
    im=Image.fromarray(a,'RGB');d=ImageDraw.Draw(im,'RGBA')
    d.line((90,135,570,135),fill=(96,118,122,155),width=2);d.line((1350,135,1830,135),fill=(96,118,122,155),width=2)
    txt(d,(100,180),'NIGHT SHIFT',47,(*DIM,255));txt(d,(100,285),'ARRIVAL',96,(*PALE,255));txt(d,(100,391),'LOG',96,(*PALE,255))
    d.rectangle((100,535,430,543),fill=(*AMBER,180));txt(d,(100,590),'SECURITY  /  02:41',42,(132,153,148,255))
    txt(d,(1394,180),'EXIT COUNT',50,(*DIM,255))
    for i in range(4):
        y0=310+i*133;txt(d,(1394,y0),f'0{i+1}',75,(*(AMBER if i<3 else RED),220));d.line((1500,y0+60,1790,y0+60),fill=(80,101,101,140),width=3)
    txt(d,(1394,904),'FLOOR  /  13',47,(145,153,135,255));im.save(path,optimize=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    for i in range(1,26):
        draw_scene(i).save(a.out/f'shot{i:02}.png',optimize=True)
        print('art',i,'/25',flush=True)
    landscape_bg(a.out/'landscape-bg.png')
    # One restrained animated detail per shot: a moving live-camera cursor.
    dot=Image.new('RGBA',(70,70));d=ImageDraw.Draw(dot)
    d.ellipse((12,12,58,58),outline=(245,197,66,100),width=3);d.ellipse((27,27,43,43),fill=(245,197,66,225));dot.save(a.out/'cursor.png')
    with (a.out/'shots.ffconcat').open('w') as f:
        f.write('ffconcat version 1.0\n')
        for i in range(1,26):f.write(f"file '{(a.out/f'shot{i:02}.png').resolve()}'\nduration 2.4\n")
        f.write(f"file '{(a.out/'shot25.png').resolve()}'\n")
if __name__=='__main__':main()
