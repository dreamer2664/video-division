#!/usr/bin/env python3
"""Create 2–5-word SRT and word-synchronised ASS from committed speech timings."""
import argparse,json
from pathlib import Path
from PIL import ImageFont

HERE=Path(__file__).resolve().parent
# Inclusive word indexes; grouping is editorial, never a reordering of the transcript.
GROUPS=[(0,3),(4,6),(7,9),(10,13),(14,16),(17,18),(19,22),(23,25),(26,28),
        (29,33),(34,38),(39,41),(42,44),(45,48),(49,51),(52,53),(54,56),
        (57,59),(60,61),(62,64),(65,66),(67,70),(71,73),(74,77),(78,80),
        (81,85),(86,88),(89,90),(91,93),(94,96),(97,99),(100,103),
        (104,107),(108,111),(112,114),(115,117),(118,120),(121,122)]
PUNCT={3:',',9:'.',13:'.',16:'.',18:':',22:',',28:'.',33:'.',38:'.',41:'.',
       48:'.',51:'.',53:',',56:'.',61:'.',64:'.',66:'.',70:',',73:'.',80:'.',
       85:'.',90:'.',93:'.',99:'.',103:'.',107:'.',111:'.',117:'.',120:':',122:'.'}

def stamp(s,ass=False):
    n=round(s*(100 if ass else 1000));scale=100 if ass else 1000
    h,n=divmod(n,3600*scale);m,n=divmod(n,60*scale);sec,frac=divmod(n,scale)
    return f'{h}:{m:02}:{sec:02}.{frac:02}' if ass else f'{h:02}:{m:02}:{sec:02},{frac:03}'

def label(e,index):
    word=e['word'].upper()
    # An abbreviation already ends in a period; a comma is still legitimate.
    return word+PUNCT.get(index,'')

def build(ass_path):
    meta=json.loads((HERE/'assets'/'word_timings.json').read_text());words=meta['words']
    assert [i for a,b in GROUPS for i in range(a,b+1)]==list(range(len(words)))
    assert all(2<=b-a+1<=5 for a,b in GROUPS)
    cues=[]
    for ci,(a,b) in enumerate(GROUPS):
        start=words[a]['start'];next_start=words[GROUPS[ci+1][0]]['start'] if ci+1<len(GROUPS) else 60.0
        end=min(next_start-0.02,words[b]['end']+0.28)
        if ci==len(GROUPS)-1:end=59.84
        text=' '.join(label(words[i],i) for i in range(a,b+1))
        cues.append({'start':start,'end':max(end,start+.15),'text':text,'a':a,'b':b})
    # Validate the source timing rather than silently accepting a late or truncated cue.
    # One video frame is the explicit tolerance; speech audio itself is not modified.
    overhang=max(max(0, cue['start']-words[i]['start'], words[i]['end']-cue['end'])
                 for cue in cues for i in range(cue['a'],cue['b']+1))
    if overhang > 1/30:
        raise ValueError(f'Caption/speech boundary mismatch: {overhang:.3f}s')
    srt='\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}\n' for i,c in enumerate(cues))
    (HERE/'captions.srt').write_text(srt)
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Anton,94,&H004ED1F5,&H00F7F9FB,&H00100B08,&H90000000,0,0,0,0,100,100,1,0,1,5,2,2,90,90,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines=[];fontpath=str(HERE/'assets'/'Anton-Regular.ttf')
    for cue in cues:
        a,b=cue['a'],cue['b'];text=cue['text'];size=94
        while size>60 and ImageFont.truetype(fontpath,size).getlength(text)>875:size-=2
        if ImageFont.truetype(fontpath,size).getlength(text)>875:
            raise ValueError(f'Caption exceeds safe width at 60 px: {text}')
        threat=(97<=a<=108)
        style=f'{{\\fs{size}'+('\\1c&H3C45E2&' if threat else '')+'}'
        chunks=[]
        for i in range(a,b+1):
            last_end=words[i+1]['start'] if i<b else cue['end']
            centis=max(1,round((last_end-words[i]['start'])*100))
            chunks.append(f'{{\\k{centis}}}'+label(words[i],i))
        lines.append(f'Dialogue: 0,{stamp(cue["start"],True)},{stamp(cue["end"],True)},Caption,,0,0,0,,{style}'+ ' '.join(chunks))
    ass_path.write_text(header+'\n'.join(lines)+'\n')
    print('captions:',len(cues),'cues, all 2–5 words; last ends',cues[-1]['end'])
    return cues
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ass',type=Path,required=True);args=p.parse_args();build(args.ass)
