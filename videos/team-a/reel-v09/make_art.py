#!/usr/bin/env python3
"""Original PERFECT TIME call-centre screen furniture and perspective art."""
import argparse,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
HERE=Path(__file__).resolve().parent;FONT=HERE/'assets/Anton-Regular.ttf';W,H=1080,1920
ICE=(207,228,237);DIM=(111,150,169);CYAN=(93,214,224);AMBER=(247,198,83);RED=(235,78,87)
_fonts={}
def font(n):
    if n not in _fonts:_fonts[n]=ImageFont.truetype(str(FONT),n)
    return _fonts[n]
def text(d,xy,s,size=50,fill=ICE,anchor=None):d.text(xy,str(s),font=font(size),fill=fill,anchor=anchor)
def centre(d,x,y,s,size=50,fill=ICE):text(d,(x,y),s,size,fill,'mm')
def rr(d,b,r,fill,outline=None,width=1):d.rounded_rectangle(b,radius=r,fill=fill,outline=outline,width=width)
def glow(im,x,y,r,c,alpha=70):
    r=int(r);layer=Image.new('RGBA',(2*r+1,2*r+1));d=ImageDraw.Draw(layer)
    d.ellipse((r*.35,r*.35,r*1.65,r*1.65),fill=(*c,alpha));layer=layer.filter(ImageFilter.GaussianBlur(r*.26));im.paste(layer,(int(x-r),int(y-r)),layer)
def background():
    x=np.linspace(-1,1,W,dtype=np.float32)[None,:];y=np.linspace(-1,1,H,dtype=np.float32)[:,None]
    light=np.exp(-((x*.92)**2+(y*.85+.07)**2)*2.0);vig=1-.54*np.clip((x*x+(y*.91)**2)**.65,0,1)
    a=np.empty((H,W,3),np.uint8)
    for k,(v,inc) in enumerate(zip((8,14,29),(18,24,40))):a[:,:,k]=np.clip((v+inc*light)*vig,0,255).astype(np.uint8)
    return Image.fromarray(a,'RGB')
BASE=background()
def header(im,num,section):
    d=ImageDraw.Draw(im,'RGBA')
    text(d,(76,154),'02:41 A.M.  /  NIGHT LINE',42,(*ICE,245));text(d,(837,154),'LIVE',42,(*CYAN,255))
    d.line((76,215,1004,215),fill=(77,145,161,150),width=2)
    text(d,(76,233),section,42,(*DIM,245));text(d,(915,233),f'{num:02}',42,(*DIM,225))
    d.line((76,300,1004,300),fill=(77,145,161,85),width=2)
    d.line((140,1270,940,1270),fill=(79,169,188,115),width=3)
    for x in range(140,941,100):d.line((x,1262,x,1278),fill=(79,169,188,125),width=2)
    for i in range(130):
        a=int(36*math.sin(math.pi*i/130)**2);d.line((65,1360+2*i,1015,1360+2*i),fill=(3,8,17,a),width=2)
    return d

def shell(im,title):
    glow(im,540,730,300,CYAN,28);d=ImageDraw.Draw(im,'RGBA')
    rr(d,(130,350,950,1148),22,(17,28,48,255),(70,117,142,255),6)
    rr(d,(165,382,915,1112),9,(11,23,40,255),(49,90,112,255),3)
    size=56
    while font(size).getlength(title)>665:size-=2
    text(d,(205,417),title,size,(*ICE,255));d.line((205,497,875,497),fill=(69,143,159,155),width=3)
    return d

