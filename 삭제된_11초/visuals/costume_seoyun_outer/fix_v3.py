"""COSTUME_01B v3 — 추천본(v2_a_brace1) 재검수 지적 사항 국소 수정.

재검수(2026-10-06) 지적:
  1) 코트 밑단이 시안 LOOK 1보다 높다(바지 노출 약 115px). → 네 패널 모두 밑단을 48px 내림
  2) 후면 보호대가 상자를 쌓은 모양이고 손이 작게 오그라듦. → 확정 v02 후면 보호대 크롭을 참조로 재인페인팅
  3) 정면 목둘레: 마스크 경계에서 오른쪽 깃 윗부분과 목 사이가 흐릿하게 번짐. → 그 영역만 재인페인팅

방법:
  - 가이드(Python/PIL, 리사이즈만): 각 패널의 밑단 위 300px 구간(패널 전체 폭)을 세로로 348px까지 늘려 긴 밑단 형태를 만든다(실루엣 연속).
    복도 문 인페인팅에서 단색 가이드를 칠한 것과 같은 위치의 전처리다.
  - ComfyUI/Qwen: 영역별로 640x1536 패널을 ImageCrop → VAEEncode → SetLatentNoiseMask → KSampler(DifferentialDiffusion)
    → VAEDecode → ImageCompositeMasked(패널, 같은 마스크) → ImageCompositeMasked(전체 시트)로 연쇄 적용한다.
  - 얼굴은 어떤 마스크에도 들어가지 않는다(정면 목둘레 마스크 상단 282, 턱 약 262).
"""
from pathlib import Path
import sys, json, hashlib, struct, time, uuid, urllib.request, urllib.parse

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
VIS = ROOT.parent
sys.path.insert(0, str(VIS / 'locations_qwen_v01'))
sys.path.insert(0, str(ROOT))
import generate_locations as g  # noqa: E402
import generate_costume as gc  # noqa: E402

SRC = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v2_a_brace1.png'
APPROVED = VIS / 'turnaround_qwen_v02/outputs/CHAR_01_서윤_turnaround_v02_HQ_repaired.png'
OUT_NAME = 'CHAR_01_서윤_COSTUME_01B_turnaround_v3'
DELTA = 48
BAND = 300
# 측정값(재검수): 패널별 밑단 y, 코트 x 범위
HEMS = {0: (1235, 160, 492), 1: (1236, 820, 1088), 2: (1251, 1442, 1765), 3: (1238, 2094, 2382)}

HEM_PROMPT = ("Image one is one view of a woman wearing a long open camel wool coat over charcoal trousers and white sneakers. In the marked lower area, render the lower part "
              "of the long camel coat naturally: continuous soft brushed wool with a fine nap and the same color and folds as above, ending in one clean straight hem at ankle level "
              "with a soft shadow under the hem, so only a narrow band of the charcoal trousers shows between the hem and the white sneakers. No seam line across the coat, "
              "no second hem, no change to the sneakers or the background. No text or watermark.")
BRACE_PROMPT = ("Image one is a straight rear-view photograph of a woman in a long camel wool coat, and image two is a close detail of her original gray structured wrist brace "
                "seen from behind. On the wrist at the LEFT SIDE OF THE IMAGE, her anatomical LEFT wrist, render the matching gray soft wrist brace exactly like image two: "
                "a contoured orthosis that follows the forearm and wraps around the base of the thumb, with two or three hook-and-loop fastening straps, starting right at the "
                "camel coat cuff. Below it, a natural relaxed hand of normal size with fingers pointing down. The wrist on the right side of the image stays bare. "
                "Keep the coat sleeve, cuff, coat body, lighting and background unchanged. No text or watermark.")
COLLAR_PROMPT = ("Image one is the front view of a woman wearing a long open camel wool coat over an oatmeal cotton round-neck top. In the marked area at the base of her neck, "
                 "render a clean, crisp finish: the camel coat collar sits neatly around the back and sides of the neck, the top of the notched lapel on the image-right side has "
                 "a sharp clean edge, and the oatmeal round neckline of the top and the natural skin of the lower neck are clearly defined. Remove any haze or smudge. "
                 "Keep the face, hair, lapel shape, lighting and background unchanged. No text or watermark.")

