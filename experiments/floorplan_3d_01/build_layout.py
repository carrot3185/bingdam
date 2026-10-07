"""Editable schematic reconstruction of the user-supplied floorplan. Run in Blender."""
import bpy, math, json, os
from mathutils import Vector, Quaternion

ROOT = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(ROOT, 'reference_floorplan.png')
HEIGHT = 2.60  # assumed; the supplied drawing has no elevation
CUT_HEIGHT = 1.10
SX, SY = 18.370/597.0, 15.520/503.0
def xy(p): return ((p[0]-157)*SX, (574-p[1])*SY)

# This script is intended for a separate background Blender process.
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
scene = bpy.context.scene
scene.name = '01_LAYOUT_CUTAWAY'
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene['reference_id'] = 'PLAN_REF_001'
scene['status'] = 'Image-traced draft; unmeasured vertical dimensions are assumptions.'
scene['wall_height_assumed_m'] = HEIGHT
collections = {}
for name in ['01_FLOORS','02_WALLS_LOWER','03_WALLS_UPPER','04_DOORS_LOWER','05_DOORS_UPPER','06_WINDOWS_LOWER','07_WINDOWS_UPPER','08_FIXTURES','09_LABELS','10_REFERENCE','11_PRESENTATION','12_CEILINGS_OPTIONAL']:
    c = bpy.data.collections.new(name); scene.collection.children.link(c); collections[name] = c

def material(name, color, roughness=.65):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=roughness
    return m
wallmat=material('Wall | warm white',(.83,.81,.75))
wood=material('Floor | schematic oak',(.56,.32,.13))
nodes=wood.node_tree.nodes; links=wood.node_tree.links
tc=nodes.new('ShaderNodeTexCoord'); wave=nodes.new('ShaderNodeTexWave'); wave.wave_type='BANDS'; wave.bands_direction='Y'; wave.inputs['Scale'].default_value=2.2
links.new(tc.outputs['Object'],wave.inputs['Vector'])
ramp=nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.08; ramp.color_ramp.elements[0].color=(.25,.115,.042,1); ramp.color_ramp.elements[1].position=.20; ramp.color_ramp.elements[1].color=(.64,.385,.19,1)
links.new(wave.outputs['Fac'],ramp.inputs[0]); links.new(ramp.outputs[0],nodes.get('Principled BSDF').inputs['Base Color'])
roommat=material('Bedroom | pale oak',(.76,.66,.45))
tile=material('Balcony | ivory tile',(.77,.74,.64))
bathmat=material('Bathroom | blue grey',(.48,.64,.67))
doormat=material('Door | light timber',(.55,.35,.18))
frame=material('Frames | white',(.90,.91,.86))
glass=material('Window | pale blue schematic glass',(.42,.66,.76),.23)
stone=material('Countertop | charcoal',(.19,.21,.20))
cabinet=material('Kitchen | taupe',(.44,.37,.29))
ceramic=material('Sanitary | porcelain',(.94,.95,.91),.22)
dark=material('Labels | charcoal',(.08,.105,.11))
base=material('Slab | concrete',(.36,.39,.40))
groundmat=material('Backdrop',(.89,.91,.91))

def link_object(o, collection): collections[collection].objects.link(o)
def box(name, loc, dims, mat, collection, bevel=0):
    dx,dy,dz=[v/2 for v in dims]
    vertices=[(x,y,z) for z in (-dz,dz) for y in (-dy,dy) for x in (-dx,dx)]
    faces=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(vertices,[],faces); mesh.update()
    o=bpy.data.objects.new(name,mesh); o.location=loc; link_object(o,collection); o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new('Soft edges','BEVEL'); mod.width=bevel; mod.segments=2
    return o

def polygon(name, points, z, thickness, mat, collection='01_FLOORS'):
    pts=[xy(p) for p in points]; n=len(pts)
    verts=[(x,y,h) for h in (z-thickness,z) for x,y in pts]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    o=bpy.data.objects.new(name,mesh); link_object(o,collection); o.data.materials.append(mat); o['reference_id']='PLAN_REF_001'; return o
def rect(name,x1,y1,x2,y2,mat,z=.015): return polygon(name,[(x1,y1),(x2,y1),(x2,y2),(x1,y2)],z,.04,mat)
def segment(name,a,b,z0,z1,width,mat,collection):
    aa,bb=Vector(xy(a)),Vector(xy(b)); mid=(aa+bb)/2; d=bb-aa
    o=box(name,(*mid,(z0+z1)/2),(d.length,width,z1-z0),mat,collection,.008)
    o.rotation_euler.z=math.atan2(d.y,d.x); return o
