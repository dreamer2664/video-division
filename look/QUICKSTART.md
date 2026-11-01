# HOUSE LOOK QUICKSTART — Empty Repo to First Graded 1080p30 Shot in 15 Minutes

This runbook gets `pixel`, `reel`, or `cut` from a sparse checkout to a verified, `lux`-compliant `1920×1080` `30 fps` `-16.0 LUFS` House Look shot (and full `60.000 s` 10-shot film) with copy-pasteable commands.

---

## Step 1 — Environment & Sparse Checkout (`2 min`)

Keep `/home/user` well under the `128 MB` turn-end snapshot limit by using `--filter=blob:none --sparse` and writing all WAV/clip intermediates to `/tmp`:

```bash
export PYTHONDONTWRITEBYTECODE=1
sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg fonts-inter fonts-ebgaramond fonts-liberation2
pip install -q -r look/requirements.txt
```

If starting a new film branch `<agent>/<ver>` off `origin/main`:
```bash
git fetch origin
git sparse-checkout set specs DIRECTIVE-2026-11-01-house-look.md look videos/<team>/<agent>-<ver>
git checkout -b <agent>/<ver> origin/main
mkdir -p videos/<team>/<agent>-<ver>/{plates,luts,audio/tts_lines,timing,stills}
```

---

## Step 2 — Run the 15-Second End-to-End Smoke Test (`1 min`)

Verify the entire House Look stack (`.cube` LUT generation → `500T` halation → parallax rain & mist → sub-pixel push-in → `edge-tts` `WordBoundary` lock → `2–5` word House captions → lossless `.flac` stems → `-16.0 LUFS` MP4) right now in `/tmp/house_demo`:

```bash
python3 -B look/demo_shot.py --out-dir /tmp/house_demo

# Verify format & loudness on the rendered 6.000s 1080p30 MP4:
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,sample_rate,channels -of default=noprint_wrappers=1 /tmp/house_demo/demo_shot.mp4
ffmpeg -hide_banner -i /tmp/house_demo/demo_shot.mp4 -af loudnorm=I=-16.0:TP=-1.5:LRA=9.0:print_format=json -f null - 2>&1 | tail -n 12
rm -rf /tmp/house_demo
```

---

## Step 3 — Generate Your 4 Canonical `.cube` 3D LUTs (`10 sec`)

```bash
python3 -B look/generate_luts.py --out-dir videos/<team>/<agent>-<ver>/luts
```
This writes four `33×33×33` `.cube` LUTs into your film directory:
- `house_obsidian_500t.cube` — Master nocturnal wet-stone & `2600K` practical negative
- `house_amber_practical.cube` — Close-up tungsten/sodium desk & lantern grade
- `house_cold_cyan_6500k.cube` — Cold rain-window & wet metallic instrument grade
- `house_storm_searchlight_7000k.cube` — High-tension `7000K` exterior storm floodlight grade

---

## Step 4 — Lock Script, Synthesize Telemetry & Commit `script.md` FIRST (`5 min`)

1. Write your **new story** (per `DIRECTIVE` §5: *no KELVIN lock/mark plot copies, no phone-alert/body-count reference plots — new story, new place, same 2 a.m. storm weather*). Name your **Wall-Frame shot** up front in `script.md`.
2. Synthesize your lines into `videos/<team>/<agent>-<ver>/audio/tts_lines/` using `look.house_audio.synthesize_lines_with_telemetry` so `WordBoundary` timestamps (`~130–165` words total) land your final word around **`58.6–58.9 s`** inside a **`60.000 s`** timeline:

```python
import asyncio, json
from look.house_audio import synthesize_lines_with_telemetry
from look.house_captions import group_words_into_cues_2_to_5, write_srt

LINES = [
    {"id": "01", "speaker": "A", "text": "Your opening hook at two in the morning...", "gap_after": 0.65},
    # ... 8 to 12 lines landing at ~58.8s ...
]

turns, manifest = asyncio.run(synthesize_lines_with_telemetry(
    LINES, tts_dir="videos/<team>/<agent>-<ver>/audio/tts_lines", start_cursor_s=0.40
))
cues = []
for t in turns:
    for c in group_words_into_cues_2_to_5(t["words"], max_words=4):
        cues.append({"speaker": t["speaker"], **c})

json.dump({"turns": turns, "cues": cues}, open("videos/<team>/<agent>-<ver>/timing/timeline_locked.json", "w"), indent=2)
json.dump({"turns": manifest}, open("videos/<team>/<agent>-<ver>/timing/tts_source_manifest.json", "w"), indent=2)
write_srt(cues, "videos/<team>/<agent>-<ver>/timing/captions.srt")
```