def office(im):
    glow(im,540,730,300,CYAN,42);d=ImageDraw.Draw(im,'RGBA')
    # Perspective: ceiling, side walls, aisle, floor seams and progressively smaller desks
    # converge toward the terminal at (540, 650), not a flat face-on diagram.
    d.polygon([(96,350),(984,350),(675,573),(405,573)],fill=(34,48,66,255))
    d.polygon([(96,350),(405,573),(405,820),(96,1148)],fill=(24,37,56,255))
    d.polygon([(984,350),(675,573),(675,820),(984,1148)],fill=(23,35,54,255))
    d.polygon([(96,1148),(984,1148),(675,820),(405,820)],fill=(29,42,58,255))
    for x in [130,300,440,640,780,950]:d.line((x,1148,540,650),fill=(80,120,133,140),width=3)
    for y,l,r in [(1070,175,905),(982,250,830),(906,325,755),(854,380,700)]:d.line((l,y,r,y),fill=(83,117,132,120),width=3)
    # Lights and the distant service desk shrink toward the vanishing point.
    for p in [[(266,386),(814,386),(765,422),(315,422)],[(356,461),(724,461),(695,484),(385,484)],[(428,516),(652,516),(638,530),(442,530)]]:d.polygon(p,fill=(137,181,191,165))
    d.rectangle((430,574,650,824),fill=(14,30,47,255),outline=(91,139,157,255),width=4)
    d.rectangle((485,627,595,694),fill=(35,95,115,255),outline=(*CYAN,230),width=3)
    centre(d,540,658,'01',39,CYAN)
    # Desk tops and monitor silhouettes form three depth planes on both sides.
    for poly in [[(95,857),(280,749),(407,789),(242,1043)],[(216,755),(345,698),(425,724),(318,863)],[(331,687),(418,660),(464,673),(398,749)]]:
        d.polygon(poly,fill=(43,65,82,255),outline=(98,145,157,235))
        d.polygon([(1080-x,y) for x,y in poly],fill=(42,64,81,255),outline=(98,145,157,235))
    for b in [(102,617,262,755),(258,615,348,698),(376,605,426,660)]:
        d.rectangle(b,fill=(13,29,44,255),outline=(100,163,175,255),width=3)
        x0,y0,x1,y1=b;d.line((x0+12,y0+20,x1-12,y0+20),fill=(*CYAN,190),width=3)
        rb=(1080-x1,y0,1080-x0,y1);d.rectangle(rb,fill=(13,29,44,255),outline=(100,163,175,255),width=3)
        d.line((rb[0]+12,y0+20,rb[2]-12,y0+20),fill=(*CYAN,190),width=3)
    text(d,(158,1038),'FLOOR  /  NIGHT SHIFT',44,(154,190,200,255))

def queue(im,mode=0):
    d=shell(im,'QUEUE  /  WAITING')
    text(d,(215,526),'CALLERS WAITING',48,(*DIM,255));text(d,(682,510),'01',96,(*AMBER,255))
    rr(d,(208,675,872,825),9,(25,49,67,255),(75,145,158,230),3)
    text(d,(245,706),('CALLER  0324' if mode==0 else 'NEXT  0325'),54,(*ICE,255))
    text(d,(682,710),'WAIT',46,(*CYAN,255))
    if mode==2:
        text(d,(230,880),'ONE LEAVES  /  ONE ENTERS',45,(171,203,209,255))
    elif mode==3:
        text(d,(230,880),'WAITING NEVER REACHES 0',45,(171,203,209,255))
    else:
        text(d,(230,880),'NEXT IN QUEUE',47,(171,203,209,255))
        text(d,(230,956),'REPLACEMENT  /  READY',45,(*DIM,255))

def ledger(im):
    d=shell(im,'RESOLUTION LEDGER')
    text(d,(215,530),'CALLER',45,(*DIM,255));text(d,(535,530),'RECORD',45,(*DIM,255))
    for i,(n,status) in enumerate([('0321','RESOLVED'),('0322','RESOLVED'),('0323','RESOLVED')]):
        y=615+i*100;d.line((215,y+80,865,y+80),fill=(67,119,136,130),width=2)
        text(d,(230,y),n,55,(*ICE,255));text(d,(530,y),status,48,(135,196,188,255))
    rr(d,(218,950,860,1040),7,(28,51,67,255),(76,145,161,200),2)
    text(d,(243,962),'NEXT  /  0324',48,(*AMBER,255))

