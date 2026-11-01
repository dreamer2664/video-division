#!/usr/bin/env python3
"""Offline, reproducible 60.000-second cinematic render for CUT V10."""
from __future__ import annotations
import gc, json, math, os, re, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from build_audio_v10 import build_audio

HERE = Path(__file__).resolve().parent
PLATES = HERE / "plates"
LUTS = HERE / "luts"
TIMING = HERE / "timing"
AUDIO = HERE / "audio"
STILLS = HERE / "stills"
OUT = HERE / "video.mp4"
W, H, FPS, FRAMES = 1376, 768, 30, 1800

# Each row is [start frame, end frame, plate, LUT, rain amount, pan-x, pan-y].
SCENES = [
    (0,    180, "junction4_road",        "blackwater_slate", 0.12,  0.000,  0.010),
    (180,  330, "junction4_road",        "amber_ledger",     0.15,  0.018,  0.005),
    (330,  510, "control_room_wide",    "amber_ledger",     0.025, 0.000,  0.000),
    (510,  660, "operator_close",       "mercury_stillness",0.020, 0.015,  0.000),
    (660,  840, "eight_feeds_wall",     "blackwater_slate", 0.025, 0.000,  0.000),
    (840,  990, "control_room_wide",    "amber_ledger",     0.020,-0.012,  0.000),
    (990, 1140, "junction4_road",       "amber_ledger",     0.12, -0.012,  0.010),
    (1140,1320, "eight_feeds_exit_empty","blackwater_slate",0.025, 0.012,  0.000),
    (1320,1470, "operator_close",       "mercury_stillness",0.020,-0.010,  0.000),
    (1470,1620, "eight_feeds_exit_empty","blackwater_slate",0.020, 0.000,  0.000),
    (1620,1800, "control_room_wide",    "amber_ledger",     0.018, 0.000,  0.000),
]
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]


def run(cmd: list[str], *, capture=False):
    return subprocess.run(cmd, check=True, text=True, capture_output=capture)


def load_cube(path: Path) -> np.ndarray:
    rows, size = [], 33
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("TITLE") or s.startswith("DOMAIN"):
                continue
            if s.startswith("LUT_3D_SIZE"):
                size = int(s.split()[1]); continue
            p = s.split()
            if len(p) == 3:
                rows.append((float(p[0]), float(p[1]), float(p[2])))
    if len(rows) != size ** 3:
        raise RuntimeError(f"Bad LUT {path}: expected {size**3} entries, got {len(rows)}")
    # Match grade-v05's .cube order (R-fastest) and trilinear lookup.
    return np.transpose(np.asarray(rows, dtype=np.float32).reshape((size, size, size, 3)), (2, 1, 0, 3)).copy()


def apply_lut(image: np.ndarray, lut: np.ndarray) -> np.ndarray:
    n = lut.shape[0] - 1
    v = np.clip(image.astype(np.float32) / 255.0, 0, 1) * np.float32(n)
    lo = np.clip(np.floor(v).astype(np.int32), 0, n - 1); hi = lo + 1
    f = v - lo
    r0,g0,b0 = lo[:,:,0],lo[:,:,1],lo[:,:,2]; r1,g1,b1 = hi[:,:,0],hi[:,:,1],hi[:,:,2]
    dr,dg,db = f[:,:,0:1],f[:,:,1:2],f[:,:,2:3]
    c00 = lut[r0,g0,b0]*(1-dr)+lut[r1,g0,b0]*dr
    c01 = lut[r0,g0,b1]*(1-dr)+lut[r1,g0,b1]*dr
    c10 = lut[r0,g1,b0]*(1-dr)+lut[r1,g1,b0]*dr
    c11 = lut[r0,g1,b1]*(1-dr)+lut[r1,g1,b1]*dr
    c0 = c00*(1-dg)+c10*dg; c1 = c01*(1-dg)+c11*dg
    return np.clip(c0*(1-db)+c1*db, 0, 1)


