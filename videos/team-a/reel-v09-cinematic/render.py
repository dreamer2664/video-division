#!/usr/bin/env python3
"""THE FOURTH ARRIVAL: offline 1080p30 photographic House Look renderer.

Uses committed generated hotel plates, grade's local House Look optical-motion
module/LUTs, actual Edge word events, and committed FLAC stems. No network.
Camera, rain and grain are 2.5D composites, not live footage.
"""
import argparse,bisect,gc,json,math,os,subprocess,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont,ImageOps
import captions,house_motion as hm

ROOT=Path(__file__).resolve().parent;W=1920;H=1080;FPS=30
# Exact 30fps boundaries; 10 different original photographs, total 1,800 frames.
SHOTS=[
 (0,180,'shot_01.jpg','obsidian',.23,[]),
 (180,345,'shot_02.jpg','obsidian',.17,[(0,.00,.37,1)]),
 (345,510,'shot_03.jpg','amber',.13,[(.52,.00,.94,.55)]),
 (510,675,'shot_04.jpg','obsidian',.12,[(.28,.26,.39,.63)]),
 (675,825,'shot_05.jpg','amber',.15,[(0,.00,.40,.58)]),
 (825,960,'shot_06.jpg','obsidian',.14,[(.50,.04,.69,.72)]),
 (960,1176,'shot_07_wall.jpg','obsidian',.18,[(0,.00,.34,.78)]),
 (1176,1356,'shot_08.jpg','amber',.14,[(0,.02,.37,.67)]),
 (1356,1584,'shot_09.jpg','amber',.13,[(.15,.02,.38,.55)]),
 (1584,1800,'shot_10.jpg','obsidian',.18,[(0,.00,.50,1)]),
]
LAMP=[(.64,.46),(.47,.42),(.18,.11),(.37,.55),(.57,.23),(.78,.38),(.61,.39),(.51,.26),(.76,.36),(.75,.50)]

def mask_for(regions):
    if not regions:return None
    im=Image.new('L',(W,H),0);d=ImageDraw.Draw(im)
    for x0,y0,x1,y1 in regions:d.rectangle((int(x0*W),int(y0*H),int(x1*W),int(y1*H)),fill=255)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(28)),dtype=np.float32)/255.0

