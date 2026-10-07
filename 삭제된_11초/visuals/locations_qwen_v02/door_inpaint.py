"""복도 문 마스크 인페인팅 (사용자 요청 2026-10-06).

목표: 문을 바깥여닫이로 보정. 경첩은 카메라 쪽 문틀, 문짝은 복도 벽 쪽으로 거의 활짝 젖혀짐.
확정 현관 뷰(LOC_03_ENTRY_v02)에서 안쪽 기준 도어록 왼쪽·경첩 오른쪽 → 복도 기준 경첩은 카메라 쪽.

1) LOC_04_CORRIDOR_v02 좌측 1280x1440을 잘라 원하는 형태를 단색 가이드로 칠한다(PIL).
2) 가이드 영역 마스크(확장+페더) 안에서만 Qwen으로 다시 그린다:
   VAEEncode(가이드) → SetLatentNoiseMask → KSampler(denoise<1), DifferentialDiffusion,
   조건: TextEncodeQwenImage21 + images.image_1=가이드.
3) ImageCompositeMasked로 원본 전체 이미지에 합성 → 마스크 밖 픽셀은 원본 그대로.
"""
from pathlib import Path
import sys, json, hashlib, struct, time, uuid, urllib.request, urllib.parse
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import generate_v02 as v  # noqa: E402
g = v.g

SRC = ROOT / 'outputs/LOC_04_CORRIDOR_v02.png'
CW, CH = 1280, 1440
WORK = ROOT / 'inpaint'
WORK.mkdir(exist_ok=True)

PROMPT = '''Turn the rough flat-colored shapes in the image into a photorealistic, fully detailed part of this apartment corridor, keeping their positions and outlines. The large warm-gray panel on the left is the apartment's front door leaf, swung fully open outward and resting almost flat against the corridor wall: a plain warm-gray powder-coated metal slab with one fine vertical reveal line and a thin darker edge visible along its free left side. On its corridor-side face, near that free edge, is a slim black digital keypad lock with a short black lever handle. The door hangs on the small brushed steel hinge knuckles along the near side of the doorway. To the right of the door leaf, the doorway is open and unobstructed, showing the apartment's small entry vestibule: pale gray porcelain floor tiles, a slim metal threshold strip, warm ivory walls and soft warm interior light spilling out onto the corridor floor. The far side of the doorway is a clean slim warm-gray metal door frame with no hinges. Match the corridor's existing materials, perspective, soft neutral-white light and photographic texture. No people, no readable text, no watermark.'''


def make_guide():
    base = Image.open(SRC).convert('RGB')
    crop = base.crop((0, 0, CW, CH))
    d = ImageDraw.Draw(crop)
    mask = Image.new('L', (CW, CH), 0)
    m = ImageDraw.Draw(mask)
    # 문짝: x 70~482, 전체 높이. 경첩 쪽(오른쪽)이 실내광으로 약간 밝음
    arr = np.array(crop)
    for x in range(70, 483):
        t = (x - 70) / 412
        arr[:, x] = (int(150 + 18 * t), int(141 + 15 * t), int(134 + 12 * t))
    crop = Image.fromarray(arr)
    d = ImageDraw.Draw(crop)
    d.rectangle((56, 0, 72, CH), fill=(92, 85, 79))            # 문짝 두께(자유단)
    d.rectangle((214, 0, 217, CH), fill=(112, 104, 97))         # 세로 리빌 라인
    d.rectangle((104, 600, 146, 795), fill=(24, 24, 26))        # 디지털 도어록
    d.rectangle((146, 668, 214, 682), fill=(36, 36, 38))        # 레버(경첩 방향)
    for y0 in (140, 640, 1170):                                  # 경첩 3개(카메라 쪽 문틀)
        d.rectangle((476, y0, 494, y0 + 110), fill=(186, 181, 176))
    m.rectangle((40, 0, 500, CH), fill=255)
    # 개구부: 실내 벽 + 현관 바닥 + 문턱
    opening = [(497, 0), (738, 100), (738, 1205), (497, 1395)]
    d.polygon(opening, fill=(244, 231, 214))
    d.polygon([(497, 1185), (738, 1102), (738, 1205), (497, 1395)], fill=(206, 198, 189))
    d.line([(497, 1185), (738, 1102)], fill=(150, 140, 130), width=4)  # 걸레받이
    d.line([(497, 1395), (738, 1205)], fill=(190, 190, 192), width=6)  # 금속 문턱
    m.polygon(opening, fill=255)
    # 먼 쪽 문틀: 경첩 제거
    d.rectangle((736, 100, 792, 1205), fill=(128, 116, 106))
    d.line([(736, 100), (736, 1205)], fill=(70, 64, 58), width=3)
    m.rectangle((728, 95, 800, 1215), fill=255)
    mask = mask.filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.GaussianBlur(10))
    crop.save(WORK / 'door_guide.png')
    # LoadImageMask는 채널을 읽으므로 RGB로 저장
    Image.merge('RGB', (mask, mask, mask)).save(WORK / 'door_mask.png')
    return WORK / 'door_guide.png', WORK / 'door_mask.png'


