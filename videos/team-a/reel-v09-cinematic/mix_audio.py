#!/usr/bin/env python3
"""Mix committed narration with deterministic hotel bed/Foley, measure and normalize."""
import argparse,json,math,re,subprocess,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
SR=48000;N=60*SR

def decode(path):
    b=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ac','2','-ar',str(SR),'-f','f32le','-'])
    a=np.frombuffer(b,dtype='<f4').reshape(-1,2)
    return np.pad(a,((0,max(0,N-len(a))),(0,0)))[:N]

def wav(path,data):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
        w.writeframes(np.rint(np.clip(data,-.9999,.9999)*32767).astype('<i2').tobytes())

def loud(path):
    p=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(path),'-af',
        'loudnorm=I=-16:TP=-2:LRA=11:print_format=json','-f','null','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=True)
    objects=re.findall(r'\{\s*"input_i".*?\}',p.stderr,re.S)
    if not objects:raise RuntimeError('no loudnorm JSON')
    return json.loads(objects[-1])

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();out=args.out
    voice=decode(ROOT/'assets/narration.flac');music=decode(out/'music.wav');foley=decode(out/'foley.wav')
    words=json.loads((ROOT/'assets/word_timings.json').read_text())['words'];mask=np.zeros(N,dtype=bool)
    for w in words:mask[max(0,round(w['start']*SR)):min(N,round(w['end']*SR))]=True
    background=music+foley
    vr=float(np.sqrt(np.mean(voice[mask].astype(np.float64)**2)))
    br=float(np.sqrt(np.mean(background[mask].astype(np.float64)**2)))
    factor=vr/(br*10**(10/20));background*=factor
    br2=float(np.sqrt(np.mean(background[mask].astype(np.float64)**2)))
    ratio=20*math.log10(vr/br2)
    mixed=voice+background;peak=float(np.max(np.abs(mixed)))
    if peak>.985:
        pre_gain=.985/peak;mixed*=pre_gain
    else:pre_gain=1.0
    wav(out/'mix-pre.wav',mixed)
    m=loud(out/'mix-pre.wav')
    filt=('loudnorm=I=-16:TP=-2:LRA=11:linear=true:print_format=json:'+
          ':'.join(f'{k}={m[v]}' for k,v in [('measured_I','input_i'),('measured_TP','input_tp'),
                                              ('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')]))
    cmd=['ffmpeg','-hide_banner','-nostats','-y','-i',str(out/'mix-pre.wav'),'-af',filt,'-ar','48000','-ac','2',
         '-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'mix.m4a')]
    proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=True)
    objs=re.findall(r'\{\s*"input_i".*?\}',proc.stderr,re.S);norm=json.loads(objs[-1]) if objs else {}
    final=loud(out/'mix.m4a')
    evidence={'method':'RMS of actual narration and combined synthesized music+Foley across service word spans before common global normalization; not a subjective intelligibility test.',
              'active_speech_duration_s':int(mask.sum())/SR,'voice_rms':vr,'background_rms_before_gain':br,
              'background_linear_gain':factor,'voice_over_combined_background_db_before_global_normalization':ratio,
              'sample_peak_before_common_gain':peak,'common_pre_gain':pre_gain,'first_pass':m,'normalization_pass':norm,'aac_final':final}
    (out/'audio-metrics.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('Voice over combined bed and Foley during word spans:',round(ratio,3),'dB; AAC',final['input_i'],'LUFS,',final['input_tp'],'dBTP',flush=True)
if __name__=='__main__':main()
