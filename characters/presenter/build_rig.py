"""Build the original Rook/Nib Blender character rig and cue-driven action.

Run with: blender --background --python build_rig.py -- --cues proof/cues.json
This scene is an editable Blender character asset; proof assembly overlays the same
cue-sheet timing with the deterministic high-resolution vector renderer.
"""
import bpy, sys, json, math, subprocess, array
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
def arg(flag,default):
    return args[args.index(flag)+1] if flag in args else default
CUES=json.loads(Path(arg('--cues',str(HERE/'proof/cues.json'))).read_text())
AUDIO=Path(arg('--audio',str(HERE/'proof/voice.mp3')))
OUT=Path(arg('--out',str(HERE/'presenter_rig.blend'))); PREVIEW=Path(arg('--preview',str(HERE/'rig-preview.png')))
FPS=CUES['frame_rate']; DURATION=CUES['duration_seconds']; END_FRAME=round(FPS*DURATION)

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for block in bpy.data.materials: bpy.data.materials.remove(block)

def mat(name,color,rough=.8):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.roughness=rough; return m
skin=mat('01 · toasted apricot skin',(0.78,.39,.24)); skin_l=mat('02 · warm light planes',(0.93,.58,.38))
hair=mat('03 · ink plum hair',(.09,.075,.16)); hair_hi=mat('04 · violet hair plane',(.24,.19,.34))
teal=mat('05 · jade overshirt',(.06,.39,.34)); teal_l=mat('06 · mint seam',(.12,.62,.52)); scarf=mat('07 · persimmon scarf',(.82,.29,.16))
gold=mat('08 · brass barrette',(.96,.67,.18)); white=mat('09 · eye ivory',(.98,.93,.79)); iris=mat('10 · deep teal eyes',(.08,.16,.19))
ink=mat('11 · mouth / outline',(.06,.065,.105)); screen=mat('12 · sidekick glass',(.04,.08,.12)); mint=mat('13 · Nib enamel',(.12,.58,.53)); glow=mat('14 · LED gold',(1,.68,.18))
floor_mat=mat('15 · dusk navy stage',(.08,.12,.19)); backdrop=mat('16 · pale ice',(.52,.65,.73))

# Rig armatures live in the scene, with explicit bone names shared with README.
def rig(name,bones,loc=(0,0,0)):
    data=bpy.data.armatures.new(name+' · Skeleton'); ob=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(ob); ob.location=loc
    bpy.context.view_layer.objects.active=ob; ob.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    for bname,head,tail,parent in bones:
        b=data.edit_bones.new(bname); b.head=head; b.tail=tail
        if parent: b.parent=data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT'); ob.select_set(False)
    for p in ob.pose.bones: p.rotation_mode='XYZ'
    return ob

rook=rig('Rook · face rig',[
 ('root',(0,0,0),(0,0,.65),None),('torso',(0,0,.65),(0,0,2.65),'root'),('neck',(0,0,2.45),(0,0,3.05),'torso'),
 ('head',(0,0,2.95),(0,0,4.15),'neck'),('jaw',(0,-.02,3.2),(0,-.02,3.52),'head'),
 ('arm.L',(-.72,0,2.45),(-1.08,0,1.84),'torso'),('forearm.L',(-1.08,0,1.84),(-1.35,-.04,1.25),'arm.L'),('hand.L',(-1.35,-.04,1.25),(-1.42,-.04,1.08),'forearm.L'),
 ('arm.R',(.72,0,2.45),(1.08,0,1.84),'torso'),('forearm.R',(1.08,0,1.84),(1.35,-.04,1.25),'arm.R'),('hand.R',(1.35,-.04,1.25),(1.42,-.04,1.08),'forearm.R')])
nib=rig('Nib · battery bug',[
 ('root',(0,0,0),(0,0,.5),None),('shell',(0,0,.25),(0,0,1.15),'root'),('tail',(0,0,.75),(.55,0,1.25),'shell'),('feet.L',(-.3,0,.25),(-.4,0,0),'root'),('feet.R',(.3,0,.25),(.4,0,0),'root')],loc=(2.4,-.1,0))

