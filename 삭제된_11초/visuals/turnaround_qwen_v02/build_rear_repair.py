from pathlib import Path
import json
import copy

base = Path(__file__).resolve().parent
w = json.loads((base/'workflows/CHAR_01_turnaround_HQ.json').read_text(encoding='utf-8'))
n = {x['id']:x for x in w['nodes']}
prompt = '''Using image one as the rear-view edit target and image two as a close detail of the original gray wrist orthosis, change only the exposed LEFT wrist in the rear-view photograph: add the matching gray structured soft wrist brace with fastening straps and thumb opening. This is the wrist on the LEFT SIDE OF THE IMAGE of the woman seen from behind. The rear-view image-left forearm must clearly wear the gray brace from the sleeve edge down over the wrist, while the image-right wrist remains completely bare. Match the original orthosis shape, texture and gray color in image two, rotated naturally to its back-facing side. Keep the rear head, long black hair, body size, oatmeal cotton top, loose charcoal trousers, bare heels, pose, skin tone, background and lighting exactly as in image one. Keep the entire rear-view body in the same pixel positions and scale. Add the single brace, no other changes, no text or watermark.'''
n[7]['widgets_values'] = ['CHAR_01_서윤_turnaround_v02_HQ.png','image']
n[34]['widgets_values'] = [640,1536,1280,0]
n[34]['title'] = 'Rear panel from generated HQ sheet'
n[10]['widgets_values'][3:5] = [640,1536]
n[4]['widgets_values'][2:] = [640,1536]
n[16]['widgets_values'] = [prompt,'',0]
n[22]['widgets_values'] = ['deleted_11s_turnaround/CHAR_01_v02_HQ_repaired']
load = copy.deepcopy(n[7]);load.update(id=35,title='Original confirmed casting A',pos=[50,650]);load['widgets_values']=['D11_CHAR_01_FINAL.png','image']
crop = copy.deepcopy(n[34]);crop.update(id=36,title='Original wrist brace detail',pos=[430,850]);crop['widgets_values']=[160,240,630,640]
composite={'id':37,'type':'ImageCompositeMasked','pos':[1330,600],'size':[290,230],'flags':{},'order':15,'mode':0,
 'title':'Replace rear panel; other three views unchanged',
 'inputs':[{'name':'destination','type':'IMAGE','link':None},{'name':'source','type':'IMAGE','link':None},
 {'name':'x','type':'INT','widget':{'name':'x'},'link':None},{'name':'y','type':'INT','widget':{'name':'y'},'link':None},
 {'name':'resize_source','type':'BOOLEAN','widget':{'name':'resize_source'},'link':None},{'name':'mask','type':'MASK','shape':7,'link':None}],
 'outputs':[{'name':'IMAGE','type':'IMAGE','links':[]}],'properties':{'Node name for S&R':'ImageCompositeMasked'},'widgets_values':[1280,0,False]}
w['nodes']=[x for x in w['nodes'] if x['id']!=11]+[load,crop,composite]
n={x['id']:x for x in w['nodes']}
for node in w['nodes']:
 for x in node.get('inputs',[]):x['link']=None
 for x in node.get('outputs',[]):x['links']=[]
w['links']=[]
def wire(a,slot,b,name,kind):
 target=next(i for i,x in enumerate(n[b]['inputs']) if x['name']==name)
 lid=len(w['links'])+1
 n[a]['outputs'][slot]['links'].append(lid)
 n[b]['inputs'][target]['link']=lid
 w['links'].append([lid,a,slot,b,target,kind])
for a,slot,b,name,kind in [
 (1,0,3,'model','MODEL'),(3,0,4,'model','MODEL'),(4,0,20,'model','MODEL'),
 (10,1,4,'width','INT'),(10,2,4,'height','INT'),(31,0,16,'clip','CLIP'),
 (6,0,16,'vae','VAE'),(6,0,21,'vae','VAE'),(7,0,34,'image','IMAGE'),
 (35,0,36,'image','IMAGE'),(34,0,16,'images.image_1','IMAGE'),(36,0,16,'images.image_2','IMAGE'),
 (16,0,20,'positive','CONDITIONING'),(16,1,20,'negative','CONDITIONING'),(16,2,20,'latent_image','LATENT'),
 (20,0,21,'samples','LATENT'),(7,0,37,'destination','IMAGE'),(21,0,37,'source','IMAGE'),(37,0,22,'images','IMAGE')]:wire(a,slot,b,name,kind)
w['last_node_id']=37;w['last_link_id']=len(w['links'])
(base/'workflows/CHAR_01_rear_brace_repair.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
(base/'prompts/CHAR_01_rear_brace_repair.txt').write_text(prompt,encoding='utf-8')
