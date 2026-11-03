#!/usr/bin/env python3
"""Independent numeric audit of the committed hotel master, without playback."""
import argparse,hashlib,json,math,re,subprocess
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from PIL import Image,ImageDraw,ImageFont
import captions
ROOT=Path(__file__).resolve().parent;QA=ROOT/'qa';FPS=30;SR=48000

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_exact(pipe,n):
    parts=[];left=n
    while left:
        b=pipe.read(left)
        if not b:break
        parts.append(b);left-=len(b)
    return b''.join(parts)
def caption_pixels(video):
    meta=json.loads((ROOT/'timing/captions_locked.json').read_text());font=ImageFont.truetype(str(ROOT/'assets/Anton-Regular.ttf'),54)
    events=[];global_idx=0
    for cue in meta['cues']:
        ws=cue['words'];labels=[w['text']+captions.PUNCT.get(global_idx+j,'') for j,w in enumerate(ws)]
        widths=[font.getlength(s) for s in labels];sp=font.getlength(' ')
        boxw=round(sum(widths)+sp*(len(labels)-1)+66);boxx=(1920-boxw)//2;localx=29
        for j,(w,lab,wd) in enumerate(zip(ws,labels,widths)):
            f=w['first_eligible_frame']
            if j>0 and (f-1)/FPS>=cue['start_s']:
                im=Image.new('L',(boxw,78),0);draw=ImageDraw.Draw(im);draw.text((round(localx),8),lab,font=font,fill=255)
                mask=np.asarray(im)>220
                ys,xs=np.where(mask)
                if len(xs):events.append({'word':w['text'],'frame':f,'xs':xs+boxx,'ys':ys,'before':None,'after':None})
            localx+=wd+sp
        global_idx+=len(ws)
    tasks=defaultdict(list)
    for e in events:tasks[e['frame']-1].append((e,'before'));tasks[e['frame']].append((e,'after'))
    maxf=max(tasks);size=1920*78*3
    p=subprocess.Popen(['ffmpeg','-v','error','-i',str(video),'-vf','crop=1920:78:0:884,format=rgb24','-an','-frames:v',str(maxf+1),'-f','rawvideo','-'],stdout=subprocess.PIPE)
    for f in range(maxf+1):
        data=read_exact(p.stdout,size)
        if len(data)!=size:raise RuntimeError('Premature video decode at frame '+str(f))
        if f in tasks:
            rgb=np.frombuffer(data,dtype=np.uint8).reshape(78,1920,3)
            for event,key in tasks[f]:event[key]=float(rgb[event['ys'],event['xs'],2].mean())
    p.stdout.close()
    if p.wait()!=0:raise RuntimeError('Caption pixel decode failed')
    out=[]
    for e in events:
        drop=e['before']-e['after'];out.append({k:e[k] for k in ['word','frame','before','after']}|{'blue_drop':round(drop,3),'passes':drop>50})
    return {'description':'Decoded actual master: interior glyph pixels of non-initial cue words change from white to amber/crimson on the first telemetry-eligible frame; prior frame is sampled. Not a perceptual intelligibility test.',
            'eligible':len(out),'pass':sum(x['passes'] for x in out),'failures':[x for x in out if not x['passes']],
            'median_blue_drop':float(np.median([x['blue_drop'] for x in out])),'checks':out}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--master-audio',required=True,type=Path);a=ap.parse_args();QA.mkdir(exist_ok=True)
    v=ROOT/'video.mp4'
    probe=subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(v)],text=True)
    (QA/'ffprobe.json').write_text(probe);pj=json.loads(probe)
    run=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(v),'-map','0:a:0','-af','loudnorm=I=-16:TP=-2.2:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    (QA/'loudnorm-full.txt').write_text(run.stderr)
    loud=json.loads(re.findall(r'\{\s*"input_i".*?\}',run.stderr,re.S)[-1]);(QA/'loudnorm.json').write_text(json.dumps(loud,indent=2)+'\n')
    sr,master=wavfile.read(a.master_audio);assert sr==SR and master.ndim==2
    b=subprocess.check_output(['ffmpeg','-v','error','-i',str(v),'-map','0:a:0','-ac','2','-ar','48000','-f','s16le','-'])
    dec=np.frombuffer(b,dtype='<i2').reshape(-1,2);n=min(len(master),len(dec));corr=[float(np.corrcoef(master[:n,c],dec[:n,c])[0,1]) for c in range(2)]
    pix=caption_pixels(v);(QA/'caption-pixels.json').write_text(json.dumps(pix,indent=2)+'\n')
    words=[w for c in json.loads((ROOT/'timing/captions_locked.json').read_text())['cues'] for w in c['words']]
    errs=[w['first_eligible_frame']/FPS-w['start_s'] for w in words]
    gain=json.loads((ROOT/'audio/gain_mapping.json').read_text())
    result={'video_sha256':sha(v),'video_bytes':v.stat().st_size,'master_audio_sha256':sha(a.master_audio),
       'master_to_decoded_aac_pearson_L_R':corr,'aac_samples':len(dec),'master_samples':len(master),
       'voice_above_combined_bed_active_db':gain['speech_minus_combined_bed_db_active'],
       'cue_count':35,'word_count':len(words),'first_frame_error_seconds_max':max(errs),
       'all_scheduled_within_one_frame':all(-1e-8<=e<1/FPS+1e-8 for e in errs),
       'pixel_word_transitions_tested':pix['eligible'],'pixel_word_transitions_passed':pix['pass'],
       'loudnorm_input_i':loud['input_i'],'loudnorm_input_tp':loud['input_tp'],
       'no_human_listened_or_continuously_watched':True}
    (QA/'numeric.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
