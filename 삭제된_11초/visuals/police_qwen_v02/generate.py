"""삭제된 11초 — 경찰 A/B v02: 사용자 제공 한국 경찰 근무복 참조 반영.

2026-10-06 사용자 지적: v01 근무복은 실제 한국 경찰 제복과 다르다. 사용자가 실제 제복 사진(references/USER_KOREAN_POLICE_UNIFORM_REF.png)을 제공했다.
참조 사진 속 실존 인물의 얼굴은 모델에 들어가지 않게 회색으로 가리고 인물 주변만 잘라 썼다(references/UNIFORM_REF_face_masked.png).
얼굴·체형은 v01 기준 전신(cast_a)을 그대로 쓴다.

1단계 dress: image_1 = v01 cast_a(인물), image_2 = 얼굴 가린 제복 참조 → 같은 인물에게 참조 제복을 입힌 1024x1536 전신
2단계 turn : v01과 같은 턴어라운드(2560x1536, image_1 = dress 결과, image_2 = 같은 파일 얼굴 크롭)

사용:
  python generate.py dress CHAR_06 [--seed N] [--tag a]
  python generate.py turn CHAR_06 --ref outputs/CHAR_06_dress_a.png [--crop 320,0] [--seed N]
"""
from pathlib import Path
import sys, json, hashlib, argparse

ROOT = Path(__file__).resolve().parent
V01 = ROOT.parent / 'police_qwen_v01'
sys.path.insert(0, str(V01))
import generate as v1  # noqa: E402  (v01의 API 그래프·제출 함수 재사용)

v1.ROOT = ROOT  # 기록·출력을 v02 폴더에 저장
for sub in ['outputs', 'prompts', 'api']:
    (ROOT / sub).mkdir(parents=True, exist_ok=True)

UNIFORM_REF = ROOT / 'references' / 'UNIFORM_REF_face_masked.png'
CAST = {'CHAR_06': V01 / 'outputs' / 'CHAR_06_cast_a.png', 'CHAR_07': V01 / 'outputs' / 'CHAR_07_cast_a.png'}

# 사용자 제공 사진에서 관찰한 제복 요소(정면만 보임)
UNIFORM = ('the current South Korean police winter patrol uniform exactly as worn in image two: '
           'a dark navy baseball-style police cap with a gold embroidered police eagle emblem on the front panel and gold leaf embroidery along the brim edge; '
           'a light cool-gray padded winter patrol jacket with a tall stand collar zipped up, gray shoulder epaulettes with small rank insignia, '
           'a zippered pocket on the upper left sleeve and dark teal knit inner cuffs showing at the wrists; '
           'over the jacket, a dark navy zip-front police duty vest with a broad horizontal silver reflective band across the chest, '
           'a white rectangular name patch reading 경찰 above POLICE on the wearer\'s right chest, a navy flap pouch with the gold police eagle badge patch on the wearer\'s left chest, '
           'a black handheld radio clipped on the wearer\'s left shoulder strap, and several navy flap pouches across the lower vest; '
           'slim black uniform trousers and polished black leather lace-up oxford shoes. ')

DRESS_TEXT = {
    cid: ('Using image one as the exact person, face, hair, body, pose, framing, camera, soft studio lighting and pale warm-gray seamless background, '
          'and image two only as the clothing reference, dress the SAME person from image one in ' + UNIFORM +
          'Image two\'s face is intentionally hidden by a gray box; take nothing from it except the clothing and cap. Do not copy image two\'s alley background, house or lighting. '
          'Keep image one\'s facial geometry, age, expression, skin tone and ' + hair + ' unchanged; do not recast, beautify or change age. '
          'One full-length vertical studio photograph, head, cap and both shoes fully visible with clear margin, standing upright facing the camera, arms resting naturally at the sides. '
          'Realistic fabric texture, quilting, seams, zipper, reflective tape and leather shoe detail in clear focus. No watermark, no extra people.')
    for cid, hair in {
        'CHAR_06': 'the neat low black bun visible beneath the cap',
        'CHAR_07': 'the short black hair with gray temples beneath the cap',
    }.items()
}

