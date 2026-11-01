#!/usr/bin/env python3
"""Offline structural checks for voice alignment, caption beats, states and actions."""
import json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parent
c=json.loads((P/'cues.json').read_text()); raw=json.loads((P/'alignment-raw.json').read_text()); text=(P/'script.txt').read_text().strip()
a=raw['alignment']; aligned=''.join(a['characters'])
assert aligned==text==c['narration_text'], 'text/audio alignment identity mismatch'
R=re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*")
word_matches=list(R.finditer(text)); starts=a['character_start_times_seconds']; ends=a['character_end_times_seconds']
assert len(word_matches)==sum(b['word_count'] for b in c['captions'])
seen=0
for idx,b in enumerate(c['captions']):
    assert 2<=b['word_count']<=5, (b['id'],b['word_count'])
    ws=b['word_times']; assert len(ws)==b['word_count']
    first=word_matches[seen]; last=word_matches[seen+b['word_count']-1]
    assert abs(b['start']-starts[first.start()])<1e-7, b['id']
    assert abs(ws[0]['start']-starts[first.start()])<1e-7
    assert abs(ws[-1]['end']-ends[last.end()-1])<1e-7
    if idx+1<len(c['captions']):
        assert abs(b['end']-c['captions'][idx+1]['start'])<1e-7
    seen+=b['word_count']
assert abs(c['captions'][0]['start'])<1e-7
assert abs(c['status'][0]['start'])<1e-7 and abs(c['status'][-1]['end']-c['duration_seconds'])<1e-7
for left,right in zip(c['status'],c['status'][1:]): assert abs(left['end']-right['start'])<1e-7
assert c['screenshot'] and c['screenshot'][0]['start']<c['screenshot'][0]['end']
assert c['motion'] and all(e['start']<e['end'] for e in c['motion'])
asset=P/c['screenshot'][0]['asset']; assert asset.exists(),asset
print(f"PASS: aligned words={len(word_matches)}; caption beats={len(c['captions'])}; word-count range=2–{max(b['word_count'] for b in c['captions'])}; status intervals={len(c['status'])}; motion events={len(c['motion'])}; screenshot={asset.name}")
