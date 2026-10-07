"""삭제된 11초 — 경찰 A/B(CHAR_06/07) 캐스팅 + 턴어라운드 v01.

2026-10-06 사용자 요청: "서윤을 제외한 나머지 인물들도 턴어라운드 이미지 만들어줘."
도현·지수는 이미 사용자 확정 턴어라운드가 있으므로 다시 만들지 않는다. 화면에 실물로 나오는데 자산이 없는 경찰 A/B만 만든다.

1단계 cast : Qwen T2I 1024x1536 전신 기준 사진 (확정 캐스팅 원본과 같은 규격·배경)
2단계 turn : 선택한 기준 사진을 image_1, 같은 사진의 얼굴 크롭(ComfyUI ImageCrop)을 image_2로 실제 입력해
             turnaround_qwen_v02와 같은 옵션(2560x1536, 60 steps, encoder resolution 0, cpu cache)으로 4방향 생성

사용:
  python generate.py cast CHAR_06 --seed N [--tag a]
  python generate.py turn CHAR_06 --ref outputs/CHAR_06_cast_a.png --crop 320,0 [--seed N]
"""
from pathlib import Path
import sys, json, hashlib, struct, time, uuid, urllib.request, urllib.parse, argparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'locations_qwen_v01'))
import generate_locations as g  # noqa: E402  (upload/post/get, TEMPLATE = 검증된 사용자 Qwen 워크플로우 사본)

for sub in ['outputs', 'prompts', 'api']:
    (ROOT / sub).mkdir(parents=True, exist_ok=True)

STEPS = 60
VERSION = 'v01'

UNIFORM = ('Current-generation South Korean police patrol uniform for a cool autumn night call: a dark navy structured patrol cap with a small metallic police emblem; '
           'a dark navy zip-front patrol jacket with a stand collar, shoulder epaulettes, chest pockets, one small embroidered police shoulder patch on each upper sleeve, '
           'and a thin silver-gray reflective band around the chest, back and forearms; a small black body-worn camera clipped at the center of the chest; '
           'straight dark navy uniform trousers; a black duty belt with closed black pouches and a closed holster, no weapon drawn; plain black leather duty shoes. '
           'The uniform carries no readable lettering, name tag text or numbers. ')

CAST_COMMON = ('Make ONE full-length vertical studio photograph of one original fictional adult Korean character for the web drama "Deleted 11 Seconds", not a collage. '
               'Head, cap, body, both hands and both feet fully visible with clear margin, centered upright relaxed stance facing the camera, arms resting naturally at the sides, '
               'neutral camera at mid-torso height, natural adult proportions. Plain pale warm-gray seamless background, soft neutral studio daylight, '
               'realistic skin texture, fine fabric weave, seams, zipper and footwear edges in clear focus, accurate hands. '
               'An ordinary, believable working police officer, not a model, action hero or riot officer. No text, labels, watermark or extra people. ')

PEOPLE = {
    'CHAR_06': ('Police Officer A, a Korean woman in her early thirties, about 165 cm, slim athletic build, oval face, calm attentive dark eyes, minimal makeup, '
                'black hair pulled back into a neat low bun beneath the cap, small natural lips, composed professional expression that reads as trustworthy and alert. '),
    'CHAR_07': ('Police Officer B, a Korean man in his mid-forties, about 178 cm, sturdy medium build with a slightly thick neck and broad shoulders, square jaw, '
                'short black hair with a little gray at the temples beneath the cap, clean-shaven with faint smile lines, steady patient gaze, calm firm expression of an experienced officer. '),
}

TURN_COMMON = ("Using image one as the exact full-body identity and costume reference and image two as a close crop of that SAME original person's head, "
               'generate a photographic turnaround of that same person. Image two only reinforces the original face and cap; it does not introduce another person or a new design. '
               'Show exactly four separate full-body views in one horizontal row: front, strict profile facing the left edge, straight rear, strict profile facing the right edge. '
               'Keep every head and foot inside the frame, views evenly spaced on the same floor baseline, same body scale and natural proportions as image one. '
               'The front-view facial geometry, eye spacing and shape, nose, lips, jaw, head size, hairline and skin tone must match the original, '
               'without beautifying, slimming, recasting or changing age. Keep the original soft studio lighting and pale warm-gray backdrop. '
               'Preserve individual hair strands, natural skin texture, subtle fabric weave, garment seams, folds, fastenings and footwear edges, '
               'with clear focused detail and without painterly smoothing or artificial sharpening. Rotate the same original person and clothes; do not reinterpret their design. '
               'No text or watermark. ')