# (패널 x, 영역 사각형[시트 좌표], blur, denoise, seed, prompt, image_2 크롭 또는 None)
REGIONS = []
for i, (hem, xa, xb) in HEMS.items():
    REGIONS.append(dict(tag=f'hem{i}', px=i * 640, rect=(i * 640, hem - 140, i * 640 + 639, hem + DELTA + 22),
                        blur=8, denoise=0.5, seed=2026100640 + i, prompt=HEM_PROMPT, ref2=None))
REGIONS.append(dict(tag='brace_rear', px=1280, rect=(1372, 660, 1505, 815), blur=6, denoise=0.9, seed=2026100650, prompt=BRACE_PROMPT, ref2=(1390, 600, 160, 240)))
REGIONS.append(dict(tag='collar_front', px=0, rect=(300, 282, 480, 340), blur=5, denoise=0.7, seed=2026100651, prompt=COLLAR_PROMPT, ref2=None))


def make_guide():
    im = Image.open(SRC).convert('RGB')
    gd = im.copy()
    for i, (hem, xa, xb) in HEMS.items():
        x0, x1 = i * 640, i * 640 + 640
        band = im.crop((x0, hem - BAND, x1, hem + 2)).resize((640, BAND + DELTA + 2), Image.LANCZOS)
        gd.paste(band, (x0, hem - BAND))
    p = ROOT / 'inpaint' / 'guide_v3_hem.png'
    gd.save(p)
    return p


def make_mask(r):
    m = Image.new('L', (640, 1536), 0)
    x0, y0, x1, y1 = r['rect']
    ImageDraw.Draw(m).rectangle([x0 - r['px'], y0, x1 - r['px'], y1], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(r['blur']))
    p = ROOT / 'inpaint' / f'mask_v3_{r["tag"]}.png'
    Image.merge('RGB', (m, m, m)).save(p)
    return p


