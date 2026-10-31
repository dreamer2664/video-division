#!/usr/bin/env python3
"""Generate the designed narration in timed 2.4-second cues via Edge TTS."""
import asyncio, csv, pathlib, subprocess, os, wave
import numpy as np
import edge_tts

ROOT=pathlib.Path(__file__).resolve().parents[1]
TMP=ROOT/'assets'/'voice-tmp'; TMP.mkdir(parents=True,exist_ok=True)
OUT=ROOT/'assets'/'narration.wav'; CUES=ROOT/'project'/'voice_cues.csv'
FPS=30; SLOT=2.4; RATE=24000; TOTAL=60
VOICE='en-US-ChristopherNeural'; RATE_CHANGE='-12%'; PITCH='-4Hz'
# shot index : narration, small in-shot offset. One voice throughout; silent beats are intentional.
LINES={
 0:('Two thirteen, eight seconds.',0.10),
 1:('Four cameras. One control room.',0.12),
 2:('The wall clock is live.',0.12),
 3:('Every feed runs four seconds ahead.',0.12),
 4:('Check it yourself.',0.12),
 5:('Corridor door is shut here.',0.12),
 6:('Camera one shows it opening.',0.12),
 7:('The guard waits.',0.12),
 8:('Now the door opens here.',0.12),
 9:('Exactly four seconds later.',0.12),
 10:('He writes it in the log.',0.12),
 11:('Plus four. No drift.',0.12),
 12:('No dropped frames.',0.12),
 13:('Camera four shows this room.',0.12),
 14:('Same sleeve. Same hand.',0.12),
 15:('Watch the timecode.',0.12),
 16:("He hasn't moved.",0.12),
 17:("Don't look away.",0.12),
 18:('Four seconds. Exact.',0.12),
 19:('Fifty-three point six. Closed here.',0.12),
 20:('Four seconds later. Open.',0.90),
 21:('The clock turns.',0.12),
 22:('Two fourteen. Feed five.',0.80),
 23:('The building has four cameras.',0.12),
 24:('Someone is sitting behind him.',0.12),
}
async def save_clip(idx,text):
    path=TMP/f'{idx:02d}.mp3'
    talk=edge_tts.Communicate(text,VOICE,rate=RATE_CHANGE,pitch=PITCH)
    await talk.save(str(path))
    return path

def decode(path):
    ffmpeg=os.environ.get('FFMPEG','ffmpeg')
    data=subprocess.check_output([ffmpeg,'-v','error','-i',str(path),'-f','s16le','-ac','1','-ar',str(RATE),'pipe:1'])
    return np.frombuffer(data,dtype='<i2').copy()

async def main():
    await asyncio.gather(*(save_clip(i,t) for i,(t,_) in LINES.items()))
    full=np.zeros(TOTAL*RATE,dtype=np.int16)
    rows=[]
    for i,(text,offset) in LINES.items():
        clip=decode(TMP/f'{i:02d}.mp3')
        start=round((i*SLOT+offset)*RATE)
        end=start+len(clip)
        slot_end=round(((i+1)*SLOT)*RATE)
        # Preserve clean cue changes: if any TTS phrase overruns its shot, time-compress
        # only that cue by at most 18%; this is recorded in the generated cue table.
        compressed=False
        if end>slot_end:
            duration=len(clip)/RATE; avail=(slot_end-start)/RATE
            tempo=min(1.18,duration/avail)
            if duration/tempo>avail+0.03: raise RuntimeError(f'voice cue {i+1} too long ({duration:.2f}s in {avail:.2f}s)')
            ffmpeg=os.environ.get('FFMPEG','ffmpeg')
            raw=subprocess.check_output([ffmpeg,'-v','error','-f','s16le','-ar',str(RATE),'-ac','1','-i','pipe:0','-af',f'atempo={tempo:.4f}','-f','s16le','pipe:1'],input=clip.astype('<i2').tobytes())
            clip=np.frombuffer(raw,dtype='<i2').copy(); end=start+len(clip); compressed=True
        full[start:min(end,len(full))]=clip[:max(0,min(end,len(full))-start)]
        rows.append((i+1,round(start/RATE,3),round(end/RATE,3),round(len(clip)/RATE,3),text,VOICE,RATE_CHANGE,PITCH,'atempo' if compressed else 'none'))
    with wave.open(str(OUT),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(full.astype('<i2').tobytes())
    with open(CUES,'w',newline='') as f:
        wr=csv.writer(f); wr.writerow(['shot','voice_start_s','voice_end_s','active_s','text','voice','rate','pitch','tempo_adjustment']); wr.writerows(rows)
    print(f'Wrote {OUT} ({len(full)/RATE:.3f}s, {sum(r[3] for r in rows):.2f}s active voice), {len(rows)} cues; no human audition/listening.')

if __name__=='__main__': asyncio.run(main())
