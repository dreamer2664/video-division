#!/usr/bin/env python3
"""Check real encoded cut transitions, word-aligned captions, and MP4 faststart.

Reads only finished media and the committed timeline. Requires FFmpeg, NumPy and
Pillow. The cut detector looks at the changing portrait shot-number/header patch;
it is a structural check, not a judgment of editorial quality.
"""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
import numpy as np
from PIL import ImageFont
from captions import GROUPS,label

HERE=Path(__file__).resolve().parent

def mp4_boxes(p):
    boxes=[]
    with p.open('rb') as f:
        pos=0
        while pos<p.stat().st_size:
            f.seek(pos);head=f.read(8)
            if len(head)<8:raise ValueError('incomplete MP4 box')
            size,kind=struct.unpack('>I4s',head)
            if size==1:size=struct.unpack('>Q',f.read(8))[0]
            elif size==0:size=p.stat().st_size-pos
            if size<8:raise ValueError('invalid MP4 box')
            boxes.append({'type':kind.decode('ascii','replace'),'offset':pos,'size':size});pos+=size
    kinds=[b['type'] for b in boxes]
    assert 'moov' in kinds and 'mdat' in kinds and kinds.index('moov')<kinds.index('mdat'),p
    return boxes

def timecode(s):
    h,m,rest=s.split(':');sec,ms=rest.split(',');return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000

def audio_hash(p):
    r=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c','copy','-f','adts','-'],stdout=subprocess.PIPE,check=True)
    return hashlib.sha256(r.stdout).hexdigest()

def cut_check(p):
    cmd=['ffmpeg','-v','error','-threads','2','-i',str(p),'-vf','crop=180:130:880:195,scale=90:65,format=gray',
         '-an','-fps_mode','passthrough','-f','rawvideo','-']
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE);size=90*65;prev=None;diff=[]
    while True:
        buf=proc.stdout.read(size)
        if not buf:break
        if len(buf)!=size:raise RuntimeError('incomplete decoded frame')
        frame=np.frombuffer(buf,dtype=np.uint8).reshape(65,90)
        if prev is not None:diff.append(float(np.abs(frame.astype(np.int16)-prev.astype(np.int16)).mean()))
        prev=frame.copy()
    assert proc.wait()==0 and len(diff)==1799
    dif=np.array(diff);boundaries=np.cumsum([54,60,66]*10)[:-1];out=[]
    for n in boundaries:
        lo=max(0,int(n)-4);hi=min(len(dif),int(n)+2)
        peak=int(np.argmax(dif[lo:hi])+lo+1)
        out.append({'frame':int(n),'seconds':float(n/30),'header_mean_abs_diff':round(float(dif[n-1]),3),'local_peak_frame':peak})
    assert all(x['frame']==x['local_peak_frame'] for x in out),'one or more cut boundaries are not the local header-change peak'
    return {'decoded_frames':len(diff)+1,'cut_boundaries_checked':len(out),'matches':len(out),
            'minimum_boundary_mean_abs_diff_0_255':round(min(x['header_mean_abs_diff'] for x in out),3),
            'median_adjacent_header_diff_0_255':round(float(np.median(dif)),3),'boundaries':out}

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);args=p.parse_args()
    meta=json.loads((HERE/'assets/word_timings.json').read_text());words=meta['words']
    script=(HERE/'script.md').read_text().split('## Narration\n',1)[1].split('## Timed picture plan',1)[0]
    script=re.sub(r'\*\[.*?\]\*',' ',script,flags=re.S)
    def tokens(s):return re.findall(r"[a-z]+(?:[.'-][a-z]+)*",s.lower())
    spoken=[]
    for word in words:spoken.extend(tokens(word['word']))
    assert tokens(script)==spoken,'script and timed narration text differ'
    blocks=re.split(r'\n\s*\n',(HERE/'captions.srt').read_text().strip());cues=[]
    for i,block in enumerate(blocks):
        rows=block.splitlines();assert int(rows[0])==i+1
        a,b=rows[1].split(' --> ');cues.append((timecode(a),timecode(b),' '.join(rows[2:])))
    assert len(words)==125 and len(cues)==len(GROUPS)==42
    assert [i for a,b in GROUPS for i in range(a,b+1)]==list(range(len(words)))
    max_overhang=0.0;max_width=0.0;minimum_font=94
    for ci,((start,end,text),(a,b)) in enumerate(zip(cues,GROUPS)):
        assert 2<=b-a+1<=5 and start<end<=60
        assert text==' '.join(label(words[i],i) for i in range(a,b+1))
        if ci:assert start>=cues[ci-1][1]
        for j in range(a,b+1):max_overhang=max(max_overhang,start-words[j]['start'],words[j]['end']-end,0)
        size=94
        while size>60 and ImageFont.truetype(str(HERE/'assets/Anton-Regular.ttf'),size).getlength(text)>875:size-=2
        width=ImageFont.truetype(str(HERE/'assets/Anton-Regular.ttf'),size).getlength(text)
        assert width<=875
        max_width=max(max_width,width);minimum_font=min(minimum_font,size)
    assert max_overhang<=1/30
    pre=[w for w in words if w['part']=='pre'];post=[w for w in words if w['part']!='pre']
    reveal=[w for w in words if w['word'].lower()=='callers'];assert len(reveal)==1
    files=[HERE/'video.mp4',HERE/'video-landscape.mp4'];audio=[audio_hash(f) for f in files];assert audio[0]==audio[1]
    output={
        'script_tokens_match_timed_words':True,'speech_word_events':len(words),'speech_first_word_start_s':round(words[0]['start'],3),
        'speech_last_word_end_s':round(words[-1]['end'],3),
        'pre_reveal_word_gap_s':round(post[0]['start']-pre[-1]['end'],3),
        'callers_reveal_word_start_s':round(reveal[0]['start'],3),
        'caption_cues':len(cues),'caption_words_min':min(b-a+1 for a,b in GROUPS),'caption_words_max':max(b-a+1 for a,b in GROUPS),
        'caption_first_start_s':cues[0][0],'caption_last_end_s':cues[-1][1],
        'caption_max_speech_boundary_overhang_s':round(max_overhang,6),
        'caption_nominal_max_text_width_px':round(max_width,2),'caption_nominal_min_font_px':minimum_font,
        'both_aac_bitstreams_adts_sha256':audio[0],
        'faststart_top_level_boxes':{f.name:mp4_boxes(f) for f in files},
        'portrait_cut_check':cut_check(files[0])}
    out=json.dumps(output,indent=2,ensure_ascii=False)+'\n'
    if args.out:args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(out)
    else:print(out,end='')
if __name__=='__main__':main()