def attach(obj,arm,bone):
    vg=obj.vertex_groups.new(name=bone); vg.add(list(range(len(obj.data.vertices))),1.0,'REPLACE')
    mod=obj.modifiers.new('Character controls','ARMATURE'); mod.object=arm
    return obj

def sphere(name,loc,scale,material,arm,bone,seg=20,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth=False
    attach(o,arm,bone); return o

def box(name,loc,scale,material,arm,bone,bevel=.1):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new('Soft graphic bevel','BEVEL'); mod.width=bevel; mod.segments=1
    attach(o,arm,bone); return o

def rod(name,a,b,r,material,arm,bone):
    a,b=Vector(a),Vector(b); v=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=v.length,location=(a+b)/2)
    o=bpy.context.object; o.name=name; o.rotation_mode='QUATERNION'; o.rotation_quaternion=v.to_track_quat('Z','Y'); o.data.materials.append(material)
    attach(o,arm,bone); return o

def curve(name,points,material,arm,bone,bevel=.045):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.bevel_depth=bevel; c.bevel_resolution=1
    s=c.splines.new('POLY'); s.points.add(len(points)-1)
    for p,co in zip(s.points,points): p.co=(*co,1)
    o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); o.data.materials.append(material)
    bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.convert(target='MESH'); o=bpy.context.object; o.select_set(False)
    attach(o,arm,bone); return o

# Rook: cropped portrait, plum asymmetrical crop, gold clip, freckles, angular clothing.
box('Rook · broad jade coat',(0,0,1.42),(2.65,.72,1.75),teal,rook,'torso',.24)
box('Rook · left lit lapel',(-.63,-.39,1.42),(.55,.09,1.45),teal_l,rook,'torso',.06)
box('Rook · persimmon scarf',(0,-.42,2.06),(.55,.14,1.05),scarf,rook,'torso',.08)
sphere('Rook · neck',(0,0,2.7),(.48,.42,.58),skin,rook,'neck')
sphere('Rook · head',(0,0,3.62),(.98,.72,1.12),skin,rook,'head',24,16)
# Side plane under light, nose and two ears.
sphere('Rook · left ear',(-.97,0,3.62),(.25,.21,.34),skin_l,rook,'head')
sphere('Rook · right ear',(.97,0,3.62),(.25,.21,.34),skin_l,rook,'head')
sphere('Rook · left cheek plane',(-.64,-.72,3.33),(.27,.055,.29),skin_l,rook,'head')
sphere('Rook · nose',(0,-.76,3.52),(.16,.18,.29),skin_l,rook,'head',12,8)
# Sculpted hair cap and a swept lock; separate light facets give cel bands.
sphere('Rook · cropped hair',(-.02,.015,4.38),(1.01,.74,.49),hair,rook,'head',16,8)
sphere('Rook · swept lock',(-.47,-.42,4.32),(.58,.38,.28),hair_hi,rook,'head',12,8)
box('Rook · brass hair clip',(.52,-.73,4.56),(.34,.09,.11),gold,rook,'head',.04)
# Eyes, brows and mouth, all tied to head/jaw controls.
for side,x in [('L',-.42),('R',.42)]:
    sphere('Rook · eye white '+side,(x,-.66,3.86),(.23,.12,.16),white,rook,'head')
    sphere('Rook · iris '+side,(x,-.78,3.84),(.085,.06,.115),iris,rook,'head',12,8)
    curve('Rook · expressive brow '+side,[(x-.24,-.76,4.13),(x,-.81,4.23),(x+.22,-.76,4.12)],hair,rook,'head',.075)
sphere('Rook · mouth / viseme',(0,-.77,3.28),(.28,.07,.07),ink,rook,'jaw',16,8)
# Freckle dots, asymmetrical and hand-placed.
for side in (-1,1):
    for i in range(3): sphere(f'Rook · freckle {side}-{i}',(side*(.57+.09*(i%2)),-.755,3.48-.07*i),(.025,.018,.025),scarf,rook,'head',8,6)
