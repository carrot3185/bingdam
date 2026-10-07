from pathlib import Path
import copy, json, urllib.request, urllib.parse, uuid, hashlib, struct, time

ROOT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8188'
TEMPLATE = ROOT.parents[2] / 'experiments/emotional_acting_01/workflows/Qwen_Emotion_AB_00_T2I.json'
# Use the already tested copy of the user's Deno Qwen T2I + Edit workflow.
TEMPLATE = Path('D:/work/Youtube/New_롱폼/experiments/emotional_acting_01/workflows/Qwen_Emotion_AB_00_T2I.json')
for sub in ['outputs', 'prompts', 'workflows', 'api', 'references']:
    (ROOT/sub).mkdir(parents=True, exist_ok=True)
COMMON = ' Empty unoccupied location, no people, no family photographs, no captions or watermark. Realistic architectural proportions, straight vertical walls, natural rectilinear perspective without fisheye distortion. Tactile matte surfaces and believable light, photographic Korean domestic drama location reference, not a furniture showroom or luxury property.'
PROMPTS = {
 'HOME_MASTER': '''The image is a wide cinematic interior photograph of an ordinary lived-in modern Korean apartment at early evening, with ivory walls, pale oak flooring and matte furniture. The camera stands just inside the short entrance passage at adult eye height, looking diagonally across the connected kitchen, dining area and living room, with the room filling the frame. On the near left edge, a partial ivory passage wall and a small section of the gray entry tile frame the view. On the left midground, an open L-shaped kitchen has matte ivory cabinets, light gray countertops and modest plain appliances, without a high island. Ahead of the kitchen stands one pale oak rectangular dining table with exactly four simple chairs and one cream pendant lamp above it. A closed plain silver laptop and one clear water glass sit unobtrusively on the table. On the right midground, a low gray-brown fabric sofa faces inward toward the living area; a small low oak coffee table stands nearby. At the far end, a broad apartment window with thin off-white curtains reveals dim blue evening sky. A clear continuous floor path runs from the near entrance beside the dining table into the living room. Overlapping doorway edges, furniture at distinct distances and floorboards converging toward the far window create readable foreground, middle distance and background; the room feels moderately sized and habitable, with space for two actors to move. Soft cool evening light enters from the far window, balanced by the warm diffuse dining pendant, leaving gently modeled corners and readable shadows. The overall palette is calm ivory, pale wood and muted gray, quietly ordinary with a hint of tension.'''+COMMON,
 'HOME_REVERSE': '''Using the apartment in the image as the actual architecture, material, furniture and lighting reference, generate a new photographic reverse view from near the far living-room window toward the original entrance. Rotate the viewpoint through the same physical apartment; preserve the room topology and furniture identities. The camera is at adult eye height, the broad room fills the frame, and no exterior window is visible behind the entrance. The gray-brown sofa now occupies the near left side and the pale oak dining table with its four chairs, closed silver laptop, water glass and cream pendant stands to the right of the central walkway. The open ivory kitchen remains behind the dining area on the right side of this reverse view. At the back center, a short entry passage leads to a recessed gray tiled shoe-removal vestibule and one gray apartment entrance door, with a matte ivory shoe cabinet beside it. Show the entry door handle and interior digital lock mounted on the door itself. Foreground sofa edge and table edge, middle-distance dining chairs and kitchen opening, and the far recessed entry form three distinct distance layers. The path from the table to the door remains continuous, wide enough for actor movement and free from furniture. Warm pendant light and cool evening light from behind the camera belong to the same evening as the reference. Preserve the same modest lived-in apartment, not a mirrored duplicate or a redesigned home.'''+COMMON,
 'LOC_02_KITCHEN': '''Using the apartment in the image as the actual connected room reference, generate a photographic view from inside its open ivory kitchen looking across the gray counter toward the dining table and living room. Preserve the existing apartment layout, materials, table, four chairs, pendant, sofa and far curtain window; only move the camera into the kitchen. The camera is at adult standing eye height, with a partial countertop edge and one plain saucepan in the lower foreground. The counter never becomes a high island and never blocks the sightline to a seated actor at the near short end of the dining table. In the middle distance, the pale oak table, closed silver laptop and water glass are visible through the unobstructed kitchen opening. Farther away, the low gray-brown sofa and cool evening window give the room depth. The entry-side end of the table has a visible free path leading out toward the entrance passage. Cabinet edges and counter lines recede naturally; foreground counter, middle-distance dining and far living room remain individually readable and in architectural focus. Warm diffused pendant light and weak cool window light match the reference. This is the same ordinary small-to-medium Korean home, with practical visibility between cooking and dining.'''+COMMON,
 'LOC_03_ENTRY': '''Using the apartment in the image as the architecture and material reference, generate a photographic location view from its dining-side passage toward the recessed shoe-removal vestibule and gray entrance door. Keep the same ivory walls, pale oak flooring, gray tiled entry patch, modest proportions and warm domestic lighting. The camera is at adult eye height, several steps back from the door, framing the passage and full vestibule with enough readable floor for two adults to stand and one to reach the handle. In the near foreground, the edge of the pale oak dining table and one chair partially enter the frame. The wooden floor walkway recedes into the middle distance and meets a shallow threshold at the pale gray entry tiles. At the back, one plain gray metal apartment door has one handle and its interior digital lock fitted directly on the door leaf, not on the wall. A matte ivory shoe cabinet stands along one vestibule side. Two pairs of simple shoes rest tidily beside the cabinet, outside the central passage. The door is closed; it will open outward into the communal corridor. Do not add a bag or discarded props yet. Warm living-room light comes from behind the camera while a soft neutral vestibule ceiling light keeps the lock and surrounding wall readable. Overlapping near table edge, passage walls and recessed door create a strong sense of connected depth without turning the entry into a spacious lobby.'''+COMMON,
 'LOC_04_CORRIDOR': '''The image is a wide realistic cinematic photograph of a short indoor communal corridor on an ordinary modern Korean apartment floor at night, with light gray walls and matte dark gray flooring. The camera stands at adult eye height a few steps from the couple's apartment entrance, looking diagonally toward the nearby elevator lobby so the entry-to-elevator route is clear. On the near left side is one gray apartment door opened outward, revealing a sliver of warm ivory interior and gray entry tiles; its inner digital lock and handle belong on the door leaf. In the middle distance a clear corridor extends only several walking steps to a small elevator alcove on the right, not a long hotel hallway. One brushed stainless steel elevator doorway is visible with closed doors and one call panel beside it. A partial foreground wall edge, the apartment doorway, receding floor joints and distant elevator recess create three visible layers of depth. Leave usable standing areas next to the apartment doorway and farther toward the elevator so actors can be separated. Sparse ordinary building finishes, no luxury marble or excessive decoration. Even neutral-white ceiling fixtures repeat down the short corridor, with a soft warm spill from the open apartment, making the spaces belong to the same residential building. The mood is clear and ordinary with restrained nighttime tension; no crowd, police, residents, dramatic fog or blue horror lighting.'''+COMMON,
 'LOC_05_ELEVATOR': '''Using the corridor in the image as the actual elevator doorway, building material and lighting reference, generate a new photographic location view from just outside that same elevator looking into its open cabin. Preserve the same brushed steel frame, gray corridor floor and neutral-white ceiling illumination. The camera stands at adult eye height about one step outside the threshold and shows the full door opening, both jambs and cabin interior; the near corridor floor, steel threshold and back cabin wall create clear depth. Inside is one modest ordinary apartment elevator with matte stainless steel walls, a plain gray floor and a softly lit ceiling, large enough for two adults but not a hotel freight lift. The control panel is mounted on the right interior wall immediately past the doorway so a person entering can use their right hand. Buttons are physically plausible, small and unobtrusive, without emphasized text or invented readable signage. Avoid a large mirror or mirror illusion of duplicate cabins. The cabin is empty with no reflections of people. Preserve the quiet practical residential appearance rather than redesigning the building.'''+COMMON,
 'LOC_06_GARAGE': '''The image is a wide realistic vehicle dashcam still of an ordinary Korean apartment underground parking garage, viewed from a fixed camera inside a parked car looking forward through its front windshield. The camera is mounted near the upper center of the windshield, slightly elevated above the dashboard, and the garage fills most of the frame. A narrow softly visible dark dashboard and windshield base occupy the bottom foreground without obscuring the space ahead; no steering wheel or driver is visible. In the middle distance, leave an open lit floor area immediately in front of the car where two adult actors can later stand, with clear visibility at head height. On both sides, gray concrete columns and parked everyday vehicles create overlapping depth; those cars stay to the sides, never blocking the space directly in front. Parking lane markings and regularly spaced columns recede toward the background. A low concrete ceiling has ordinary exposed utility pipes and white ceiling lights, with believable garage proportions and no cathedral scale. Neutral white overhead light makes the prospective standing area readable, with gentle darker corners and modest reflections on the concrete floor. The image has restrained dashcam compression and limited dynamic range, but structural detail remains understandable. No timestamp, recording icon, license-plate close-up, visible faces, collision, wreckage or crime props. Keep a fixed forward windshield perspective rather than an exterior movie-camera shot.'''
}
TITLES = {'HOME_MASTER':'집 전체 · 현관에서 거실', 'HOME_REVERSE':'집 역방향 · 거실에서 현관', 'LOC_02_KITCHEN':'주방에서 식탁·거실', 'LOC_03_ENTRY':'현관과 출구', 'LOC_04_CORRIDOR':'복도와 엘리베이터 동선', 'LOC_05_ELEVATOR':'엘리베이터 내부', 'LOC_06_GARAGE':'블랙박스 시점 지하주차장'}

