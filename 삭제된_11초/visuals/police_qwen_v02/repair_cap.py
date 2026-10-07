"""CHAR_07 턴어라운드 v02(패치 수정본)의 모자 색·자수를 CHAR_06(경찰 A)에 맞춘다.

2026-10-07 사용자 요청: "B모자 색이랑 자수 A에 맞춰줘".
네 방향 패널마다 ComfyUI 그래프 안에서:
  B 시트 모자 주변 320x256 ImageCrop → 3배 확대 → Qwen Edit image_1
  A 시트의 같은 방향 같은 위치 ImageCrop → 3배 확대 → image_2 (모자 색·자수 참조)
  결과 → 축소 → 모자 박스 마스크(페더)로만 합성. 네 합성을 차례로 이어 한 장으로 저장.
"""
from pathlib import Path
import sys, json, hashlib

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'police_qwen_v01'))
import generate as v1  # noqa: E402
v1.ROOT = ROOT

TARGET = ROOT / 'outputs' / 'CHAR_07_turnaround_v02_patchfix.png'
REF = ROOT / 'outputs' / 'CHAR_06_turnaround_v02.png'
CW, CH, UP, FEATHER, SEED = 320, 256, 3, 10, 2026100751
# view: (crop x, crop y, mask w, h, x, y in crop)
PANELS = {
    'front':         (256, 0, 172, 120, 84, 40),
    'profile_left':  (832, 0, 240, 140, 33, 40),
    'rear':          (1440, 0, 170, 135, 85, 40),
    'profile_right': (2048, 0, 250, 150, 47, 40),
}
VIEW_TEXT = {
    'front': 'front view; the gold police eagle emblem sits inside the same framed gold badge shape as image two, and the brim edge carries the same single thin row of gold leaf embroidery',
    'profile_left': 'side view; the brim edge carries the same single thin row of gold leaf embroidery as image two, and the small gold emblem at the front of the crown matches image two',
    'rear': 'rear view; only the cap fabric color and the back strap color change to match image two',
    'profile_right': 'side view; the brim edge carries the same single thin row of gold leaf embroidery as image two, and the small gold emblem at the front of the crown matches image two',
}


def prompt(view):
    return ('Using image one as the edit target and image two as the cap reference, change only the police cap worn by the man in image one so that it matches the cap in image two: '
            'the same dark navy blue cap fabric color, not black, with the same matte cotton twill texture and seams; ' + VIEW_TEXT[view] + '. '
            'Do not make the gold embroidery thicker or denser than image two. Keep the cap shape, size, angle and position on his head exactly as in image one. '
            "Keep the man's face, ears, gray-templed short hair, skin, collar, background and lighting exactly as in image one. Do not copy the woman, her face or her hair bun from image two. No text, no watermark.")


