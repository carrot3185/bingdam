import generate_locations as g
import json, urllib.request, urllib.parse, uuid, hashlib, struct, time

TASKS = [
 ('HOME_REVERSE_v02','HOME_REVERSE', '''Move the gray entrance door with its existing handle and digital lock from the wall left of the tiled entry recess to the blank gray rear wall inside that recess, centered directly at the end of the wooden-floor approach and gray tiled shoe-removal area. Replace the old door and old frame on the left with continuous plain ivory wall matching the surrounding wall. Keep exactly one apartment entrance door. Keep the ivory shoe cabinet inside the tiled vestibule, along its left side, with two pairs of shoes beside it clear of the approach. Preserve the original camera view, sofa on the left, dining table and kitchen on the right, all furniture designs, floor, pendant, quiet evening lighting and every other part of the room. This is a targeted architectural correction, not a new apartment design. The doorway must terminate the recessed vestibule so the escape route has a clear readable destination. No people, captions or watermark.'''),
 ('LOC_02_KITCHEN_v02','HOME_MASTER', '''Generate a genuinely different camera position inside the existing kitchen shown on the left of this apartment, looking out toward the dining area and far living room. Recompose the entire photographic view from behind the actual kitchen sink and worktop, not from the entrance passage. The camera now stands at adult eye height in the left kitchen, looking diagonally right across its low gray counter. In the lower-left foreground show the existing sink edge, a metal faucet and one plain saucepan on the counter. At the near left edge show part of the original ivory kitchen cabinetry, without introducing another kitchen or counter in the entry passage. The pale oak table with exactly four chairs, the original closed silver laptop, water glass and cream pendant occupies the middle-right distance. The gray-brown sofa and the original curtained blue evening window are farther back, smaller because they are more distant. The countertop and furniture overlap naturally, and the table remains visible from the cooking position. Keep the original apartment's materials, room dimensions, furniture designs and calm evening light. Strong separation of near worktop, mid-distance table and far sofa/window, with physically believable perspective and readable flooring between them. No people, high island, captions or watermark.''')
]

def main():
    dest=g.ROOT/'REFINEMENTS.json'
    rec=json.loads(dest.read_text(encoding='utf-8')) if dest.exists() else {'purpose':'Observed location corrections','runs':[]}
    rec['status']='in progress'
    for cid,src,prompt in TASKS:
        if any(x['id']==cid and x['status']=='generated' for x in rec['runs']): continue
        path=g.ROOT/'outputs'/f'{src}.png'
        reference=g.upload(path)
        g.PROMPTS[cid]=prompt
        api,w,seed=g.build(cid,reference)
        r=g.post('/prompt',{'prompt':api,'client_id':'d11-refine-'+uuid.uuid4().hex,'extra_data':{'extra_pnginfo':{'workflow':w}}})
        run={'id':cid,'source':str(path),'reference_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'uploaded_name':reference,'actual_destination':'16 images.image_1','prompt_id':r['prompt_id'],'seed':seed,'node_errors':r.get('node_errors',{}),'status':'queued','visual_review':'pending'}
        rec['runs'].append(run);dest.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
        print('REFINEMENT QUEUED',cid,r['prompt_id'],flush=True)
        while True:
            h=g.get('/history/'+r['prompt_id']).get(r['prompt_id'])
            if h:
                if h.get('status',{}).get('status_str')=='error':
                    run['status']='failed';run['error']=h['status'];dest.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8');raise RuntimeError(h['status'])
                imgs=h.get('outputs',{}).get('22',{}).get('images',[])
                if imgs:
                    blob=urllib.request.urlopen(g.BASE+'/view?'+urllib.parse.urlencode(imgs[0]),timeout=60).read()
                    target=g.ROOT/'outputs'/f'{cid}.png';target.write_bytes(blob)
                    run.update(status='generated',output=str(target),actual_size=list(struct.unpack('>II',blob[16:24])),sha256=hashlib.sha256(blob).hexdigest())
                    dest.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8');print('REFINEMENT SAVED',cid,flush=True);break
            time.sleep(5)
    rec['status']='generated; visual review pending';dest.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__': main()