TURN_DETAIL = {
    'CHAR_06': "Preserve the original woman's exact face, slim athletic build and the neat low black bun visible below the back of the cap in the rear and profile views. ",
    'CHAR_07': "Preserve the original man's exact face, short black hair with gray temples visible below the cap, and his sturdy build. ",
}
TURN_UNIFORM = ('Keep exactly the same uniform: dark navy police cap with gold embroidered eagle emblem and gold-embroidered brim edge; '
                'light cool-gray padded winter jacket with stand collar, epaulettes, upper-left-sleeve zip pocket and teal inner cuffs; '
                'dark navy zip-front duty vest with the silver reflective band continuing around the back, the white 경찰 POLICE name patch on the wearer\'s right chest, '
                'the gold eagle badge pouch on the wearer\'s left chest, the black radio on the wearer\'s left shoulder strap and the same lower pouches on the same sides; '
                'slim black trousers and black leather oxford shoes. The rear of the vest shows the reflective band; do not invent large back lettering. '
                'Arms rest naturally at the sides in all four views.')

NAMES = v1.NAMES


def _ref_entry(path, uploaded, dest):
    return {'source': str(path), 'uploaded_name': uploaded, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'destination': dest}


def dress(cid, seed, tag):
    out_name = f'{cid}_dress_{tag}'
    text = DRESS_TEXT[cid]
    (ROOT / 'prompts' / f'{out_name}.txt').write_text(text, encoding='utf-8')
    api, template, unet = v1._base_api(text, seed, 1024, 1536, 0, out_name)
    api['22']['inputs']['filename_prefix'] = 'deleted_11s_police_v02/' + out_name
    up1, up2 = v1.g.upload(CAST[cid]), v1.g.upload(UNIFORM_REF)
    api['7'] = {'class_type': 'LoadImage', 'inputs': {'image': up1}}
    api['8'] = {'class_type': 'LoadImage', 'inputs': {'image': up2}}
    api['16']['inputs']['images.image_1'] = ['7', 0]
    api['16']['inputs']['images.image_2'] = ['8', 0]
    return v1.submit(api, {'id': out_name, 'character': cid, 'name': NAMES[cid], 'stage': 'uniform edit', 'seed': seed,
                           'size': [1024, 1536], 'steps': v1.STEPS, 'encoder_resolution': 0, 'template': template, 'unet': unet,
                           'reference': _ref_entry(CAST[cid], up1, '16 images.image_1'),
                           'reference2': _ref_entry(UNIFORM_REF, up2, '16 images.image_2')}, out_name)


def turn(cid, ref, crop, seed):
    ref = Path(ref)
    if not ref.is_absolute():
        ref = ROOT / ref
    v1.TURN_DETAIL = TURN_DETAIL
    v1.TURN_UNIFORM = TURN_UNIFORM
    v1.VERSION = 'v02'
    orig_base = v1._base_api

    def base(text, seed_, W, H, enc, prefix):
        api, t, u = orig_base(text, seed_, W, H, enc, prefix)
        api['22']['inputs']['filename_prefix'] = 'deleted_11s_police_v02/' + prefix
        return api, t, u
    v1._base_api = base
    out = v1.turn(cid, ref, crop, seed)
    v1._base_api = orig_base
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['dress', 'turn'])
    ap.add_argument('cid', choices=list(CAST))
    ap.add_argument('--seed', type=int, default=2026100621)
    ap.add_argument('--tag', default='a')
    ap.add_argument('--ref')
    ap.add_argument('--crop', default='320,0')
    a = ap.parse_args()
    rec = v1.load_record()
    rec.setdefault('v02_note', '사용자 제공 실제 한국 경찰 근무복 사진을 제복 참조로 사용. 사진 속 실존 인물 얼굴은 회색 사각형으로 가리고 인물 주변만 잘라 입력(얼굴 정체성 미사용).')
    v1.save_record(rec)
    if a.stage == 'dress':
        dress(a.cid, a.seed, a.tag)
    else:
        turn(a.cid, a.ref, tuple(int(v) for v in a.crop.split(',')), a.seed)
