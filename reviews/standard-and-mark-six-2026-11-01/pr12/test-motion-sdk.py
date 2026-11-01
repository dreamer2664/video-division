from pathlib import Path
import sys,numpy as np,json,hashlib,subprocess
from PIL import Image
sys.path.insert(0,'/home/user/look-clean')
from look.house_motion import load_cube_lut,render_moving_shot_clip
from look.house_captions import group_words_into_cues_2_to_5,render_house_caption_patch
p=Path('/home/user/standard-review/videos/team-b/grade-v06/plates/shot_05.jpg');im=np.asarray(Image.open(p).convert('RGB'),dtype=np.float32)/255
lut=load_cube_lut('/home/user/look-clean/look/luts/house_obsidian_500t.cube');d=Path('/home/user/standard-motion-test');d.mkdir(exist_ok=True);render_moving_shot_clip(im,lut,str(d/'motion.mp4'),n_frames=30,halation_strength=.22,rain_amount=.24,mist_amount=.08)
fail=[]
for n in range(2,41):
 ws=[{'text':f'word{k}','start':k*.4,'end':k*.4+.3} for k in range(n)];c=group_words_into_cues_2_to_5(ws);sizes=[len(z['text'].split()) for z in c]
 if any(x<2 or x>5 for x in sizes):fail.append({'n':n,'sizes':sizes})
x,y,rgba=render_house_caption_patch('Cold rain outside',amber_words=['rain']);Image.fromarray((rgba*255).astype('uint8')).save(d/'caption-test.png');out={'motion_fixture':'actual committed MARK FIVE photographic shot05, not Gaussian fallback','rendered_frames':30,'fps':30,'seconds':1,'size':(d/'motion.mp4').stat().st_size,'sha256':hashlib.sha256((d/'motion.mp4').read_bytes()).hexdigest(),'caption_group_test_lengths_2_through_40_failures':fail,'caption_patch_position':[x,y],'caption_patch_shape':list(rgba.shape),'no_production_film_rerender':True};Path('/home/user/standard-review/reviews/standard-and-mark-six-2026-11-01/pr12/motion-and-captions-tests.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
