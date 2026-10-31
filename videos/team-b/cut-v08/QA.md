# QA — The Monitor Knows (cut v08)

## Measured deliverables

- Vertical master: **60.000000 s**, 1080×1920, 30/1 fps, H.264, yuv420p, MP4 faststart; 37,718,527 bytes.
- Landscape derivative: **60.000000 s**, 1920×1080, 30/1 fps, H.264, yuv420p, MP4 faststart; 5,858,586 bytes. It keeps the vertical picture centered over an expanded, softened night-scene background.
- Master audio: AAC, 48,000 Hz, stereo; integrated loudness **−15.97 LUFS**, true peak **−1.94 dBTP**, LRA 3.70 LU. Target is within −16 LUFS ±0.5; true peak is below −1 dBTP.
- Narration stem: 60.000000 s PCM S16LE, 24,000 Hz, mono; 104 spoken words over 45.30 seconds of active speech, computed pace **137.8 wpm**. The remaining stem duration contains deliberate cue gaps; the score remains under them.
- Mix balance: narration active 100 ms-window RMS median −19.13 dBFS; original score stem RMS −34.70 dBFS with the render's +3.52 dB bed gain (−31.18 dBFS), approximately **12.0 dB below** active narration by RMS. This is a stem RMS comparison, not a psychoacoustic LUFS measurement.
- `silencedetect=noise=-50dB:d=0.5` on the master returned no silence events. Vertical master `blackdetect=d=0.5:pix_th=0.02,freezedetect=n=-50dB:d=0.5` returned no black/freeze events. First and final second were checked at 0.2 s and 59.8 s; both show active illustrated content and captions.
- The same strict whole-frame freeze detector reports intervals in the **landscape derivative** because its softened side-fill occupies most of the frame and moves only subtly. The centered portrait program remains animated and captioned throughout; these are global-frame detector hits from the derivative's low-motion side-fill, not repeated/frozen portrait frames. No black events were reported.
- Three evidence stills are in `stills/`: 01 at 2.4 s, 02 at 21.6 s, 03 at 45.6 s. Captions are burned in; no voice-over text is omitted. No separate SRT is needed.
- The generated score and two diegetic effects are original Python synthesis (`project/sound.py`); no reference audio, footage, frames, photos, stock, or third-party music is used. The radiator tick and crib groan are the two reported sounds that happen; the third/latch is deliberately not sounded.
- Reproduction: `FFMPEG=/path/to/ffmpeg ./render.sh` exited 0 on the committed sources and narration stem. The render (picture generation + mix + landscape export + stills) took about 300 seconds in this sandbox. Picture and score intermediates are written under `/tmp/cut-v08-build`.

## Required ffprobe output — vertical master (verbatim)
Command: `ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,codec_type -of default=noprint_wrappers=1 video.mp4`

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
size=37718527
```

## ffprobe output — landscape derivative
Same command with `video-landscape.mp4`:

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
size=5858586
```

## Narration-stem probe
Command: `ffprobe -v error -show_entries format=duration,size:stream=codec_name,sample_rate,channels,codec_type -of default=noprint_wrappers=1 assets/narration.wav`

```text
codec_name=pcm_s16le
codec_type=audio
sample_rate=24000
channels=1
duration=60.000000
size=2880044
```

## loudnorm JSON — master input measurement
Command: `ffmpeg -i video.mp4 -af loudnorm=I=-16:TP=-1:print_format=json -f null -`

```json
{
	"input_i" : "-15.97",
	"input_tp" : "-1.94",
	"input_lra" : "3.70",
	"input_thresh" : "-28.52",
	"output_i" : "-15.95",
	"output_tp" : "-1.00",
	"output_lra" : "3.40",
	"output_thresh" : "-28.25",
	"normalization_type" : "dynamic",
	"target_offset" : "-0.05"
}
```

`input_i` and `input_tp` are the measurements of the encoded master. The `output_*` fields describe a hypothetical normalization pass, not the file's present levels. AAC master measurements are −15.97 LUFS / −1.94 dBTP.

## Voice decision

I chose **Microsoft Edge TTS, `en-US-ChristopherNeural`, `--rate=-12% --pitch=-4Hz`**: the neural US male voice best fits a close, controlled, low-register monitor narrator while keeping the build small. Each of the 25 lines was synthesized separately, then time-compressed with pitch-preserving FFmpeg `atempo` to the cue grid; the resulting active speech measured 137.8 wpm. This is a deliberately designed synthetic voice, not a real-person claim or clone. No human listened; the verification is numeric and structural. If the network engine degrades or becomes unavailable and the committed stem is missing, fallback is local Piper `en_US-lessac-medium`; eSpeak NG is the absolute last resort and must be disclosed if used. Neither fallback was used or auditioned.

## Caption and speech timelines

The caption window is the 2.4-second shot/cut grid. Speech start/end are measured from the committed narration stem's generated cue CSV; cues begin about 0.12 s after each shot, except the twist line, which is delayed to preserve the 1.25 s pre-twist pause. Karaoke word tint advances proportionally through the actual measured speech segment. The twist starts at 45.6 s (76%).

