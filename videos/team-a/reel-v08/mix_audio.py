#!/usr/bin/env python3
"""Measure isolated stems, set music 10 LU below speech, and two-pass-normalize mix."""
import argparse,json,re,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent

def run(args):
    subprocess.run(args,check=True)

def loud(path):
    p=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(path),'-af',
                      'loudnorm=I=-16:TP=-2:LRA=11:print_format=json','-f','null','-'],
                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=True)
    objects=re.findall(r'\{\s*"input_i".*?\}',p.stderr,re.S)
    if not objects:raise RuntimeError('No loudnorm JSON from '+str(path)+'\n'+p.stderr)
    return json.loads(objects[-1])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out
    voice=HERE/'assets'/'narration.flac';music=out/'music.wav';sfx=out/'sfx.wav'
    v=loud(voice);m=loud(music);s=loud(sfx)
    music_gain=round(float(v['input_i'])-10-float(m['input_i']),2)
    sfx_gain=round(float(v['input_i'])-15-float(s['input_i']),2)
    print('stem LUFS:',v['input_i'],m['input_i'],s['input_i'],'gain dB:',music_gain,sfx_gain,flush=True)
    filt=(f'[0:a]apad,atrim=0:60[v];[1:a]volume={music_gain}dB[m];'
          f'[2:a]volume={sfx_gain}dB[s];[v][m][s]amix=inputs=3:normalize=0:duration=longest:'
          f'dropout_transition=0,atrim=0:60,aresample=48000[out]')
    mix=out/'mix.wav'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(voice),'-i',str(music),'-i',str(sfx),
         '-filter_complex',filt,'-map','[out]','-c:a','pcm_s24le',str(mix)])
    measured=loud(mix)
    arg=('loudnorm=I=-16:TP=-2:LRA=11:linear=true:print_format=json:'+
         ':'.join(f'{k}={measured[v]}' for k,v in [('measured_I','input_i'),('measured_TP','input_tp'),
                                                   ('measured_LRA','input_lra'),('measured_thresh','input_thresh'),
                                                   ('offset','target_offset')]))
    cmd=['ffmpeg','-hide_banner','-nostats','-y','-i',str(mix),'-af',arg,'-ar','48000','-ac','2',
         '-c:a','aac','-b:a','192k','-movflags','+faststart',str(out/'mix.m4a')]
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=True)
    objs=re.findall(r'\{\s*"input_i".*?\}',p.stderr,re.S);normalized=json.loads(objs[-1]) if objs else {}
    measured_aac=loud(out/'mix.m4a')
    evidence={'voice_stem':v,'music_raw':m,'foley_raw':s,'music_gain_db':music_gain,'foley_gain_db':sfx_gain,
              'voice_minus_music_lu_before_global_normalization':round(float(v['input_i'])-(float(m['input_i'])+music_gain),2),
              'mix_first_pass':measured,'mix_second_pass':normalized,'final_aac_analysis':measured_aac}
    (out/'audio-metrics.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('normalized AAC input loudness',measured_aac['input_i'],'LUFS, true peak',measured_aac['input_tp'],'dBTP',flush=True)
if __name__=='__main__':main()
