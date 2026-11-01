# QA — CUT V10: TWO LIGHTS

## Pre-render brief and visual gate (written before render)

- Deliverable: exactly 60.000 s, 1920×1080 landscape, 30/1 fps CFR, H.264/yuv420p, AAC 48 kHz stereo.
- Story gate: one car enters at Junction 4 and is never shown leaving; eight synchronized camera feeds show the same pair of headlights; the operator's counted result remains **two**.
- Image gate: generated photorealistic motorway/control-room plates only; no flat-vector sequence, no empty dark-field cutaway, no portrait material. Film the rain-glazed room, operator, tactile tally counter, and physical CRTs; screen imagery supports the room rather than replacing it.
- House-look source: read the root directive and the available `videos/team-b/grade-v05/` `generate_luts.py`, all four 33³ `.cube` LUTs, `render_v05.py`, plates, `script.md`, and `QA.md`. `look/HOUSE-LOOK.md` is **not present in the checked-out `main` tree**; this source-availability limitation is recorded, not silently claimed as read. Continue with the root directive and the first-party grade-v05 reference implementation. Its approach is a 33³ trilinear LUT, filmic S-curve, cool nocturnal shadows / warm practical, photographic plates, parallax rain, halation, grain, and slow camera push.
- **Planned wall-worthy hero frame, named before render:** `HERO-01 — TWO LIGHTS IN THE WINDOW`, at 00:56.700 (frame 1701). A real rain-glazed motorway-control room and its operator stay in focus; the previously established eight-feed anomaly resolves into a pair of headlights reflected in the window behind the operator. The physical amber desk practical is the only warm source. Full-frame photographic composition; no title card.
- Voice locked: `edge-tts en-US-ChristopherNeural --rate=-12% --pitch=-4Hz`. Ominous sound bed; captions are 2–5-word groups timed to captured synthesizer WordBoundary telemetry.
- No manager/director polling. The earlier baby-monitor cut is withdrawn and is not part of this deliverable.

## Post-render evidence

- Reproducible offline render command: `python3 videos/team-b/cut-v10/render_v10.py` (requires Python dependencies in `requirements.txt`, `ffmpeg`, and `ffprobe`; no network call during render).
- Rendered file: `video.mp4` (35387386 bytes; SHA-256 `6ae4575ed74e722a12188b4ea9891506a13be3751d62a37ef3fc6f9524d40611`).
- Narration source: `audio/narration_source.mp3`; committed lossless stem `audio/narration_stem_48k.flac`; captured telemetry `timing/word_telemetry.json` (84 WordBoundary events); locked captions `timing/captions_locked.json` (28 cues, 2–5 words per cue, boundary-derived).
- Audio: 48 kHz stereo AAC final; deterministic procedural bed `audio/bed_stem_48k.flac`; lossless mix `audio/master_audio_48k.wav`; voice RMS -24.68 dBFS, bed RMS -30.07 dBFS, mix peak -5.75 dBFS.
- Planned hero captured at `stills/HERO-01-two-lights-in-the-window.png` (00:56.700 / frame 1701).
- Structural gate: 60.000000 s; 1800 CFR frames; 1920×1080; h264 / yuv420p; AAC 48000 Hz stereo. PASS.
- Black/freeze scan (`blackdetect` / `freezedetect`, 0.5 s threshold): 0 black events; 0 freeze events.
- Human review disclosure: **no human listened**; audio verification is numeric/structural only.

### Pasted final `ffprobe` output

```json
{
  "streams": [
    {
      "index": 0,
      "codec_name": "h264",
      "codec_long_name": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
      "profile": "High",
      "codec_type": "video",
      "codec_tag_string": "avc1",
      "codec_tag": "0x31637661",
      "width": 1920,
      "height": 1080,
      "coded_width": 1920,
      "coded_height": 1080,
      "closed_captions": 0,
      "film_grain": 0,
      "has_b_frames": 2,
      "pix_fmt": "yuv420p",
      "level": 41,
      "chroma_location": "left",
      "field_order": "progressive",
      "refs": 1,
      "is_avc": "true",
      "nal_length_size": "4",
      "id": "0x1",
      "r_frame_rate": "30/1",
      "avg_frame_rate": "30/1",
      "time_base": "1/15360",
      "start_pts": 0,
      "start_time": "0.000000",
      "duration_ts": 921600,
      "duration": "60.000000",
      "bit_rate": "4516267",
      "bits_per_raw_sample": "8",
      "nb_frames": "1800",
      "extradata_size": 47,
      "disposition": {
        "default": 1,
        "dub": 0,
        "original": 0,
        "comment": 0,
        "lyrics": 0,
        "karaoke": 0,
        "forced": 0,
        "hearing_impaired": 0,
        "visual_impaired": 0,
        "clean_effects": 0,
        "attached_pic": 0,
        "timed_thumbnails": 0,
        "non_diegetic": 0,
        "captions": 0,
        "descriptions": 0,
        "metadata": 0,
        "dependent": 0,
        "still_image": 0
      },
      "tags": {
        "language": "und",
        "handler_name": "VideoHandler",
        "vendor_id": "[0][0][0][0]",
        "encoder": "Lavc61.3.100 libx264"
      }
    },
    {
      "index": 1,
      "codec_name": "aac",
      "codec_long_name": "AAC (Advanced Audio Coding)",
      "profile": "LC",
      "codec_type": "audio",
      "codec_tag_string": "mp4a",
      "codec_tag": "0x6134706d",
      "sample_fmt": "fltp",
      "sample_rate": "48000",
      "channels": 2,
      "channel_layout": "stereo",
      "bits_per_sample": 0,
      "initial_padding": 0,
      "id": "0x2",
      "r_frame_rate": "0/0",
      "avg_frame_rate": "0/0",
      "time_base": "1/48000",
      "start_pts": 0,
      "start_time": "0.000000",
      "duration_ts": 2880000,
      "duration": "60.000000",
      "bit_rate": "192981",
      "nb_frames": "2814",
      "extradata_size": 5,
      "disposition": {
        "default": 1,
        "dub": 0,
        "original": 0,
        "comment": 0,
        "lyrics": 0,
        "karaoke": 0,
        "forced": 0,
        "hearing_impaired": 0,
        "visual_impaired": 0,
        "clean_effects": 0,
        "attached_pic": 0,
        "timed_thumbnails": 0,
        "non_diegetic": 0,
        "captions": 0,
        "descriptions": 0,
        "metadata": 0,
        "dependent": 0,
        "still_image": 0
      },
      "tags": {
        "language": "und",
        "handler_name": "SoundHandler",
        "vendor_id": "[0][0][0][0]"
      }
    }
  ],
  "format": {
    "filename": "/tmp/cut-v09/videos/team-b/cut-v10/video.mp4",
    "nb_streams": 2,
    "nb_programs": 0,
    "nb_stream_groups": 0,
    "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
    "format_long_name": "QuickTime / MOV",
    "start_time": "0.000000",
    "duration": "60.000000",
    "size": "35387386",
    "bit_rate": "4718318",
    "probe_score": 100,
    "tags": {
      "major_brand": "isom",
      "minor_version": "512",
      "compatible_brands": "isomiso2avc1mp41",
      "encoder": "Lavf61.1.100"
    }
  }
}
```

