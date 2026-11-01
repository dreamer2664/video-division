#!/usr/bin/env python3
"""Reproducible WARD TEN voice/mix and per-word caption telemetry audit.

Uses the committed FLAC, Edge word events, script/caption source and final MP4s.
Decodes audio to mono 16 kHz, clips AAC padding to exactly 60 seconds, and measures
zero/peak-lag correlation plus a least-squares source-versus-residual energy ratio.
The latter is an estimate, not isolated stems or a perceptual intelligibility test.
Generates ASS in a temporary copy, without rewriting committed caption files.
"""
import argparse,hashlib,json,math,re,shutil,subprocess,tempfile
from pathlib import Path
import numpy as np
from scipy import signal
import captions

ROOT=Path(__file__).resolve().parent
SR=16000; DURATION=60; N=SR*DURATION

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def decode(p):
    b=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-ac','1','-ar',str(SR),'-f','f32le','-'])
    a=np.frombuffer(b,'<f4').astype(np.float64)
    actual=len(a)
    a=a[:N] if len(a)>=N else np.pad(a,(0,N-len(a)))
    return a,actual

def adts_hash(p):
    b=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c','copy','-f','adts','-'])
    return hashlib.sha256(b).hexdigest()

def stamp(t):
    h,m,s=t.split(':');return int(h)*3600+int(m)*60+float(s)

