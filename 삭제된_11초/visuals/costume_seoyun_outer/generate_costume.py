"""삭제된 11초 — 서윤 외투·운동화 착용 상태 참조 (COSTUME_01B).

사용자 확정(2026-10-06): LOOK 1 카멜 울 롱코트(원본 길이) + LOOK 3 흰색 끈 운동화, 가방 제외.
확정 서윤 v02 턴어라운드와 같은 Qwen 파이프라인(2560x1536, 60 steps, CFG 1, Euler/simple, cpu/default,
빈 latent에서 네 방향 생성)을 쓰고 참조만 바꾼다. 크롭·축소는 ComfyUI 노드가 수행한다.

참조 슬롯:
  image_1 = 확정 서윤 턴어라운드(...v02_HQ_repaired.png), ImageScaleBy 0.75 → 1920x1152 (토큰 수 절감)
  image_2 = 사용자 시안 LOOK 1 패널 크롭(코트 디자인; 얼굴·가방·로퍼는 쓰지 않음)
  image_3 = 사용자 시안 LOOK 3 운동화 제품 크롭
  image_4 = 확정 캐스팅 A 원본의 얼굴 크롭(384x384, x=320, y=0; v02와 동일)

사용: python generate_costume.py [--seed N] [--tag a]
"""
from pathlib import Path
import sys, json, hashlib, struct, time, uuid, urllib.request, urllib.parse, argparse

ROOT = Path(__file__).resolve().parent
VIS = ROOT.parent
sys.path.insert(0, str(VIS / 'locations_qwen_v01'))
import generate_locations as g  # noqa: E402  (upload/post/get 재사용)

for sub in ['outputs', 'prompts', 'api']:
    (ROOT / sub).mkdir(exist_ok=True)

W, H, STEPS = 2560, 1536, 60
TEMPLATE_WF = VIS / 'turnaround_qwen_v02/workflows/CHAR_01_turnaround_HQ.json'  # 모델·인코더·샘플링 이름의 출처
REFS = {
    'turnaround': VIS / 'turnaround_qwen_v02/outputs/CHAR_01_서윤_turnaround_v02_HQ_repaired.png',
    'lookbook': ROOT / 'USER_LOOKBOOK_4LOOKS.webp',
    'casting': VIS / 'turnaround_qwen_v02/references/D11_CHAR_01_FINAL.png',
}
CROPS = {  # (x, y, w, h) — USER_LOOKBOOK_4LOOKS.webp 1448x1086 / D11_CHAR_01_FINAL.png 1024x1536
    'look1_coat': (0, 0, 360, 705),      # LOOK 1 전신 패널, 로퍼 위에서 자름
    'look3_sneaker': (912, 876, 150, 134),  # LOOK 3 흰색 운동화 제품 사진
    'face': (320, 0, 384, 384),
}

