#!/usr/bin/env python3
"""2–5-word cinematic SRT and ASS captions, locked to committed Edge word starts."""
import argparse,json,math
from pathlib import Path
from PIL import ImageFont

ROOT=Path(__file__).resolve().parent
# Inclusive, contiguous indices into the 124 actual synthesizer word events.
GROUPS=[(0,2),(3,7),(8,11),(12,15),(16,20),(21,25),(26,30),(31,34),
        (35,37),(38,42),(43,47),(48,50),(51,53),(54,56),(57,60),
        (61,62),(63,65),(66,68),(69,71),(72,76),(77,78),(79,81),
        (82,84),(85,89),(90,91),(92,93),(94,96),(97,99),(100,103),
        (104,105),(106,110),(111,113),(114,117),(118,120),(121,123)]
PUNCT={2:',',7:'.',11:'.',15:'.',20:'.',25:'.',30:'.',37:'.',47:'.',
       53:'.',56:'.',60:'.',62:',',65:',',71:'.',78:'.',84:'.',89:'.',
       91:',',93:',',99:'.',103:'.',105:',',113:'.',123:'.'}
def label(word,index):return word['word']+PUNCT.get(index,'')
def srt_stamp(s):
    ms=round(s*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);sec,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{sec:02},{ms:03}'
def ass_stamp(cs):
    h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);s,cs=divmod(cs,100)
    return f'{h}:{m:02}:{s:02}.{cs:02}'
def build(ass):
    words=json.loads((ROOT/'assets/word_timings.json').read_text())['words']
    assert [i for a,b in GROUPS for i in range(a,b+1)]==list(range(len(words)))
    assert all(2<=b-a+1<=5 for a,b in GROUPS)
    cues=[]
    for ci,(a,b) in enumerate(GROUPS):
        start=words[a]['start'];next_start=words[GROUPS[ci+1][0]]['start'] if ci+1<len(GROUPS) else 60
        end=min(next_start-.015,words[b]['end']+(.55 if ci==len(GROUPS)-1 else .24))
        text=' '.join(label(words[i],i) for i in range(a,b+1))
        cues.append(dict(start=start,end=end,text=text,a=a,b=b))
    assert max(max(0,c['start']-words[i]['start'],words[i]['end']-c['end']) for c in cues for i in range(c['a'],c['b']+1))<=1/30
    (ROOT/'captions.srt').write_text('\n'.join(f'{n+1}\n{srt_stamp(c["start"])} --> {srt_stamp(c["end"])}\n{c["text"]}\n' for n,c in enumerate(cues)))
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Anton,68,&H004ED1F5,&H00F4F5F7,&H00080705,&H90000000,0,0,0,0,100,100,0.3,0,1,4,2,2,180,180,125,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    font=str(ROOT/'assets/Anton-Regular.ttf');lines=[]
    for c in cues:
        a,b=c['a'],c['b'];size=68
        while size>48 and ImageFont.truetype(font,size).getlength(c['text'])>1400:size-=2
        assert ImageFont.truetype(font,size).getlength(c['text'])<=1400
        targets=[math.floor(words[i]['start']*100+1e-8) for i in range(a,b+1)]
        end=round(c['end']*100);assert all(targets[j+1]>targets[j] for j in range(len(targets)-1)) and end>targets[-1]
        tags=[]
        for j,i in enumerate(range(a,b+1)):
            nxt=targets[j+1] if j+1<len(targets) else end
            tags.append(f'{{\\k{nxt-targets[j]}}}'+label(words[i],i))
        # The actual spoken threat, not every late cue, changes active words to crimson.
        color='\\1c&H3C45E8&' if a in (94,97) else ''
        lines.append(f'Dialogue: 0,{ass_stamp(targets[0])},{ass_stamp(end)},Caption,,0,0,0,,{{\\fs{size}{color}}}'+ ' '.join(tags))
    ass.write_text(header+'\n'.join(lines)+'\n')
    print(f'{len(cues)} cues, 2–5 words, {len(words)} actual service boundaries; final cue clears at {cues[-1]["end"]:.3f}s')
    return cues
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ass',type=Path,required=True);a=p.parse_args();build(a.ass)
