#!/usr/bin/env python3
"""Deterministic 1920x1080/30 fps kinetic-type animation, CC0 1.0 by reel.

With no arguments, write exactly 1800 RGB frames to stdout for FFmpeg.
`--preview seconds output.png` writes a single frame without an encoder.
"""
import functools
import math
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SECONDS = 1920, 1080, 30, 60
HERE = Path(__file__).resolve().parent
INK = (17, 40, 43)
DARK = (13, 48, 50)
CREAM = (247, 243, 226)
PAPER = (241, 236, 218)
PALE = (224, 239, 222)
TEAL = (0, 106, 94)
MINT = (181, 219, 191)
CORAL = (244, 126, 91)
YELLOW = (250, 205, 96)
MUTED_DARK = (29, 69, 69)
MUTED_PAPER = (221, 222, 200)
FONT_FILES = {
    'regular': HERE / 'DejaVuSans.ttf',
    'bold': HERE / 'DejaVuSans-Bold.ttf',
    'mono': HERE / 'DejaVuSansMono.ttf',
}
SHOTS = [
    (0, 6, 'Why does waiting explode before a system is full?'),
    (6, 13, 'One barista finishes one order a minute, on average.'),
    (13, 21, 'But arrivals and service times vary. Little rushes make a queue.'),
    (21, 29, 'At 50% busy, this model predicts a 1-minute average wait.'),
    (29, 39, 'At 90% busy, the average wait is 9 minutes—before service.'),
    (39, 49, 'In this random queue model, waiting rises nonlinearly.'),
    (49, 56, 'Spare capacity absorbs the unexpected instead of passing it on as delay.'),
    (56, 60, 'Leave room for the rush.'),
]
BG = [INK, PAPER, DARK, PALE, CORAL, INK, PALE, DARK]
LIGHT = [False, True, False, True, True, False, True, False]


@functools.lru_cache(maxsize=128)
def font(style, size):
    assert size >= 54, f'All screen typography must be >= 54 px, got {size}'
    return ImageFont.truetype(str(FONT_FILES[style]), size)


def clamp(x, a=0., b=1.):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1-x)**3


def lerp(a, b, x):
    return a + (b-a)*x


def text(draw, xy, content, size, color, style='bold', anchor='lt'):
    draw.text(xy, content, font=font(style, size), fill=color, anchor=anchor,
              stroke_width=0)


def circle(draw, x, y, r, fill=None, outline=None, width=1):
    draw.ellipse((round(x-r), round(y-r), round(x+r), round(y+r)),
                 fill=fill, outline=outline, width=width)


def arrow(draw, x1, y1, x2, y2, color, width=8, head=22):
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    a = math.atan2(y2-y1, x2-x1)
    p1 = (x2-head*math.cos(a-.55), y2-head*math.sin(a-.55))
    p2 = (x2-head*math.cos(a+.55), y2-head*math.sin(a+.55))
    draw.polygon([(x2,y2), p1, p2], fill=color)


def wrap(draw, content, max_width, f):
    words = content.split()
    lines, line = [], ''
    for word in words:
        test = (line + ' ' + word).strip()
        if draw.textlength(test, font=f) <= max_width or not line:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    assert len(lines) <= 2, (content, lines)
    return lines


@functools.lru_cache(maxsize=8)
def background(idx):
    im = Image.new('RGB', (W,H), BG[idx])
    d = ImageDraw.Draw(im)
    # A quiet drafting grid gives depth without competing with the type.
    col = MUTED_PAPER if LIGHT[idx] else MUTED_DARK
    if idx == 4:
        col = (225, 109, 80)
    for x in range(0, W, 160):
        d.line((x, 150, x, 910), fill=col, width=2)
    for y in (210, 370, 530, 690, 850):
        d.line((0, y, W, y), fill=col, width=2)
    return im


def backdrop_motion(d, idx, t):
    # Large, slowly moving graphic accents keep even the quiet shots alive.
    # Bands move visibly enough to register as motion even in quiet diagram
    # sections after H.264 compression; they remain behind the text/graphics.
    if idx == 4:
        c = (210, 94, 70)
    elif LIGHT[idx]:
        c = (196, 211, 190)
    else:
        c = (44, 80, 76)
    for k in range(5):
        x = (int(t*220) + k*410) % 2320 - 200
        d.line((x, 150, x+260, 910), fill=c, width=6)


def header(d, idx):
    color = INK if LIGHT[idx] else CREAM
    text(d, (96, 61), 'THE CAPACITY PROBLEM', 54, color, 'mono')
    text(d, (1820, 61), f'{idx+1:02d} / 08', 54, color, 'mono', 'rt')
    d.line((96, 136, 1824, 136), fill=color, width=3)