### Structural scan log

```text
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from '/tmp/cut-v09/videos/team-b/cut-v10/video.mp4':
  Metadata:
    major_brand     : isom
    minor_version   : 512
    compatible_brands: isomiso2avc1mp41
    encoder         : Lavf61.1.100
  Duration: 00:01:00.00, start: 0.000000, bitrate: 4718 kb/s
  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p(progressive), 1920x1080, 4516 kb/s, 30 fps, 30 tbr, 15360 tbn (default)
      Metadata:
        handler_name    : VideoHandler
        vendor_id       : [0][0][0][0]
        encoder         : Lavc61.3.100 libx264
  Stream #0:1[0x2](und): Audio: aac (LC) (mp4a / 0x6134706D), 48000 Hz, stereo, fltp, 192 kb/s (default)
      Metadata:
        handler_name    : SoundHandler
        vendor_id       : [0][0][0][0]
Stream mapping:
  Stream #0:0 -> #0:0 (h264 (native) -> wrapped_avframe (native))
Press [q] to stop, [?] for help
Output #0, null, to 'pipe:':
  Metadata:
    major_brand     : isom
    minor_version   : 512
    compatible_brands: isomiso2avc1mp41
    encoder         : Lavf61.1.100
  Stream #0:0(und): Video: wrapped_avframe, yuv420p(progressive), 1920x1080, q=2-31, 200 kb/s, 30 fps, 30 tbn (default)
      Metadata:
        handler_name    : VideoHandler
        vendor_id       : [0][0][0][0]
        encoder         : Lavc61.3.100 wrapped_avframe
frame=   83 fps=0.0 q=-0.0 size=N/A time=00:00:02.76 bitrate=N/A speed=5.53x    
frame=  172 fps=172 q=-0.0 size=N/A time=00:00:05.73 bitrate=N/A speed=5.72x    
frame=  248 fps=165 q=-0.0 size=N/A time=00:00:08.26 bitrate=N/A speed= 5.5x    
frame=  328 fps=164 q=-0.0 size=N/A time=00:00:10.93 bitrate=N/A speed=5.46x    
frame=  453 fps=181 q=-0.0 size=N/A time=00:00:15.10 bitrate=N/A speed=6.03x    
frame=  570 fps=190 q=-0.0 size=N/A time=00:00:19.00 bitrate=N/A speed=6.33x    
frame=  706 fps=202 q=-0.0 size=N/A time=00:00:23.53 bitrate=N/A speed=6.72x    
frame=  829 fps=207 q=-0.0 size=N/A time=00:00:27.63 bitrate=N/A speed= 6.9x    
frame=  942 fps=209 q=-0.0 size=N/A time=00:00:31.40 bitrate=N/A speed=6.97x    
frame= 1029 fps=206 q=-0.0 size=N/A time=00:00:34.30 bitrate=N/A speed=6.85x    
frame= 1118 fps=203 q=-0.0 size=N/A time=00:00:37.26 bitrate=N/A speed=6.77x    
frame= 1235 fps=206 q=-0.0 size=N/A time=00:00:41.16 bitrate=N/A speed=6.85x    
frame= 1364 fps=210 q=-0.0 size=N/A time=00:00:45.46 bitrate=N/A speed=6.99x    
frame= 1485 fps=212 q=-0.0 size=N/A time=00:00:49.50 bitrate=N/A speed=7.06x    
frame= 1618 fps=216 q=-0.0 size=N/A time=00:00:53.93 bitrate=N/A speed=7.18x    
frame= 1738 fps=217 q=-0.0 size=N/A time=00:00:57.93 bitrate=N/A speed=7.23x    
[out#0/null @ 0x2bd25c40] video:773KiB audio:0KiB subtitle:0KiB other streams:0KiB global headers:0KiB muxing overhead: unknown
frame= 1800 fps=218 q=-0.0 Lsize=N/A time=00:01:00.00 bitrate=N/A speed=7.28x
```