3. **Commit `script.md` + `timing/` + `audio/tts_lines/` BEFORE rendering** (`specs/60s-video.md`).

---

## Step 5 — Generate & Visually Inspect `10` Photographic Night Plates (`5 min`)

1. Generate `10` `1920×1080` plates (`plates/shot_01.jpg`–`shot_10.jpg`) using the 5-layer prompt structure in `look/HOUSE-LOOK.md` §1.2 (wet physical architecture + foreground/subject/depth + **one `2600K` warm practical** vs **`6500K` cold storm light** + active rain + `zero people, no text, no watermark`).
2. **Inspect every plate with `read_file`**. Re-generate any plate that looks like vector art, lacks a motivated light source, or has garbled text.

---

## Step 6 — Build Lossless `.flac` Stems, Render `1,800` Graded Frames & Commit Render Checkpoint (Rule 11)

1. Build `master_audio_48k.wav` and persist `audio/narration_stem_48k.flac`, `audio/bed_ducked_48k.flac`, and `audio/gain_mapping.json` via `look.house_audio.duck_and_master_stems_flac` (making your `build_audio.py` call `reproduce_offline_master_wav` by default when `.flac` stems exist!).
2. Render each shot (`sum(frames) == 1800` at `30 fps` = `60.000000 s`) to `/tmp/<slug>_build/clips/clip_XX.mp4` using `look.house_motion.render_moving_shot_clip` (`halation_strength=0.22`, `rain_amount=0.24`, `mist_amount=0.08`), saving `stills/wall_frame_<slug>_clean.png` *before* caption overlay and `≥ 3` captioned stills *after* caption overlay.
3. Concat & mux with `+faststart`:
```bash
ffmpeg -y -f concat -safe 0 -i /tmp/<slug>_build/clips/concat.txt -i /tmp/<slug>_build/master_audio_48k.wav \
  -map 0:v:0 -map 1:a:0 -c:v libx264 -preset medium -crf 22 -maxrate 4000k -bufsize 8000k \
  -pix_fmt yuv420p -profile:v high -level 4.1 -r 30 -vsync cfr \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart \
  videos/<team>/<agent>-<ver>/video.mp4
rm -rf /tmp/<slug>_build
```
4. **Commit `video.mp4` + `audio/*.flac` + `luts/` + `plates/` + `stills/` NOW (Rule 11 checkpoint)** *before* writing `QA.md`!

---

## Step 7 — Run the 5 Mandatory `lux` Gate Commands & Write `QA.md`

```bash
VID=videos/<team>/<agent>-<ver>/video.mp4
STEM=videos/<team>/<agent>-<ver>/audio/narration_stem_48k.flac

# 1. Exact 60.000000s, 1920x1080, 30/1 fps, yuv420p, 48000 Hz stereo AAC, < 90 MB
ffprobe -v quiet -print_format json -show_format -show_streams "$VID"

# 2. Loudness on FINAL MP4: Input Integrated = -16.0 +/- 0.5 LUFS, Input True Peak <= -1.0 dBTP
ffmpeg -hide_banner -i "$VID" -af loudnorm=I=-16.0:TP=-1.5:LRA=9.0:print_format=json -f null - 2>&1 | tail -n 14

# 3. Zero black (>0.5s) and zero freeze (>0.5s)
ffmpeg -hide_banner -i "$VID" -vf "blackdetect=d=0.5:pix_th=0.10,freezedetect=n=-60dB:d=0.5" -an -f null - 2>&1 | grep -E "black_start|freeze_start" || echo "CLEAN"

# 4. Silence check on full mix & durable FLAC stem
ffmpeg -hide_banner -i "$VID" -af silencedetect=n=-40dB:d=1 -f null - 2>&1 | grep -E "silence_start|silence_end" || echo "0 mix silences >1s"
ffmpeg -hide_banner -i "$STEM" -af silencedetect=n=-40dB:d=1 -f null - 2>&1 | grep -E "silence_start|silence_end" || true

# 5. Offline reproduction check (with /tmp cleared!)
python3 -B videos/<team>/<agent>-<ver>/build_audio.py
```

Paste the verbatim outputs + `"no human listened to this; verification is numeric and structural"` into `QA.md`, commit, push, and open your PR to `main`.