def build(up):
    nm = gc._wf_names()
    api = {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': nm['unet'], 'weight_dtype': 'default'}},
        '3': {'class_type': 'QwenImage21Cache', 'inputs': {'model': ['1', 0], 'device': 'cpu', 'dtype': 'default'}},
        '50': {'class_type': 'DifferentialDiffusion', 'inputs': {'model': ['3', 0], 'strength': 1.0}},
        '4': {'class_type': 'ModelSamplingFlux', 'inputs': {'model': ['50', 0], 'max_shift': nm['max_shift'], 'base_shift': nm['base_shift'], 'width': 640, 'height': 1536}},
        '6': {'class_type': 'VAELoader', 'inputs': {'vae_name': nm['vae']}},
        '31': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': nm['clip'], 'type': 'qwen_image', 'device': 'default'}},
        '7': {'class_type': 'LoadImage', 'inputs': {'image': up['guide']}},
        '8': {'class_type': 'LoadImage', 'inputs': {'image': up['approved']}},
    }
    cur = ['7', 0]
    for k, r in enumerate(REGIONS):
        b = 100 + k * 20
        api[f'{b}'] = {'class_type': 'LoadImageMask', 'inputs': {'image': up['mask_' + r['tag']], 'channel': 'red'}}
        api[f'{b+1}'] = {'class_type': 'ImageCrop', 'inputs': {'image': cur, 'x': r['px'], 'y': 0, 'width': 640, 'height': 1536}}
        api[f'{b+2}'] = {'class_type': 'VAEEncode', 'inputs': {'pixels': [f'{b+1}', 0], 'vae': ['6', 0]}}
        api[f'{b+3}'] = {'class_type': 'SetLatentNoiseMask', 'inputs': {'samples': [f'{b+2}', 0], 'mask': [f'{b}', 0]}}
        enc = {'clip': ['31', 0], 'vae': ['6', 0], 'prompt': r['prompt'], 'negative_prompt': '', 'resolution': 0, 'images.image_1': [f'{b+1}', 0]}
        if r['ref2']:
            x, y, w, h = r['ref2']
            api[f'{b+4}'] = {'class_type': 'ImageCrop', 'inputs': {'image': ['8', 0], 'x': x, 'y': y, 'width': w, 'height': h}}
            enc['images.image_2'] = [f'{b+4}', 0]
        api[f'{b+5}'] = {'class_type': 'TextEncodeQwenImage21', 'inputs': enc}
        api[f'{b+6}'] = {'class_type': 'KSampler', 'inputs': {'model': ['4', 0], 'positive': [f'{b+5}', 0], 'negative': [f'{b+5}', 1], 'latent_image': [f'{b+3}', 0],
                                                          'seed': r['seed'], 'steps': 50, 'cfg': 1, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': r['denoise']}}
        api[f'{b+7}'] = {'class_type': 'VAEDecode', 'inputs': {'samples': [f'{b+6}', 0], 'vae': ['6', 0]}}
        api[f'{b+8}'] = {'class_type': 'ImageCompositeMasked', 'inputs': {'destination': [f'{b+1}', 0], 'source': [f'{b+7}', 0], 'x': 0, 'y': 0, 'resize_source': False, 'mask': [f'{b}', 0]}}
        api[f'{b+9}'] = {'class_type': 'ImageCompositeMasked', 'inputs': {'destination': cur, 'source': [f'{b+8}', 0], 'x': r['px'], 'y': 0, 'resize_source': False}}
        cur = [f'{b+9}', 0]
        (ROOT / 'prompts' / f'{OUT_NAME}__{r["tag"]}.txt').write_text(r['prompt'], encoding='utf-8')
    api['22'] = {'class_type': 'SaveImage', 'inputs': {'images': cur, 'filename_prefix': 'deleted_11s_costume/' + OUT_NAME}}
    (ROOT / 'api' / f'{OUT_NAME}.json').write_text(json.dumps(api, ensure_ascii=False, indent=2), encoding='utf-8')
    return api


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    guide = make_guide()
    up = {'guide': g.upload(guide), 'approved': g.upload(APPROVED)}
    masks = {}
    for r in REGIONS:
        mp = make_mask(r)
        masks[r['tag']] = mp
        up['mask_' + r['tag']] = g.upload(mp)
    api = build(up)
    rec = json.loads((ROOT / 'GENERATION_RECORD.json').read_text(encoding='utf-8'))
    r = g.post('/prompt', {'prompt': api, 'client_id': 'd11-costume-v3-' + uuid.uuid4().hex, 'extra_data': {'extra_pnginfo': {'api_graph': api}}})
    entry = {'id': OUT_NAME, 'type': 'local fixes on v2_a_brace1: hem lengthening (guide shift + inpaint), rear brace, front collar', 'prompt_id': r['prompt_id'],
             'node_errors': r.get('node_errors', {}),
             'references': {'source': {'file': str(SRC.relative_to(VIS)), 'sha256': sha(SRC)},
                            'guide': {'file': str(guide.relative_to(VIS)), 'sha256': sha(guide), 'method': f'PIL: 패널별 밑단 위 {BAND}px 구간(패널 전체 폭)을 세로 {BAND + DELTA}px로 늘림(lanczos)'},
                            'approved_brace': {'file': str(APPROVED.relative_to(VIS)), 'sha256': sha(APPROVED), 'slot': 'ImageCrop (1390,600,160,240) → images.image_2 (brace_rear만)'}},
             'regions': [{k: (v if k != 'prompt' else None) for k, v in x.items() if k != 'prompt'} | {'mask': str(masks[x['tag']].relative_to(VIS)), 'mask_sha256': sha(masks[x['tag']])} for x in REGIONS],
             'settings': {'steps': 50, 'cfg': 1, 'sampler': 'euler', 'scheduler': 'simple', 'differential_diffusion': 1.0, 'encoder_resolution': 0},
             'status': 'queued', 'visual_review': 'pending'}
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
