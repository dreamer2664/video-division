#!/usr/bin/env python3
"""Export burned-caption cues to WebVTT without changing their aligned boundaries."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CUES=json.loads((ROOT/'cues.json').read_text())
OUT=Path(__file__).resolve().parents[3]/'videos/team-a/vox-presenter-register/captions.vtt'
def stamp(seconds):
    ms=round(seconds*1000); h,ms=divmod(ms,3_600_000); m,ms=divmod(ms,60_000); s,ms=divmod(ms,1000)
    return f'{h:02d}:{m:02d}:{s:02d}.{ms:03d}'
rows=['WEBVTT','']
for cue in CUES['captions']:
    rows += [cue['id'],f"{stamp(cue['start'])} --> {stamp(cue['end'])}",cue['text'],'']
OUT.write_text('\n'.join(rows),encoding='utf-8')
print(f'Wrote {OUT}: {len(CUES["captions"])} cues / {CUES["duration_seconds"]:.3f}s')
