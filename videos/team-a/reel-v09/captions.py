#!/usr/bin/env python3
"""Make 2–5-word SRT and measured-word ASS for PERFECT TIME."""
import argparse,json,math
from pathlib import Path
from PIL import ImageFont

HERE=Path(__file__).resolve().parent
GROUPS=[(0,3),(4,6),(7,10),(11,13),(14,15),(16,18),(19,22),(23,25),
        (26,28),(29,31),(32,34),(35,36),(37,39),(40,41),(42,45),(46,47),
        (48,49),(50,52),(53,55),(56,60),(61,63),(64,65),(66,67),(68,70),
        (71,72),(73,75),(76,78),(79,82),(83,84),(85,88),(89,92),(93,94),
        (95,97),(98,100),(101,102),(103,106),(107,109),(110,111),(112,114),
        (115,118),(119,122),(123,124)]
PUNCT={3:',',10:'.',15:'.',22:'.',28:':',31:'.',32:'.',36:'.',41:'.',
       47:'.',48:':',49:'.',55:'.',60:'.',61:'.',63:'.',72:'.',78:'.',84:'.',
       88:'.',94:'.',102:'.',106:'.',111:'.',118:'.',124:'.'}
def label(w,i):return w['word'].upper()+PUNCT.get(i,'')
def srt_stamp(s):
    n=round(s*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);sec,ms=divmod(n,1000)
    return f'{h:02}:{m:02}:{sec:02},{ms:03}'
def ass_stamp(cs):
    h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);sec,cs=divmod(cs,100)
    return f'{h}:{m:02}:{sec:02}.{cs:02}'
def build(path,landscape=False):
    words=json.loads((HERE/'assets/word_timings.json').read_text())['words']
    assert [i for a,b in GROUPS for i in range(a,b+1)]==list(range(len(words)))
    assert all(2<=b-a+1<=5 for a,b in GROUPS)
    cues=[]
    for ci,(a,b) in enumerate(GROUPS):
        start=words[a]['start'];next_start=words[GROUPS[ci+1][0]]['start'] if ci+1<len(GROUPS) else 60
        end=min(next_start-.02,words[b]['end']+.28)
        if ci==len(GROUPS)-1:end=59.84
        text=' '.join(label(words[i],i) for i in range(a,b+1))
        cues.append({'start':start,'end':end,'text':text,'a':a,'b':b})
    overhang=max(max(0,c['start']-words[i]['start'],words[i]['end']-c['end']) for c in cues for i in range(c['a'],c['b']+1))
    assert overhang<=1/30
    (HERE/'captions.srt').write_text('\n'.join(f'{i+1}\n{srt_stamp(c["start"])} --> {srt_stamp(c["end"])}\n{c["text"]}\n' for i,c in enumerate(cues)))
    if landscape:w,h,ml,mv=1920,1080,150,120
    else:w,h,ml,mv=1080,1920,90,400
    header=f'''[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Anton,94,&H0052CEF7,&H00F7F9FB,&H00110B08,&H90000000,0,0,0,0,100,100,1,0,1,5,2,2,{ml},{ml},{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines=[];fontpath=str(HERE/'assets/Anton-Regular.ttf')
    for cue in cues:
        a,b=cue['a'],cue['b'];size=94
        while size>60 and ImageFont.truetype(fontpath,size).getlength(cue['text'])>875:size-=2
        if ImageFont.truetype(fontpath,size).getlength(cue['text'])>875:raise ValueError('caption wider than safe area')
        # Floor actual word starts in centiseconds, preventing rounded-late word
        # tags from slipping an extra video frame. Per-word starts, not word lengths.
        targets=[math.floor(words[i]['start']*100+1e-8) for i in range(a,b+1)]
        cs_start=targets[0];cs_end=round(cue['end']*100)
        assert all(targets[k+1]>targets[k] for k in range(len(targets)-1)) and cs_end>targets[-1]
        tags=[]
        for j,i in enumerate(range(a,b+1)):
            nxt=targets[j+1] if j+1<len(targets) else cs_end
            tags.append(f'{{\\k{nxt-targets[j]}}}'+label(words[i],i))
        style=f'{{\\fs{size}'+('\\1c&H5850E7&' if a>=95 else '')+'}'
        lines.append(f'Dialogue: 0,{ass_stamp(cs_start)},{ass_stamp(cs_end)},Caption,,0,0,0,,{style}'+ ' '.join(tags))
    path.write_text(header+'\n'.join(lines)+'\n')
    print(f'captions: {len(cues)} cues, 2–5 words, {len(words)} measured word events')
    return cues
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ass',type=Path,required=True);p.add_argument('--landscape',action='store_true');args=p.parse_args();build(args.ass,args.landscape)
