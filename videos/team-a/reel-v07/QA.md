# QA — ARRIVAL LOG / reel-v07

**Verification statement:** no human listened; verification is numeric and structural. Selected decoded stills were visually inspected by the agent, not a continuous human audiovisual screening. A person should review performance, sound balance and storytelling before further use. No external publishing is authorized.

## Final measurements

| Property | Vertical `video.mp4` | Landscape `video-landscape.mp4` |
|---|---:|---:|
| Runtime | 60.000000 s | 60.000000 s |
| Resolution / fps | 1080×1920 / 30 | 1920×1080 / 30 |
| Codec / pixel format | H.264 / yuv420p | H.264 / yuv420p |
| Audio | AAC, 48 kHz stereo | AAC, 48 kHz stereo |
| Integrated loudness / true peak | −16.11 LUFS / −1.88 dBTP | −16.11 LUFS / −1.88 dBTP |
| Video / audio bitrate | 1,076,126 / 193,370 bit/s | 560,897 / 193,370 bit/s |
| Container bitrate | 1,278,563 bit/s | 763,334 bit/s |
| Size | 9,589,223 bytes | 5,725,007 bytes |
| Decoded frames | 1,800 | 1,800 |
| SHA-256 | `89942ed1d0717940ad9f83f743ef76918ae3282e2c5e4e29e29b20900e914d85` | `0f9a6ff8511b080d6393a9bdf25c5279d73d19347af228e9752a59b317fb7cf3` |

The two renders total **15,314,230 bytes** (14.61 MiB), below 128 MB combined. `moov` precedes `mdat`: vertical byte offsets 36 and 67475; landscape 36 and 67479. The landscape contains the entire vertical picture within original static sidebars. Measurements below are from the final files in the previous sandbox session; the hashes above were rechecked after the session resumed.

## Voice decision

I independently selected **Edge TTS 7.3.1, `en-US-ChristopherNeural`, rate −12%, pitch −4 Hz** as the requested consistent low-register male neural profile. The successful service output was committed as an offline 48 kHz stereo FLAC; no fallback was needed. Twenty-two near-digital-silence intervals between sentences were trimmed (loudest removed interval −89.5 dBFS); speech was not time-stretched or pitch-shifted after synthesis. The 123 Edge word events yield 123 words/min over the 60-second film, or 125.99 words/min across the 58.577-second first-to-last-word span. The final word before the reveal ends at 40.402 s; the next begins at 43.490 s, a 3.088 s pause. There is no subjective claim about voice performance.

## Audio provenance and mix

The narration is a designed synthetic element, not a real-person claim. The original music uses 55/82/110 Hz oscillators; ticks, low impacts, relay and pen sounds are original deterministic oscillator/seeded-noise synthesis in `make_sound.py`. No reference recording, stock or music sample is reused. Anton is bundled under SIL Open Font License 1.1.

| Isolated source before final common loudness normalization | Measured integrated loudness / gain |
|---|---:|
| Narration | −19.45 LUFS / 0 dB |
| Original music | −27.84 LUFS / −1.61 dB → −29.45 LUFS |
| Dry effects | −40.56 LUFS / +6.11 dB → −34.45 LUFS |

Voice is **10.00 LU above music** on the isolated pre-normalization integrated measurements. Final loudnorm acts dynamically on the combined mix, so this does not claim an identical instantaneous difference throughout. The JSON `input_*` values below measure the delivered file; `output_*` describes a hypothetical further normalization.

## Structural and picture checks

`references/NOTES-reel.md` was committed first at `fd49ec6`, after computationally decoding all 5,714 release frames and examining the three supplied contact sheets and audio waveforms. The original script and shot plan were committed at `fd424f4` and the final script/voice at `01b3ee7`, **before production picture rendering**. Twenty-five shots use 2.4 s hard-cut intervals, an eased 1.00→1.06 push and one moving camera cursor. The timestamp is in the first shot; the betrayal begins at 45.368 s (75.6%); the next-shift hook precedes the final sentence, “Floor thirteen.”

