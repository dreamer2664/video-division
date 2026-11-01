#!/usr/bin/env python3
"""Recreate this dated all-English-male Edge catalog benchmark.
Network service, output and catalog may change; the committed audio is evidence.
"""
import asyncio,hashlib,json
from pathlib import Path
import edge_tts
R=Path(__file__).resolve().parent
TEXT=(R/'ab-reel/benchmark.txt').read_text().strip()
VOICES=[l.split()[0] for l in (R/'voice-matrix/edge_catalog.txt').read_text().splitlines() if l.strip()]
if 'en-AU-WilliamNeural' not in VOICES:VOICES.append('en-AU-WilliamNeural') # specifically requested, even if unlisted
SETTINGS=[('neutral','+0%','+0Hz'),('house','-12%','-5Hz')]
SEM=asyncio.Semaphore(4)

async def one(voice,setting,rate,pitch):
    base=R/'voice-matrix/edge'/f'{voice}--{setting}'
    if base.with_suffix('.mp3').exists() and base.with_suffix('.json').exists():return
    async with SEM:
        err=None
        for retry in range(3):
            try:
                chunks=[];events=[]
                async for e in edge_tts.Communicate(TEXT,voice,rate=rate,pitch=pitch,boundary='WordBoundary').stream():
                    if e['type']=='audio':chunks.append(e['data'])
                    elif e['type']=='WordBoundary':events.append({'text':e['text'],'offset_ticks':e['offset'],'duration_ticks':e['duration']})
                data=b''.join(chunks)
                if not data:raise ValueError('empty audio')
                base.with_suffix('.mp3').write_bytes(data)
                base.with_suffix('.json').write_text(json.dumps({'engine':'edge-tts','voice':voice,'condition':setting,'rate':rate,'pitch':pitch,'characters':len(TEXT),'sha256':hashlib.sha256(data).hexdigest(),'events':events},indent=2)+'\n')
                print('OK',voice,setting,len(data),len(events),flush=True);return
            except Exception as e:
                err=type(e).__name__
                await asyncio.sleep(1+retry*2)
        base.with_suffix('.failure.json').write_text(json.dumps({'voice':voice,'condition':setting,'failure':err})+'\n')
        print('UNAVAILABLE',voice,setting,err,flush=True)

async def main():
    jobs=[one(v,s,r,p) for v in VOICES for s,r,p in SETTINGS]
    # The v10 film used -12%/-4Hz rather than the general -12%/-5Hz habit.
    jobs.append(one('en-US-ChristopherNeural','v10','-12%','-4Hz'))
    await asyncio.gather(*jobs)
    print('EDGE BENCHMARK REQUESTS COMPLETE',flush=True)
if __name__=='__main__':asyncio.run(main())
