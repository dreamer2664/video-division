#!/usr/bin/env python3
"""Optional online stem regeneration. The renderer itself uses the committed offline FLAC.

Requires edge-tts==7.3.1, numpy, ffmpeg and internet. Boundaries are captured from
Edge's WordBoundary stream. We remove only near-digital-silence in long sentence gaps;
speech is neither pitch-shifted nor time-stretched. A separate 2 s gap is inserted
before the reveal. The generated FLAC and timing JSON are the render inputs.
"""
import argparse, asyncio, json, math, subprocess, tempfile
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
PRE = "At two forty-one a.m., the call centre has one caller waiting. The queue never reaches zero. Each resolved call is replaced at once. The dashboard says average handling time: exactly forty seconds. Perfect. The phones say otherwise. Every line is still connected. You open the first caller's record. Status: finished. But the call is still live. You check the next record. Finished. Still live. The waveform keeps moving after the voice goes quiet. A timer appears beside your headset. The average was never measuring calls."
POST = 'It was measuring callers. The system is not ending conversations. It is finishing the people on the line. Your timer reaches forty. The queue stays at one. A new agent picks up your line. Do not give them your name.'
SR = 48000
LEAD = 0.15
MAX_GAP = 0.25
PRE_REVEAL_INSERT = 2.0

async def synth(name, text, folder):
    import edge_tts
    stream = edge_tts.Communicate(text, 'en-US-ChristopherNeural', rate='-12%',
                                  pitch='-4Hz', boundary='WordBoundary')
    words = []
    with (folder / f'{name}-final.mp3').open('wb') as output:
        async for chunk in stream.stream():
            if chunk['type'] == 'audio': output.write(chunk['data'])
            elif chunk['type'] == 'WordBoundary': words.append(chunk)
    (folder / f'{name}-final.json').write_text(json.dumps(words, indent=2))

async def generate(folder):
    await asyncio.gather(synth('pre', PRE, folder), synth('post', POST, folder))

def process_part(name, folder):
    words = json.loads((folder / f'{name}-final.json').read_text())
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(folder / f'{name}-final.mp3'),
                                   '-ac', '2', '-ar', str(SR), '-f', 's16le', '-'])
    audio = np.frombuffer(raw, dtype='<i2').reshape(-1, 2)
    cuts = []
    for a, b in zip(words, words[1:]):
        end = (a['offset'] + a['duration']) / 1e7
        start = b['offset'] / 1e7
        if start - end > 0.50:
            lo = round((end + MAX_GAP / 2) * SR)
            hi = round((start - MAX_GAP / 2) * SR)
            seg = audio[lo:hi].astype(np.float64) / 32768.0
            rms = float(np.sqrt(np.mean(seg * seg) + 1e-15))
            db = 20 * math.log10(rms)
            if db > -55: raise RuntimeError(f'Refusing to cut audible material: {name} {lo/SR:.3f}s {db:.1f} dBFS')
            cuts.append((lo, hi, db))
    pieces=[];cursor=0
    for lo,hi,_ in cuts:
        pieces.append(audio[cursor:lo]);cursor=hi
    pieces.append(audio[cursor:])
    trimmed=np.concatenate(pieces)
    def new_time(t):
        n=round(t*SR)
        return (n-sum(max(0,min(n,hi)-lo) for lo,hi,_ in cuts))/SR
    events=[]
    for word in words:
        start=word['offset']/1e7;end=(word['offset']+word['duration'])/1e7
        events.append({'word':word['text'],'start':new_time(start),'end':new_time(end),'part':name})
    return trimmed,events,cuts

def main():
    p=argparse.ArgumentParser();p.add_argument('--reuse-dir',type=Path,help='folder of previously synthesised pre/post-final.mp3 and .json');args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='reel-v09-voice-') as td:
        folder=args.reuse_dir or Path(td)
        if not args.reuse_dir: asyncio.run(generate(folder))
        pre, pw, pc=process_part('pre',folder);post, qw, qc=process_part('post',folder)
        lead=round(LEAD*SR); gap=round(PRE_REVEAL_INSERT*SR)
        post_start=(lead+len(pre)+gap)/SR
        for e in pw: e['start']+=LEAD;e['end']+=LEAD
        for e in qw: e['start']+=post_start;e['end']+=post_start
        samples=np.concatenate([np.zeros((lead,2),dtype='<i2'),pre,np.zeros((gap,2),dtype='<i2'),post])
        duration=len(samples)/SR
        if duration > 60.0: raise RuntimeError(f'Stem too long: {duration:.3f}s')
        out=HERE/'assets'/'narration.flac';out.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['ffmpeg','-v','error','-y','-f','s16le','-ar',str(SR),'-ac','2','-i','-',
                        '-c:a','flac',str(out)],input=samples.tobytes(),check=True)
        metadata={'engine':'edge-tts 7.3.1','voice':'en-US-ChristopherNeural',
                  'rate':'-12%','pitch':'-4Hz','duration_seconds':duration,
                  'lead_seconds':LEAD,'inserted_pre_reveal_silence_seconds':PRE_REVEAL_INSERT,
                  'sentence_gap_cap_seconds':MAX_GAP,'words':pw+qw,
                  'cut_count':len(pc)+len(qc),'quietest_cut_dbfs':min(x[2] for x in pc+qc),
                  'loudest_cut_dbfs':max(x[2] for x in pc+qc)}
        (HERE/'assets'/'word_timings.json').write_text(json.dumps(metadata,indent=2)+'\n')
        print(f'narration {duration:.3f}s; {len(pw)+len(qw)} Edge words; removed {len(pc)+len(qc)} silent intervals, loudest {metadata["loudest_cut_dbfs"]:.1f} dBFS')
        print(f'pre-reveal last word ends {pw[-1]["end"]:.3f}s; next begins {qw[0]["start"]:.3f}s; gap {qw[0]["start"]-pw[-1]["end"]:.3f}s')
        for i,e in enumerate(pw+qw): print(f'{i:03d} {e["start"]:6.3f}–{e["end"]:6.3f} {e["word"]}')
if __name__=='__main__': main()