class Captions:
    def __init__(self,ass_path):
        self.cues=captions.build(ass_path)
        self.words=json.loads((ROOT/'timing/word_timings.json').read_text())['words']
        self.starts=[c['start'] for c in self.cues]
        self.wordstarts=[[self.words[i]['start'] for i in range(c['a'],c['b']+1)] for c in self.cues]
        self.patch=[];self.meta=[]
        font=ImageFont.truetype(str(ROOT/'assets/Anton-Regular.ttf'),54)
        for cue in self.cues:
            labels=[captions.label(self.words[i],i) for i in range(cue['a'],cue['b']+1)]
            widths=[font.getlength(x) for x in labels];sp=font.getlength(' ')
            boxw=round(sum(widths)+sp*(len(labels)-1)+66);boxh=78
            states=[]
            for spoken in range(len(labels)):
                im=Image.new('RGBA',(boxw,boxh),(0,0,0,0));draw=ImageDraw.Draw(im)
                draw.rounded_rectangle((0,0,boxw-1,boxh-1),radius=14,fill=(4,8,15,185),outline=(240,245,255,28),width=1)
                draw.rounded_rectangle((4,9,8,boxh-9),radius=2,fill=(245,209,78,230))
                x=29
                for j,(lab,wd) in enumerate(zip(labels,widths)):
                    idx=cue['a']+j
                    col=(234,68,60,255) if j<=spoken and 94<=idx<=99 else (245,209,78,255) if j<=spoken else (244,245,248,255)
                    draw.text((round(x),8),lab,font=font,fill=col,stroke_width=2,stroke_fill=(5,8,13,245))
                    x+=wd+sp
                a=np.asarray(im,dtype=np.float32)/255.0
                states.append((a[:,:,:3],a[:,:,3:4]))
            self.patch.append(states)
            self.meta.append({'start_s':cue['start'],'end_s':cue['end'],'text':cue['text'],
                'words':[{'text':self.words[i]['word'],'start_s':self.words[i]['start'],'end_s':self.words[i]['end'],
                          'first_eligible_frame':math.ceil(self.words[i]['start']*FPS-1e-8)} for i in range(cue['a'],cue['b']+1)]})
        (ROOT/'timing/captions_locked.json').write_text(json.dumps({'fps':FPS,'method':'Direct comparison of frame presentation time against actual Edge word starts; active and previous words recolor at the first eligible 30fps frame, with no proportional timing or ASS centisecond rounding.','cues':self.meta},indent=2)+'\n')
    def apply(self,frame,t):
        j=bisect.bisect_right(self.starts,t+1e-10)-1
        if j<0 or t>=self.cues[j]['end']:return frame
        k=bisect.bisect_right(self.wordstarts[j],t+1e-10)-1
        if k<0:return frame
        rgb,alpha=self.patch[j][k];h,w=alpha.shape[:2];x=(W-w)//2;y=H-118-h
        part=frame[y:y+h,x:x+w];part[:]=part*(1-alpha)+rgb*alpha
        return frame

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build-dir',type=Path,help='retained scratch directory; default temporary')
    ap.add_argument('--test-shot',type=int,help='1-based shot for a short test only');ap.add_argument('--test-frames',type=int,default=60)
    ap.add_argument('--crf',type=int,default=20);args=ap.parse_args()
    if args.build_dir:out=args.build_dir;out.mkdir(parents=True,exist_ok=True)
    else:out=Path(tempfile.mkdtemp(prefix='reel-hotel-build-'))
    print('Build intermediates:',out,flush=True)
    cap=Captions(out/'captions.ass')
    luts={'obsidian':hm.load_cube_lut(str(ROOT/'luts/house_obsidian_500t.cube')),'amber':hm.load_cube_lut(str(ROOT/'luts/house_amber_practical.cube'))}
    far=hm.build_rain_tile(seed=801,density=.00055,length=46,angle_deg=13,blur_r=.7)
    near=hm.build_rain_tile(seed=802,density=.00024,length=90,angle_deg=14.5,blur_r=1.15)
    mist=hm.build_mist_tile(seed=905)
    clips=[]
    for i,(start,end,name,lut,rain,regions) in enumerate(SHOTS):
        if args.test_shot and i+1!=args.test_shot:continue
        n=end-start if not args.test_shot else min(args.test_frames,end-start)
        with Image.open(ROOT/'plates'/name) as im:
            photo=ImageOps.fit(im.convert('RGB'),(W,H),method=Image.Resampling.LANCZOS)
        plate=np.asarray(photo,dtype=np.float32)/255.0;rainmask=mask_for(regions)
        clip=out/f'clip_{i+1:02d}.mp4';lcx,lcy=LAMP[i];cx=int(lcx*W);cy=int(lcy*H)
        rx=74;ry=52;x0=max(0,cx-rx);x1=min(W,cx+rx);y0=max(0,cy-ry);y1=min(H,cy+ry)
        yy,xx=np.mgrid[y0:y1,x0:x1];halo=np.exp(-.5*(((xx-cx)/(rx*.44))**2+((yy-cy)/(ry*.44))**2)).astype(np.float32)[:,:,None]
        color=np.array([.016,.006,.001],np.float32)[None,None,:]
        def hook(frame,gf,t):
            # Subtle warm practical breath; rain remains outside via each soft mask.
            frame[y0:y1,x0:x1]+=halo*color*(.5+.5*math.sin(t*4.2))
            return cap.apply(frame,t)
        print(f'shot {i+1:02d}: {start/FPS:.2f}–{end/FPS:.2f}s, {n} frames, {name}',flush=True)
        hm.render_moving_shot_clip(plate,luts[lut],str(clip),n_frames=n,start_frame_global=start,
            zoom_start=1.015,zoom_end=1.075,pan_x_start=(-.004 if i%2 else .004),pan_x_end=(.004 if i%2 else -.004),
            pan_y_start=.003,pan_y_end=-.003,halation_strength=.22,rain_amount=rain,
            mist_amount=.035 if i==0 else 0,rain_far=far,rain_near=near,mist_tile=mist,rain_mask=rainmask,frame_hook=hook,crf=args.crf)
        clips.append(clip);del plate,photo,rainmask;gc.collect();print(f'shot {i+1:02d} encoded',flush=True)
    if args.test_shot:print('TEST_CLIP',clips[0],flush=True);return
    assert len(clips)==10 and sum(e-s for s,e,*_ in SHOTS)==1800
    subprocess.run(['python3',str(ROOT/'build_audio.py'),'--out',str(out)],check=True)
    concat=out/'clips.ffconcat';concat.write_text('ffconcat version 1.0\n'+''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in clips))
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',str(out/'mix.m4a'),
         '-map','0:v:0','-map','1:a:0','-c','copy','-t','60','-movflags','+faststart','-metadata','title=The Fourth Arrival',str(ROOT/'video.mp4')]
    subprocess.run(cmd,check=True);(out/'final-mux-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    print('Rendered',ROOT/'video.mp4',flush=True)
if __name__=='__main__':main()