def get(path):
    return json.load(urllib.request.urlopen(BASE+path, timeout=30))
def post(path, obj):
    req=urllib.request.Request(BASE+path,json.dumps(obj).encode(),{'Content-Type':'application/json'})
    try:
        return json.load(urllib.request.urlopen(req,timeout=60))
    except urllib.error.HTTPError as e:
        raise RuntimeError(e.read().decode()) from e
def upload(path):
    boundary='D11'+uuid.uuid4().hex
    blob=path.read_bytes()
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{path.name}"\r\nContent-Type: image/png\r\n\r\n'.encode()+blob+f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="type"\r\n\r\ninput\r\n--{boundary}\r\nContent-Disposition: form-data; name="overwrite"\r\n\r\nfalse\r\n--{boundary}--\r\n'.encode())
    req=urllib.request.Request(BASE+'/upload/image',body,{'Content-Type':'multipart/form-data; boundary='+boundary})
    r=json.load(urllib.request.urlopen(req,timeout=60))
    return (r.get('subfolder','')+'/' if r.get('subfolder') else '')+r['name']

def build(cid, reference=None):
    index=list(PROMPTS).index(cid)
    seed=202610051100+index
    text=PROMPTS[cid]
    w=json.loads(TEMPLATE.read_text(encoding='utf-8-sig'))
    n={x['id']:x for x in w['nodes']}
    for node in w['nodes']: node.pop('widgets_values_named',None)
    n[3]['widgets_values']=['cpu','default']
    n[10]['widgets_values']=['Manual Input','16:9',2.36,2048,1152,'32','Center Crop (Fill)','lanczos',.5,.5,1]
    n[11]['widgets_values']=[2048,1152,1]
    n[4]['widgets_values'][2:]=[2048,1152]
    n[16]['widgets_values']=[text,'',1536 if reference else 1024]
    n[20]['widgets_values']=[seed,'fixed',40,1,'euler','simple',1]
    n[22]['widgets_values']=['deleted_11s_locations_v01/'+cid]
    n[7]['mode']=0 if reference else 4
    if reference: n[7]['widgets_values']=[reference,'image']
    api={
      '1':{'class_type':'UNETLoader','inputs':{'unet_name':n[1]['widgets_values'][0],'weight_dtype':'default'}},
      '3':{'class_type':'QwenImage21Cache','inputs':{'model':['1',0],'device':'cpu','dtype':'default'}},
      '4':{'class_type':'ModelSamplingFlux','inputs':{'model':['3',0],'max_shift':n[4]['widgets_values'][0],'base_shift':n[4]['widgets_values'][1],'width':['10',1],'height':['10',2]}},
      '6':{'class_type':'VAELoader','inputs':{'vae_name':n[6]['widgets_values'][0]}},
      '31':{'class_type':'CLIPLoader','inputs':{'clip_name':n[31]['widgets_values'][0],'type':'qwen_image','device':'default'}},
      '10':{'class_type':'DenoResolutionSetup','inputs':dict(zip(['mode','ratio_preset','megapixels','width','height','divisible_by','resize_method','interpolation','crop_x','crop_y','crop_zoom'],n[10]['widgets_values']))},
      '11':{'class_type':'EmptyLatentImage','inputs':{'width':['10',1],'height':['10',2],'batch_size':1}},
      '16':{'class_type':'TextEncodeQwenImage21','inputs':{'clip':['31',0],'vae':['6',0],'prompt':text,'negative_prompt':'','resolution':1536 if reference else 1024}},
      '20':{'class_type':'KSampler','inputs':{'model':['4',0],'positive':['16',0],'negative':['16',1],'latent_image':['11',0],'seed':seed,'steps':40,'cfg':1,'sampler_name':'euler','scheduler':'simple','denoise':1}},
      '21':{'class_type':'VAEDecode','inputs':{'samples':['20',0],'vae':['6',0]}},
      '22':{'class_type':'SaveImage','inputs':{'images':['21',0],'filename_prefix':n[22]['widgets_values'][0]}}
    }
    if reference:
        api['7']={'class_type':'LoadImage','inputs':{'image':reference}}
        api['16']['inputs']['images.image_1']=['7',0]
    (ROOT/'prompts'/f'{cid}.txt').write_text(text,encoding='utf-8')
    (ROOT/'workflows'/f'{cid}.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'api'/f'{cid}.json').write_text(json.dumps(api,ensure_ascii=False,indent=2),encoding='utf-8')
    return api,w,seed

def save(record):
    (ROOT/'GENERATION_RECORD.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
    record={'engine':'local ComfyUI Desktop / Deno Qwen-Image 2.1 T2I + Edit','date':'2026-10-05','status':'in progress','design_status':'검토용 생성 시안; 사용자 확정 전','settings':{'width':2048,'height':1152,'steps':40,'cfg':1,'sampler':'euler','scheduler':'simple','cache':'cpu/default'},'runs':[]}
    save(record)
    for cid in PROMPTS:
        refcid='HOME_MASTER' if cid in ['HOME_REVERSE','LOC_02_KITCHEN','LOC_03_ENTRY'] else 'LOC_04_CORRIDOR' if cid=='LOC_05_ELEVATOR' else None
        refpath=ROOT/'outputs'/f'{refcid}.png' if refcid else None
        ref=upload(refpath) if refpath else None
        if refpath: (ROOT/'references'/f'{refcid}.png').write_bytes(refpath.read_bytes())
        api,w,seed=build(cid,ref)
        result=post('/prompt',{'prompt':api,'client_id':'d11-locations-'+uuid.uuid4().hex,'extra_data':{'extra_pnginfo':{'workflow':w}}})
        run={'id':cid,'title':TITLES[cid],'seed':seed,'prompt_id':result['prompt_id'],'node_errors':result.get('node_errors',{}),'reference':{'source':str(refpath),'uploaded_name':ref,'sha256':hashlib.sha256(refpath.read_bytes()).hexdigest(),'destination':'16 images.image_1'} if refpath else None,'status':'queued','visual_review':'pending'}
        record['runs'].append(run);save(record)
        print('QUEUED',cid,result['prompt_id'],flush=True)
        started=time.monotonic()
        while True:
            history=get('/history/'+result['prompt_id']).get(result['prompt_id'])
            if history:
                if history.get('status',{}).get('status_str')=='error':
                    run['status']='failed';run['error']=history.get('status');save(record);raise RuntimeError(run['error'])
                imgs=history.get('outputs',{}).get('22',{}).get('images',[])
                if imgs:
                    obj=imgs[0]
                    blob=urllib.request.urlopen(BASE+'/view?'+urllib.parse.urlencode(obj),timeout=60).read()
                    path=ROOT/'outputs'/f'{cid}.png';path.write_bytes(blob)
                    width,height=struct.unpack('>II',blob[16:24])
                    run.update(status='generated',output=str(path),server_output=obj,actual_size=[width,height],elapsed_seconds=round(time.monotonic()-started,1),sha256=hashlib.sha256(blob).hexdigest())
                    save(record);print('SAVED',cid,width,height,'seconds',run['elapsed_seconds'],flush=True);break
            time.sleep(5)
    record['status']='all images generated; visual review pending';save(record)
    print('ALL COMPLETE',flush=True)
if __name__=='__main__': main()