# Separate tapered arms and hands for expressive beats.
for side,label in [(-1,'L'),(1,'R')]:
    shoulder=(side*.83,0,2.14); elbow=(side*1.12,-.02,1.72); wrist=(side*1.36,-.06,1.26)
    rod('Rook · upper sleeve '+label,shoulder,elbow,.28,teal,rook,'arm.'+label)
    rod('Rook · forearm '+label,elbow,wrist,.21,teal_l,rook,'forearm.'+label)
    sphere('Rook · hand '+label,wrist,(.19,.15,.18),skin,rook,'hand.'+label,12,8)
    for f in range(3): rod(f'Rook · finger {label}-{f}',(wrist[0]+side*.06*(f-1),wrist[1]-.1,wrist[2]-.07),(wrist[0]+side*.07*(f-1),wrist[1]-.11,wrist[2]-.24),.035,skin,rook,'hand.'+label)

# Nib: teal battery casing, dark glass face, amber pixel eyes, orange cable tail and feet.
sphere('Nib · enamel shell',(2.4,-.05,1.16),(.66,.42,.65),mint,nib,'shell',16,10)
box('Nib · dark glass face',(2.4,-.45,1.20),(.85,.12,.45),screen,nib,'shell',.18)
for x in (2.18,2.62): sphere('Nib · LED eye '+str(x),(x,-.54,1.22),(.07,.045,.09),glow,nib,'shell',10,8)
curve('Nib · curled charging tail',[(2.95,-.04,1.15),(3.28,-.05,1.42),(3.18,-.05,1.72),(3.48,-.05,1.80)],scarf,nib,'tail',.075)
box('Nib · brass terminal',(3.47,-.05,1.80),(.19,.16,.15),gold,nib,'tail',.04)
for x,label in [(2.12,'L'),(2.68,'R')]:
    rod('Nib · foot '+label,(x,0,.72),(x-.08,0,.35),.09,scarf,nib,'feet.'+label)

# Small orthographic studio stage with an actual world-plane backdrop.
for stage_name,loc,scale,material in [('Stage · floor',(0,1,-.2),(20,16,.25),floor_mat),('Stage · backdrop',(0,3,4),(18,.2,9),backdrop)]:
    stage_obj=box(stage_name,loc,scale,material,rook,'root',0)
    for mod in list(stage_obj.modifiers): stage_obj.modifiers.remove(mod)
# Warm key and cool fill.
def area(name,loc,power,color,size):
    bpy.ops.object.light_add(type='AREA',location=loc); o=bpy.context.object; o.name=name; o.data.energy=power; o.data.color=color; o.data.shape='DISK'; o.data.size=size
    o.rotation_euler=(Vector((0,0,2.6))-o.location).to_track_quat('-Z','Y').to_euler()