def footer(d, caption, t):
    d.rectangle((0, 910, W, H), fill=INK)
    d.line((0, 910, W, 910), fill=YELLOW, width=5)
    lines = wrap(d, caption, 1715, font('regular', 54))
    y = 929 if len(lines) == 2 else 957
    for line in lines:
        text(d, (100,y), line, 54, CREAM, 'regular')
        y += 65
    d.rectangle((0, 1068, W, 1079), fill=(47, 75, 69))
    d.rectangle((0, 1068, round(W*clamp((t+1/FPS)/60)), 1079), fill=YELLOW)


def token(d, x, y, r, fill, outline=None):
    circle(d, x, y, r, fill=fill, outline=outline, width=5)
    # Highlight is deliberately not a letter or a numeral.
    circle(d, x-r*.25, y-r*.25, max(3, r*.12), fill=CREAM if fill != CREAM else TEAL)


def clock(d, cx, cy, r, t, color, accent, track):
    circle(d, cx, cy, r, fill=None, outline=track, width=20)
    d.arc((cx-r, cy-r, cx+r, cy+r), start=-90, end=-90+(t*80)%360, fill=accent, width=20)
    for n in range(12):
        a = 2*math.pi*n/12 - math.pi/2
        r1, r2 = r-28, r-13
        d.line((cx+r1*math.cos(a), cy+r1*math.sin(a),
                cx+r2*math.cos(a), cy+r2*math.sin(a)), fill=color, width=5)
    a = -math.pi/2 + t*2*math.pi/4.4
    d.line((cx,cy,cx+math.cos(a)*r*.68,cy+math.sin(a)*r*.68), fill=color, width=12)
    a2 = -math.pi/2 + t*2*math.pi/14
    d.line((cx,cy,cx+math.cos(a2)*r*.42,cy+math.sin(a2)*r*.42), fill=accent, width=15)
    circle(d,cx,cy,13, fill=color)


def animated_text(draw, xy, content, size, color, t, delay=0.0, style='bold', anchor='lt'):
    """Staggered kinetic entrance; copy remains readable after settling."""
    if t < delay:
        return
    a = ease((t-delay)/.72)
    x,y = xy
    text(draw, (x-56*(1-a), y+20*(1-a)), content, size, color, style, anchor)


def shot_hook(d, t):
    animated_text(d, (100, 190), 'WHY DOES', 70, YELLOW, t, .0)
    animated_text(d, (100, 292), 'WAITING', 175, CREAM, t, .10)
    animated_text(d, (100, 483), 'EXPLODE?', 155, CORAL, t, .35)
    cx,cy,r = 1500,450,225
    clock(d, cx,cy,r,t,CREAM,YELLOW,(56,87,80))
    # Tokens feed a distinct bottleneck rather than orbiting in place.
    arrow(d, 1150, 832, 1775, 832, MINT, 7, 22)
    d.rounded_rectangle((1735, 695, 1795, 799), radius=14, fill=CORAL, outline=CREAM, width=4)
    for i in range(7):
        xx = 1170 + ((t*92+i*100) % 548)
        yy = 752 + 7*math.sin(t*3.0+i*.6)
        token(d, xx, yy, 28, CORAL if i < 4 else YELLOW)


def shot_server(d, t):
    animated_text(d, (100, 230), 'ONE ORDER', 128, INK, t, .0)
    animated_text(d, (100, 390), 'A MINUTE', 128, TEAL, t, .22)
    animated_text(d, (100, 582), 'ONE SERVER.', 66, INK, t, .8, 'mono')
    d.rounded_rectangle((1120, 208, 1790, 835), radius=48, fill=PALE, outline=INK, width=7)
    d.rounded_rectangle((1180, 267, 1730, 770), radius=28, fill=PAPER, outline=TEAL, width=5)
    clock(d,1455,414,125,t,INK,CORAL,(194,214,193))
    animated_text(d, (1232, 570), 'SERVICE', 58, INK, t, 1.0, 'mono')
    # A continuous flow crosses one service gate; this is an illustration, not a simulation.
    arrow(d, 1225, 690, 1690, 690, TEAL, 8, 22)
    d.rounded_rectangle((1427, 625, 1483, 754), radius=12, fill=TEAL, outline=INK, width=4)
    for i in range(5):
        x = 1220 + ((t*125+i*105)%470)
        token(d,x,690,22,CORAL if i%2 == 0 else YELLOW)