There are **38 burned-in and SRT beats**, each 2–5 Edge word events, in heavy Anton at 84–94 px on the 1080-wide vertical image. Full-frame landscape scales the captions to roughly 47–53 px; incidental portrait HUD labels are smaller. Comparing the SRT cues with Edge word metadata gave a maximum word-boundary overhang of 0.006 s, under one 30 fps frame. This is a structural metadata comparison, not a human sync judgment. First cue starts 0.257 s and last holds through 59.840 s.

Five stills were decoded from the final vertical file at 1.0, 20.9, 46.6, 58.4 and 24.7 s (`stills/01.png`–`05.png`). Selected frames including two and four exit silhouettes and the landscape reveal were inspected, not the entire film continuously.

Both outputs were fully decoded with **zero error bytes**. Whole-file `blackdetect=d=0.5:pix_th=0.10:pic_th=0.98`, a second near-digital-black pass at `pix_th=0.02`, `freezedetect=n=-60dB:d=0.5`, and full-mix `silencedetect=noise=-50dB:d=0.5` returned **no events**. These threshold-based tests do not substitute for human review. `./verify.sh` repeats the commands and saves detailed logs under `/tmp`; it requires FFmpeg and ffprobe.

## Exact ffprobe output

The spec command was `ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 FILE`.

**video.mp4**

```text
codec_name=h264
codec_type=video
width=1080
height=1920
r_frame_rate=30/1
codec_name=aac
codec_type=audio
r_frame_rate=0/0
duration=60.000000
size=9589223
```

**video-landscape.mp4**

```text
codec_name=h264
codec_type=video
width=1920
height=1080
r_frame_rate=30/1
codec_name=aac
codec_type=audio
r_frame_rate=0/0
duration=60.000000
size=5725007
```

Additional actual stream probe used `ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_name,codec_type,width,height,pix_fmt,r_frame_rate,avg_frame_rate,sample_rate,channels,channel_layout,bit_rate,start_time,duration,nb_frames -of compact=p=0:nk=0 FILE`.

**video.mp4**

```text
codec_name=h264|codec_type=video|width=1080|height=1920|pix_fmt=yuv420p|r_frame_rate=30/1|avg_frame_rate=30/1|start_time=0.000000|duration=60.000000|bit_rate=1076126|nb_frames=1800
codec_name=aac|codec_type=audio|sample_rate=48000|channels=2|channel_layout=stereo|r_frame_rate=0/0|avg_frame_rate=0/0|start_time=0.000000|duration=60.000000|bit_rate=193370|nb_frames=2814
duration=60.000000|size=9589223|bit_rate=1278563
```

**video-landscape.mp4**

```text
codec_name=h264|codec_type=video|width=1920|height=1080|pix_fmt=yuv420p|r_frame_rate=30/1|avg_frame_rate=30/1|start_time=0.000000|duration=60.000000|bit_rate=560897|nb_frames=1800
codec_name=aac|codec_type=audio|sample_rate=48000|channels=2|channel_layout=stereo|r_frame_rate=0/0|avg_frame_rate=0/0|start_time=0.000000|duration=60.000000|bit_rate=193370|nb_frames=2814
duration=60.000000|size=5725007|bit_rate=763334
```

## Narration stem ffprobe — actual output

`ffprobe -v error -show_streams -show_format assets/narration.flac`

