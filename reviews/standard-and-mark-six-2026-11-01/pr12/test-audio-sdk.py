from pathlib import Path
import sys,subprocess,json,hashlib,numpy as np
sys.path.insert(0,'/home/user/look-clean')
from look.house_audio import duck_and_master_stems_flac,reproduce_offline_master_wav,build_rain_and_sub_bed
root=Path('/home/user/standard-audio-test');root.mkdir(exist_ok=True);e=Path('/home/user/standard-review/reviews/standard-and-mark-six-2026-11-01/pr12')
f=Path('/home/user/standard-review/videos/team-b/grade-v06/audio/dialogue_stem_48k.flac');v=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(f),'-f','f32le','-']),dtype='<f4').reshape(-1,2)
results=[]
for seconds in [6,60]:
 d=root/str(seconds);d.mkdir(exist_ok=True);voice=v[:seconds*48000].copy();gate=(np.max(np.abs(voice),axis=1)>.001).astype(np.float32);bed=build_rain_and_sub_bed(seconds);g=duck_and_master_stems_flac(voice,bed,gate,str(d/'audio'),str(d/'master.wav'),tmp_dir=str(d/'scratch'));actual=hashlib.sha256((d/'master.wav').read_bytes()).hexdigest();repro=reproduce_offline_master_wav(str(d/'audio'),str(d/'repro.wav'),tmp_dir=str(d/'fresh-scratch'));mp4=d/'encoded.m4a';subprocess.run(['ffmpeg','-y','-v','error','-i',str(d/'master.wav'),'-c:a','aac','-b:a','192k','-ar','48000','-ac','2',str(mp4)],check=True)
 stats={}
 for label,path in [('wav',d/'master.wav'),('aac',mp4)]:
  c=['ffmpeg','-hide_banner','-nostats','-i',str(path),'-af','loudnorm=print_format=json','-f','null','-'];r=subprocess.run(c,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True);(e/(str(seconds)+'s-'+label+'-loudness.txt')).write_text(' '.join(c)+'\n'+r.stdout);import re;st=json.loads(re.search(r'\{\s*"input_i".*?\}',r.stdout,re.S).group(0));stats[label]={'LUFS':st['input_i'],'TP_dBTP':st['input_tp']}
 results.append({'fixture':'committed MARK FIVE dialogue FLAC, decoded; NOT online synthesized demo','seconds':seconds,'gmap_master_sha256':g['master_wav_sha256'],'actual_master_sha256':actual,'fresh_directory_offline_repro_sha256':repro,'bit_exact_offline':actual==repro,'measured_loudness':stats})
(e/'audio-chain-tests.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