area('Key · warm softbox',(-4,-6,8),550,(1,.72,.49),6)
area('Fill · ice bounce',(4,-5,5),360,(.52,.75,1),5)
# Camera faces the character front and preserves full vertical portrait framing.
bpy.ops.object.camera_add(location=(.82,-11,4.3)); cam=bpy.context.object; cam.name='Portrait 9:16'; cam.rotation_euler=(Vector((.82,0,2.7))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=8.7
scene=bpy.context.scene; scene.camera=cam
scene.frame_start=1; scene.frame_end=END_FRAME; scene.render.fps=FPS
scene.render.resolution_x=720; scene.render.resolution_y=1280; scene.render.resolution_percentage=100
scene.render.engine='BLENDER_WORKBENCH'; scene.display.shading.light='STUDIO'; scene.display.shading.color_type='MATERIAL'; scene.display.shading.show_shadows=True; scene.display.shading.show_cavity=True; scene.display.shading.cavity_type='WORLD'; scene.display.shading.cavity_ridge_factor=1.2; scene.display.shading.cavity_valley_factor=1.0
scene.world.color=(.22,.28,.35); scene.display.shading.background_type='WORLD'
scene.view_settings.view_transform='Standard'

# Timing: continuous idle keys + speech-energy mouth openings sampled from the VO itself.
def audio_levels(path,frames):
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ac','1','-ar',str(FPS*10),'-f','f32le','pipe:1'])
    vals=array.array('f'); vals.frombytes(raw)
    if sys.byteorder!='little': vals.byteswap()
    a=[]
    for i in range(frames):
        seg=vals[i*10:min((i+1)*10,len(vals))]
        a.append(math.sqrt(sum(x*x for x in seg)/max(1,len(seg))) if seg else 0.)
    peak=sorted(a)[max(0,int(.88*len(a))-1)] or 1.
    return [min(1.,x/peak) for x in a]

def key(posebone,prop,frame,value,index=None):
    if index is None: setattr(posebone,prop,value); posebone.keyframe_insert(data_path=prop,frame=frame)
    else:
        arr=list(getattr(posebone,prop)); arr[index]=value; setattr(posebone,prop,arr); posebone.keyframe_insert(data_path=prop,frame=frame,index=index)
levels=audio_levels(AUDIO,END_FRAME)
head=rook.pose.bones['head']; jaw=rook.pose.bones['jaw']; root=rook.pose.bones['root']; shell=nib.pose.bones['root']
for f in range(1,END_FRAME+1):
    t=(f-1)/FPS
    head.rotation_euler=(.045*math.sin(t*1.6),.045*math.sin(t*.84),.025*math.sin(t*.64))
    root.location.z=.035*math.sin(t*2*math.pi/3.6)
    key(head,'rotation_euler',f,head.rotation_euler)
    key(root,'location',f,root.location)
    # Jaw squash drives a clear, repeatable viseme from the recorded signal envelope.
    jaw.scale=(1,1,.35+.85*levels[f-1]); key(jaw,'scale',f,jaw.scale)
    shell.location.z=.035*math.sin(t*2.4); key(shell,'location',f,shell.location)
# Blinks are reusable rig behavior (not keyed to each sentence/caption).
eye_objs=[o for o in bpy.data.objects if o.name.startswith('Rook · eye white')]
for bt in (2.8,5.25,8.6,12.1,15.7,18.35,21.2):
    fr=round(bt*FPS)+1
    for o in eye_objs:
        o.scale.z*=.12; o.keyframe_insert(data_path='scale',frame=fr)
        o.scale.z/= .12; o.keyframe_insert(data_path='scale',frame=fr+5)
# Cue-sheet event keys share the same phrase-anchored starts as captions/status.
for event in CUES['motion']:
    a=round(event['start']*FPS)+1; b=max(a+1,round(event['end']*FPS)+1); mid=(a+b)//2
    actor=event['actor']; action=event['action']
    rigob=rook if actor=='presenter' else nib
    if action=='nod':
        pb=rigob.pose.bones['head']; key(pb,'rotation_euler',a,(0,0,0)); key(pb,'rotation_euler',mid,(-.18,0,0)); key(pb,'rotation_euler',b,(0,0,0))
    elif action in ('open_palm','point_screen','shrug'):
        names=['arm.R'] if action!='shrug' else ['arm.L','arm.R']
        for name in names:
            pb=rook.pose.bones[name]; key(pb,'rotation_euler',a,(0,0,0)); val=(0,-.50 if action=='point_screen' else .36,0); key(pb,'rotation_euler',mid,val); key(pb,'rotation_euler',b,(0,0,0))
    elif action in ('shiver','comic_recoil','squint','peek'):
        pb=nib.pose.bones['root']; amp=.18 if action in ('shiver','comic_recoil') else .1
        key(pb,'rotation_euler',a,(0,0,0)); key(pb,'rotation_euler',mid,(0,0,amp)); key(pb,'rotation_euler',b,(0,0,0))
# Use ease-in/out curves; hold facial/cue cues only where authored.
for ob in (rook,nib):
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation='BEZIER'
scene.frame_set(1)
OUT.parent.mkdir(parents=True,exist_ok=True); PREVIEW.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(PREVIEW); scene.frame_set(1)
bpy.ops.render.render(write_still=True)
print('RIG_SAVED',OUT); print('PREVIEW_RENDERED',PREVIEW); print('frames',END_FRAME,'bones',len(rook.data.bones),len(nib.data.bones))
