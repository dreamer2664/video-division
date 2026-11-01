#!/usr/bin/env python3
"""Apply the committed loudnorm master to the existing cut; copy, never encode, video."""
from __future__ import annotations
import json, os, subprocess
from pathlib import Path
from build_audio_v10 import build_audio

HERE=Path(__file__).resolve().parent
VIDEO=HERE/"video.mp4"
TEMP=HERE/"video.audiofix.tmp.mp4"


def run(cmd, capture=False):
    return subprocess.run(cmd,check=True,text=True,capture_output=capture)


def frame_hashes(path: Path) -> list[str]:
    out=run(["ffmpeg","-hide_banner","-loglevel","error","-i",str(path),"-map","0:v:0","-f","framemd5","-"],capture=True).stdout
    return [line.split(",")[-1].strip() for line in out.splitlines() if line and not line.startswith("#")]


def probe(path: Path) -> dict:
    p=run(["ffprobe","-v","quiet","-print_format","json","-show_format","-show_streams",str(path)],capture=True)
    return json.loads(p.stdout)


def main():
    before=frame_hashes(VIDEO)
    audio=build_audio()
    master=HERE/audio["normalized_master"]
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(VIDEO),"-i",str(master),
         "-map","0:v:0","-map","1:a:0","-map_metadata","0",
         "-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2",
         "-movflags","+faststart",str(TEMP)])
    after=frame_hashes(TEMP)
    if len(before)!=1800 or before!=after:
        TEMP.unlink(missing_ok=True)
        raise RuntimeError(f"Video frame hashes changed during audio-only remux: {len(before)} before / {len(after)} after")
    info=probe(TEMP)
    v=next(s for s in info["streams"] if s.get("codec_type")=="video")
    a=next(s for s in info["streams"] if s.get("codec_type")=="audio")
    duration=float(info["format"]["duration"])
    if (v.get("codec_name")!="h264" or v.get("width")!=1920 or v.get("height")!=1080 or
        v.get("avg_frame_rate")!="30/1" or v.get("nb_frames")!="1800" or
        a.get("codec_name")!="aac" or a.get("sample_rate")!="48000" or a.get("channels")!=2 or
        abs(duration-60.0)>0.001):
        TEMP.unlink(missing_ok=True)
        raise RuntimeError(f"Post-remux stream gate failed: {json.dumps(info,indent=2)}")
    os.replace(TEMP,VIDEO)
    print(json.dumps({"video_frame_hashes_identical":len(before),"duration_s":duration,
                      "video_codec":v["codec_name"],"video_raster":[v["width"],v["height"]],
                      "video_frames":v["nb_frames"],"audio_codec":a["codec_name"],
                      "audio_sample_rate_hz":a["sample_rate"],"audio_channels":a["channels"],
                      "loudnorm_pass1":audio["loudnorm_pass1_json"],
                      "loudnorm_pass2":audio["loudnorm_pass2_json"]},indent=2))

if __name__=="__main__":
    main()
