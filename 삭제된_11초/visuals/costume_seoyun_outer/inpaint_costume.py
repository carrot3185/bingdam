"""COSTUME_01B v2 — 확정 v02 시트의 얼굴을 픽셀 그대로 두고 목 아래만 인페인팅.

배경(2026-10-06): turnaround_a/b(빈 latent 생성)와 b_repaired(패널 전체 재생성)는 얼굴이 확정 v02와 달라져
사용자 지적·재검수로 불채택. 정면·오른쪽 측면은 b와 머리 위치가 어긋나 머리 합성도 불가.

방법(로케이션 복도 문 인페인팅과 같은 구조):
  확정 v02 시트 → VAEEncode → SetLatentNoiseMask(목 아래 마스크) → KSampler(denoise 1, DifferentialDiffusion)
  → VAEDecode → ImageCompositeMasked(같은 마스크)로 확정 시트에 합성 → 마스크 밖(얼굴·앞머리·윗머리) 픽셀 불변.
참조 슬롯:
  image_1 = 확정 v02 시트 ×0.75 (편집 대상 맥락)
  image_2 = turnaround_b_repaired ×0.5 (코트 길이·왼손목 보호대 노출·흰 운동화의 의상 참조; 얼굴은 마스크 밖이라 반영되지 않음)
  image_3 = 사용자 시안 LOOK 1, 목 아래 크롭(얼굴 제외) — 코트 원본 디자인
  image_4 = 사용자 시안 LOOK 3 운동화 제품 크롭
마스크: 패널별 수평선 아래 전체 폭(코트가 몸보다 넓으므로), 가우시안 블러로 경계를 부드럽게.
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

W, H, STEPS = 2560, 1536, 60
APPROVED = VIS / 'turnaround_qwen_v02/outputs/CHAR_01_서윤_turnaround_v02_HQ_repaired.png'
COSTUME_REF = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_b_repaired.png'
LOOKBOOK = ROOT / 'USER_LOOKBOOK_4LOOKS.webp'
# 패널 x 시작과 마스크 시작선 y. 턱 위치(확정 시트 실측): 정면 약 262, 측면 약 230.
LINES = {0: 300, 640: 268, 1280: 268, 1920: 268}
BLUR = 12
LOOK1_BODY = (0, 150, 360, 555)   # x, y, w, h — LOOK 1 목 아래부터 로퍼 위까지(얼굴 제외)
SNEAKER = gc.CROPS['look3_sneaker']
OUT_PREFIX = 'CHAR_01_서윤_COSTUME_01B_turnaround_v2'

PROMPT = (
"Image one is the approved four-view turnaround of this woman: front, strict profile facing the left edge, straight rear, strict profile facing the right edge. "
"Edit image one so that she wears an outdoor outfit, keeping her head, face, bangs and the hair on top of her head exactly as they are, and keeping each figure in the same position, "
"scale, standing pose and arm position. Image two shows the target outfit on the same four views and is the guide for coat length, sleeve length and where the wrist brace shows; "
"image three is the original styling reference for the coat; image four is the sneaker reference. "
"Over her unchanged oatmeal cotton top and loose charcoal trousers she wears a long single-breasted camel coat in soft brushed wool with a fine visible nap, notched lapels, "
"dropped shoulders and side welt pockets, worn open and unbelted. The coat is very long: in every view its hem reaches down to the ankles, so only a narrow band of charcoal trouser "
"leg shows above the sneakers. The open front shows the oatmeal top and the charcoal trousers between the coat panels. Her long black hair continues naturally from her head and "
"falls over the coat: over the shoulders and chest in front, down to the mid-back over the coat from behind. "
"On her feet are plain white leather lace-up low-top sneakers with white laces and flat white soles; the trouser hems rest on them. "
"The gray structured wrist brace with its straps and thumb opening stays on her anatomical LEFT wrist only, clearly visible below the left coat cuff in three views: in the FRONT view "
"on the wrist at the image-right side, in the REAR view on the wrist at the image-left side, and in the left-facing profile on the near arm. Her anatomical right wrist stays bare. "
"Arms rest alongside the body, hands visible and relaxed, not in pockets. No bag, no strap, no loafers, no belt, no scarf, no jewelry. "
"Keep the soft studio lighting and pale warm-gray backdrop of image one. Natural skin texture, individual hair strands, wool nap, seams and sneaker edges in clear focus, "
"without painterly smoothing. No text, labels or watermark."
)


def make_mask():
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    for x0, y in LINES.items():
        d.rectangle([x0, y, x0 + 639, H - 1], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(BLUR))
    # 블러가 패널 경계 사이로 번지지 않게 하는 처리는 불필요(패널 하단은 모두 255)
    path = ROOT / 'inpaint' / 'mask_below_neck.png'
    path.parent.mkdir(exist_ok=True)
    Image.merge('RGB', (m, m, m)).save(path)
    return path


def build(up, seed, out_name):
    nm = gc._wf_names()
    x, y, w, h = LOOK1_BODY
    sx, sy, sw, sh = SNEAKER
    api = {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': nm['unet'], 'weight_dtype': 'default'}},
        '3': {'class_type': 'QwenImage21Cache', 'inputs': {'model': ['1', 0], 'device': 'cpu', 'dtype': 'default'}},
        '50': {'class_type': 'DifferentialDiffusion', 'inputs': {'model': ['3', 0], 'strength': 1.0}},
        '4': {'class_type': 'ModelSamplingFlux', 'inputs': {'model': ['50', 0], 'max_shift': nm['max_shift'], 'base_shift': nm['base_shift'], 'width': W, 'height': H}},
        '6': {'class_type': 'VAELoader', 'inputs': {'vae_name': nm['vae']}},
        '31': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': nm['clip'], 'type': 'qwen_image', 'device': 'default'}},
        '7': {'class_type': 'LoadImage', 'inputs': {'image': up['approved']}},
        '8': {'class_type': 'LoadImage', 'inputs': {'image': up['costume_ref']}},
        '9': {'class_type': 'LoadImage', 'inputs': {'image': up['lookbook']}},
        '42': {'class_type': 'LoadImageMask', 'inputs': {'image': up['mask'], 'channel': 'red'}},
        '60': {'class_type': 'ImageScaleBy', 'inputs': {'image': ['7', 0], 'upscale_method': 'lanczos', 'scale_by': 0.75}},
        '61': {'class_type': 'ImageScaleBy', 'inputs': {'image': ['8', 0], 'upscale_method': 'lanczos', 'scale_by': 0.5}},
        '62': {'class_type': 'ImageCrop', 'inputs': {'image': ['9', 0], 'x': x, 'y': y, 'width': w, 'height': h}},
        '63': {'class_type': 'ImageCrop', 'inputs': {'image': ['9', 0], 'x': sx, 'y': sy, 'width': sw, 'height': sh}},
        '44': {'class_type': 'VAEEncode', 'inputs': {'pixels': ['7', 0], 'vae': ['6', 0]}},
        '45': {'class_type': 'SetLatentNoiseMask', 'inputs': {'samples': ['44', 0], 'mask': ['42', 0]}},
        '16': {'class_type': 'TextEncodeQwenImage21', 'inputs': {'clip': ['31', 0], 'vae': ['6', 0], 'prompt': PROMPT, 'negative_prompt': '', 'resolution': 0,
                                                                 'images.image_1': ['60', 0], 'images.image_2': ['61', 0], 'images.image_3': ['62', 0], 'images.image_4': ['63', 0]}},
        '20': {'class_type': 'KSampler', 'inputs': {'model': ['4', 0], 'positive': ['16', 0], 'negative': ['16', 1], 'latent_image': ['45', 0], 'seed': seed, 'steps': STEPS,
                                                    'cfg': 1, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': 1.0}},
        '21': {'class_type': 'VAEDecode', 'inputs': {'samples': ['20', 0], 'vae': ['6', 0]}},
        '46': {'class_type': 'ImageCompositeMasked', 'inputs': {'destination': ['7', 0], 'source': ['21', 0], 'x': 0, 'y': 0, 'resize_source': False, 'mask': ['42', 0]}},
        '22': {'class_type': 'SaveImage', 'inputs': {'images': ['46', 0], 'filename_prefix': 'deleted_11s_costume/' + out_name}},
    }
    (ROOT / 'prompts' / f'{out_name}.txt').write_text(PROMPT, encoding='utf-8')
    (ROOT / 'api' / f'{out_name}.json').write_text(json.dumps(api, ensure_ascii=False, indent=2), encoding='utf-8')
    return api


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(seeds):
    mask = make_mask()
    up = {'approved': g.upload(APPROVED), 'costume_ref': g.upload(COSTUME_REF), 'lookbook': g.upload(LOOKBOOK), 'mask': g.upload(mask)}
    rec = json.loads((ROOT / 'GENERATION_RECORD.json').read_text(encoding='utf-8'))
    for tag, seed in seeds:
        out_name = f'{OUT_PREFIX}_{tag}'
        api = build(up, seed, out_name)
        r = g.post('/prompt', {'prompt': api, 'client_id': 'd11-costume-inpaint-' + uuid.uuid4().hex, 'extra_data': {'extra_pnginfo': {'api_graph': api}}})
        entry = {'id': out_name, 'type': 'masked inpaint below neck on approved v02 sheet', 'seed': seed, 'prompt_id': r['prompt_id'], 'node_errors': r.get('node_errors', {}),
                 'references': {'edit_target': {'source': str(APPROVED.relative_to(VIS)), 'sha256': sha(APPROVED), 'slot': 'VAEEncode + images.image_1 (×0.75) + composite destination'},
                                'costume_guide': {'source': str(COSTUME_REF.relative_to(VIS)), 'sha256': sha(COSTUME_REF), 'slot': 'images.image_2 (×0.5)'},
                                'lookbook': {'source': str(LOOKBOOK.relative_to(VIS)), 'sha256': sha(LOOKBOOK), 'slot': f'images.image_3 crop {LOOK1_BODY} (no face), images.image_4 crop {SNEAKER}'},
                                'mask': {'source': str(mask.relative_to(VIS)), 'sha256': sha(mask), 'lines': LINES, 'blur': BLUR}},
                 'settings': {'steps': STEPS, 'cfg': 1, 'sampler': 'euler', 'scheduler': 'simple', 'denoise': 1.0, 'differential_diffusion': 1.0, 'encoder_resolution': 0},
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
                    break
            time.sleep(5)


if __name__ == '__main__':
    main([('a', 2026100621), ('b', 2026100622)])