```text
[STREAM]
index=0
codec_name=flac
codec_long_name=FLAC (Free Lossless Audio Codec)
profile=unknown
codec_type=audio
codec_tag_string=[0][0][0][0]
codec_tag=0x0000
sample_fmt=s16
sample_rate=48000
channels=2
channel_layout=stereo
bits_per_sample=0
initial_padding=0
id=N/A
r_frame_rate=0/0
avg_frame_rate=0/0
time_base=1/48000
start_pts=0
start_time=0.000000
duration_ts=2871152
duration=59.815667
bit_rate=N/A
max_bit_rate=N/A
bits_per_raw_sample=16
nb_frames=N/A
nb_read_frames=N/A
nb_read_packets=N/A
extradata_size=34
DISPOSITION:default=0
DISPOSITION:dub=0
DISPOSITION:original=0
DISPOSITION:comment=0
DISPOSITION:lyrics=0
DISPOSITION:karaoke=0
DISPOSITION:forced=0
DISPOSITION:hearing_impaired=0
DISPOSITION:visual_impaired=0
DISPOSITION:clean_effects=0
DISPOSITION:attached_pic=0
DISPOSITION:timed_thumbnails=0
DISPOSITION:captions=0
DISPOSITION:descriptions=0
DISPOSITION:metadata=0
DISPOSITION:dependent=0
DISPOSITION:still_image=0
DISPOSITION:multilayer=0
[/STREAM]
[FORMAT]
filename=assets/narration.flac
nb_streams=1
nb_programs=0
nb_stream_groups=0
format_name=flac
format_long_name=raw FLAC
start_time=0.000000
duration=59.815667
size=1593167
bit_rate=213076
probe_score=100
TAG:encoder=Lavf61.7.103
[/FORMAT]
```

## Loudness — actual command output and JSON

The exact spec command `ffmpeg -v error -i video.mp4 -af loudnorm=print_format=summary -f null - 2>&1 | tail -12` returned **zero bytes** (also for the landscape file): `-v error` suppresses the filter’s informational summary. Its actual output is empty:

```text

```

A meaningful measurement was obtained with `ffmpeg -hide_banner -nostats -i FILE -af loudnorm=I=-16:TP=-1:LRA=11:print_format=json -f null -`. The actual JSON below was identical for both files because their AAC audio is copied unchanged.

```json
{
  "input_i" : "-16.11",
  "input_tp" : "-1.88",
  "input_lra" : "2.70",
  "input_thresh" : "-26.52",
  "output_i" : "-15.99",
  "output_tp" : "-1.77",
  "output_lra" : "2.50",
  "output_thresh" : "-26.39",
  "normalization_type" : "dynamic",
  "target_offset" : "-0.01"
}
```

## Speech and caption timelines

Rows show first/last captured speech-word boundaries and the corresponding on-screen/SRT cue; the gap during the pre-reveal pause is deliberate. Word highlighting is generated from the committed timing metadata.

