#!/usr/bin/env python3
"""Voice-first final mux: two-pass EBU R128 loudness, 48 kHz AAC, no music bed."""
import json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
VIDEO=ROOT/'video-silent.mp4'; AUDIO=ROOT/'voice.mp3'; CUES=json.loads((ROOT/'cues.json').read_text())
OUT=Path(__file__).resolve().parents[3]/'videos/team-a/vox-presenter-register/video.mp4'
OUT.parent.mkdir(parents=True,exist_ok=True); duration=float(CUES['duration_seconds'])
base=['ffmpeg','-hide_banner','-y','-nostats','-v','info']
probe=subprocess.run(base+['-i',str(AUDIO),'-af','apad=pad_dur=0.2,loudnorm=I=-15.6:TP=-1.5:LRA=7:print_format=json','-t',str(duration),'-f','null','-'],capture_output=True,text=True)
if probe.returncode: raise SystemExit(probe.stderr[-3000:])
blocks=re.findall(r'\{[^{}]*"input_i"[^{}]*\}',probe.stderr,re.S)
if not blocks: raise SystemExit('Could not parse first-pass loudnorm measurements.')
measure=json.loads(blocks[-1]); parts=[f"measured_I={measure['input_i']}",f"measured_TP={measure['input_tp']}",
       f"measured_LRA={measure['input_lra']}",f"measured_thresh={measure['input_thresh']}",
       f"offset={measure['target_offset']}"]
filter_='[1:a]apad=pad_dur=0.2,loudnorm=I=-15.6:TP=-1.5:LRA=7:'+':'.join(parts)+':linear=true:print_format=summary,aresample=48000[a]'
cmd=base+['-i',str(VIDEO),'-i',str(AUDIO),'-filter_complex',filter_,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-ac','2','-b:a','192k','-ar','48000','-t',str(duration),'-shortest','-movflags','+faststart',str(OUT)]
r=subprocess.run(cmd,capture_output=True,text=True)
if r.returncode: raise SystemExit(r.stderr[-5000:])
print('OUTPUT',OUT); print('DURATION',duration); print('FIRST_PASS',json.dumps(measure)); print(r.stderr[-1400:])