def generated_ass():
    with tempfile.TemporaryDirectory(prefix='ward-ten-caption-audit-') as td:
        root=Path(td);(root/'assets').mkdir()
        shutil.copy2(ROOT/'captions.py',root/'captions.py')
        for name in ('word_timings.json','Anton-Regular.ttf'):shutil.copy2(ROOT/'assets'/name,root/'assets'/name)
        def run(name,extra=()):
            p=root/name
            subprocess.run(['python3',str(root/'captions.py'),'--ass',str(p),*extra],check=True,stdout=subprocess.DEVNULL)
            return [x for x in p.read_text().splitlines() if x.startswith('Dialogue:')]
        portrait=run('portrait.ass');landscape=run('landscape.ass',('--landscape',))
        assert (root/'captions.srt').read_bytes()==(ROOT/'captions.srt').read_bytes(),'regenerated SRT differs'
        return portrait,landscape

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);args=p.parse_args()
    stem=ROOT/'assets/narration.flac';video=ROOT/'video.mp4';land=ROOT/'video-landscape.mp4'
    wpath=ROOT/'assets/word_timings.json';words=json.loads(wpath.read_text())['words']
    x,nx=decode(stem);y,ny=decode(video)
    x=x-x.mean();y=y-y.mean();denom=float(np.linalg.norm(x)*np.linalg.norm(y))
    r0=float(np.dot(x,y)/denom)
    corr=signal.correlate(y,x,mode='full',method='fft');center=N-1;radius=SR//2
    lag=int(np.argmax(corr[center-radius:center+radius+1]))-radius
    rmax=float(corr[center+lag]/denom)
    gain=float(np.dot(x,y)/np.dot(x,x));voice=x*gain;residual=y-voice
    mask=np.zeros(N,dtype=bool)
    for word in words:mask[max(0,round(word['start']*SR)):min(N,round(word['end']*SR))]=True
    def energy_ratio(m):
        vr=float(np.sqrt(np.mean(voice[m]**2)));rr=float(np.sqrt(np.mean(residual[m]**2)))
        return {'voice_estimate_rms':vr,'residual_rms':rr,'voice_minus_residual_db':20*math.log10(vr/rr)}
    audio={'sample_rate_hz':SR,'analysis_seconds':DURATION,'decoded_stem_samples_before_pad':nx,
           'decoded_mix_samples_before_trim':ny,'zero_lag_pearson_r':r0,'peak_lag_search_seconds':[-.5,.5],
           'peak_lag_samples':lag,'peak_lag_seconds':lag/SR,'peak_normalized_correlation':rmax,
           'least_squares_stem_gain':gain,'aggregate_60s':energy_ratio(np.ones(N,dtype=bool)),
           'timed_word_spans_only':energy_ratio(mask),
           'method':'Pearson on aligned mono PCM; mix = fitted scalar * committed stem + residual. Residual includes music, effects, AAC error and any nonlinear gain. Not a perceptual or source-separation measurement.'}
    portrait,landscape=generated_ass();assert portrait==landscape
    assert len(portrait)==len(captions.GROUPS)==44 and len(words)==130
    spans=[]
    for ci,(line,(first,last)) in enumerate(zip(portrait,captions.GROUPS),1):
        fields=line.split(',',9);cue_start=stamp(fields[1]);cue_end=stamp(fields[2]);time=cue_start
        pairs=re.findall(r'\{\\k(\d+)\}([^{}]+)',fields[9]);assert len(pairs)==last-first+1
        for j,(centis,text) in enumerate(pairs):
            i=first+j;word=words[i];assert text.strip()==captions.label(word,i)
            # ASS instant karaoke tag begins this word at the accumulated event offset.
            logical=time;first_frame=math.ceil(logical*30-1e-8)/30
            overhang=max(0,cue_start-word['start'],word['end']-cue_end)
            spans.append({'index':i,'word':word['word'],'cue':ci,'speech_start_s':word['start'],'speech_end_s':word['end'],
                          'cue_start_s':cue_start,'cue_end_s':cue_end,'highlight_ass_start_s':round(logical,6),
                          'estimated_first_eligible_video_frame_s':round(first_frame,6),
                          'ass_start_error_s':round(logical-word['start'],6),
                          'estimated_frame_start_error_s':round(first_frame-word['start'],6),
                          'cue_speech_overhang_s':round(overhang,6),'karaoke_duration_centiseconds':int(centis)})
            time+=int(centis)/100
    tol=1/30
    aud={'method':'Measured Edge word starts drive ASS instant karaoke per word, not proportional allocation by word length. Each nonfinal tag lasts to the next measured word start, rounded to centiseconds; the final tag extends to cue end. The first eligible 30 fps frame is calculated from the ASS time, not measured by observing pixel changes. This validates service telemetry, not human phonetic alignment.',
         'portrait_and_landscape_ass_dialogues_identical':True,'cue_count':len(portrait),'word_count':len(spans),
         'word_spans_inside_cues_within_one_frame':sum(x['cue_speech_overhang_s']<=tol for x in spans),
         'maximum_cue_speech_overhang_s':max(x['cue_speech_overhang_s'] for x in spans),
         'logical_word_highlights_within_one_frame':sum(abs(x['ass_start_error_s'])<=tol for x in spans),
         'maximum_absolute_logical_highlight_error_s':max(abs(x['ass_start_error_s']) for x in spans),
         'estimated_first_eligible_frames_within_one_frame':sum(abs(x['estimated_frame_start_error_s'])<=tol for x in spans),
         'maximum_absolute_estimated_frame_start_error_s':max(abs(x['estimated_frame_start_error_s']) for x in spans),
         'word_spans':spans}
    ah=[adts_hash(video),adts_hash(land)];assert ah[0]==ah[1]
    out={'assets_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [stem,wpath,ROOT/'captions.py',ROOT/'captions.srt',ROOT/'script.md',ROOT/'audit_narration.py',video,land]},
         'portrait_and_landscape_identical_adts_audio_sha256':ah[0],
         'audio_source_to_mix':audio,'caption_timing':aud}
    assert lag==0,'source/mix correlation peak is not zero lag'
    assert aud['word_spans_inside_cues_within_one_frame']==130
    assert aud['logical_word_highlights_within_one_frame']==130
    result=json.dumps(out,indent=2,ensure_ascii=False)+'\n'
    if args.out:args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(result)
    else:print(result,end='')
if __name__=='__main__':main()
