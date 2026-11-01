#!/usr/bin/env python3
"""Make five identically scripted, approximately RMS-matched audition excerpts.
All are cut from the longer committed benchmark, so no extra API characters are spent.
"""
import json,math,subprocess,tempfile
from pathlib import Path
import numpy as np
from scipy.io import wavfile
R=Path(__file__).resolve().parent;A=R/'ab-reel';SR=48000
SPECS=[
 ('A','current house Christopher −12%/−4 Hz',R/'voice-matrix/edge/en-US-ChristopherNeural--v10.mp3','edge'),
 ('B','Edge Andrew Multilingual neutral',R/'voice-matrix/edge/en-US-AndrewMultilingualNeural--neutral.mp3','edge'),
 ('C','Edge Brian Multilingual neutral',R/'voice-matrix/edge/en-US-BrianMultilingualNeural--neutral.mp3','edge'),
 ('D','Piper Joe length scale 1.12',R/'voice-matrix/piper/joe--slow.flac','piper'),
 ('E','ElevenLabs Roger multilingual v2',R/'voice-matrix/eleven/roger_multilingual_v2.mp3','eleven'),
]
def decode(p):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-ac','1','-ar',str(SR),'-f','f32le','-']),'<f4').copy()
def limits(path,typ):
    if typ=='edge':
        m=json.loads(path.with_suffix('.json').read_text());e=m['events'];assert [x['text'].lower() for x in e[:5]]==['the','ledger','has','four','names']
        return max(0,e[0]['offset_ticks']/1e7-.04),(e[4]['offset_ticks']+e[4]['duration_ticks'])/1e7+.10
    if typ=='eleven':
        m=json.loads(path.with_suffix('.json').read_text());a=m['alignment'];s=''.join(a['characters']);i=s.index('.')
        return 0,a['character_end_times_seconds'][i]+.08
    # Full Piper sentence ends at the measured energy valley 1.70–1.80s before sentence two.
    return 0,1.78

def main():
    A.mkdir(exist_ok=True);parts=[];rows=[];offset=0
    with tempfile.TemporaryDirectory(prefix='reel-ab-') as tmp:
        for letter,name,path,typ in SPECS:
            start,end=limits(path,typ);x=decode(path)[round(start*SR):round(end*SR)].astype(np.float64)
            rms=np.sqrt(np.mean(x*x));peak=np.max(np.abs(x));target=10**(-21/20);scale=min(.89/max(peak,1e-9),target/max(rms,1e-9));x=np.clip(x*scale,-1,1)
            pcm=np.round(x*32767).astype(np.int16);wav=Path(tmp)/f'{letter}.wav';wavfile.write(wav,SR,pcm)
            dest=A/f'voice-{letter}.mp3';subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-c:a','libmp3lame','-b:a','160k',str(dest)],check=True)
            duration=len(x)/SR;rows.append({'sample':letter,'description':name,'source':str(path.relative_to(R)),'source_in':round(start,3),'source_out':round(end,3),'duration':round(duration,3),'reel_start':round(offset,3),'reel_end':round(offset+duration,3),'target_rms_dbfs':-21,'achieved_rms_dbfs':round(20*math.log10(np.sqrt(np.mean(x*x))),2),'peak_dbfs':round(20*math.log10(np.max(np.abs(x))),2)})
            parts.append(pcm);offset+=duration
            if letter!='E':parts.append(np.zeros(int(.10*SR),np.int16));offset+=.10
        mix=np.concatenate(parts);assert len(mix)/SR<=10, f'Exceeds ten seconds: {len(mix)/SR}'
        wav=Path(tmp)/'five.wav';wavfile.write(wav,SR,mix)
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-c:a','libmp3lame','-b:a','192k',str(A/'five-voices-under-10s.mp3')],check=True)
    (A/'voice-samples.json').write_text(json.dumps({'sentence':'The ledger has four names.','gap_s':.1,'concatenated_pcm_duration_s':round(offset,3),'note':'Same text and matched RMS; different engines retain their original sentence context. Piper boundary estimated from energy valley. No human listening test has been performed.','samples':rows},indent=2)+'\n')
    print(json.dumps(rows,indent=2));print('CONCAT PCM SECONDS',round(offset,3))
if __name__=='__main__':main()
