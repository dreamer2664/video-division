#!/usr/bin/env python3
"""Compile ElevenLabs character timestamps into word-locked caption and motion cues.

Voice is the source of truth: this consumes the exact narrated script and the provider's
character-level alignment. No timing is inferred from a guessed read.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--text', required=True)
    ap.add_argument('--alignment', required=True)
    ap.add_argument('--config', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    text = Path(args.text).read_text().strip()
    raw = json.loads(Path(args.alignment).read_text())
    cfg = json.loads(Path(args.config).read_text())
    align = raw['alignment']
    aligned_text = ''.join(align['characters'])
    starts, ends = align['character_start_times_seconds'], align['character_end_times_seconds']
    if text != aligned_text:
        raise SystemExit('The cue text does not exactly match the voice-aligned text.')
    words = []
    for m in WORD_RE.finditer(text):
        words.append({'text':m.group(), 'start':float(starts[m.start()]),
                      'end':float(ends[m.end()-1]), 'char_start':m.start(), 'char_end':m.end()})
    # Split at sentence punctuation, then partition each sentence into balanced 2-5 word beats.
    sentences=[]; first=0
    for i,w in enumerate(words):
        token=text[w['char_end']:words[i+1]['char_start']] if i+1<len(words) else text[w['char_end']:]
        if re.search(r'[.!?]',token) or i==len(words)-1:
            sentences.append(list(range(first,i+1))); first=i+1
    groups=[]
    for sentence in sentences:
        n=len(sentence); k=max(1,(n+3)//4)
        if n>1 and n<2*k: k=max(1,n//2)
        q,r=divmod(n,k); offset=0
        for j in range(k):
            size=q+(1 if j<r else 0)
            groups.append(sentence[offset:offset+size]); offset+=size
    beats=[]
    for n,g in enumerate(groups):
        first,last=words[g[0]],words[g[-1]]
        tail_end=words[g[-1]+1]['char_start'] if g[-1]+1<len(words) else len(text)
        punctuation=''.join(ch for ch in text[last['char_end']:tail_end] if ch in '.,!?;:')
        caption=text[first['char_start']:last['char_end']]+punctuation
        next_start=words[groups[n+1][0]]['start'] if n+1<len(groups) else float(cfg['duration_seconds'])
        beats.append({'id':f'cap_{n+1:02d}','text':caption,'start':first['start'],
                      'end':max(last['end'],next_start),'word_count':len(g),
                      'word_indices':[g[0],g[-1]+1],
                      'word_times':[{'text':words[i]['text'],'start':words[i]['start'],'end':words[i]['end']} for i in g]})
    if any(not 2<=b['word_count']<=5 for b in beats):
        raise SystemExit('Generated beat outside the 2–5 word rule.')
    def anchor_time(phrase):
        needle=[m.group().lower() for m in WORD_RE.finditer(phrase)]
        hay=[w['text'].lower() for w in words]
        for j in range(len(hay)-len(needle)+1):
            if hay[j:j+len(needle)]==needle: return words[j]['start']
        raise SystemExit(f'Anchor phrase not found in voice: {phrase!r}')
    def resolve(items, kind):
        result=[]
        for item in items:
            row=dict(item)
            if 'anchor' in row: row['start']=anchor_time(row.pop('anchor'))
            if 'end_anchor' in row: row['end']=anchor_time(row.pop('end_anchor'))
            if 'duration' in row: row['end']=row['start']+float(row.pop('duration'))
            row.setdefault('end',float(cfg['duration_seconds']))
            row.setdefault('start',0.0)
            row['id']=row.get('id',f'{kind}_{len(result)+1:02d}')
            result.append(row)
        return result
    out={'schema_version':1,'title':cfg['title'],'voice_first':True,
         'voice':cfg['voice'],'duration_seconds':float(cfg['duration_seconds']),
         'frame_rate':int(cfg['frame_rate']),'resolution':cfg['resolution'],
         'narration_text':text,'captions':beats,
         'status':resolve(cfg['status'],'status'),'labels':resolve(cfg['labels'],'label'),
         'motion':resolve(cfg['motion'],'motion'),
         'screenshot':resolve(cfg['screenshot'],'screenshot'),'source_note':cfg['source_note']}
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    Path(args.out).write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(f"wrote {args.out}: {len(words)} words, {len(beats)} caption beats")

if __name__=='__main__': main()