PROMPT = (
"Image one is the approved four-view character turnaround of this woman; it fixes her identity, face, long black hair, body proportions, "
"oatmeal cotton top, loose charcoal trousers, the gray wrist brace on her anatomical LEFT wrist, the four-view layout, studio lighting and backdrop. "
"Image four is a close crop of the SAME woman's original head and only reinforces her face and hair. "
"Image two is a styling reference used ONLY for the long camel wool coat; ignore that model's face, her handbag and her black loafers. "
"Image three is a product photo used ONLY for the white lace-up sneakers. "
"Generate a new photographic turnaround of the same woman from image one, now dressed for going outside: show exactly four separate full-body views in one horizontal row "
"in the same order, spacing, floor baseline and body scale as image one: front, strict profile facing the left edge, straight rear, strict profile facing the right edge. "
"Keep every head and foot inside the frame. "
"She wears the camel wool coat from image two over her unchanged oatmeal top and charcoal trousers: a long single-breasted camel coat in soft brushed wool with a fine visible nap, "
"notched lapels, dropped shoulders, side welt pockets, worn open and unbelted. The coat is very long, exactly as long as in image two: its hem reaches down to the ankles in every view, "
"so only a narrow band of charcoal trouser leg shows between the coat hem and the sneakers; it is not a knee-length or mid-calf coat. "
"The open front shows the oatmeal top and the charcoal trousers between the coat panels. From behind, her long black hair falls over the coat's back down to mid-back, "
"and the coat back shows a plain center seam and the long hem. "
"On her feet are the plain white leather lace-up low-top sneakers from image three, with white laces and flat white soles; the loose charcoal trouser hems rest on them. "
"No bag, no strap, no handbag, no loafers, no socks visible, no belt, no scarf, no jewelry, no hat. "
"The gray structured wrist brace with its straps and thumb opening stays on her anatomical LEFT wrist only. Both coat sleeves end at the wrist bone, and the brace on the left forearm "
"is clearly visible below the left coat cuff in three views: in the FRONT view on the wrist at the image-right side, in the REAR view on the wrist at the image-left side, "
"and in the left-facing profile on the near arm. In the right-facing profile that arm is hidden behind the body. Her anatomical right wrist stays bare in every view. "
"Arms rest alongside the body, hands visible and relaxed, not in pockets. "
"The front-view facial geometry, eye spacing and shape, nose, lips, jaw, head size, hairline, thin wispy bangs and skin tone must match image one and image four, "
"without beautifying, slimming, recasting or changing age; calm neutral expression. Keep the original soft studio lighting and the pale warm-gray backdrop of image one. "
"Preserve individual hair strands, natural skin texture, the wool nap and seams of the coat, fabric folds and sneaker edges with clear focused detail, "
"without painterly smoothing or artificial sharpening. No text, labels or watermark."
)


def _wf_names():
    w = json.loads(TEMPLATE_WF.read_text(encoding='utf-8-sig'))
    n = {x['id']: x for x in w['nodes']}
    return {'unet': n[1]['widgets_values'][0], 'vae': n[6]['widgets_values'][0], 'clip': n[31]['widgets_values'][0],
            'max_shift': n[4]['widgets_values'][0], 'base_shift': n[4]['widgets_values'][1]}