def wall(name,a,b,width=.19,z0=0,z1=HEIGHT):
    if z0<CUT_HEIGHT: segment(name+'_LOW',a,b,z0,min(z1,CUT_HEIGHT),width,wallmat,'02_WALLS_LOWER')
    if z1>CUT_HEIGHT: segment(name+'_HIGH',a,b,max(z0,CUT_HEIGHT),z1,width,wallmat,'03_WALLS_UPPER')

# Wall centerlines traced from the supplied bitmap, in original image pixels.
outline=[(161,313),(220,313),(220,226),(298,226),(298,148),(411,148),(411,125),(611,125),(611,71),(754,71),(754,375),(725,375),(725,574),(574,574),(574,590),(386,590),(386,574),(247,574),(242,582),(234,589),(220,593),(206,589),(196,582),(191,574),(161,574)]
polygon('SLAB_APARTMENT',outline,0,.22,base)
polygon('FLOOR_LIVING_KITCHEN_HALL',[(220,320),(414,320),(414,197),(611,197),(611,315),(574,315),(574,517),(389,517),(389,399),(220,399)],.01,.05,wood)
rect('ROOM_BED_01_SW',161,399,283,517,roommat)
rect('ROOM_BED_02_S',283,399,389,517,roommat)
rect('ROOM_BED_03_NW',298,197,414,320,roommat)
rect('ROOM_BED_04_NE',611,115,754,240,roommat)
rect('ROOM_BED_05_SE',574,375,725,537,roommat)
rect('ROOM_BATH_01_W',243,226,298,320,bathmat)
rect('ROOM_BATH_02_E',651,293,754,375,bathmat)
rect('ROOM_ENTRY',161,313,220,399,tile)
rect('ROOM_HALL_E',611,240,651,375,tile)
rect('ROOM_HALL_MID',574,315,611,375,tile)
polygon('ROOM_BALCONY_NW',[(298,148),(411,148),(411,125),(574,125),(574,197),(298,197)],.01,.04,tile)
rect('ROOM_BALCONY_NE',611,71,754,115,tile)
polygon('ROOM_BALCONY_S',[(161,517),(574,517),(574,537),(684,537),(684,574),(574,574),(574,590),(386,590),(386,560),(161,560)],.01,.04,tile)
rect('SERVICE_W',220,226,243,320,tile)
rect('SERVICE_NE',574,125,611,197,tile)
rect('SERVICE_SE',684,537,725,574,tile)

# Opening specification: actual widths follow the raster; height/sill are assumptions.
openings=[]
def partition(name,a,b,holes=(),width=.19):
    va,vb=Vector(a),Vector(b); delta=vb-va
    intervals=[]
    for kind,start,end in holes:
        intervals.append((start,end,kind))
    cursor=0
    for start,end,kind in sorted(intervals):
        if start>cursor: wall(name+f'_SEG_{cursor:.3f}',va+delta*cursor,va+delta*start,width)
        p,q=va+delta*start,va+delta*end
        if kind=='door':
            wall(name+'_LINTEL',p,q,width,2.10,HEIGHT)
        else:
            wall(name+'_SILL',p,q,width,0,.85); wall(name+'_LINTEL',p,q,width,2.20,HEIGHT)
        openings.append((name,kind,tuple(p),tuple(q))); cursor=end
    if cursor<1: wall(name+f'_SEG_{cursor:.3f}',va+delta*cursor,vb,width)
def horizontal(name,x1,x2,y,holes=(),width=.19):
    partition(name,(x1,y),(x2,y),[(k,(s-x1)/(x2-x1),(e-x1)/(x2-x1)) for k,s,e in holes],width)
def vertical(name,x,y1,y2,holes=(),width=.19):
    partition(name,(x,y1),(x,y2),[(k,(s-y1)/(y2-y1),(e-y1)/(y2-y1)) for k,s,e in holes],width)

# Exterior perimeter; entrance opening is in its upper horizontal edge.
for i,a in enumerate(outline):
    b=outline[(i+1)%len(outline)]
    if i==0: horizontal('EXT_ENTRY',161,220,313,[('door',181,211)],.25)
    else: wall(f'EXT_{i:02}',a,b,.25)
