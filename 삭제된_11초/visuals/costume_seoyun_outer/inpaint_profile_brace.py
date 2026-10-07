"""COSTUME_01B v2_a — 왼쪽 측면(패널 2) 앞쪽 팔(해부학적 왼손목)에만 보호대를 국소 인페인팅.

v2_a 검수(2026-10-06): 얼굴 픽셀은 확정 v02와 동일, 정면·후면 보호대는 맞음. 왼쪽 측면의 보호대만 없다.
v2_a 패널 2(x=640..1279)를 ComfyUI ImageCrop으로 잘라 VAEEncode → SetLatentNoiseMask(손목 주변만) → KSampler
→ ImageCompositeMasked(같은 마스크)로 패널에 합성 → ImageCompositeMasked로 전체 시트 x=640에 넣는다.
마스크 밖 픽셀은 v2_a 그대로다. 얼굴은 마스크에서 600px 이상 떨어져 있다.
image_1 = v2_a 패널 2, image_2 = 확정 v02 시트의 같은 각도 보호대 크롭(860,600,160,240).
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

SRC = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v2_a.png'
APPROVED = VIS / 'turnaround_qwen_v02/outputs/CHAR_01_서윤_turnaround_v02_HQ_repaired.png'
PX, PW, PH = 640, 640, 1536
RECT = (860, 690, 980, 835)   # 시트 좌표, 소매 끝~손 위쪽
BLUR = 6
BRACE_CROP = (860, 600, 160, 240)
DENOISE = 0.9

PROMPT = (
"Image one is a left-facing strict profile photograph of a woman in a long open camel wool coat, and image two is a close detail of her original gray structured wrist brace "
"seen from the same side. On her near arm, the arm closest to the camera, which is her anatomical LEFT arm, add the matching gray soft wrist brace with its fastening straps "
"and thumb opening: it starts right at the camel coat cuff and covers the wrist and the base of the hand, clearly visible below the cuff. The fingers below the brace stay natural, "
"relaxed and the same size. Match the brace shape, gray color, straps and fabric texture of image two. Keep the camel coat sleeve, its cuff position, the coat body, "
"lighting and everything else unchanged. No text or watermark."
)


def make_mask():
    m = Image.new('L', (PW, PH), 0)
    x0, y0, x1, y1 = RECT
    ImageDraw.Draw(m).rectangle([x0 - PX, y0, x1 - PX, y1], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(BLUR))
    p = ROOT / 'inpaint' / 'mask_profileL_wrist.png'
    Image.merge('RGB', (m, m, m)).save(p)
    return p


def build(up, seed, out_name):
    nm = gc._wf_names()
    bx, by, bw, bh = BRACE_CROP
    api = {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': nm['unet'], 'weight_dtype': 'default'}},
        '3': {'class_type': 'QwenImage21Cache', 'inputs': {'model': ['1', 0], 'device': 'cpu', 'dtype': 'default'}},
        '50': {'class_type': 'DifferentialDiffusion', 'inputs': {'model': ['3', 0], 'strength': 1.0}},
        '4': {'class_type': 'ModelSamplingFlux', 'inputs': {'model': ['50', 0], 'max_shift': nm['max_shift'], 'base_shift': nm['base_shift'], 'width': PW, 'height': PH}},
        '6': {'class_type': 'VAELoader', 'inputs': {'vae_name': nm['vae']}},
        '31': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': nm['clip'], 'type': 'qwen_image', 'device': 'default'}},
        '7': {'class_type': 'LoadImage', 'inputs': {'image': up['src']}},
        '8': {'class_type': 'LoadImage', 'inputs': {'image': up['approved']}},
        '42': {'class_type': 'LoadImageMask', 'inputs': {'image': up['mask'], 'channel': 'red'}},
        '60': {'class_type': 'ImageCrop', 'inputs': {'image': ['7', 0], 'x': PX, 'y': 0, 'width': PW, 'height': PH}},
        '61': {'class_type': 'ImageCrop', 'inputs': {'image': ['8', 0], 'x': bx, 'y': by, 'width': bw, 'height': bh}},
        '44': {'class_type': 'VAEEncode', 'inputs': {'pixels': ['60', 0], 'vae': ['6', 0]}},
        '45': {'class_type': 'SetLatentNoiseMask', 'inputs': {'samples': ['44', 0], 'mask': ['42', 0]}},
        '16': {'class_type': 'TextEncodeQwenImage21', 'inputs': {'clip': ['31', 0], 'vae': ['6', 0], 'prompt': PROMPT, 'negative_prompt': '', 'resolution': 0,
                                                                 'images.image_1': ['60', 0], 'images.image_2': ['61', 0]}},
        '20': {'class_type': 'KSampler', 'inputs': {'model': ['4', 0], 'positive': ['16', 0], 'negative': ['16', 1], 'latent_image': ['45', 0], 'seed': seed, 'steps': 50,
                                                    'cfg': 1, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': DENOISE}},
        '21': {'class_type': 'VAEDecode', 'inputs': {'samples': ['20', 0], 'vae': ['6', 0]}},
        '46': {'class_type': 'ImageCompositeMasked', 'inputs': {'destination': ['60', 0], 'source': ['21', 0], 'x': 0, 'y': 0, 'resize_source': False, 'mask': ['42', 0]}},
        '47': {'class_type': 'ImageCompositeMasked', 'inputs': {'destination': ['7', 0], 'source': ['46', 0], 'x': PX, 'y': 0, 'resize_source': False}},
        '22': {'class_type': 'SaveImage', 'inputs': {'images': ['47', 0], 'filename_prefix': 'deleted_11s_costume/' + out_name}},
    }
    (ROOT / 'prompts' / f'{out_name}.txt').write_text(PROMPT, encoding='utf-8')
    (ROOT / 'api' / f'{out_name}.json').write_text(json.dumps(api, ensure_ascii=False, indent=2), encoding='utf-8')
    return api


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(seeds):
    mask = make_mask()
    up = {'src': g.upload(SRC), 'approved': g.upload(APPROVED), 'mask': g.upload(mask)}
    rec = json.loads((ROOT / 'GENERATION_RECORD.json').read_text(encoding='utf-8'))
    for tag, seed in seeds:
        out_name = f'CHAR_01_서윤_COSTUME_01B_turnaround_v2_a_brace{tag}'
        api = build(up, seed, out_name)
        r = g.post('/prompt', {'prompt': api, 'client_id': 'd11-costume-brace-' + uuid.uuid4().hex, 'extra_data': {'extra_pnginfo': {'api_graph': api}}})
        entry = {'id': out_name, 'type': 'local masked inpaint, left-profile near wrist only', 'seed': seed, 'prompt_id': r['prompt_id'], 'node_errors': r.get('node_errors', {}),
                 'references': {'edit_target': {'source': str(SRC.relative_to(VIS)), 'sha256': sha(SRC), 'slot': f'ImageCrop panel x={PX} → VAEEncode + images.image_1'},
                                'brace': {'source': str(APPROVED.relative_to(VIS)), 'sha256': sha(APPROVED), 'slot': f'ImageCrop {BRACE_CROP} → images.image_2'},
                                'mask': {'source': str(mask.relative_to(VIS)), 'sha256': sha(mask), 'rect_sheet': RECT, 'blur': BLUR}},
                 'settings': {'steps': 50, 'denoise': DENOISE, 'cfg': 1, 'sampler': 'euler', 'scheduler': 'simple', 'differential_diffusion': 1.0},
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
            time.sleep(4)


if __name__ == '__main__':
    main([('1', 2026100631), ('2', 2026100632)])