def metric(im,mode=0):
    d=shell(im,'HANDLING TIME')
    if mode in (0,1,2):text(d,(215,526),'AVERAGE',49,(*DIM,255))
    if mode==0:
        text(d,(215,606),'00:40',125,(*AMBER,255));text(d,(215,795),'TARGET MET',53,(*CYAN,255))
        text(d,(215,915),'CALLS  /  RESOLVED',46,(*DIM,255))
    elif mode==1:
        d.ellipse((245,554,835,1004),outline=(63,132,151,255),width=8)
        d.arc((245,554,835,1004),start=220,end=520,fill=(*AMBER,245),width=15)
        centre(d,540,747,'00:40',112,AMBER);centre(d,540,885,'EXACTLY',48,ICE)
    elif mode==2:
        text(d,(215,570),'PERFECT',85,(*AMBER,255));text(d,(215,684),'00:40  /  12 OF 12',58,(*ICE,255))
        for i in range(12):
            x=220+i*52;d.rectangle((x,868,x+29,1010),fill=(82,177,186,220))
        text(d,(215,1032),'HANDLING TIME',42,(*DIM,255))
    elif mode=='hidden':
        text(d,(215,555),'AVERAGE  /  00:40',63,(*AMBER,255));text(d,(215,707),'MEASURING',54,(*DIM,255))
        for j in range(7):d.rectangle((225+j*88,808,286+j*88,875),fill=(72,117,133,205))
        text(d,(215,964),'LINE  /  CONNECTED',48,(*CYAN,255))
    else:
        text(d,(215,555),'AVERAGE  /  00:40',63,(*AMBER,255));text(d,(215,707),'MEASURING',54,(*DIM,255))
        text(d,(215,793),'CALLERS',98,(*RED,255));text(d,(215,970),'NOT CALLS',54,(*ICE,255))

def lines(im,variant=0):
    d=shell(im,'LINE STATUS')
    text(d,(215,526),'CHANNEL',44,(*DIM,255));text(d,(480,526),'RECORD',44,(*DIM,255));text(d,(720,526),'LINE',44,(*DIM,255))
    for i in range(5):
        y=601+i*88
        if i==variant:rr(d,(210,y-5,870,y+70),7,(25,52,67,255),(72,154,166,180),2)
        text(d,(225,y),f'{i+1:02}',49,(*ICE,255));text(d,(470,y),'RESOLVED',44,(180,181,166,255))
        text(d,(732,y),'LIVE',46,(*CYAN,255))
        d.line((218,y+75,865,y+75),fill=(74,127,143,105),width=2)
    text(d,(220,1055),'CONNECTED  /  05',42,(*CYAN,255))

def search(im,second=False):
    d=shell(im,'CALLER SEARCH')
    text(d,(215,540),'QUERY',46,(*DIM,255));rr(d,(215,615,865,756),7,(24,47,64,255),(84,151,168,255),3)
    text(d,(245,641),'CALLER  /  '+('02' if second else '01'),67,(*ICE,255))
    text(d,(215,825),'OPEN RECORD',54,(*CYAN,255))
    text(d,(215,950),'LINE  /  LIVE',52,(*AMBER,255))

def record(im,n=1,emphasize='caller'):
    d=shell(im,'CALLER RECORD')
    text(d,(215,525),'CALLER',45,(*DIM,255));text(d,(714,515),f'{n:02}',78,(*ICE,255))
    rr(d,(215,642,865,794),8,(62,32,45,255),(*RED,210),3)
    text(d,(240,655),'STATUS',43,(196,150,155,255));text(d,(455,653),'FINISHED',70,(*RED,255))
    rr(d,(215,844,865,994),8,(24,57,67,255),(85,177,184,230),3)
    text(d,(240,858),'LINE',43,(153,190,196,255));text(d,(480,855),'LIVE',76,(*CYAN,255))
    if emphasize=='line':text(d,(220,1030),'CONNECTION  /  OPEN',42,(*DIM,255))

