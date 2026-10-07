"""COSTUME_01B 턴어라운드 b — 왼쪽 측면·후면 패널의 왼손목 보호대 보완.

관찰(2026-10-06): turnaround_b는 정면 보호대·코트 길이는 맞지만, 왼쪽을 향한 측면(패널 2)과
후면(패널 3)의 해부학적 왼손목에 보호대가 없다.
방법은 v02 서윤 후면 보완(turnaround_qwen_v02/build_rear_repair.py)과 같다:
ComfyUI ImageCrop으로 640x1536 패널을 잘라 Qwen 편집 대상(image_1)으로 넣고,
확정 v02 시트에서 같은 각도의 보호대 크롭을 image_2로 넣은 뒤 ImageCompositeMasked로 원래 위치에 합성한다.
정면(패널 1)·오른쪽 측면(패널 4)은 그대로 둔다.
"""
from pathlib import Path
import sys, json, hashlib, struct, time, uuid, urllib.request, urllib.parse

ROOT = Path(__file__).resolve().parent
VIS = ROOT.parent
sys.path.insert(0, str(VIS / 'locations_qwen_v01'))
sys.path.insert(0, str(ROOT))
import generate_locations as g  # noqa: E402
import generate_costume as gc  # noqa: E402

TARGET = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_b.png'
APPROVED = VIS / 'turnaround_qwen_v02/outputs/CHAR_01_서윤_turnaround_v02_HQ_repaired.png'
OUT_NAME = 'CHAR_01_서윤_COSTUME_01B_turnaround_b_repaired'
STEPS = 60

PANELS = {
    'profile_left': dict(x=640, seed=2026100611, brace_crop=(860, 600, 160, 240), prompt=(
        "Using image one as the edit target, a left-facing strict profile photograph of a woman in a long open camel wool coat, and image two as a close detail of her "
        "original gray structured wrist brace seen from the same side, change only her near arm, the arm closest to the camera, which is her anatomical LEFT arm: "
        "below the camel coat cuff, add the matching gray soft wrist brace with its fastening straps and thumb opening over the wrist and the base of the hand. "
        "Match the brace shape, gray color, straps and fabric texture of image two. The hand and fingers below the brace stay natural and relaxed. "
        "Keep her face, long black hair, the camel coat with its length and seams, the charcoal trousers, the white sneakers, her pose, body size, skin tone, "
        "background and lighting exactly as in image one, in the same pixel positions and scale. Add the single brace, no other changes, no text or watermark.")),
    'rear': dict(x=1280, seed=2026100612, brace_crop=(1390, 600, 160, 240), prompt=(
        "Using image one as the edit target, a straight rear-view photograph of a woman in a long camel wool coat, and image two as a close detail of her original gray "
        "structured wrist brace seen from behind, change only the wrist on the LEFT SIDE OF THE IMAGE, which is her anatomical LEFT wrist: below the camel coat cuff, "
        "add the matching gray soft wrist brace with its fastening straps over the wrist and the base of the hand. The wrist on the right side of the image stays completely bare. "
        "Match the brace shape, gray color, straps and fabric texture of image two, rotated naturally to its back-facing side. "
        "Keep the long black hair, the camel coat with its length and center seam, the charcoal trousers, the white sneakers, her pose, body size, skin tone, "
        "background and lighting exactly as in image one, in the same pixel positions and scale. Add the single brace, no other changes, no text or watermark.")),
}