horizontal('BALCONY_NE',611,754,115,[('window',657,723)])
horizontal('BALCONY_NW',298,574,197,[('window',318,386),('window',430,496),('door',529,558)])
vertical('BED_NW_E',414,197,320)
vertical('BED_NW_W',298,226,320)
horizontal('BATH_BED_NW_DOORS',243,414,320,[('door',267,297),('door',303,333)])
vertical('SERVICE_BATH_W',243,226,320)
horizontal('BATH_W_N',243,298,226)
vertical('ENTRY_E',220,313,399)
horizontal('BED_S_N',161,389,399,[('door',250,279),('door',286,316)])
vertical('BED_S_DIV',283,399,517)
vertical('BED_S_E',389,399,560)
horizontal('BALCONY_S_N',161,574,517,[('window',183,250),('window',299,366),('window',427,534)])
vertical('LIVING_E',574,315,537,[('door',329,364)])
vertical('BED_NE_W',611,115,315,[('door',204,240)])
horizontal('BED_NE_S',611,754,240,[('window',681,747)])
horizontal('BATH_E_N',651,754,293)
vertical('BATH_E_W',651,293,375,[('door',314,344)])
horizontal('BED_SE_N',574,754,375,[('door',578,607)])
horizontal('BED_SE_S',574,725,537,[('window',596,662)])
vertical('SERVICE_NW_E',574,125,197)
horizontal('SERVICE_NW_DIV',574,611,171)
horizontal('BALCONY_S_SERVICE',161,389,560)
vertical('SERVICE_SE_W',684,537,574)

# Closets and small plumbing shafts shown as simple solid blocks.
for name,coords in [('Closet_SW',(164,379,236,398)),('Closet_S',(318,379,388,398)),('Bath_E_shaft',(653,295,682,311)),('Bath_W_shaft',(245,228,261,262))]:
    x1,y1,x2,y2=coords; p,q=xy((x1,y1)),xy((x2,y2)); box(name,((p[0]+q[0])/2,(p[1]+q[1])/2,.52),(abs(p[0]-q[0]),abs(p[1]-q[1]),1.04),cabinet,'08_FIXTURES',.018)

def part_split(name,a,b,mat,thickness,z0,z1,low_col,high_col):
    if z0<CUT_HEIGHT: segment(name+'_LOW',a,b,z0,min(CUT_HEIGHT,z1),thickness,mat,low_col)
    if z1>CUT_HEIGHT: segment(name+'_HIGH',a,b,max(CUT_HEIGHT,z0),z1,thickness,mat,high_col)
for i,(owner,kind,a,b) in enumerate(openings):
    if kind=='door':
        # Store a hinge pivot; schematic leaves open by 65 degrees, adjustable as objects.
        reversed_hinge = owner in ['EXT_ENTRY','BALCONY_NW','BATH_E_W'] or (owner=='BATH_BED_NW_DOORS' and a[0]<300) or (owner=='BED_S_N' and a[0]<280)
        turn = -65 if owner in ['EXT_ENTRY','BALCONY_NW','BATH_E_W','BED_SE_N'] or (owner=='BATH_BED_NW_DOORS' and a[0]<300) or (owner=='BED_S_N' and a[0]>280) else 65
        if reversed_hinge: a,b=b,a
        hinge=xy(a); end=xy(b); d=Vector(end)-Vector(hinge); angle=math.atan2(d.y,d.x)+math.radians(turn)
        aa=a; dest=(hinge[0]+d.length*math.cos(angle),hinge[1]+d.length*math.sin(angle))
        pp=(dest[0]/SX+157,574-dest[1]/SY)
        part_split(f'DOOR_{i:02}_{owner}',a,pp,doormat,.045,0,2.07,'04_DOORS_LOWER','05_DOORS_UPPER')
        for col in ['04_DOORS_LOWER','05_DOORS_UPPER']:
            for o in list(collections[col].objects)[-1:]:
                o['hinge_world_xy']=hinge; o['opening_width_m']=d.length; o['height_assumed_m']=2.1
                pivot=Vector((hinge[0],hinge[1],0)); offset=o.rotation_euler.to_matrix().inverted() @ (o.location-pivot)
                for v in o.data.vertices: v.co += offset
                o.location=pivot
    else:
        part_split(f'WINDOW_{i:02}',a,b,glass,.035,.88,2.17,'06_WINDOWS_LOWER','07_WINDOWS_UPPER')
        segment(f'WINDOW_{i:02}_SILL',a,b,.84,.90,.24,frame,'06_WINDOWS_LOWER')
        segment(f'WINDOW_{i:02}_TOP',a,b,2.17,2.22,.10,frame,'07_WINDOWS_UPPER')
        for t in [0,.5,1]:
            p=Vector(a)+(Vector(b)-Vector(a))*t; x,y=xy(p)
            for z0,z1,col in [(.90,CUT_HEIGHT,'06_WINDOWS_LOWER'),(CUT_HEIGHT,2.17,'07_WINDOWS_UPPER')]:
                box(f'WINDOW_{i:02}_MULLION', (x,y,(z0+z1)/2),(.06,.06,z1-z0),frame,col,.006)

