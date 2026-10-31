#!/usr/bin/env python3
"""Generate Edge TTS narration and a frame-aligned mono PCM stem. Build work stays in /tmp."""
import argparse, asyncio, csv, math, os, pathlib, subprocess, wave
import numpy as np
import edge_tts

VOICE = 'en-US-ChristopherNeural'
RATE = '-12%'
PITCH = '-4Hz'
SLOT = 2.4
SR = 24000
LINES = pathlib.Path(__file__).with_name('voice_lines.txt').read_text().splitlines()

async def generate_all(work):
    work.mkdir(parents=True, exist_ok=True)
    sem=asyncio.Semaphore(4)
    async def one(i, text):
        async with sem:
            out=work/f'{i+1:02}.mp3'
            await edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH).save(str(out))
            return out
    return await asyncio.gather(*(one(i,s) for i,s in enumerate(LINES)))

def decode(path, ffmpeg, tempo):
    cmd=[ffmpeg,'-hide_banner','-loglevel','error','-i',str(path),'-af',f'atempo={tempo}',
         '-ac','1','-ar',str(SR),'-f','s16le','pipe:1']
    p=subprocess.run(cmd,check=True,stdout=subprocess.PIPE)
    return np.frombuffer(p.stdout,dtype='<i2').copy()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--work',default='/tmp/cut-v08-build/voice-clips')
    ap.add_argument('--out',default='../assets/narration.wav')
    ap.add_argument('--csv',default='voice_cues.csv')
    ap.add_argument('--ffmpeg',default='ffmpeg')
    args=ap.parse_args()
    work=pathlib.Path(args.work); out=pathlib.Path(args.out); cues=pathlib.Path(args.csv)
    asyncio.run(generate_all(work))
    # Locally time-compress by a modest amount to keep the chosen slow TTS within 2.4-second shots.
    # The fixed TTS delivery settings remain -12% / -4 Hz; every adjusted duration is recorded below.
    x=np.zeros(round(60*SR),dtype=np.int16)
    rows=[]; clips=[]; tempos=[]
    for i,text in enumerate(LINES):
        mp3=work/f'{i+1:02}.mp3'
        native=decode(mp3,args.ffmpeg,1.0)
        target=len(text.split())*60/138.0
        tempo=max(1.0,(len(native)/SR)/target)
        if tempo > 2.2: raise RuntimeError(f'voice beat {i+1} needs tempo {tempo:.2f}; shorten line')
        clip=decode(mp3,args.ffmpeg,tempo)
        duration=len(clip)/SR
        if duration > SLOT-0.12:
            raise RuntimeError(f'voice beat {i+1} lasts {duration:.3f}s; exceeds 2.28s slot; shorten line')
        clips.append(clip); tempos.append(tempo)
    for i,(text,raw,tempo) in enumerate(zip(LINES,clips,tempos)):
        start=i*SLOT + 0.12
        # Preserve at least 1.25 s of bed-only space before the turning line at cue 20.
        if i == 19:
            start=max(start, (i-1)*SLOT + 0.12 + len(clips[18])/SR + 1.25)
        a=round(start*SR); b=min(len(x),a+len(raw))
        seg=raw[:b-a].astype(np.float32)
        fade=min(round(.012*SR),len(seg)//3)
        if fade:
            ramp=np.linspace(0,1,fade,dtype=np.float32); seg[:fade]*=ramp; seg[-fade:]*=ramp[::-1]
        x[a:b]=np.clip(seg,-32768,32767).astype(np.int16)
        rows.append((i+1,start,start+len(raw)/SR,len(raw)/SR,tempo,len(text.split()),text))
    out.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(out),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.astype('<i2').tobytes())
    with open(cues,'w',newline='') as f:
        wr=csv.writer(f); wr.writerow(['shot','voice_start_s','voice_end_s','duration_s','post_tempo','words','text']); wr.writerows(rows)
    total=sum(r[5] for r in rows); active=sum(r[3] for r in rows)
    print(f'voice={VOICE} rate={RATE} pitch={PITCH}; {len(LINES)} beats, {total} words, {active:.2f}s speech, effective {total*60/active:.1f} wpm')
    print(f'narration stem: {out}; duration 60.000s, {SR} Hz mono PCM')
    for r in rows: print(f'{r[0]:02d} {r[1]:05.2f}-{r[2]:05.2f} ({r[5]}w, tempo {r[4]:.2f}) {r[6]}')

if __name__=='__main__': main()