def build(up):
    nm = gc._wf_names()
    api = {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': nm['unet'], 'weight_dtype': 'default'}},
        '3': {'class_type': 'QwenImage21Cache', 'inputs': {'model': ['1', 0], 'device': 'cpu', 'dtype': 'default'}},
        '4': {'class_type': 'ModelSamplingFlux', 'inputs': {'model': ['3', 0], 'max_shift': nm['max_shift'], 'base_shift': nm['base_shift'], 'width': 640, 'height': 1536}},
        '6': {'class_type': 'VAELoader', 'inputs': {'vae_name': nm['vae']}},
        '31': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': nm['clip'], 'type': 'qwen_image', 'device': 'default'}},
        '7': {'class_type': 'LoadImage', 'inputs': {'image': up['target']}},
        '35': {'class_type': 'LoadImage', 'inputs': {'image': up['approved']}},
    }
    dest = ['7', 0]
    for i, (pid, p) in enumerate(PANELS.items()):
        b = 100 + i * 10
        bx, by, bw, bh = p['brace_crop']
        api.update({
            f'{b}': {'class_type': 'ImageCrop', 'inputs': {'image': ['7', 0], 'width': 640, 'height': 1536, 'x': p['x'], 'y': 0}},
            f'{b+1}': {'class_type': 'ImageCrop', 'inputs': {'image': ['35', 0], 'width': bw, 'height': bh, 'x': bx, 'y': by}},
            f'{b+2}': {'class_type': 'TextEncodeQwenImage21', 'inputs': {'clip': ['31', 0], 'vae': ['6', 0], 'prompt': p['prompt'], 'negative_prompt': '', 'resolution': 0,
                                                                     'images.image_1': [f'{b}', 0], 'images.image_2': [f'{b+1}', 0]}},
            f'{b+3}': {'class_type': 'KSampler', 'inputs': {'model': ['4', 0], 'positive': [f'{b+2}', 0], 'negative': [f'{b+2}', 1], 'latent_image': [f'{b+2}', 2],
                                                        'seed': p['seed'], 'steps': STEPS, 'cfg': 1, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': 1}},
            f'{b+4}': {'class_type': 'VAEDecode', 'inputs': {'samples': [f'{b+3}', 0], 'vae': ['6', 0]}},
            f'{b+5}': {'class_type': 'ImageCompositeMasked', 'inputs': {'destination': dest, 'source': [f'{b+4}', 0], 'x': p['x'], 'y': 0, 'resize_source': False}},
        })
        dest = [f'{b+5}', 0]
    api['22'] = {'class_type': 'SaveImage', 'inputs': {'images': dest, 'filename_prefix': 'deleted_11s_costume/' + OUT_NAME}}
    for pid, p in PANELS.items():
        (ROOT / 'prompts' / f'{OUT_NAME}__{pid}.txt').write_text(p['prompt'], encoding='utf-8')
    (ROOT / 'api' / f'{OUT_NAME}.json').write_text(json.dumps(api, ensure_ascii=False, indent=2), encoding='utf-8')
    return api


def main():
    rec = json.loads((ROOT / 'GENERATION_RECORD.json').read_text(encoding='utf-8'))
    up = {'target': g.upload(TARGET), 'approved': g.upload(APPROVED)}
    api = build(up)
    r = g.post('/prompt', {'prompt': api, 'client_id': 'd11-costume-repair-' + uuid.uuid4().hex, 'extra_data': {'extra_pnginfo': {'api_graph': api}}})
    entry = {'id': OUT_NAME, 'type': 'panel repair (left profile + rear brace)', 'prompt_id': r['prompt_id'], 'node_errors': r.get('node_errors', {}),
             'references': {'target': {'source': str(TARGET.relative_to(VIS)), 'uploaded_name': up['target'], 'sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(),
                                       'slot': 'ImageCrop 640x1536 per panel → images.image_1'},
                            'approved_brace': {'source': str(APPROVED.relative_to(VIS)), 'uploaded_name': up['approved'], 'sha256': hashlib.sha256(APPROVED.read_bytes()).hexdigest(),
                                               'slot': 'ImageCrop brace detail per panel → images.image_2'}},
             'panels': {k: {'x': v['x'], 'seed': v['seed'], 'brace_crop': v['brace_crop']} for k, v in PANELS.items()},
             'unchanged_panels': ['front x=0', 'profile_right x=1920'], 'status': 'queued', 'visual_review': 'pending'}
    rec['runs'].append(entry)
    (ROOT / 'GENERATION_RECORD.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
    print('QUEUED', r['prompt_id'], flush=True)
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
                out = ROOT / 'outputs' / f'{OUT_NAME}.png'
                out.write_bytes(blob)
                entry.update(status='generated', output=f'outputs/{OUT_NAME}.png', actual_size=list(struct.unpack('>II', blob[16:24])),
                             elapsed_seconds=round(time.monotonic() - t0, 1), sha256=hashlib.sha256(blob).hexdigest())
                (ROOT / 'GENERATION_RECORD.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
                print('SAVED', out, entry['actual_size'], entry['elapsed_seconds'], 's', flush=True)
                return
        time.sleep(5)


if __name__ == '__main__':
    main()