| # | Speech start–end (s) | Caption start → end | Caption |
|---:|---:|---|---|
| 1 | 0.257–1.890 | 00:00:00,257 --> 00:00:02,154 | AT TWO FORTY-ONE A.M., |
| 2 | 2.174–3.098 | 00:00:02,174 --> 00:00:03,092 | THE LIFT STOPS |
| 3 | 3.112–4.376 | 00:00:03,112 --> 00:00:04,656 | AT FLOOR THIRTEEN. |
| 4 | 4.876–6.552 | 00:00:04,876 --> 00:00:06,832 | YOUR TOWER HAS TWELVE. |
| 5 | 7.052–8.089 | 00:00:07,052 --> 00:00:08,369 | YOU'RE THE GUARD. |
| 6 | 8.589–9.342 | 00:00:08,589 --> 00:00:09,622 | YOUR RULE: |
| 7 | 9.683–10.805 | 00:00:09,683 --> 00:00:11,041 | WHEN THE DOORS OPEN, |
| 8 | 11.061–11.842 | 00:00:11,061 --> 00:00:11,836 | COUNT THE PEOPLE |
| 9 | 11.856–12.609 | 00:00:11,856 --> 00:00:12,889 | WHO GET OUT. |
| 10 | 13.109–14.487 | 00:00:13,109 --> 00:00:14,767 | WRITE IT IN YOUR LOG. |
| 11 | 14.987–16.592 | 00:00:14,987 --> 00:00:16,872 | NEVER COUNT WHO GOES IN. |
| 12 | 17.092–18.299 | 00:00:17,092 --> 00:00:18,579 | ONE STEPS OUT. |
| 13 | 18.799–19.950 | 00:00:18,799 --> 00:00:19,944 | THE ARRIVAL CAMERA |
| 14 | 19.964–21.385 | 00:00:19,964 --> 00:00:21,665 | SHOWS AN EMPTY CAR. |
| 15 | 21.885–22.808 | 00:00:21,885 --> 00:00:23,088 | YOU WRITE ONE. |
| 16 | 23.308–24.160 | 00:00:23,308 --> 00:00:24,396 | NEXT STOP, |
| 17 | 24.416–25.495 | 00:00:24,416 --> 00:00:25,775 | TWO STEP OUT. |
| 18 | 25.995–26.819 | 00:00:25,995 --> 00:00:26,814 | THE CAR IS |
| 19 | 26.834–27.714 | 00:00:26,834 --> 00:00:27,994 | EMPTY AGAIN. |
| 20 | 28.214–29.208 | 00:00:28,214 --> 00:00:29,488 | YOU WRITE TWO. |
| 21 | 29.708–30.603 | 00:00:29,708 --> 00:00:30,883 | THEN THREE. |
| 22 | 31.103–32.623 | 00:00:31,103 --> 00:00:32,816 | THE LOG WRITES ITSELF, |
| 23 | 32.836–33.902 | 00:00:32,836 --> 00:00:34,182 | IN YOUR HANDWRITING. |
| 24 | 34.402–35.453 | 00:00:34,402 --> 00:00:35,447 | YOUR PEN IS STILL |
| 25 | 35.467–36.262 | 00:00:35,467 --> 00:00:36,542 | ON THE DESK. |
| 26 | 36.762–38.325 | 00:00:36,762 --> 00:00:38,605 | YOU CHECK THE FLOOR PLAN. |
| 27 | 38.825–39.478 | 00:00:38,825 --> 00:00:39,473 | THERE IS NO |
| 28 | 39.493–40.402 | 00:00:39,493 --> 00:00:40,682 | GUARD BOOTH. |
| 29 | 43.490–44.868 | 00:00:43,490 --> 00:00:45,148 | THE CAMERA TURNS. |
| 30 | 45.368–46.192 | 00:00:45,368 --> 00:00:46,186 | YOUR DESK IS |
| 31 | 46.206–47.385 | 00:00:46,206 --> 00:00:47,665 | INSIDE THE LIFT. |
| 32 | 47.885–49.106 | 00:00:47,885 --> 00:00:49,386 | YOU WEREN'T WATCHING IT. |
| 33 | 49.606–50.899 | 00:00:49,606 --> 00:00:51,179 | IT WAS CARRYING YOU. |
| 34 | 51.399–52.933 | 00:00:51,399 --> 00:00:53,213 | FOUR PEOPLE STEP OUT. |
| 35 | 53.433–54.356 | 00:00:53,433 --> 00:00:54,351 | THE NEXT SHIFT |
| 36 | 54.371–55.592 | 00:00:54,371 --> 00:00:55,872 | HAS ALREADY BEGUN. |
| 37 | 56.092–57.328 | 00:00:56,092 --> 00:00:57,578 | THE DISPLAY READS: |
| 38 | 57.598–58.834 | 00:00:57,598 --> 00:00:59,840 | FLOOR THIRTEEN. |

Full speech-word timeline, seconds (start–end, Edge event):

