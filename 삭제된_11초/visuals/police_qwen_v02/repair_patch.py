"""CHAR_07 턴어라운드 v02 정면 이름 패치 글자 수정("경차" → "경찰").

ComfyUI 그래프만으로 수행한다:
  턴어라운드 시트 → ImageCrop(정면 가슴 512x512, x=96,y=200) → 2배 확대 → Qwen Edit(image_1)
  CHAR_06 턴어라운드 v02 정면 패치("경찰" 정상) → ImageCrop → 확대 → image_2(글자 참조)
  결과 → 512로 축소 → 패치 주변 박스 마스크(가장자리 페더)로만 원래 시트에 합성. 마스크 밖 픽셀은 원본 그대로.
"""
from pathlib import Path
import sys, json, hashlib

ROOT = Path(__file__).resolve().parent
V01 = ROOT.parent / 'police_qwen_v01'
sys.path.insert(0, str(V01))
import generate as v1  # noqa: E402
v1.ROOT = ROOT

TARGET = ROOT / 'outputs' / 'CHAR_07_turnaround_v02.png'
TEXT_REF = ROOT / 'outputs' / 'CHAR_06_turnaround_v02.png'
CX, CY, CS = 96, 200, 512          # 시트에서 자를 가슴 영역
REF_BOX = (110, 85, 290, 375)       # CHAR_06 정면 패치 (w, h, x, y)
MASK_BOX = (100, 80, 206, 180)      # 크롭 좌표의 패치 박스 (w, h, x, y)
FEATHER = 10
SEED = 2026100641

PROMPT = ('Using image one as the edit target and image two as the exact lettering reference, change only the white rectangular name patch on the vest '
          'so that its upper line reads the Korean word 경찰 in the same bold black Korean lettering as image two, with POLICE below it exactly as now. '
          'The second Korean syllable must be 찰, not 차 or 착. Keep the patch size, position, white color, border, perspective and fabric texture. '
          'Keep the zipper, radio, eagle badge, reflective band, gray jacket, face, lighting and every other pixel of image one unchanged. No other text, no watermark.')


def main():
    out_name = 'CHAR_07_turnaround_v02_patchfix'
    _, template, unet = v1._base_api('', 0, 64, 64, 0, 'x')
    t = v1.g.TEMPLATE
    w = json.loads(t.read_text(encoding='utf-8-sig'))
    n = {x['id']: x for x in w['nodes']}
    up_t, up_r = v1.g.upload(TARGET), v1.g.upload(TEXT_REF)
    rw, rh, rx, ry = REF_BOX
    mw, mh, mx, my = MASK_BOX
    api = {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': n[1]['widgets_values'][0], 'weight_dtype': 'default'}},
        '3': {'class_type': 'QwenImage21Cache', 'inputs': {'model': ['1', 0], 'device': 'cpu', 'dtype': 'default'}},
        '4': {'class_type': 'ModelSamplingFlux', 'inputs': {'model': ['3', 0], 'max_shift': n[4]['widgets_values'][0], 'base_shift': n[4]['widgets_values'][1], 'width': 1024, 'height': 1024}},
        '6': {'class_type': 'VAELoader', 'inputs': {'vae_name': n[6]['widgets_values'][0]}},
        '31': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': n[31]['widgets_values'][0], 'type': 'qwen_image', 'device': 'default'}},
        '40': {'class_type': 'LoadImage', 'inputs': {'image': up_t}},
        '41': {'class_type': 'ImageCrop', 'inputs': {'image': ['40', 0], 'width': CS, 'height': CS, 'x': CX, 'y': CY}},
        '42': {'class_type': 'ImageScale', 'inputs': {'image': ['41', 0], 'upscale_method': 'lanczos', 'width': CS * 2, 'height': CS * 2, 'crop': 'disabled'}},
        '43': {'class_type': 'LoadImage', 'inputs': {'image': up_r}},
        '44': {'class_type': 'ImageCrop', 'inputs': {'image': ['43', 0], 'width': rw, 'height': rh, 'x': rx, 'y': ry}},
        '45': {'class_type': 'ImageScale', 'inputs': {'image': ['44', 0], 'upscale_method': 'lanczos', 'width': rw * 4, 'height': rh * 4, 'crop': 'disabled'}},
        '16': {'class_type': 'TextEncodeQwenImage21', 'inputs': {'clip': ['31', 0], 'vae': ['6', 0], 'prompt': PROMPT, 'negative_prompt': '', 'resolution': 0,
                                                                 'images.image_1': ['42', 0], 'images.image_2': ['45', 0]}},
        '20': {'class_type': 'KSampler', 'inputs': {'model': ['4', 0], 'positive': ['16', 0], 'negative': ['16', 1], 'latent_image': ['16', 2], 'seed': SEED, 'steps': v1.STEPS,
                                                    'cfg': 1, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': 1}},
        '21': {'class_type': 'VAEDecode', 'inputs': {'samples': ['20', 0], 'vae': ['6', 0]}},
        '46': {'class_type': 'ImageScale', 'inputs': {'image': ['21', 0], 'upscale_method': 'lanczos', 'width': CS, 'height': CS, 'crop': 'disabled'}},
        '47': {'class_type': 'SolidMask', 'inputs': {'value': 0.0, 'width': CS, 'height': CS}},
        '48': {'class_type': 'SolidMask', 'inputs': {'value': 1.0, 'width': mw, 'height': mh}},
        '49': {'class_type': 'FeatherMask', 'inputs': {'mask': ['48', 0], 'left': FEATHER, 'top': FEATHER, 'right': FEATHER, 'bottom': FEATHER}},
        '50': {'class_type': 'MaskComposite', 'inputs': {'destination': ['47', 0], 'source': ['49', 0], 'x': mx, 'y': my, 'operation': 'add'}},
        '51': {'class_type': 'ImageCompositeMasked', 'inputs': {'destination': ['40', 0], 'source': ['46', 0], 'x': CX, 'y': CY, 'resize_source': False, 'mask': ['50', 0]}},
        '22': {'class_type': 'SaveImage', 'inputs': {'images': ['51', 0], 'filename_prefix': 'deleted_11s_police_v02/' + out_name}},
        '52': {'class_type': 'SaveImage', 'inputs': {'images': ['46', 0], 'filename_prefix': 'deleted_11s_police_v02/' + out_name + '_editcrop'}},
    }
    (ROOT / 'prompts' / f'{out_name}.txt').write_text(PROMPT, encoding='utf-8')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    return v1.submit(api, {'id': out_name, 'character': 'CHAR_07', 'name': '경찰 B', 'stage': 'name patch repair', 'seed': SEED, 'steps': v1.STEPS,
                           'reference': {'source': str(TARGET.relative_to(ROOT)), 'uploaded_name': up_t, 'sha256': sha(TARGET),
                                         'destination': f'ImageCrop {CS}x{CS}@({CX},{CY}) → x2 → 16 images.image_1; also composite destination'},
                           'reference2': {'source': str(TEXT_REF.relative_to(ROOT)), 'uploaded_name': up_r, 'sha256': sha(TEXT_REF),
                                          'destination': f'ImageCrop {rw}x{rh}@({rx},{ry}) → x4 → 16 images.image_2'},
                           'mask': {'box_in_crop': MASK_BOX, 'feather': FEATHER}}, out_name)


if __name__ == '__main__':
    main()