def make_rain(seed: int, length: int, density: int, blur: float) -> Image.Image:
    tw, th = 2240, 1280
    rng = np.random.default_rng(seed)
    im = Image.new("L", (tw, th), 0); d = ImageDraw.Draw(im)
    for _ in range(density):
        x = int(rng.integers(0, tw)); y = int(rng.integers(0, th))
        ln = int(rng.integers(max(8, length // 2), length + 1))
        val = int(rng.integers(42, 170))
        d.line((x, y, x + int(ln * 0.22), y + ln), fill=val, width=1 if rng.random() < 0.83 else 2)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return im


def load_plates_and_luts():
    luts = {p.stem: load_cube(p) for p in LUTS.glob("*.cube")}
    plates = {}
    for row in SCENES:
        _,_,name,lut_name,*_ = row
        key = (name, lut_name)
        if key not in plates:
            src = np.asarray(Image.open(PLATES / f"{name}.png").convert("RGB"))
            if src.shape[:2] != (H, W):
                raise RuntimeError(f"Plate raster mismatch: {name} {src.shape}")
            plates[key] = Image.fromarray((apply_lut(src, luts[lut_name]) * 255.0 + 0.5).astype(np.uint8))
    return plates


def make_caption_cues() -> list[dict]:
    data = json.loads((TIMING / "word_telemetry.json").read_text(encoding="utf-8"))
    text = (AUDIO / "narration_text.txt").read_text(encoding="utf-8").strip()
    tokens = text.split()
    events = data["words"]
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.casefold())
    # A rare Edge response can bundle adjacent lexical tokens into one WordBoundary event.
    # Expand its text for word-count purposes while retaining that exact event's shared
    # start/end timestamps; captions still begin/end only on captured synthesizer boundaries.
    words=[]; cursor=0
    for event_index,event in enumerate(events):
        parts=event["text"].split()
        for part in parts:
            if cursor>=len(tokens) or norm(tokens[cursor])!=norm(part):
                raise RuntimeError(f"Source/WordBoundary mismatch at token {cursor}: {tokens[cursor:cursor+1]} vs {part!r}")
            words.append({"text":tokens[cursor],"start_s":event["start_s"],"end_s":event["end_s"],"event_index":event_index})
            cursor+=1
    if cursor!=len(tokens):
        raise RuntimeError(f"Source/WordBoundary token count mismatch: {cursor} of {len(tokens)}")
    cues = []; i=0
    while i < len(words):
        remaining=len(words)-i
        size=3 if remaining>4 else remaining
        group=words[i:i+size]
        source_group=[w["text"] for w in group]
        if not 2 <= len(group) <= 5:
            raise RuntimeError("Caption group outside 2–5 word requirement")
        cues.append({"start": 0.300 + group[0]["start_s"],
                     "end": 0.300 + group[-1]["end_s"],
                     "text": " ".join(source_group),
                     "words": source_group,
                     "first_word_index": i,
                     "source_event_indices": sorted(set(w["event_index"] for w in group))})
        i+=size
    (TIMING / "captions_locked.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cues


def caption_patch(text: str) -> Image.Image:
    font_path = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
    font = ImageFont.truetype(font_path, 31) if font_path else ImageFont.load_default()
    tmp = Image.new("RGBA", (W, 90), (0,0,0,0)); d = ImageDraw.Draw(tmp)
    box = d.textbbox((0,0), text, font=font, stroke_width=1)
    tw, th = box[2]-box[0], box[3]-box[1]
    pw, ph = tw + 42, 60
    patch = Image.new("RGBA", (pw, ph), (0,0,0,0)); pd = ImageDraw.Draw(patch)
    pd.rounded_rectangle((0,0,pw-1,ph-1), radius=13, fill=(4,8,14,172), outline=(236,242,248,40), width=1)
    pd.text(((pw-tw)//2, (ph-th)//2-box[1]), text, font=font, fill=(244,244,237,250), stroke_width=1, stroke_fill=(2,5,8,180))
    return patch


def make_reflection() -> Image.Image:
    # A restrained pair of cold headlamps and vertical rain-glass bloom for the final room shot.
    p = Image.new("RGBA", (300, 180), (0,0,0,0)); d = ImageDraw.Draw(p)
    for x in (83, 197):
        d.ellipse((x-27, 45, x+27, 99), fill=(184,225,255,22))
        d.ellipse((x-13, 58, x+13, 84), fill=(205,232,255,74))
        d.ellipse((x-5, 65, x+5, 75), fill=(255,250,226,245))
        d.line((x,82,x+2,144), fill=(187,216,240,45), width=7)
    p = p.filter(ImageFilter.GaussianBlur(12))
    # Restore the sharp cores over the soft glass halation.
    d = ImageDraw.Draw(p)
    for x in (83,197):
        d.ellipse((x-4,65,x+4,73), fill=(255,250,232,210))
    return p


def blend_patch(frame: np.ndarray, patch: Image.Image, x: int, y: int, opacity: float = 1.0) -> None:
    rgba = np.asarray(patch, dtype=np.float32) / 255.0
    ph,pw = rgba.shape[:2]
    x=max(0,min(W-pw,x)); y=max(0,min(H-ph,y))
    roi=frame[y:y+ph,x:x+pw]
    a=rgba[:,:,3:4]*np.float32(opacity)
    roi[:] = roi*(1-a)+rgba[:,:,:3]*a


def motion_crop(plate: Image.Image, u: float, pan_x: float, pan_y: float) -> np.ndarray:
    z = 1.0 + 0.070 * (0.35 * (0.5 - 0.5 * math.cos(math.pi*u)) + 0.65*u)
    cw,ch=W/z,H/z
    cx=W*0.5 + pan_x*W; cy=H*0.5 + pan_y*H
    x0=max(0.0,min(W-cw,cx-cw*0.5)); y0=max(0.0,min(H-ch,cy-ch*0.5))
    moved=plate.transform((W,H),Image.Transform.EXTENT,(x0,y0,x0+cw,y0+ch),Image.Resampling.BICUBIC)
    return np.asarray(moved,dtype=np.float32)/255.0


def render():
    STILLS.mkdir(parents=True, exist_ok=True)
    audio_info = build_audio()
    captions = make_caption_cues()
    caption_imgs = [caption_patch(c["text"]) for c in captions]
    plates = load_plates_and_luts()
    far = make_rain(701, 50, 4700, 0.55); near = make_rain(702, 90, 2200, 1.0)
    tile_w,tile_h=far.size
    reflection=make_reflection()
    mix_path=AUDIO/"master_audio_48k.wav"
    raw_cmd=["ffmpeg","-y","-hide_banner","-loglevel","error",
             "-f","rawvideo","-vcodec","rawvideo","-pixel_format","rgb24",
             "-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","pipe:0",
             "-i",str(mix_path),"-filter_complex",
             "[0:v]noise=alls=3:allf=t+u:all_seed=1101,scale=1920:1080:flags=lanczos,format=yuv420p[v]",
             "-map","[v]","-map","1:a:0","-t","60","-r",str(FPS),"-fps_mode","cfr",
             "-c:v","libx264","-preset","fast","-crf","19","-profile:v","high","-level","4.1",
             "-x264-params","threads=2:rc-lookahead=12","-c:a","aac","-b:a","192k","-ar","48000","-ac","2",
             "-movflags","+faststart",str(OUT)]
    proc=subprocess.Popen(raw_cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    active_caption=0
    still_frames={90:"still-junction4-entry.png",720:"still-eight-feeds.png",1225:"still-exit-empty.png",1701:"HERO-01-two-lights-in-the-window.png"}
    road_mask=(np.exp(-((np.arange(H,dtype=np.float32)[:,None]-H*0.68)/(H*0.25))**2)*0.12).astype(np.float32)
    rain_color=np.array([0.67,0.80,0.98],dtype=np.float32)
    try:
        for fidx in range(FRAMES):
            scene=next(s for s in SCENES if s[0]<=fidx<s[1])
            st,en,name,lut_name,rain_amt,pan_x,pan_y=scene
            u=(fidx-st)/max(1,en-st-1)
            plate=plates[(name,lut_name)]
            frame=motion_crop(plate,u,pan_x,pan_y)
            # Mildly moving, two-plane rain/spray; stronger outdoors, restrained across glass indoors.
            if rain_amt>0:
                ox1=(fidx*17)%(tile_w-W); oy1=(fidx*31)%(tile_h-H)
                ox2=(fidx*29+311)%(tile_w-W); oy2=(fidx*53+173)%(tile_h-H)
                rf=np.asarray(far.crop((ox1,oy1,ox1+W,oy1+H)),dtype=np.float32)/255.0
                rn=np.asarray(near.crop((ox2,oy2,ox2+W,oy2+H)),dtype=np.float32)/255.0
                rain=np.clip((rf*0.60+rn*0.40)*rain_amt,0,0.22)
                frame=frame*(1-rain[:,:,None])+rain_color*rain[:,:,None]
                if name=="junction4_road":
                    m=road_mask*rain_amt*0.72
                    frame=frame*(1-m[:,:,None])+np.array([0.60,0.73,0.87],dtype=np.float32)*m[:,:,None]
            # Final story reveal: the headlights are now reflected inside the room glass.
            if fidx>=1620:
                reveal=min(1.0,max(0.0,(fidx-1620)/(FPS*1.1)))
                blend_patch(frame,reflection,308,214,reveal)
            # Captions are exactly 3 source words per beat and use the captured WordBoundary start/end.
            t=fidx/FPS
            while active_caption<len(captions) and t>captions[active_caption]["end"]:
                active_caption+=1
            if active_caption<len(captions):
                cue=captions[active_caption]
                if cue["start"]<=t<=cue["end"]:
                    patch=caption_imgs[active_caption]
                    blend_patch(frame,patch,(W-patch.width)//2,H-98,1.0)
            out8=(np.clip(frame,0,1)*255.0+0.5).astype(np.uint8)
            if fidx in still_frames:
                Image.fromarray(out8).resize((1920,1080),Image.Resampling.LANCZOS).save(STILLS/still_frames[fidx])
            proc.stdin.write(out8.tobytes())
            if fidx % 180 == 179:
                print(f"Rendered {fidx+1}/{FRAMES} frames",flush=True)
        proc.stdin.close()
        err=proc.stderr.read().decode("utf-8","replace")
        rc=proc.wait()
        if rc:
            raise RuntimeError(f"FFmpeg render failed ({rc}): {err[-4000:]}")
    except Exception:
        try: proc.stdin.close()
        except Exception: pass
        proc.kill(); raise
    finally:
        del plates,far,near
        gc.collect()

    probe=run(["ffprobe","-v","quiet","-print_format","json","-show_format","-show_streams",str(OUT)],capture=True).stdout
    info=json.loads(probe)
    video=next(s for s in info["streams"] if s.get("codec_type")=="video")
    audio=next(s for s in info["streams"] if s.get("codec_type")=="audio")
    duration=float(info["format"]["duration"])
    if not (video.get("width")==1920 and video.get("height")==1080 and video.get("avg_frame_rate")=="30/1" and int(video.get("nb_frames",0))==1800 and abs(duration-60.0)<0.03 and audio.get("sample_rate")=="48000" and audio.get("channels")==2):
        raise RuntimeError(f"Final probe failed acceptance checks: {probe}")
    scan=run(["ffmpeg","-hide_banner","-i",str(OUT),"-vf","blackdetect=d=0.5:pix_th=0.10,freezedetect=n=-60dB:d=0.5","-an","-f","null","-"],capture=True)
    scanlog=scan.stderr
    qa_path=HERE/"QA.md"
    qa=qa_path.read_text(encoding="utf-8")
    qa=qa.split("## Post-render evidence",1)[0]
    qa += "## Post-render evidence\n\n"
    qa += f"- Reproducible offline render command: `python3 videos/team-b/cut-v10/render_v10.py` (requires Python dependencies in `requirements.txt`, `ffmpeg`, and `ffprobe`; no network call during render).\n"
    qa += f"- Rendered file: `video.mp4` ({info['format'].get('size','?')} bytes; SHA-256 `{__import__('hashlib').sha256(OUT.read_bytes()).hexdigest()}`).\n"
    qa += f"- Narration source: `audio/narration_source.mp3`; committed lossless stem `audio/narration_stem_48k.flac`; captured telemetry `timing/word_telemetry.json` ({len(json.loads((TIMING/'word_telemetry.json').read_text())['words'])} WordBoundary events); locked captions `timing/captions_locked.json` ({len(captions)} cues, 2–5 words per cue, boundary-derived).\n"
    qa += f"- Audio: 48 kHz stereo AAC final; deterministic procedural bed `audio/bed_stem_48k.flac`; lossless mix `audio/master_audio_48k.wav`; voice RMS {audio_info['narration_rms_dbfs']:.2f} dBFS, bed RMS {audio_info['bed_rms_dbfs']:.2f} dBFS, mix peak {audio_info['mix_peak_dbfs']:.2f} dBFS.\n"
    qa += "- Planned hero captured at `stills/HERO-01-two-lights-in-the-window.png` (00:56.700 / frame 1701).\n"
    qa += f"- Structural gate: {duration:.6f} s; {video.get('nb_frames')} CFR frames; {video.get('width')}×{video.get('height')}; {video.get('codec_name')} / {video.get('pix_fmt')}; AAC {audio.get('sample_rate')} Hz stereo. PASS.\n"
    black_events=re.findall(r"black_start:[^\n]+",scanlog)
    freeze_events=re.findall(r"freeze_start:[^\n]+",scanlog)
    qa += f"- Black/freeze scan (`blackdetect` / `freezedetect`, 0.5 s threshold): {len(black_events)} black events; {len(freeze_events)} freeze events.\n"
    qa += "- Human review disclosure: **no human listened**; audio verification is numeric/structural only.\n\n"
    qa += "### Pasted final `ffprobe` output\n\n```json\n"+json.dumps(info,indent=2)+"\n```\n\n"
    if scanlog.strip():
        qa += "### Structural scan log\n\n```text\n"+scanlog.strip()+"\n```\n"
    qa_path.write_text(qa,encoding="utf-8")
    print(f"FINAL {OUT} duration={duration:.6f}s frames={video.get('nb_frames')} resolution={video.get('width')}x{video.get('height')}",flush=True)

if __name__ == "__main__":
    render()