def build(out_name, seed, up):
    nm = _wf_names()
    c = CROPS
    api = {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': nm['unet'], 'weight_dtype': 'default'}},
        '3': {'class_type': 'QwenImage21Cache', 'inputs': {'model': ['1', 0], 'device': 'cpu', 'dtype': 'default'}},
        '4': {'class_type': 'ModelSamplingFlux', 'inputs': {'model': ['3', 0], 'max_shift': nm['max_shift'], 'base_shift': nm['base_shift'], 'width': W, 'height': H}},
        '6': {'class_type': 'VAELoader', 'inputs': {'vae_name': nm['vae']}},
        '31': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': nm['clip'], 'type': 'qwen_image', 'device': 'default'}},
        '11': {'class_type': 'EmptyLatentImage', 'inputs': {'width': W, 'height': H, 'batch_size': 1}},
        '7': {'class_type': 'LoadImage', 'inputs': {'image': up['turnaround']}},
        '40': {'class_type': 'ImageScaleBy', 'inputs': {'image': ['7', 0], 'upscale_method': 'lanczos', 'scale_by': 0.75}},
        '8': {'class_type': 'LoadImage', 'inputs': {'image': up['lookbook']}},
        '41': {'class_type': 'ImageCrop', 'inputs': {'image': ['8', 0], 'x': c['look1_coat'][0], 'y': c['look1_coat'][1], 'width': c['look1_coat'][2], 'height': c['look1_coat'][3]}},
        '42': {'class_type': 'ImageCrop', 'inputs': {'image': ['8', 0], 'x': c['look3_sneaker'][0], 'y': c['look3_sneaker'][1], 'width': c['look3_sneaker'][2], 'height': c['look3_sneaker'][3]}},
        '9': {'class_type': 'LoadImage', 'inputs': {'image': up['casting']}},
        '34': {'class_type': 'ImageCrop', 'inputs': {'image': ['9', 0], 'x': c['face'][0], 'y': c['face'][1], 'width': c['face'][2], 'height': c['face'][3]}},
        '16': {'class_type': 'TextEncodeQwenImage21', 'inputs': {'clip': ['31', 0], 'vae': ['6', 0], 'prompt': PROMPT, 'negative_prompt': '', 'resolution': 0,
                                                                 'images.image_1': ['40', 0], 'images.image_2': ['41', 0], 'images.image_3': ['42', 0], 'images.image_4': ['34', 0]}},
        '20': {'class_type': 'KSampler', 'inputs': {'model': ['4', 0], 'positive': ['16', 0], 'negative': ['16', 1], 'latent_image': ['11', 0], 'seed': seed, 'steps': STEPS,
                                                    'cfg': 1, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': 1}},
        '21': {'class_type': 'VAEDecode', 'inputs': {'samples': ['20', 0], 'vae': ['6', 0]}},
        '22': {'class_type': 'SaveImage', 'inputs': {'images': ['21', 0], 'filename_prefix': 'deleted_11s_costume/' + out_name}},
    }
    (ROOT / 'prompts' / f'{out_name}.txt').write_text(PROMPT, encoding='utf-8')
    (ROOT / 'api' / f'{out_name}.json').write_text(json.dumps(api, ensure_ascii=False, indent=2), encoding='utf-8')
    return api


def load_record():
    p = ROOT / 'GENERATION_RECORD.json'
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return {'engine': 'local ComfyUI Desktop / Deno Qwen-Image 2.1 T2I + Edit (API graph copy; 원본 워크플로우 미수정)', 'date': '2026-10-06',
            'purpose': 'COSTUME_01B 서윤 외투·운동화 착용 상태 참조 턴어라운드',
            'settings': {'width': W, 'height': H, 'steps': STEPS, 'cfg': 1, 'sampler': 'euler', 'scheduler': 'simple', 'denoise': 1,
                         'cache': 'cpu/default', 'encoder_resolution': 0, 'image_1_scale': 0.75},
            'crops': CROPS, 'runs': []}


def main(seed, tag):
    out_name = 'CHAR_01_서윤_COSTUME_01B_turnaround' + (f'_{tag}' if tag else '')
    rec = load_record()
    up, refs = {}, {}
    for k, p in REFS.items():
        up[k] = g.upload(p)
        refs[k] = {'source': str(p.relative_to(VIS)), 'uploaded_name': up[k], 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    refs['slots'] = {'image_1': 'turnaround → ImageScaleBy 0.75', 'image_2': 'lookbook → ImageCrop look1_coat',
                     'image_3': 'lookbook → ImageCrop look3_sneaker', 'image_4': 'casting → ImageCrop face'}
    api = build(out_name, seed, up)
    r = g.post('/prompt', {'prompt': api, 'client_id': 'd11-costume-' + uuid.uuid4().hex, 'extra_data': {'extra_pnginfo': {'api_graph': api}}})
    entry = {'id': out_name, 'seed': seed, 'prompt_id': r['prompt_id'], 'node_errors': r.get('node_errors', {}), 'references': refs,
             'status': 'queued', 'visual_review': 'pending'}
    rec['runs'].append(entry)
    (ROOT / 'GENERATION_RECORD.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
    print('QUEUED', out_name, r['prompt_id'], flush=True)
    t0 = time.monotonic()
    while True:
        h = g.get('/history/' + r['prompt_id']).get(r['prompt_id'])
        if h:
            if h.get('status', {}).get('status_str') == 'error':
                entry.update(status='failed', error=h.get('status'))
                (ROOT / 'GENERATION_RECORD.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
                raise RuntimeError(entry['error'])
            imgs = h.get('outputs', {}).get('22', {}).get('images', [])
            if imgs:
                blob = urllib.request.urlopen(g.BASE + '/view?' + urllib.parse.urlencode(imgs[0]), timeout=120).read()
                out = ROOT / 'outputs' / f'{out_name}.png'
                out.write_bytes(blob)
                entry.update(status='generated', output=f'outputs/{out_name}.png', actual_size=list(struct.unpack('>II', blob[16:24])),
                             elapsed_seconds=round(time.monotonic() - t0, 1), sha256=hashlib.sha256(blob).hexdigest())
                (ROOT / 'GENERATION_RECORD.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
                print('SAVED', out, entry['actual_size'], entry['elapsed_seconds'], 's', flush=True)
                return
        time.sleep(5)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=2026100601)
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    main(a.seed, a.tag)