TURN_DETAIL = {
    'CHAR_06': ("Preserve the original woman's exact face, slim athletic build and the neat low black bun visible below the back of the cap in the rear and profile views. "),
    'CHAR_07': ("Preserve the original man's exact face, short black hair with gray temples visible below the cap, and his sturdy build. "),
}
TURN_UNIFORM = ('Keep the same dark navy patrol cap and emblem, the same dark navy zip-front patrol jacket with stand collar, epaulettes, chest pockets, sleeve patches '
                'and thin silver-gray reflective bands continuing around the back, the small black chest body camera, the black duty belt with the same closed pouches and holster '
                'on the same sides, straight navy trousers and black duty shoes. The rear of the jacket shows only the reflective band, with no lettering. '
                'Arms rest naturally at the sides in all four views.')

NAMES = {'CHAR_06': '경찰 A', 'CHAR_07': '경찰 B'}


def _base_api(text, seed, W, H, enc_res, prefix):
    w = json.loads(g.TEMPLATE.read_text(encoding='utf-8-sig'))
    n = {x['id']: x for x in w['nodes']}
    api = {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': n[1]['widgets_values'][0], 'weight_dtype': 'default'}},
        '3': {'class_type': 'QwenImage21Cache', 'inputs': {'model': ['1', 0], 'device': 'cpu', 'dtype': 'default'}},
        '4': {'class_type': 'ModelSamplingFlux', 'inputs': {'model': ['3', 0], 'max_shift': n[4]['widgets_values'][0], 'base_shift': n[4]['widgets_values'][1], 'width': ['10', 1], 'height': ['10', 2]}},
        '6': {'class_type': 'VAELoader', 'inputs': {'vae_name': n[6]['widgets_values'][0]}},
        '31': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': n[31]['widgets_values'][0], 'type': 'qwen_image', 'device': 'default'}},
        '10': {'class_type': 'DenoResolutionSetup', 'inputs': dict(zip(['mode', 'ratio_preset', 'megapixels', 'width', 'height', 'divisible_by', 'resize_method', 'interpolation', 'crop_x', 'crop_y', 'crop_zoom'],
                                                                     ['Manual Input', '3:2', round(W * H / 1e6, 2), W, H, '32', 'Center Crop (Fill)', 'lanczos', .5, .5, 1]))},
        '11': {'class_type': 'EmptyLatentImage', 'inputs': {'width': ['10', 1], 'height': ['10', 2], 'batch_size': 1}},
        '16': {'class_type': 'TextEncodeQwenImage21', 'inputs': {'clip': ['31', 0], 'vae': ['6', 0], 'prompt': text, 'negative_prompt': '', 'resolution': enc_res}},
        '20': {'class_type': 'KSampler', 'inputs': {'model': ['4', 0], 'positive': ['16', 0], 'negative': ['16', 1], 'latent_image': ['11', 0], 'seed': seed, 'steps': STEPS, 'cfg': 1, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': 1}},
        '21': {'class_type': 'VAEDecode', 'inputs': {'samples': ['20', 0], 'vae': ['6', 0]}},
        '22': {'class_type': 'SaveImage', 'inputs': {'images': ['21', 0], 'filename_prefix': 'deleted_11s_police_v01/' + prefix}},
    }
    return api, str(g.TEMPLATE), n[1]['widgets_values'][0]


def load_record():
    p = ROOT / 'GENERATION_RECORD.json'
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return {'engine': 'local ComfyUI 127.0.0.1:8188 / Deno Qwen-Image 2.1 T2I + Edit (검증된 워크플로우 사본의 API 그래프)',
            'date': '2026-10-06',
            'user_request': '서윤을 제외한 나머지 인물들도 턴어라운드 이미지 만들어줘.',
            'scope_decision': ('도현·지수는 2026-10-05 사용자 확정 턴어라운드가 있어 재생성하지 않음. 민재(목소리만)·낯선 남자(얼굴 없이 어깨만, SHOT_PLAN §1-7 텍스트 생성)는 '
                               '기존 기록상 인물 자산을 만들지 않으므로 제외. 화면 실물 등장하는 경찰 A/B만 제작.'),
            'design_status': '경찰 외형·근무복은 제작 제안이며 사용자 확정 전. 실제 경찰 제복 휘장·문구는 정밀 재현하지 않고 판독 가능한 글자를 넣지 않음.',
            'runs': []}


def save_record(rec):
    (ROOT / 'GENERATION_RECORD.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')


def submit(api, entry, out_name):
    rec = load_record()
    r = g.post('/prompt', {'prompt': api, 'client_id': 'd11-police-' + uuid.uuid4().hex})
    entry.update(prompt_id=r['prompt_id'], node_errors=r.get('node_errors', {}), status='queued', visual_review='pending')
    rec['runs'].append(entry)
    save_record(rec)
    (ROOT / 'api' / f'{out_name}.json').write_text(json.dumps(api, ensure_ascii=False, indent=2), encoding='utf-8')
    print('QUEUED', out_name, r['prompt_id'], flush=True)
    t0 = time.monotonic()
    while True:
        h = g.get('/history/' + r['prompt_id']).get(r['prompt_id'])
        if h:
            if h.get('status', {}).get('status_str') == 'error':
                entry['status'] = 'failed'
                entry['error'] = h.get('status')
                save_record(rec)
                raise RuntimeError(entry['error'])
            imgs = h.get('outputs', {}).get('22', {}).get('images', [])
            if imgs:
                blob = urllib.request.urlopen(g.BASE + '/view?' + urllib.parse.urlencode(imgs[0]), timeout=120).read()
                (ROOT / 'outputs' / f'{out_name}.png').write_bytes(blob)
                entry.update(status='generated', output=f'outputs/{out_name}.png', actual_size=list(struct.unpack('>II', blob[16:24])),
                             elapsed_seconds=round(time.monotonic() - t0, 1), sha256=hashlib.sha256(blob).hexdigest())
                save_record(rec)
                print('SAVED', out_name, entry['actual_size'], entry['elapsed_seconds'], 's', flush=True)
                return entry
        time.sleep(5)


def cast(cid, seed, tag):
    out_name = f'{cid}_cast_{tag}'
    text = CAST_COMMON + PEOPLE[cid] + UNIFORM
    (ROOT / 'prompts' / f'{out_name}.txt').write_text(text, encoding='utf-8')
    api, template, unet = _base_api(text, seed, 1024, 1536, 1024, out_name)
    return submit(api, {'id': out_name, 'character': cid, 'name': NAMES[cid], 'stage': 'casting T2I', 'seed': seed,
                        'size': [1024, 1536], 'steps': STEPS, 'reference': None, 'template': template, 'unet': unet}, out_name)


def turn(cid, ref, crop, seed):
    ref = Path(ref)
    if not ref.is_absolute():
        ref = ROOT / ref
    uploaded = g.upload(ref)
    out_name = f'{cid}_turnaround_{VERSION}'
    text = TURN_COMMON + TURN_DETAIL[cid] + TURN_UNIFORM
    (ROOT / 'prompts' / f'{out_name}.txt').write_text(text, encoding='utf-8')
    api, template, unet = _base_api(text, seed, 2560, 1536, 0, out_name)
    x, y = crop
    api['7'] = {'class_type': 'LoadImage', 'inputs': {'image': uploaded}}
    api['34'] = {'class_type': 'ImageCrop', 'inputs': {'image': ['7', 0], 'width': 384, 'height': 384, 'x': x, 'y': y}}
    api['16']['inputs']['images.image_1'] = ['7', 0]
    api['16']['inputs']['images.image_2'] = ['34', 0]
    return submit(api, {'id': out_name, 'character': cid, 'name': NAMES[cid], 'stage': 'turnaround Edit', 'seed': seed,
                        'size': [2560, 1536], 'steps': STEPS, 'encoder_resolution': 0, 'template': template, 'unet': unet,
                        'reference': {'source': str(ref.relative_to(ROOT)), 'uploaded_name': uploaded,
                                      'sha256': hashlib.sha256(ref.read_bytes()).hexdigest(), 'destination': '16 images.image_1'},
                        'reference2': {'source': 'ImageCrop 34 of node 7 (same file)', 'crop': [384, 384, x, y], 'destination': '16 images.image_2'}},
                  out_name)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['cast', 'turn'])
    ap.add_argument('cid', choices=list(PEOPLE))
    ap.add_argument('--seed', type=int, default=2026100601)
    ap.add_argument('--tag', default='a')
    ap.add_argument('--ref')
    ap.add_argument('--crop', default='320,0')
    a = ap.parse_args()
    if a.stage == 'cast':
        cast(a.cid, a.seed, a.tag)
    else:
        turn(a.cid, a.ref, tuple(int(v) for v in a.crop.split(',')), a.seed)
