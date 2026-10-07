from pathlib import Path
import json, struct, hashlib, re

root=Path(__file__).resolve().parent
checks=[]
for path in sorted((root/'outputs').glob('*.png')):
    blob=path.read_bytes();pos=8;metadata={}
    while pos<len(blob):
        length=struct.unpack('>I',blob[pos:pos+4])[0];typ=blob[pos+4:pos+8];data=blob[pos+8:pos+8+length];pos+=length+12
        if typ==b'tEXt':
            key,txt=data.split(b'\0',1)
            if key in [b'prompt',b'workflow']:metadata[key.decode()]=json.loads(txt)
    actual=metadata['prompt'];api=json.loads((root/'api'/f'{path.stem}.json').read_text(encoding='utf-8'))
    checks.append({'id':path.stem,'actual_dimensions':list(struct.unpack('>II',blob[16:24])),'submitted_inputs_equal_png_prompt':all(actual[k]['inputs']==v['inputs'] for k,v in api.items()),'actual_reference':actual.get('7',{}).get('inputs',{}).get('image'),'prompt_file_equal_actual':(root/'prompts'/f'{path.stem}.txt').read_text(encoding='utf-8')==actual['16']['inputs']['prompt'],'sha256':hashlib.sha256(blob).hexdigest()})
(root/'METADATA_CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print('Metadata checked:',len(checks),'images; all match:',all(x['submitted_inputs_equal_png_prompt'] and x['prompt_file_equal_actual'] for x in checks))
selected=['HOME_MASTER','HOME_REVERSE_v02','LOC_02_KITCHEN_v03','LOC_03_ENTRY','LOC_04_CORRIDOR','LOC_05_ELEVATOR','LOC_06_GARAGE_v02']
assert all((root/'outputs'/f'{x}.png').exists() for x in selected)
selection={'status':'generated, visually reviewed design proposals; not user-confirmed','selected_outputs':{x:'outputs/'+x+'.png' for x in selected},'actual_generation_count':len(checks),'selected_view_count':len(selected)}
(root/'SELECTION.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
html=(root/'index.html').read_text(encoding='utf-8').replace('LOC_02_KITCHEN_v02.png','LOC_02_KITCHEN_v03.png').replace('LOC_06_GARAGE.png','LOC_06_GARAGE_v02.png').replace('깊이와 식탁 시야를 보여주는 보완 시안이며, 뒤쪽에 남은 싱크대는 세트 통일 단계에서 정리할 부분입니다.','깊이와 식탁 시야를 보여주는 보완 시안. 중복 생성된 뒤쪽 싱크대를 제거한 결과이며, 가구 세부는 기준 뷰와 차이가 있습니다.')
(root/'index.html').write_text(html,encoding='utf-8')
for file in ['GENERATION_RECORD.json','REFINEMENTS.json']:
    obj=json.loads((root/file).read_text(encoding='utf-8'))
    for run in obj['runs']:run['visual_review']='completed; see README.md for observations and limitations'
    obj['status']='generated and visually reviewed; design proposal, not user-confirmed'
    (root/file).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
print('Selected views:',len(selected))