```text
00.257–00.512  At
00.527–00.797  two
00.811–01.351  forty-one
01.365–01.890  a.m.
02.174–02.302  the
02.316–02.601  lift
02.615–03.098  stops
03.112–03.211  at
03.226–03.595  floor
03.609–04.376  thirteen
04.876–05.103  Your
05.118–05.629  tower
05.643–05.913  has
05.927–06.552  twelve
07.052–07.379  You're
07.393–07.521  the
07.535–08.089  guard
08.589–08.930  Your
08.944–09.342  rule
09.683–09.825  when
09.839–09.953  the
09.967–10.379  doors
10.393–10.805  open
11.061–11.331  count
11.345–11.444  the
11.458–11.842  people
11.856–11.970  who
11.984–12.169  get
12.183–12.609  out
13.109–13.436  Write
13.450–13.564  it
13.578–13.720  in
13.734–13.905  your
13.919–14.487  log
14.987–15.385  Never
15.399–15.754  count
15.768–15.924  who
15.939–16.237  goes
16.251–16.592  in
17.092–17.447  One
17.461–17.887  steps
17.902–18.299  out
18.799–18.927  The
18.941–19.495  arrival
19.510–19.950  camera
19.964–20.348  shows
20.362–20.518  an
20.532–20.859  empty
20.873–21.385  car
21.885–22.126  You
22.140–22.410  write
22.424–22.808  one
23.308–23.691  Next
23.706–24.160  stop
24.416–24.686  two
24.700–25.055  step
25.069–25.495  out
25.995–26.152  The
26.166–26.564  car
26.578–26.819  is
26.834–27.174  empty
27.189–27.714  again
28.214–28.441  You
28.456–28.726  write
28.740–29.208  two
29.708–30.035  Then
30.049–30.603  three
31.103–31.274  The
31.288–31.672  log
31.686–31.998  writes
32.012–32.623  itself
32.836–32.978  in
32.993–33.149  your
33.163–33.902  handwriting
34.402–34.629  Your
34.643–34.970  pen
34.984–35.112  is
35.126–35.453  still
35.467–35.581  on
35.595–35.680  the
35.694–36.262  desk
36.762–36.961  You
36.975–37.288  check
37.302–37.416  the
37.430–37.771  floor
37.785–38.325  plan
38.825–39.052  There
39.066–39.208  is
39.223–39.478  no
39.493–39.876  guard
39.890–40.402  booth
43.490–43.646  The
43.660–44.115  camera
44.129–44.868  turns
45.368–45.595  Your
45.609–46.035  desk
46.050–46.192  is
46.206–46.746  inside
46.760–46.859  the
46.873–47.385  lift
47.885–48.098  You
48.112–48.382  weren't
48.396–48.865  watching
48.879–49.106  it
49.606–49.777  It
49.791–49.976  was
49.990–50.558  carrying
50.572–50.899  you
51.399–51.768  Four
51.783–52.152  people
52.166–52.507  step
52.521–52.933  out
53.433–53.575  The
53.589–53.916  next
53.930–54.356  shift
54.371–54.555  has
54.570–55.010  already
55.024–55.592  begun
56.092–56.248  The
56.263–56.774  display
56.788–57.328  reads
57.598–58.010  Floor
58.024–58.834  thirteen
```

## How this differs from the references

The supplied README appears to swap descriptions of the actual 01 and 03 files; this comparison follows their decoded pictures. **01:** no “do not turn on the light” rule, no texts from tomorrow-night-you, no phone-or-door choice. **02:** no emergency phone notification reporting a body/family count, no family impostor or bathroom/dad double. **03:** no phone alert claiming “four people in your home,” no bedroom/mother-double scenario, and no family-count story. The original rule is a lift exit protocol, the count is people exiting, and the betrayal is the guard being carried. Composition, pace, contrast and caption grammar were studied; stories, frames and audio were not copied.

## Honest self-review and sandbox limits

The art is intentionally diagrammatic: figures do not independently walk, the same camera cursor supplies the small moving detail each shot, and the third count is explicit in the caption/ledger rather than a fully animated group. Landscape preserves the portrait picture and readable captions, but its incidental portrait HUD text scales below 40 px. The reveal uses a nested-desk diagram rather than a physically continuous camera move. Edge TTS and the final mix have not been heard by a human in the sandbox, so performance, intelligibility, balance and emotional impact remain unverified. The optional voice regeneration requires network/service access; rendering uses the committed stem offline.