def shot_variation(d, t):
    animated_text(d, (100, 223), 'REAL LIFE', 135, CREAM, t, .0)
    animated_text(d, (100, 388), "ISN’T EVEN.", 122, YELLOW, t, .25)
    animated_text(d, (100, 565), 'VARIATION', 66, MINT, t, .9, 'mono')
    # Show the causal contrast: evenly spaced arrivals versus a clumped rush.
    animated_text(d,(1055,235),'EVEN FLOW',58,CREAM,t,.2,'mono')
    arrow(d,1045,365,1770,365,MINT,8,24)
    for i in range(6):
        xx=1065+((t*150+i*115)%670)
        token(d,xx,365,25,MINT)
    d.rounded_rectangle((1730,292,1800,430),radius=16,fill=TEAL,outline=CREAM,width=4)
    animated_text(d,(1055,525),'LITTLE RUSHES',58,YELLOW,t,1.0,'mono')
    arrow(d,1045,670,1770,670,MINT,8,24)
    for i,off in enumerate([0,55,110,345,400,455,510]):
        xx=1065+((t*150+off)%670)
        token(d,xx,670,28,CORAL if i%3 == 0 else YELLOW)
    d.rounded_rectangle((1730,596,1800,740),radius=16,fill=CORAL,outline=CREAM,width=4)


def gauge(d, cx, cy, r, value, t, bg, track, accent, color):
    circle(d,cx,cy,r,fill=bg,outline=track,width=32)
    # The 90% comparison continues from the prior 50% rather than starting over.
    initial = .5 if value == .9 else 0.0
    p = initial+(value-initial)*ease((t+.05)/1.8)
    d.arc((cx-r,cy-r,cx+r,cy+r), -90, -90+360*p, fill=accent, width=32)
    text(d, (cx, cy-30), f'{round(p*100)}%', 130, color, 'bold', 'mm')
    text(d, (cx, cy+93), 'BUSY', 61, color, 'mono', 'mm')
    a = t*2.0
    circle(d,cx+math.cos(a)*(r+27),cy+math.sin(a)*(r+27),11,fill=accent)


def shot_compare(d, t, busy):
    c = INK
    animated_text(d,(100,170),'SIMPLE RANDOM QUEUE MODEL',55,c,t,.0,'mono')
    gauge_bg = PAPER if busy == .5 else (249,166,134)
    accent = TEAL if busy == .5 else INK
    gauge(d,414,520,205,busy,t,gauge_bg,(160,196,168) if busy == .5 else (220,105,78),accent,c)
    animated_text(d,(900,273),'AVERAGE WAIT',65,c,t,.6,'mono')
    number = '1' if busy == .5 else '9'
    unit = 'MINUTE' if busy == .5 else 'MINUTES'
    animated_text(d,(903,368),number,250,c,t,1.0)
    animated_text(d,(1100,453),unit,100,c,t,1.2)
    animated_text(d,(904,608),'BEFORE SERVICE',58,c,t,1.35,'mono')
    for i in range(9):
        x1=905+i*87
        reveal=1.55+(i*.63 if busy == .9 else 0)
        filled=i < (1 if busy == .5 else 9) and t >= reveal
        d.rounded_rectangle((x1,710,x1+69,780),radius=10,
                            fill=(TEAL if busy == .5 else INK) if filled else None,
                            outline=c,width=5)
    # A moving marker progresses along the same time ruler as it is built.
    if t >= 1.55:
        width = 69 if busy == .5 else 8*87+69
        duration = 1.4 if busy == .5 else 5.7
        xp = 905 + width*clamp((t-1.55)/duration)
        circle(d,xp,797,10,fill=TEAL if busy == .5 else INK)
    if busy == .9:
        animated_text(d,(905,815),'9× THE WAIT',58,c,t,7.2,'mono')
    else:
        animated_text(d,(905,815),'ROOM TO RECOVER',58,c,t,3.5,'mono')