# Kitchen L counter and sanitary fixture proxies correspond to the plan symbols.
def pixel_box(name,coords,z,h,mat,col='08_FIXTURES'):
    x1,y1,x2,y2=coords; p,q=xy((x1,y1)),xy((x2,y2)); return box(name,((p[0]+q[0])/2,(p[1]+q[1])/2,z),(abs(q[0]-p[0]),abs(q[1]-p[1]),h),mat,col,.022)
pixel_box('KITCHEN_CABINET_N_S',(589,197,609,306),.44,.88,cabinet)
pixel_box('KITCHEN_CABINET_RETURN',(515,293,589,315),.44,.88,cabinet)
pixel_box('KITCHEN_TOP_N_S',(588,197,612,307),.91,.06,stone)
pixel_box('KITCHEN_TOP_RETURN',(514,292,588,317),.91,.06,stone)
pixel_box('SINK',(546,295,565,311),.95,.025,ceramic)
pixel_box('SINK_INNER',(549,298,562,308),.965,.015,stone)
pixel_box('COOKTOP',(591,204,605,232),.96,.025,stone)
for j,y in enumerate([210,224]):
    xw,yw=xy((598,y)); bpy.ops.mesh.primitive_torus_add(major_radius=.14,minor_radius=.015,location=(xw,yw,.983)); o=bpy.context.object; o.name=f'COOKTOP_RING_{j}'
    for c in list(o.users_collection): c.objects.unlink(o)
    link_object(o,'08_FIXTURES'); o.data.materials.append(frame)
pixel_box('BATHTUB_E',(657,346,721,369),.25,.50,ceramic)
pixel_box('BATHTUB_INNER',(662,350,716,365),.505,.025,bathmat)
pixel_box('WASHBASIN_W',(248,271,274,293),.75,.10,ceramic)
pixel_box('WASHBASIN_W_INNER',(253,275,267,288),.806,.016,bathmat)
pixel_box('WC_W_PROXY',(248,294,265,313),.22,.44,ceramic)
pixel_box('WC_E_PROXY',(729,327,746,354),.22,.44,ceramic)

# Floor labels use a packed Korean font. They can be hidden as a collection.
fontpath='C:/Windows/Fonts/malgun.ttf'
font=bpy.data.fonts.load(fontpath) if os.path.exists(fontpath) else None
labels=[('침실 1',220,453),('침실 2',338,453),('침실 3',355,261),('침실 4',684,177),('침실 5',648,456),('거실',480,440),('주방 · 식당',499,249),('현관',190,350),('욕실',274,243),('욕실',704,324),('발코니',482,553),('발코니',492,163),('발코니',683,93)]
for text,x,y in labels:
    curve=bpy.data.curves.new('LABEL_'+text,'FONT'); curve.body=text; curve.align_x='CENTER'; curve.align_y='CENTER'; curve.size=.40; curve.extrude=.001
    if font: curve.font=font
    o=bpy.data.objects.new('LABEL_'+text,curve); o.location=(*xy((x,y)),.042); link_object(o,'09_LABELS'); curve.materials.append(dark)

image=bpy.data.images.load(REFERENCE); image.pack()
ref=bpy.data.objects.new('PLAN_REF_001 | source bitmap',None); ref.empty_display_type='IMAGE'; ref.data=image; ref.empty_display_size=910*SX; ref.location=xy((455,333))+( -.28,); ref.rotation_euler=(0,0,0); ref.hide_render=True; ref.hide_viewport=True; link_object(ref,'10_REFERENCE')
polygon('CEILING_OPTIONAL',outline,HEIGHT,.12,wallmat,'12_CEILINGS_OPTIONAL')
collections['12_CEILINGS_OPTIONAL'].hide_render=True; collections['12_CEILINGS_OPTIONAL'].hide_viewport=True

