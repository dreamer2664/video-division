#!/usr/bin/env python3
"""Reproducible 3-plate Lanczos/USM/depth/atmosphere comparison; no network."""
import csv,hashlib,json
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageOps
R=Path(__file__).resolve().parent;A=R/'ab-reel';W,H=1920,1080
# Relative foreground and background evaluation ROIs (x0,y0,x1,y1), selected for scene geometry,
# not equal content. Results are same-ROI before/after, not a perceptual depth score.
SCENES=[
 {'name':'awning','source':'shot_01.jpg','foreground':(.03,.72,.41,.97),'background':(.00,.25,.22,.66),
  'farpoly':[(0,.04),(.26,.04),(.32,.68),(0,.81)],'rainpoly':[(0,0),(1,0),(1,1),(0,1)]},
 {'name':'ledger','source':'shot_03.jpg','foreground':(.15,.68,.76,.95),'background':(.57,.10,.91,.38),
  'farpoly':[(.47,0),(1,0),(1,.50),(.48,.50)],'rainpoly':[(.48,0),(1,0),(1,.49),(.48,.49)]},
 {'name':'reception','source':'shot_07_wall.jpg','foreground':(.28,.74,.66,.98),'background':(.43,.22,.56,.57),
  'farpoly':[(.34,.06),(.63,.06),(.65,.67),(.35,.67)],'rainpoly':[(0,0),(.32,0),(.32,.78),(0,.78)]},
]
def region(im,coords):
    x0,y0,x1,y1=coords;return im[int(y0*H):int(y1*H),int(x0*W):int(x1*W)]
def mask(poly,blur=44):
    im=Image.new('L',(W,H),0);ImageDraw.Draw(im).polygon([(int(x*W),int(y*H)) for x,y in poly],fill=255)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(blur)),dtype=np.float32)/255
def srgb_to_linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def linear_to_srgb(x):
    x=np.clip(x,0,1);return np.where(x<=.0031308,x*12.92,1.055*x**(1/2.4)-.055)