def build_api(full_name, guide_name, mask_name, seed, denoise, out_prefix):
    w = json.loads(g.TEMPLATE.read_text(encoding='utf-8-sig'))
    n = {x['id']: x for x in w['nodes']}
    return {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': n[1]['widgets_values'][0], 'weight_dtype': 'default'}},
        '3': {'class_type': 'QwenImage21Cache', 'inputs': {'model': ['1', 0], 'device': 'cpu', 'dtype': 'default'}},
        '40': {'class_type': 'DifferentialDiffusion', 'inputs': {'model': ['3', 0], 'strength': 1.0}},
        '4': {'class_type': 'ModelSamplingFlux', 'inputs': {'model': ['40', 0], 'max_shift': n[4]['widgets_values'][0], 'base_shift': n[4]['widgets_values'][1], 'width': CW, 'height': CH}},
        '6': {'class_type': 'VAELoader', 'inputs': {'vae_name': n[6]['widgets_values'][0]}},
        '31': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': n[31]['widgets_values'][0], 'type': 'qwen_image', 'device': 'default'}},
        '41': {'class_type': 'LoadImage', 'inputs': {'image': guide_name}},
        '42': {'class_type': 'LoadImageMask', 'inputs': {'image': mask_name, 'channel': 'red'}},
        '43': {'class_type': 'LoadImage', 'inputs': {'image': full_name}},
        '44': {'class_type': 'VAEEncode', 'inputs': {'pixels': ['41', 0], 'vae': ['6', 0]}},
        '45': {'class_type': 'SetLatentNoiseMask', 'inputs': {'samples': ['44', 0], 'mask': ['42', 0]}},
        '16': {'class_type': 'TextEncodeQwenImage21', 'inputs': {'clip': ['31', 0], 'vae': ['6', 0], 'prompt': PROMPT, 'negative_prompt': '', 'resolution': 0, 'images.image_1': ['41', 0]}},
        '20': {'class_type': 'KSampler', 'inputs': {'model': ['4', 0], 'positive': ['16', 0], 'negative': ['16', 1], 'latent_image': ['45', 0], 'seed': seed, 'steps': 50, 'cfg': 1, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': denoise}},
        '21': {'class_type': 'VAEDecode', 'inputs': {'samples': ['20', 0], 'vae': ['6', 0]}},
        '46': {'class_type': 'ImageCompositeMasked', 'inputs': {'destination': ['43', 0], 'source': ['21', 0], 'x': 0, 'y': 0, 'resize_source': False, 'mask': ['42', 0]}},
        '22': {'class_type': 'SaveImage', 'inputs': {'images': ['46', 0], 'filename_prefix': 'deleted_11s_locations_v02/' + out_prefix}},
    }


def submit_and_wait(api, out_path):
    r = g.post('/prompt', {'prompt': api, 'client_id': 'd11-door-' + uuid.uuid4().hex})
    t0 = time.monotonic()
    while True:
        h = g.get('/history/' + r['prompt_id']).get(r['prompt_id'])
        if h:
            if h.get('status', {}).get('status_str') == 'error':
                raise RuntimeError(h.get('status'))
            imgs = h.get('outputs', {}).get('22', {}).get('images', [])
            if imgs:
                blob = urllib.request.urlopen(g.BASE + '/view?' + urllib.parse.urlencode(imgs[0]), timeout=120).read()
                out_path.write_bytes(blob)
                return r['prompt_id'], round(time.monotonic() - t0, 1), blob
        time.sleep(5)


if __name__ == '__main__':
    guide, mask = make_guide()
    full_up, guide_up, mask_up = g.upload(SRC), g.upload(guide), g.upload(mask)
    for tag, denoise, seed in (('a', 0.75, 202610060101), ('b', 0.88, 202610060102)):
        out_name = f'LOC_04_CORRIDOR_v04{tag}'
        api = build_api(full_up, guide_up, mask_up, seed, denoise, out_name)
        (ROOT / 'api' / f'{out_name}.json').write_text(json.dumps(api, ensure_ascii=False, indent=2), encoding='utf-8')
        (ROOT / 'prompts' / f'{out_name}.txt').write_text(PROMPT, encoding='utf-8')
        out = ROOT / 'outputs' / f'{out_name}.png'
        print('QUEUED', out_name, flush=True)
        pid, sec, blob = submit_and_wait(api, out)
        # 마스크 밖 픽셀 불변 확인
        a = np.asarray(Image.open(SRC).convert('RGB')).astype(int)
        b = np.asarray(Image.open(out).convert('RGB')).astype(int)
        mk = np.zeros(a.shape[:2], bool)
        mk[:CH, :CW] = np.asarray(Image.open(mask).convert('L')) > 0
        outside_delta = int(np.abs(a - b)[~mk].max())
        rec = v.load_record()
        rec['runs'].append({'id': out_name, 'view': 'LOC_04_CORRIDOR', 'title': '복도 (문 마스크 인페인팅)', 'type': 'masked inpaint + composite',
                            'seed': seed, 'denoise': denoise, 'steps': 50, 'prompt_id': pid,
                            'source': 'outputs/LOC_04_CORRIDOR_v02.png', 'source_sha256': hashlib.sha256(SRC.read_bytes()).hexdigest(),
                            'guide': 'inpaint/door_guide.png', 'mask': 'inpaint/door_mask.png (crop 0,0,1280,1440; dilate 25, blur 10)',
                            'wiring': 'guide→VAEEncode→SetLatentNoiseMask(mask)→KSampler; guide→16 images.image_1 (resolution 0); DifferentialDiffusion; ImageCompositeMasked onto source',
                            'output': f'outputs/{out_name}.png', 'actual_size': list(struct.unpack('>II', blob[16:24])), 'elapsed_seconds': sec,
                            'sha256': hashlib.sha256(blob).hexdigest(), 'outside_mask_max_rgb_delta': outside_delta,
                            'status': 'generated', 'visual_review': 'pending'})
        v.save_record(rec)
        print('SAVED', out_name, sec, 's outside_delta', outside_delta, flush=True)