def signal_panel(im,variant=0):
    d=shell(im,'HEADSET SIGNAL')
    text(d,(215,525),'LINE  /  CONNECTED',52,(*CYAN,255))
    rr(d,(215,660,865,925),9,(18,44,61,255),(69,137,156,255),3)
    for yy in [720,790,860]:d.line((242,yy,838,yy),fill=(61,111,133,100),width=2)
    pts=[]
    for x in range(245,836,4):
        y=790+43*math.sin((x-245)*.04)+18*math.sin((x-245)*.08);pts.append((x,y))
    d.line(pts,fill=(*CYAN,255),width=5)
    text(d,(220,980),('VOICE  /  QUIET' if variant else 'SIGNAL  /  ACTIVE'),51,(*AMBER,255))

def headset(im,timer='00:23'):
    d=shell(im,'AGENT  /  HEADSET')
    d.arc((225,560,610,945),start=180,end=359,fill=(108,167,180,255),width=28)
    rr(d,(215,731,275,907),14,(59,99,113,255),(135,190,197,255),4)
    rr(d,(560,731,620,907),14,(59,99,113,255),(135,190,197,255),4)
    d.line((605,860,670,918,717,918),fill=(135,190,197,255),width=10)
    d.ellipse((710,906,737,933),fill=(*CYAN,255))
    text(d,(220,993),'LINE  /  LIVE',48,(*CYAN,255))
    rr(d,(657,631,865,817),9,(53,43,37,255),(171,136,81,220),3)
    centre(d,761,691,'TIMER',43,AMBER);centre(d,761,765,timer,63,ICE)

def call_status(im,mode=0):
    d=shell(im,'ACTIVE CONNECTION')
    text(d,(215,530),'CHANNEL  /  01',52,(*DIM,255));text(d,(215,625),'LINE  LIVE',76,(*CYAN,255))
    d.line((215,750,865,750),fill=(75,140,156,190),width=3)
    text(d,(215,800),'CALLER STATUS',50,(*DIM,255))
    if mode==0:text(d,(215,890),'IN PROGRESS',68,(*ICE,255))
    else:text(d,(215,890),'FINISHED',84,(*RED,255))

def timer(im):
    d=shell(im,'AGENT TIMER')
    text(d,(215,535),'CALLER  /  0325',49,(*DIM,255));centre(d,540,746,'00:40',135,AMBER)
    text(d,(215,920),'LINE  /  STILL LIVE',53,(*CYAN,255))

def handoff(im):
    d=shell(im,'AGENT HANDOFF')
    text(d,(215,535),'NEW AGENT',53,(*DIM,255))
    rr(d,(215,645,865,803),9,(24,57,67,255),(80,170,182,230),3)
    text(d,(243,675),'AGENT  /  02',62,(*ICE,255))
    text(d,(215,884),'LINE  CONNECTED',57,(*CYAN,255))
    text(d,(215,1001),'WAITING  /  01',47,(*AMBER,255))

def name_prompt(im,hook=False):
    d=shell(im,'INCOMING VOICE')
    if not hook:
        text(d,(215,545),'PLEASE IDENTIFY',55,(*DIM,255))
        rr(d,(215,665,865,835),8,(25,48,64,255),(88,153,166,255),3)
        text(d,(245,710),'NAME  /  _',72,(*ICE,255));text(d,(215,940),'NEXT AGENT  /  LIVE',48,(*CYAN,255))
    else:
        text(d,(215,545),'NEXT VOICE',55,(*DIM,255))
        rr(d,(215,650,865,1010),9,(61,31,43,255),(*RED,220),3)
        centre(d,540,735,'DO NOT GIVE',76,RED)
        centre(d,540,825,'THEM YOUR',76,ICE)
        centre(d,540,920,'NAME',98,RED)

