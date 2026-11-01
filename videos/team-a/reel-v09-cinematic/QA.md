# THE FOURTH ARRIVAL — QA and evidence

## Wall-frame decision, made before imagery

**THE UNCOUNTED GUEST**, Shot 07 at 32.0–39.2 s, was named here before generation or rendering. It is a one-point view from the rainy hotel entrance across wet footprints toward the brass-lit desk and the deep empty lift. The desk and open ledger form the middle distance; the footprints and reflections give a foreground. The unseen arrival is conveyed by its physical trace, not a diagram or floating interface. The clean frame extracted from the final master at 37.3 s is `stills/07-wall-frame-uncounted-guest.png`.

## Delivery

- Master `video.mp4`: 60.000 s, 1,800 frames, 1920×1080 landscape, H.264 High/yuv420p, 30 fps; AAC-LC stereo, 48 kHz. SHA-256 **`3cd0eda74cfb4a605fc7a95b781958b050899a869261182a91f5b02e93fcffc4`**.
- Voice: `audio/narration_stem_48k.flac`, genuinely synthesized with `en-US-ChristopherNeural --rate=-12% --pitch=-4Hz`; exact service streams and boundary events are in `audio/tts_lines/`, with the cut/EQ mapping and hashes in `timing/tts_source_manifest.json`. The final voice is 52.924 s; 124 event words, last word ends at 51.934 s. The 2.683 s pre-reveal gap is deliberate.
- Sound: original synthesized score, awning rain, telephone, lift, footfalls and thunder, mixed with committed `audio/bed_ducked_48k.flac`; offline gain and loudness parameters are in `audio/gain_mapping.json`. Measured voice versus combined bed on actual word spans: **+10.500 dB before common normalization**. This ratio does not establish perceptual intelligibility.
- Captions: 35 cues, 2–5 words each; 54 px Anton, lower-third, white/amber with the threat line crimson. `timing/captions_locked.json` maps all 124 real Edge word starts to the first eligible 30 fps frame; maximum scheduling delay **0.033292 s**, less than one frame. An independent audit decoded the finished master and checked glyph color at the prior and first eligible frame for **89/89 non-initial words**. The remaining 35 first-of-cue words were schedule-checked, not separately pixel-transition tested. Last cue clears at 52.484 s.
- Visual process: ten original photographic-style generated plates; source dimensions **1376×768, not native 1080p**, Lanczos-normalized to 1920×1080. Grade's published House Look 33³ LUTs are applied with trilinear interpolation; float-coordinate bicubic motion, halation, two-depth procedural rain with indoor window masks, grain and a subtle lamp breath are composited. The exterior foreground has rain across the camera plane. Plates are 2.5D stills, not filmed motion: the lift is shown open rather than animated opening and the footprint stopping is implied. Lamp design, architecture and a dim ceiling fixture vary between plates; these continuity limits are documented in `plates/README.md`.
- The wall frame and stills from all ten shots were extracted from the actual master. Selected frames were visually inspected; the automated freeze/black scan reported no events at its recorded thresholds (`qa/freeze-black.txt`). Grain can mask a static image, so this is not proof of motion or artistic quality.

**No human listened to or continuously watched this film.** No perceptual claims about the performance, mix, pacing or caption readability are made on the basis of numerical tests alone.

## Actual final-master loudnorm JSON

Command: `ffmpeg -hide_banner -nostats -i video.mp4 -map 0:a:0 -af 'loudnorm=I=-16:TP=-2.2:LRA=9:print_format=json' -f null -`. The values to assess are `input_i` and `input_tp`; `output_*` describes a hypothetical additional normalization, not the delivered audio. Full console output is `qa/loudnorm-full.txt`.

```json
{
  "input_i": "-16.28",
  "input_tp": "-2.15",
  "input_lra": "5.50",
  "input_thresh": "-26.40",
  "output_i": "-16.71",
  "output_tp": "-2.47",
  "output_lra": "4.60",
  "output_thresh": "-26.85",
  "normalization_type": "dynamic",
  "target_offset": "0.71"
}
```

The delivered AAC measures −16.28 LUFS and −2.15 dBTP, inside the requested −16 ±0.5 LUFS and ≤−1 dBTP. Pearson correlation of the rebuilt PCM master with decoded delivered AAC, first 2,880,000 aligned samples: **0.999304 left / 0.999300 right**. The decoder emits 512 additional AAC padding samples; `ffprobe` reports both streams and the container at exactly 60.000 s.

## Pasted final `ffprobe` output

Command: `ffprobe -v error -count_frames -show_entries 'stream=index,codec_name,profile,codec_type,width,height,pix_fmt,r_frame_rate,avg_frame_rate,nb_read_frames,nb_frames,sample_rate,channels,duration,bit_rate:format=format_name,duration,size' -of json video.mp4`. Full unabridged stream data is `qa/ffprobe.json`.

```json
{
  "programs": [],
  "stream_groups": [],
  "streams": [
    {"index":0,"codec_name":"h264","profile":"High","codec_type":"video","width":1920,"height":1080,"pix_fmt":"yuv420p","r_frame_rate":"30/1","avg_frame_rate":"30/1","duration":"60.000000","bit_rate":"4165956","nb_frames":"1800","nb_read_frames":"1800"},
    {"index":1,"codec_name":"aac","profile":"LC","codec_type":"audio","sample_rate":"48000","channels":2,"r_frame_rate":"0/0","avg_frame_rate":"0/0","duration":"60.000000","bit_rate":"193250","nb_frames":"2814","nb_read_frames":"2813"}
  ],
  "format":{"format_name":"mov,mp4,m4a,3gp,3g2,mj2","duration":"60.000000","size":"32762154"}
}
```

## Reproduce offline

From this project directory, with FFmpeg/ffprobe 7.1.5, Python 3, NumPy 2.3.5, Pillow 12.3, SciPy 1.17, and OpenCV 4.11 installed:

```sh
python3 render.py --build-dir /tmp/reel-hotel-build --crf 20
python3 audit_master.py --master-audio /tmp/reel-hotel-build/master_audio_48k.wav
```

The renderer needs no network or Edge request: it uses the committed plates, LUTs, font, narration, ducked bed, gain mapping and actual word events. `build_audio.py` checks both FLAC hashes and the rebuilt PCM master SHA-256; this PCM rebuild was byte-identical on the audit host. Shot 07 was separately re-rendered offline for all 216 frames and matched its original encoded clip byte-for-byte (SHA-256 `4afe8cd58ad94260064a58c5901a9890cdff18218017b737d32550e10fbd8254`). The **entire** film was not re-rendered a second time. `qa/numeric.json` and `qa/caption-pixels.json` document the numerical checks; other software versions may not yield bit-identical encoded output. See `house-look-addendum.md` and `reference-study.md` for Grade technique and attribution.