def main():
    out_name = 'CHAR_07_turnaround_v02_capfix'
    w = json.loads(v1.g.TEMPLATE.read_text(encoding='utf-8-sig'))
    n = {x['id']: x for x in w['nodes']}
    up_t, up_r = v1.g.upload(TARGET), v1.g.upload(REF)
    api = {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': n[1]['widgets_values'][0], 'weight_dtype': 'default'}},
        '3': {'class_type': 'QwenImage21Cache', 'inputs': {'model': ['1', 0], 'device': 'cpu', 'dtype': 'default'}},
        '4': {'class_type': 'ModelSamplingFlux', 'inputs': {'model': ['3', 0], 'max_shift': n[4]['widgets_values'][0], 'base_shift': n[4]['widgets_values'][1], 'width': CW * UP, 'height': CH * UP}},
        '6': {'class_type': 'VAELoader', 'inputs': {'vae_name': n[6]['widgets_values'][0]}},
        '31': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': n[31]['widgets_values'][0], 'type': 'qwen_image', 'device': 'default'}},
        '40': {'class_type': 'LoadImage', 'inputs': {'image': up_t}},
        '41': {'class_type': 'LoadImage', 'inputs': {'image': up_r}},
    }
    dest = ['40', 0]
    prompts = {}
    for i, (view, (cx, cy, mw, mh, mx, my)) in enumerate(PANELS.items()):
        b = 100 + i * 20
        k = lambda o: str(b + o)
        prompts[view] = prompt(view)
        api.update({
            k(0): {'class_type': 'ImageCrop', 'inputs': {'image': ['40', 0], 'width': CW, 'height': CH, 'x': cx, 'y': cy}},
            k(1): {'class_type': 'ImageScale', 'inputs': {'image': [k(0), 0], 'upscale_method': 'lanczos', 'width': CW * UP, 'height': CH * UP, 'crop': 'disabled'}},
            k(2): {'class_type': 'ImageCrop', 'inputs': {'image': ['41', 0], 'width': CW, 'height': CH, 'x': cx, 'y': cy}},
            k(3): {'class_type': 'ImageScale', 'inputs': {'image': [k(2), 0], 'upscale_method': 'lanczos', 'width': CW * UP, 'height': CH * UP, 'crop': 'disabled'}},
            k(4): {'class_type': 'TextEncodeQwenImage21', 'inputs': {'clip': ['31', 0], 'vae': ['6', 0], 'prompt': prompts[view], 'negative_prompt': '', 'resolution': 0,
                                                                     'images.image_1': [k(1), 0], 'images.image_2': [k(3), 0]}},
            k(5): {'class_type': 'KSampler', 'inputs': {'model': ['4', 0], 'positive': [k(4), 0], 'negative': [k(4), 1], 'latent_image': [k(4), 2], 'seed': SEED + i,
                                                        'steps': v1.STEPS, 'cfg': 1, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': 1}},
            k(6): {'class_type': 'VAEDecode', 'inputs': {'samples': [k(5), 0], 'vae': ['6', 0]}},
            k(7): {'class_type': 'ImageScale', 'inputs': {'image': [k(6), 0], 'upscale_method': 'lanczos', 'width': CW, 'height': CH, 'crop': 'disabled'}},
            k(8): {'class_type': 'SolidMask', 'inputs': {'value': 0.0, 'width': CW, 'height': CH}},
            k(9): {'class_type': 'SolidMask', 'inputs': {'value': 1.0, 'width': mw, 'height': mh}},
            k(10): {'class_type': 'FeatherMask', 'inputs': {'mask': [k(9), 0], 'left': FEATHER, 'top': FEATHER, 'right': FEATHER, 'bottom': FEATHER}},
            k(11): {'class_type': 'MaskComposite', 'inputs': {'destination': [k(8), 0], 'source': [k(10), 0], 'x': mx, 'y': my, 'operation': 'add'}},
            k(12): {'class_type': 'ImageCompositeMasked', 'inputs': {'destination': dest, 'source': [k(7), 0], 'x': cx, 'y': cy, 'resize_source': False, 'mask': [k(11), 0]}},
        })
        dest = [k(12), 0]
    api['22'] = {'class_type': 'SaveImage', 'inputs': {'images': dest, 'filename_prefix': 'deleted_11s_police_v02/' + out_name}}
    (ROOT / 'prompts' / f'{out_name}.json').write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding='utf-8')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    return v1.submit(api, {'id': out_name, 'character': 'CHAR_07', 'name': '경찰 B', 'stage': 'cap color/embroidery match to CHAR_06', 'seed': SEED, 'steps': v1.STEPS,
                           'reference': {'source': str(TARGET.relative_to(ROOT)), 'uploaded_name': up_t, 'sha256': sha(TARGET), 'destination': 'per-panel crop x3 → image_1; composite destination'},
                           'reference2': {'source': str(REF.relative_to(ROOT)), 'uploaded_name': up_r, 'sha256': sha(REF), 'destination': 'same-view crop x3 → image_2'},
                           'panels': PANELS, 'feather': FEATHER, 'upscale': UP}, out_name)


if __name__ == '__main__':
    main()