LABELS=['FLOOR / NIGHT SHIFT','QUEUE / ONE WAITING','QUEUE / REPLACEMENT','LEDGER / RESOLVED','QUEUE / REPLACEMENT',
        'DASHBOARD / AHT','AHT / 00:40','AHT / PERFECT','LINE GRID / LIVE','CHANNELS / CONNECTED',
        'SEARCH / CALLER 01','RECORD / CALLER 01','CALLER / LINE LIVE','SEARCH / CALLER 02','RECORD / CALLER 02',
        'HEADSET / SIGNAL','SIGNAL / AFTER VOICE','HEADSET / TIMER','AGENT / TIMER','METRIC / UNKNOWN',
        'METRIC / HOLD','METRIC / CALLERS','CONNECTION / LIVE','CALLER / STATUS','STATUS / FINISHED',
        'TIMER / 00:40','QUEUE / STILL ONE','HANDOFF / NEW AGENT','VOICE / NAME','VOICE / WARNING']
def draw_scene(i):
    im=BASE.copy();header(im,i,LABELS[i-1])
    if i==1:office(im)
    elif i==2:queue(im,0)
    elif i==3:queue(im,2)
    elif i==4:ledger(im)
    elif i==5:queue(im,3)
    elif i in (6,7,8):metric(im,i-6)
    elif i in (9,10):lines(im,i-9)
    elif i==11:search(im,False)
    elif i==12:record(im,1)
    elif i==13:record(im,1,'line')
    elif i==14:search(im,True)
    elif i==15:record(im,2,'line')
    elif i in (16,17):signal_panel(im,i==17)
    elif i==18:headset(im,'00:23')
    elif i==19:headset(im,'00:25')
    elif i in (20,21):metric(im,'hidden')
    elif i==22:metric(im,'reveal')
    elif i==23:call_status(im,0)
    elif i in (24,25):call_status(im,1)
    elif i==26:timer(im)
    elif i==27:queue(im,3)
    elif i==28:handoff(im)
    elif i==29:name_prompt(im,False)
    elif i==30:name_prompt(im,True)
    return im

def landscape_bg(path):
    w,h=1920,1080;x=np.linspace(-1,1,w,dtype=np.float32)[None,:];y=np.linspace(-1,1,h,dtype=np.float32)[:,None];l=np.exp(-((x*.7)**2+y*y)*2.1)
    a=np.empty((h,w,3),np.uint8)
    for k,(v,c) in enumerate(zip((6,12,27),(16,22,36))):a[:,:,k]=np.clip(v+c*l,0,255).astype(np.uint8)
    im=Image.fromarray(a,'RGB');d=ImageDraw.Draw(im,'RGBA')
    d.line((64,130,370,130),fill=(83,149,162,160),width=2);d.line((1540,130,1850,130),fill=(83,149,162,160),width=2)
    text(d,(76,185),'NIGHT LINE',48,(*DIM,255));text(d,(76,310),'PERFECT',72,(*ICE,255));text(d,(76,407),'TIME',92,(*ICE,255))
    d.rectangle((76,548,340,555),fill=(*AMBER,190));text(d,(76,602),'02:41 A.M.',48,(145,184,194,255))
    text(d,(1530,185),'QUEUE',53,(*DIM,255));text(d,(1530,265),'WAITING',48,(*DIM,255));text(d,(1530,335),'01',91,(*AMBER,255))
    for i in range(3):
        y0=520+i*125;d.rectangle((1530,y0,1554,y0+24),outline=(106,158,170,200),width=3);d.line((1590,y0+18,1850,y0+18),fill=(81,132,151,130),width=3)
    text(d,(1530,920),'LINE  /  LIVE',43,(145,190,198,255));im.save(path,optimize=True)

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
