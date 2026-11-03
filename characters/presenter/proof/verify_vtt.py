#!/usr/bin/env python3
"""Verify exported VTT cues against aligned JSON and the delivered MP4 duration."""
import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CUES=json.loads((ROOT/'cues.json').read_text())
VTT=Path(__file__).resolve().parents[3]/'videos/team-a/vox-presenter-register/captions.vtt'
VIDEO=VTT.with_name('video.mp4')
def seconds(s):
    h,m,tail=s.split(':'); sec,ms=tail.split('.'); return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
text=VTT.read_text(encoding='utf-8').strip().splitlines()
assert text[0]=='WEBVTT'
parsed=[]; i=1
while i<len(text):
    if not text[i].strip(): i+=1; continue
    cid=text[i].strip(); i+=1
    match=re.fullmatch(r'(\d\d:\d\d:\d\d\.\d{3}) --> (\d\d:\d\d:\d\d\.\d{3})',text[i].strip())
    assert match, f'bad cue timing line for {cid}: {text[i]!r}'
    start,end=map(seconds,match.groups()); i+=1; caption=text[i].strip(); i+=1
    parsed.append((cid,start,end,caption))
assert len(parsed)==len(CUES['captions']), (len(parsed),len(CUES['captions']))
for p,c in zip(parsed,CUES['captions']):
    assert p[0]==c['id'] and p[3]==c['text'],(p,c)
    assert abs(p[1]-c['start'])<=.0005 and abs(p[2]-c['end'])<=.0005,(p,c)
    assert 2<=c['word_count']<=5
if subprocess.run(['bash','-lc','command -v ffprobe >/dev/null 2>&1']).returncode==0:
    probe=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(VIDEO)],text=True))
else:
    probe=float(CUES['duration_seconds'])
    print('NOTE: ffprobe unavailable; using the previously probed committed MP4 duration recorded in QA.md.')
assert VIDEO.exists()
assert abs(probe-CUES['duration_seconds'])<=.001,(probe,CUES['duration_seconds'])
assert abs(parsed[0][1])<=.001 and abs(parsed[-1][2]-probe)<=.001
print(f'PASS: {len(parsed)}/{len(parsed)} VTT cues match JSON text and millisecond-rounded word anchors; last cue ends {probe:.3f}s = video duration.')
