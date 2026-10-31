#!/usr/bin/env python3
"""Generate timed narration and synchronized caption cues with one Edge TTS voice."""
import asyncio, csv, pathlib, subprocess, os, wave
import numpy as np
import edge_tts
ROOT=pathlib.Path(__file__).resolve().parents[1]
TMP=ROOT/'assets'/'voice-tmp'; TMP.mkdir(parents=True,exist_ok=True)
OUT=ROOT/'assets'/'narration.wav'; CUES=ROOT/'project'/'voice_cues.csv'; CAP=ROOT/'project'/'caption_cues.csv'
RATE=24000; TOTAL=60; VOICE='en-US-ChristopherNeural'; RATE_CHANGE='-8%'; PITCH='-4Hz'
# cue index: spoken line, burn-in caption. Captions change on the spoken beat, not every cut.
LINES={
 0:('Two thirteen, eight seconds.','02:13:08.000'),
 1:('Four cameras, one control room.','FOUR CAMERAS. ONE ROOM.'),
 2:('The wall clock is live.','WALL CLOCK: LIVE'),
 3:('Every feed runs four seconds ahead.','FEEDS: PLUS FOUR'),
 4:('Check it yourself.','CHECK IT YOURSELF'),
 5:('Corridor door is shut here.','CORRIDOR. DOOR SHUT.'),
 6:('Camera one shows it opening.','CAM ONE: IT OPENS'),
 7:('The guard waits.','THE GUARD WAITS'),
 8:('Now the door opens here.','NOW IT OPENS HERE'),
 9:('Exactly four seconds later.','FOUR SECONDS LATER'),
 10:('He writes it in the log.','OFFSET: PLUS FOUR'),
 11:('Plus four, no drift.','NO DRIFT'),
 12:('No dropped frames.','NO DROPPED FRAMES'),
 13:('Camera four shows this room.','CAM FOUR: THIS ROOM'),
 14:('Same sleeve, same hand.','SAME SLEEVE. SAME HAND.'),
 15:('Watch the timecode.','LOOK AT THE TIME'),
 16:("He hasn't moved.",'IT HASN’T MOVED'),
 17:("Don't look away.",'DON’T LOOK AWAY'),
 18:('Four seconds.','FOUR SECONDS. EXACT.'),
 19:('Fifty-three point six: still closed.',"HIS HAND ISN'T OPEN YET"),
 20:('Now. Open.','NOW. EXACTLY.'),
 22:('Feed five.','FEED FIVE: ONLINE'),
 23:('Four cameras.','THERE ARE FOUR CAMERAS'),
 24:('Someone behind.','WHO IS BEHIND HIM?'),
}
# The hero and the impossible action are frame-locked; speech lands on those exact events.
FORCED={17:40.8,18:43.2,19:45.6,20:49.6,22:53.6,23:55.32,24:57.72}
async def save_clip(i,text):
    p=TMP/f'{i:02d}.mp3'
    await edge_tts.Communicate(text,VOICE,rate=RATE_CHANGE,pitch=PITCH).save(str(p))
    return p

def decode(p):
    ff=os.environ.get('FFMPEG','ffmpeg')
    b=subprocess.check_output([ff,'-v','error','-i',str(p),'-af','areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,areverse','-f','s16le','-ac','1','-ar',str(RATE),'pipe:1'])
    return np.frombuffer(b,dtype='<i2').copy()

async def main():
    await asyncio.gather(*(save_clip(i,text) for i,(text,_) in LINES.items()))
    clips={i:decode(TMP/f'{i:02d}.mp3') for i in LINES}
    starts={}; cursor=.10
    gap=(FORCED[17]-.10-sum(len(clips[i])/RATE for i in range(17)))/17
    if gap<0: raise RuntimeError('opening narration does not fit before the locked 40.8s cue')
    for i in range(17):
        starts[i]=cursor; cursor += len(clips[i])/RATE+gap
    for i,t in FORCED.items(): starts[i]=t
    # Captions not spoken aloud remain on screen through their visual event.
    caption_events=[(0.0,'02:13:08.000')]
    for i,(_,caption) in LINES.items(): caption_events.append((starts[i],caption))
    caption_events += [(52.0,'THE CLOCK TURNS'),(59.4,'CAM FIVE HAS NO KEY')]
    caption_events.sort(key=lambda p:p[0])
    full=np.zeros(TOTAL*RATE,dtype=np.int16); cue_rows=[]
    # Enforce no overlapping narration clips; forced cues must fit their event window.
    sorted_ids=sorted(starts)
    for j,i in enumerate(sorted_ids):
        start=round(starts[i]*RATE); clip=clips[i]
        next_t=starts[sorted_ids[j+1]] if j+1<len(sorted_ids) else 60.0
        max_end=round(next_t*RATE)
        if start+len(clip)>max_end:
            available=(max_end-start)/RATE
            tempo=(len(clip)/RATE)/available
            if tempo>1.35: raise RuntimeError(f'voice cue {i+1} needs excessive speedup ({tempo:.2f}x)')
            ff=os.environ.get('FFMPEG','ffmpeg')
            raw=subprocess.check_output([ff,'-v','error','-f','s16le','-ar',str(RATE),'-ac','1','-i','pipe:0','-af',f'atempo={tempo:.4f}','-f','s16le','pipe:1'],input=clip.astype('<i2').tobytes())
            clip=np.frombuffer(raw,dtype='<i2').copy()
        end=start+len(clip)
        if end>len(full): raise RuntimeError(f'voice cue {i+1} exceeds the 60s master')
        full[start:end]=clip
        cue_rows.append((i+1,round(start/RATE,3),round(end/RATE,3),round(len(clip)/RATE,3),LINES[i][0],LINES[i][1],VOICE,RATE_CHANGE,PITCH,'atempo' if len(clip)!=len(clips[i]) else 'none'))
    with wave.open(str(OUT),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(full.astype('<i2').tobytes())
    with open(CUES,'w',newline='') as f:
        wr=csv.writer(f); wr.writerow(['shot','voice_start_s','voice_end_s','active_s','text','caption','voice','rate','pitch','tempo_adjustment']); wr.writerows(cue_rows)
    with open(CAP,'w',newline='') as f:
        wr=csv.writer(f); wr.writerow(['caption_start_s','caption']); wr.writerows(caption_events)
    words=sum(len(text.split()) for text,_ in LINES.values()); active=sum(r[3] for r in cue_rows)
    print(f'Wrote {OUT}: {TOTAL}s, {len(cue_rows)} speech cues, {active:.2f}s active speech, {words*60/active:.1f} words/min (counted from cue text); captions in {CAP}. No human listening.')
if __name__=='__main__': asyncio.run(main())