def rain_sheet(seed,n,length):
    rng=np.random.default_rng(seed);im=Image.new('L',(W,H),0);d=ImageDraw.Draw(im)
    for _ in range(n):
        x=int(rng.integers(0,W));y=int(rng.integers(0,H));l=int(rng.integers(max(2,length//2),length+1))
        d.line((x,y,x+max(1,l//6),y+l),fill=int(rng.integers(80,190)),width=1 if length<30 else 2)
    return np.asarray(im.filter(ImageFilter.GaussianBlur(.4 if length<30 else .9)),dtype=np.float32)/255
def gray(a):return cv2.cvtColor(a,cv2.COLOR_RGB2GRAY).astype(np.float32)
def stat_before_after(before,after,roi):
    b=gray(region(before,roi));a=gray(region(after,roi))
    lap_b=float(cv2.Laplacian(b,cv2.CV_32F).var());lap_a=float(cv2.Laplacian(a,cv2.CV_32F).var())
    def grad(g):
        x=cv2.Sobel(g,cv2.CV_32F,1,0,ksize=3);y=cv2.Sobel(g,cv2.CV_32F,0,1,ksize=3);return cv2.magnitude(x,y)/8
    gb,ga=grad(b),grad(a);edge=gb>=np.percentile(gb,80)
    # Fixed baseline edges: mean normal derivative / 4px local edge contrast.
    # A scene-based acutance proxy in inverse pixels, NOT ISO slanted-edge MTF/acutance.
    gx=cv2.Sobel(b,cv2.CV_32F,1,0,ksize=3)/8;gy=cv2.Sobel(b,cv2.CV_32F,0,1,ksize=3)/8
    nx=gx/np.maximum(gb,1e-6);ny=gy/np.maximum(gb,1e-6);yy,xx=np.mgrid[:b.shape[0],:b.shape[1]].astype(np.float32)
    def contrast(g):
        plus=cv2.remap(g,xx+2*nx,yy+2*ny,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        minus=cv2.remap(g,xx-2*nx,yy-2*ny,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        return np.abs(plus-minus)
    cb=contrast(b);ca=contrast(a);sel=edge&(gb>5)&(cb>10)
    agx=cv2.Sobel(a,cv2.CV_32F,1,0,ksize=3)/8;agy=cv2.Sobel(a,cv2.CV_32F,0,1,ksize=3)/8
    anormal=np.abs(agx*nx+agy*ny)
    return {'laplacian_variance_before':lap_b,'laplacian_variance_after':lap_a,
            'edge_gradient_before':float(gb[edge].mean()),'edge_gradient_after':float(ga[edge].mean()),
            'edge_acutance_before_per_pixel':float((gb[sel]/cb[sel]).mean()),
            'edge_acutance_after_per_pixel':float((anormal[sel]/np.maximum(ca[sel],10)).mean()),'edge_samples':int(sel.sum()),
            'contrast_std_before':float(b.std()),'contrast_std_after':float(a.std()),'pixels':int(b.size)}
def main():
    rows=[]
    for idx,s in enumerate(SCENES,1):
        with Image.open(A/'inputs'/s['source']) as im:scaled=ImageOps.fit(im.convert('RGB'),(W,H),method=Image.Resampling.LANCZOS)
        before=np.asarray(scaled,dtype=np.float32)/255
        far=mask(s['farpoly']);window=mask(s['rainpoly'],18)
        # Controlled 0.42-gain, 0.8px USM is softened toward far depth; threshold suppresses noise.
        blur=cv2.GaussianBlur(before,(0,0),.8);detail=before-blur;detail[np.abs(detail)<1.0/255]=0
        sharpen=np.clip(before+detail*.42*(1-.75*far[:,:,None]),0,1)
        # A continuously feathered depth mask blends toward a 1.6px Gaussian, never a global blur.
        bokeh=cv2.GaussianBlur(sharpen,(0,0),1.6);dof=sharpen*(1-.48*far[:,:,None])+bokeh*(.48*far[:,:,None])
        # Scene-referred-ish approximation: 10% cool veil at maximum far-mask opacity in linear light.
        lin=srgb_to_linear(dof);air=srgb_to_linear(np.array([.17,.23,.27],np.float32))[None,None,:];alpha=.10*far[:,:,None]
        result=linear_to_srgb(lin*(1-alpha)+air*alpha)
        # Two different depth sheets: thin far drops and fewer blurred near drops, windows only.
        deep=rain_sheet(100+idx,800,24)*window*.09;near=rain_sheet(200+idx,160,62)*window*.12
        rain=np.clip(deep+near,0,.25)[:,:,None];result=np.clip(result*(1-rain)+np.array([.65,.75,.83],np.float32)[None,None,:]*rain,0,1)
        beforefile=A/f'image-{idx:02d}-{s["name"]}-before.jpg';afterfile=A/f'image-{idx:02d}-{s["name"]}-after.jpg'
        Image.fromarray(np.uint8(np.round(before*255))).save(beforefile,quality=95,subsampling=0)
        Image.fromarray(np.uint8(np.round(result*255))).save(afterfile,quality=95,subsampling=0)
        # Audit decoded deliverables rather than floating-point intermediates.
        b=np.array(Image.open(beforefile).convert('RGB'));a=np.array(Image.open(afterfile).convert('RGB'))
        fg=stat_before_after(b,a,s['foreground']);bg=stat_before_after(b,a,s['background'])
        data={'scene':s['name'],'source':s['source'],'native':'1376x768','output':'1920x1080','foreground_roi':s['foreground'],'background_roi':s['background'],
          'foreground':fg,'background':bg,'background_contrast_below_foreground_before':bg['contrast_std_before']<fg['contrast_std_before'],
          'background_contrast_below_foreground_after':bg['contrast_std_after']<fg['contrast_std_after'],
          'source_sha256':hashlib.sha256((A/'inputs'/s['source']).read_bytes()).hexdigest(),
          'before_sha256':hashlib.sha256(beforefile.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(afterfile.read_bytes()).hexdigest()}
        rows.append(data);print(s['name'],json.dumps(data,sort_keys=True),flush=True)
    (R/'image-metrics.json').write_text(json.dumps(rows,indent=2)+'\n')
    with (R/'image-metrics.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['scene','region','lapvar_before','lapvar_after','acutance_proxy_before_per_px','acutance_proxy_after_per_px','edge_gradient_before','edge_gradient_after','contrast_std_before','contrast_std_after','background_contrast_less_than_foreground_after'])
        for x in rows:
            for zone in ['foreground','background']:
                d=x[zone];w.writerow([x['scene'],zone,*[round(d[k],4) for k in ['laplacian_variance_before','laplacian_variance_after','edge_acutance_before_per_pixel','edge_acutance_after_per_pixel','edge_gradient_before','edge_gradient_after','contrast_std_before','contrast_std_after']],x['background_contrast_below_foreground_after']])
if __name__=='__main__':main()