| # | Caption window | Burned-in caption | Speech segment | Spoken narration |
|---:|:---:|---|:---:|---|
| 01 | 00:00.0–00:02.4 | 2:13 A.M. NURSERY | 00:00.12–00:01.87 | At two thirteen a.m. |
| 02 | 00:02.4–00:04.8 | PARENT CHECKS MONITOR | 00:02.52–00:04.69 | The parent checks the monitor. |
| 03 | 00:04.8–00:07.2 | BABY SLEEPS | 00:04.92–00:06.23 | The baby sleeps. |
| 04 | 00:07.2–00:09.6 | YOU COUNT WHAT YOU HEAR | 00:07.32–00:09.06 | Count what you hear. |
| 05 | 00:09.6–00:12.0 | ONE: RADIATOR TICKS | 00:09.72–00:11.47 | One: the radiator ticks. |
| 06 | 00:12.0–00:14.4 | PARENT HEARS IT | 00:12.12–00:13.86 | The parent hears it. |
| 07 | 00:14.4–00:16.8 | TWO: CRIB GROANS | 00:14.52–00:16.27 | Two: the crib groans. |
| 08 | 00:16.8–00:19.2 | HEARD THAT, TOO | 00:16.92–00:18.23 | Heard that too. |
| 09 | 00:19.2–00:21.6 | TWO SOUNDS HAPPENED | 00:19.32–00:20.63 | Two sounds happened. |
| 10 | 00:21.6–00:24.0 | MONITOR REPORTS THREE | 00:21.72–00:23.47 | The monitor reports three. |
| 11 | 00:24.0–00:26.4 | THREE: LATCH TURNS | 00:24.12–00:25.87 | Three: the latch turns. |
| 12 | 00:26.4–00:28.8 | DOOR STAYS SHUT | 00:26.52–00:28.26 | The door stays shut. |
| 13 | 00:28.8–00:31.2 | BABY'S HAND OPENS | 00:28.92–00:31.09 | The baby's left hand opens. |
| 14 | 00:31.2–00:33.6 | ONE FINGER CURLS | 00:31.32–00:32.63 | One finger curls. |
| 15 | 00:33.6–00:36.0 | SHE TURNS TO LENS | 00:33.72–00:35.89 | She turns to the lens. |
| 16 | 00:36.0–00:38.4 | NOW IT NAMES THE PARENT | 00:36.12–00:38.29 | Now it names the parent. |
| 17 | 00:38.4–00:40.8 | THEIR THUMB COVERS GLASS | 00:38.52–00:40.69 | Their thumb covers the glass. |
| 18 | 00:40.8–00:43.2 | PARENT STANDS OUTSIDE | 00:40.92–00:42.67 | The parent stands outside. |
| 19 | 00:43.2–00:45.6 | LENS FACES THE CHILD | 00:43.32–00:44.63 | Lens faces her. |
| 20 | 00:45.6–00:48.0 | VOICE ISN'T INSIDE | 00:45.88–00:48.05 | But the voice isn't inside. |
| 21 | 00:48.0–00:50.4 | BESIDE THE REFLECTION | 00:48.12–00:50.29 | It stands by the reflection. |
| 22 | 00:50.4–00:52.8 | ON THIS SIDE OF GLASS | 00:50.52–00:52.69 | On this side of glass. |
| 23 | 00:52.8–00:55.2 | NOT THE CHILD'S SIDE | 00:52.92–00:54.66 | Not the child's side. |
| 24 | 00:55.2–00:57.6 | REACH FOR THE PLUG | 00:55.32–00:57.49 | Parent reaches for the plug. |
| 25 | 00:57.6–01:00.0 | THE MONITOR GOES QUIET | 00:57.72–00:59.47 | The monitor goes quiet. |

## How this differs from the references

- **Reference 01:** deliberately avoided emergency-phone alerts, a household body count, and the family's headcount changing. The count here is explicitly two audible nursery sounds versus three voice-reported sounds; nobody is counted or missing.
- **Reference 02:** avoided its family-count counter, hallway/bathroom silhouette reveal, and message-based accusation about a parent. The nursery door remains shut; the turn is a monitor narrator crossing from child observations to a reflection beyond the lens.
- **Reference 03:** avoided a future-self message, “don't turn on the light” rule, chat-bubble plot, and phone-versus-door audience poll. There is no phone messaging or choice poll; the last spoken line is the monitor going quiet, followed only by a visual `HALL MIC: LIVE` continuation tag.

## Blunt self-review

The procedural night palette, moving waveform, restrained glow, and third-person speech support the premise better than v03's abstract grid did. The 76% reflection reveal and the three-reported/two-heard count are understandable from caption-only viewing. The vector figures are extremely simple and a little diagrammatic; the monitor UI is not photoreal and the final green sequel tag is small. The opening duplicates `2:13 A.M.` once as HUD and once in the lower caption; it is clear but mildly redundant. Several shots are deliberately held as quiet vector compositions rather than visually complex action. I checked first/last frames and numeric scans but did not do a full real-time watch-through. **No human listened; verification is numeric and structural.**
