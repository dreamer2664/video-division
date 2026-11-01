# FOUR SECONDS AHEAD — cut v09 QA

## Delivery and arithmetic

- Vertical master: `video.mp4`; landscape derivative: `video-landscape.mp4`; 60.000 s, 30 fps; both H.264/yuv420p + AAC stereo/48 kHz.
- Sizes: vertical **13,806,883 bytes**, landscape **13,696,888 bytes** (each well below the 128 MiB ceiling).
- The camera time is computed from the integer frame index, not a wall-clock timer: `feed_ms = wall_ms + 4000`. For every camera panel and frame, the burned-in feed time is exactly 4,000 ms ahead of the room clock, including the 02:13→02:14 rollover.
- **Named deliberate image:** `stills/HERO-01-open-palm.png`, frame 1368 / **00:45.600**. Wall readout `02:13:53.600`; CAM 04 readout `02:13:57.600`; the future feed shows the open palm while the current control-room strip shows the hand still closed. The image and exact shot were in `script.md` before the first render. Four seconds later, at 00:49.600, the current-room hand opens. CAM 05 first appears at wall time 02:14:01.600.
- The hero narration cue is 45.600–48.710 s. Its caption begins at 45.600 and remains through 49.600 (next caption onset), so the caption covers the entire spoken cue rather than ending at the shot cut.
- The branch's first commit locks the script and hero plan (`300a9d876846c54199d2f55f55f4aa64621712dc`); renderer source was committed before rendering. Final pushed delivery commit: `d0c3d9cbc6568c0ea3c76d0bdb1489d525ca8721`.

## Verbatim media probes

Command: `ffprobe -v error -show_entries format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels,pix_fmt -of default=noprint_wrappers=1 video.mp4`

```text
codec_name=h264
codec_type=video
width=1080
height=1920
pix_fmt=yuv420p
r_frame_rate=30/1
codec_name=aac
codec_type=audio
sample_rate=48000
channels=2
r_frame_rate=0/0
duration=60.000000
size=13806883
```

Command: same probe on `video-landscape.mp4`.

```text
codec_name=h264
codec_type=video
width=1920
height=1080
pix_fmt=yuv420p
r_frame_rate=30/1
codec_name=aac
codec_type=audio
sample_rate=48000
channels=2
r_frame_rate=0/0
duration=60.000000
size=13696888
```

Both files fully decoded to FFmpeg's null muxer with exit 0. Frame scan on each: `blackdetect=d=0.5:pix_th=0.02,freezedetect=n=-50dB:d=0.5` — **zero black events and zero freeze events**. Audio scan on each: `silencedetect=noise=-50dB:d=0.5` — **zero silence events**.

## Loudness and voice

FFmpeg 7.0.2 `loudnorm=print_format=summary` on the AAC masters:

| File | Integrated loudness | True peak | LRA |
|---|---:|---:|---:|
| Vertical | −15.8 LUFS | −1.5 dBTP | 4.7 LU |
| Landscape | −15.8 LUFS | −1.5 dBTP | 4.7 LU |

Both pass the −16 LUFS ±0.5 target. The narration stem is 60.000 s, mono PCM 24 kHz. One designed voice throughout: Edge TTS `en-US-ChristopherNeural`, rate −8%, pitch −4 Hz; 91 spoken words, 42.104 s active cue duration, **129.7 words/min** from the committed cue table. No voice fallback was needed.

Score is original oscillator-generated low drone and relay clicks; no reference audio or sampled music. A measured 10 dB active-voice side-chain target is used. In 100 ms stem-RMS blocks, measured voice-over-score margin is median **12.8 dB**, 10th percentile **7.4 dB**, minimum **−2.1 dB** (brief transient/onset blocks). This is not represented as a uniform 10 dB margin; see self-review below.

## Reproduction and checks

- `./render.sh` from the package directory; dependencies and the FFmpeg path are documented in `project/README.md` and `project/requirements.txt`.
- Frame sources are procedural Pillow vectors; narration cues are recorded in `project/voice_cues.csv`, caption onsets (including silent visual beats) in `project/caption_cues.csv`; sound is procedurally generated in `project/sound.py`.
- Versions at render: FFmpeg/ffprobe 7.0.2-static, Python 3.13, Pillow 12.3.0, NumPy 2.3.5, edge-tts 7.3.1.
- **No human listened; verification is numeric and structural.**

## Blunt self-review

The hero comparison is precise and legible, but the people and hands are geometric vectors rather than naturalistic figures; the procedural style is part of the intent, but may feel sparse. The surprise depends on viewers reading the two clocks, not on a sound cue. The new fifth-feed tile is intentionally compact to retain the whole control-room image. The drone is numerically normalized, but the measured short-block voice/score minimum shows the score transient is not consistently 8–12 dB under the quietest speech onsets. No full human watch/listen-through was done.