# A separate full-height scene shares the same editable geometry.
full=bpy.data.scenes.new('02_LAYOUT_FULL_HEIGHT'); full.unit_settings.system='METRIC'
for c in collections.values(): full.collection.children.link(c)
for key in ['03_WALLS_UPPER','05_DOORS_UPPER','07_WINDOWS_UPPER']:
    scene.view_layers[0].layer_collection.children[key].exclude=True

def setup(s):
    s.render.engine='BLENDER_EEVEE'; s.render.resolution_x=1500; s.render.resolution_y=1200; s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG'; s.render.film_transparent=False
    s.world=bpy.data.worlds.new(s.name+'_World'); s.world.use_nodes=True; s.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.82,.88,1); s.world.node_tree.nodes['Background'].inputs[1].default_value=.55
    s.view_settings.view_transform='AgX'
setup(scene); setup(full)
box('Presentation ground',(9,7.8,-.35),(27,27,.20),groundmat,'11_PRESENTATION',.08)
def camera(name,location,target,scale):
    data=bpy.data.cameras.new(name); data.type='ORTHO'; data.ortho_scale=scale
    o=bpy.data.objects.new(name,data); link_object(o,'11_PRESENTATION'); o.location=location; o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler(); return o
cam=camera('CAM_DOLLHOUSE',(28,-21,33),(9.3,7.5,.0),25.5)
top=camera('CAM_PLAN',(9.2,7.6,35),(9.2,7.6,0),21)
scene.camera=cam; full.camera=cam
for name,location,power,size in [('KEY',(4,-2,19),2200,12),('FILL',(22,15,16),1800,10)]:
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.shape='DISK'; data.size=size; o=bpy.data.objects.new(name,data); link_object(o,'11_PRESENTATION'); o.location=location; o.rotation_euler=(Vector((9,8,0))-o.location).to_track_quat('-Z','Y').to_euler()

notes='''PLAN_REF_001: user supplied bitmap. Image-traced layout draft, not a measured architectural model.
Units: metres. X anchored by 18,370 mm dimension, pixel x157..754.
Y anchored by 15,520 mm right dimension, pixel y71..574. Bottom centre balcony projects below that datum.
Wall height 2.60m, door height 2.10m, sill .85m, window head 2.20m and wall thickness .19/.25m are assumptions.
Room shapes, door swings and fixtures are approximate bitmap interpretations. Original vector/CAD and elevation absent.
01_LAYOUT_CUTAWAY excludes upper wall/door/window collections above 1.10m.
02_LAYOUT_FULL_HEIGHT includes all upper collections. Ceiling optional and hidden.
Doors, windows, fixtures and room floors are separate named objects. No beds or living furniture were specified.
'''
txt=bpy.data.texts.new('README_LAYOUT'); txt.write(notes)
bpy.context.window.scene=scene
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=26
            area.spaces.active.region_3d.view_location=(9.2,7.6,0)
            area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
            area.spaces.active.shading.type='MATERIAL'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'floorplan_layout_v01.blend'))
scene.render.filepath=os.path.join(ROOT,'layout_perspective.png'); bpy.ops.render.render(write_still=True)
scene.camera=top; scene.render.resolution_x=1300; scene.render.resolution_y=1300; scene.render.filepath=os.path.join(ROOT,'layout_top.png'); bpy.ops.render.render(write_still=True)
scene.camera=cam; scene.render.resolution_x=1500; scene.render.resolution_y=1200
# Keep the initial saved file intact; render camera was restored.
summary={'blender_version':bpy.app.version_string,'reference_id':'PLAN_REF_001','objects':len(bpy.data.objects),'scenes':[s.name for s in bpy.data.scenes],'assumed_wall_height_m':HEIGHT,'opening_count':len(openings),'bedrooms':5,'source_dimensions_m':{'bottom_width':18.370,'right_height_datum':15.520},'status':'draft_from_raster','outputs':['floorplan_layout_v01.blend','layout_perspective.png','layout_top.png']}
with open(os.path.join(ROOT,'model_summary.json'),'w',encoding='utf-8') as f: json.dump(summary,f,ensure_ascii=False,indent=2)
print(json.dumps(summary,ensure_ascii=False))