def shot_curve(d, t):
    animated_text(d,(100,169),'THE WAITING CURVE',96,CREAM,t,.0)
    animated_text(d,(100,284),'AVG WAIT',55,MINT,t,.3,'mono')
    left,right,top,bottom=315,1605,342,770
    d.line((left,top,left,bottom,right,bottom),fill=MINT,width=5)
    for w in [1,5,9]:
        y=bottom-(w/10)*(bottom-top)
        d.line((left,y,right,y),fill=(41,76,72),width=3)
    def point(u):
        wait=u/(1-u)  # μ = 1 order/minute; expected queue wait in minutes
        return (left+(u/.9)*(right-left),bottom-(wait/10)*(bottom-top))
    for u in (.5,.9):
        px,py=point(u)
        d.line((px,py,px,bottom),fill=(64,101,90),width=4)
    # Linear reveal makes the comparison emerge over most of the shot, rather than in 2 s.
    amount=clamp((t-.35)/6.7)
    n=max(2,int(200*amount)+1)
    coords=[point(.9*amount*i/(n-1)) for i in range(n)]
    if amount > .005:
        d.polygon([(left,bottom)]+coords+[(coords[-1][0],bottom)],fill=(24,61,58))
        d.line(coords,fill=CORAL,width=13,joint='curve')
    ex,ey=coords[-1]
    d.line((ex,ey,ex,bottom),fill=(92,125,104),width=4)
    circle(d,ex,ey,16+2*math.sin(t*5),fill=YELLOW)
    if amount >= .5/.9:
        x,y=point(.5); circle(d,x,y,16,fill=YELLOW)
        d.line((x,y,x-105,y-74),fill=YELLOW,width=5)
        text(d,(x-380,y-145),'50% = 1 MIN',58,CREAM,'mono')
    if amount >= .995:
        x,y=point(.9); circle(d,x,y,16,fill=YELLOW)
        d.line((x,y,x-78,y-42),fill=YELLOW,width=5)
        text(d,(x-450,y-115),'90% = 9 MIN',58,CREAM,'mono')
    text(d,(310,811),'0%',54,MINT,'mono')
    text(d,(910,811),'50%',54,MINT,'mono')
    text(d,(1510,811),'90%',54,MINT,'mono')
    text(d,(100,811),'BUSY',54,MINT,'mono')


def shot_buffer(d, t):
    animated_text(d,(100,190),'LEAVE ROOM',130,INK,t,.0)
    animated_text(d,(100,355),'FOR THE RUSH.',120,TEAL,t,.25)
    animated_text(d,(102,555),'CAPACITY',58,INK,t,.5,'mono')
    filled_count=9 if t < 2.0 else 8 if t < 3.25 else 7
    text(d,(1445,555),f'{filled_count} / 10',58,INK,'mono')
    for i in range(10):
        bx=105+i*160
        d.rounded_rectangle((bx,648,bx+132,752),radius=15,
                            fill=TEAL if i < filled_count else PAPER,outline=INK,width=5)
    if t >= 2.0:
        animated_text(d,(1225,802),'BUFFER',58,INK,t,2.0,'mono')
        # Orders move into the newly open room instead of stopping at a full strip.
        for i in range(3):
            xx=1220+((t-2.0)*118+i*130)%440
            token(d,xx,700,22,YELLOW)


def shot_end(d, t):
    animated_text(d,(100,223),"SPACE ISN’T WASTE.",120,CREAM,t,.0)
    animated_text(d,(100,400),"IT’S RESILIENCE.",132,YELLOW,t,.45)
    animated_text(d,(100,665),'MAKE ROOM FOR SURPRISES',62,MINT,t,1.15,'mono')
    arrow(d,1270,856,1795,856,MINT,6,20)
    for i in range(5):
        px=1290+((t*90+i*104)%500)
        token(d,px,796,27,CORAL if i<3 else YELLOW)


def frame_at(frame):
    t = frame/FPS
    idx = next(i for i,(start,end,_) in enumerate(SHOTS) if start <= t < end)
    start,end,caption = SHOTS[idx]
    local = t-start
    im = background(idx).copy()
    d = ImageDraw.Draw(im)
    backdrop_motion(d,idx,t)
    if idx == 0: shot_hook(d,local)
    elif idx == 1: shot_server(d,local)
    elif idx == 2: shot_variation(d,local)
    elif idx == 3: shot_compare(d,local,.5)
    elif idx == 4: shot_compare(d,local,.9)
    elif idx == 5: shot_curve(d,local)
    elif idx == 6: shot_buffer(d,local)
    else: shot_end(d,local)
    header(d,idx)
    footer(d,caption,t)
    return im


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--preview':
        sec = float(sys.argv[2])
        if not 0 <= sec < SECONDS:
            raise SystemExit('Preview seconds must be in [0,60).')
        frame_at(round(sec*FPS)).save(sys.argv[3])
        return
    if len(sys.argv) != 1:
        raise SystemExit('Use: visuals.py [--preview SECONDS output.png]')
    out = sys.stdout.buffer
    for frame in range(FPS*SECONDS):
        out.write(frame_at(frame).tobytes())
        if frame % 150 == 0:
            print(f'Frames {frame}/{FPS*SECONDS}', file=sys.stderr, flush=True)
    out.flush()

if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
