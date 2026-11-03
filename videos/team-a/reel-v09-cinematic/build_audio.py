#!/usr/bin/env python3
"""Reproduce the committed hotel master audio OFFLINE from durable FLAC stems."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
ROOT=Path(__file__).resolve().parent;SR=48000;N=60*SR

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def decode(p):
    b=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-ac','2','-ar',str(SR),'-f','s16le','-'])
    x=np.frombuffer(b,dtype='<i2').reshape(-1,2).astype(np.float32)/32767.0
    return np.pad(x,((0,max(0,N-len(x))),(0,0)))[:N]
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=True)
    mapping=json.loads((ROOT/'audio/gain_mapping.json').read_text())
    for name,expected in mapping['stems_sha256'].items():
        actual=sha(ROOT/'audio'/name)
        if actual!=expected:raise ValueError(f'Stem hash mismatch: {name}')
    v=decode(ROOT/'audio/narration_stem_48k.flac');b=decode(ROOT/'audio/bed_ducked_48k.flac')
    pre=out/'mix-pre.wav';wavfile.write(pre,SR,np.rint(np.clip((v+b)*mapping['pre_scale'],-1,1)*32767).astype(np.int16))
    master=out/'master_audio_48k.wav'
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(pre),'-af',mapping['loudnorm_filter'],'-ar','48000','-ac','2','-c:a','pcm_s16le',str(master)],check=True)
    actual=sha(master)
    if actual!=mapping['master_wav_sha256']:raise ValueError(f'Offline master hash differs: {actual}')
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(master),'-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-movflags','+faststart',str(out/'mix.m4a')],check=True)
    print('Verified offline master',actual,flush=True)
if __name__=='__main__':main()
