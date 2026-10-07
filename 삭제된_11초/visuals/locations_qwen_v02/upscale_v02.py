"""선정 로케이션 이미지 업스케일 (사용자 요청 2026-10-06: 배경 해상도 상향).

내용을 바꾸지 않는 픽셀 업스케일만 사용한다(확산 재생성 없음 → 확정 이미지의 구도·가구·마감 유지).
ComfyUI: LoadImage → UpscaleModelLoader(RealESRGAN_x4plus) → ImageUpscaleWithModel(x4) → ImageScale(lanczos, 5120x2880) → SaveImage.
후처리(PIL): ESRGAN 결과와 원본 lanczos 2배 확대를 50:50 혼합 + UnsharpMask(r1.6, 40%, t2).
ESRGAN 단독은 나뭇결·잎이 뭉개지고, lanczos 단독은 흐려서 시험 비교 후 혼합을 채택했다(HOME_MASTER_b 100% 크롭 비교).
출력: outputs_5k/<원본 이름>_5k.png

사용: python upscale_v02.py [파일명 ...]   (기본: SELECTION.json의 선정 이미지 전체)
"""
from pathlib import Path
import sys, json, hashlib, struct, time, uuid, urllib.request, urllib.parse, io
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import generate_v02 as v  # noqa: E402
g = v.g

TW, TH = 5120, 2880
MODEL = 'RealESRGAN_x4plus.safetensors'
OUT = ROOT / 'outputs_5k'
OUT.mkdir(exist_ok=True)


def selected():
    s = json.loads((ROOT / 'SELECTION.json').read_text(encoding='utf-8'))
    files = list(s['selected_outputs'].values()) + list(s.get('floor_garage_selected', {}).values())
    return [ROOT / f for f in files]


def upscale(src):
    up = g.upload(src)
    name = src.stem + '_5k'
    api = {
        '1': {'class_type': 'LoadImage', 'inputs': {'image': up}},
        '2': {'class_type': 'UpscaleModelLoader', 'inputs': {'model_name': MODEL}},
        '3': {'class_type': 'ImageUpscaleWithModel', 'inputs': {'upscale_model': ['2', 0], 'image': ['1', 0]}},
        '4': {'class_type': 'ImageScale', 'inputs': {'image': ['3', 0], 'upscale_method': 'lanczos', 'width': TW, 'height': TH, 'crop': 'disabled'}},
        '5': {'class_type': 'SaveImage', 'inputs': {'images': ['4', 0], 'filename_prefix': 'deleted_11s_locations_v02_5k/' + name}},
    }
    r = g.post('/prompt', {'prompt': api, 'client_id': 'd11-up-' + uuid.uuid4().hex})
    t0 = time.monotonic()
    while True:
        h = g.get('/history/' + r['prompt_id']).get(r['prompt_id'])
        if h:
            if h.get('status', {}).get('status_str') == 'error':
                raise RuntimeError(h.get('status'))
            imgs = h.get('outputs', {}).get('5', {}).get('images', [])
            if imgs:
                blob = urllib.request.urlopen(g.BASE + '/view?' + urllib.parse.urlencode(imgs[0]), timeout=300).read()
                out = OUT / f'{name}.png'
                esr = Image.open(io.BytesIO(blob)).convert('RGB')
                lz = Image.open(src).convert('RGB').resize((TW, TH), Image.LANCZOS)
                Image.blend(lz, esr, 0.5).filter(ImageFilter.UnsharpMask(radius=1.6, percent=40, threshold=2)).save(out)
                blob = out.read_bytes()
                return {'source': str(src.relative_to(ROOT)), 'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
                        'output': str(out.relative_to(ROOT)), 'size': list(struct.unpack('>II', blob[16:24])),
                        'sha256': hashlib.sha256(blob).hexdigest(), 'prompt_id': r['prompt_id'],
                        'elapsed_seconds': round(time.monotonic() - t0, 1)}
        time.sleep(3)


if __name__ == '__main__':
    files = [ROOT / 'outputs' / f for f in sys.argv[1:]] or selected()
    recp = ROOT / 'UPSCALE_RECORD.json'
    rec = json.loads(recp.read_text(encoding='utf-8')) if recp.exists() else {
        'method': f'{MODEL} x4 → lanczos {TW}x{TH} (ComfyUI) 결과와 원본 lanczos 확대를 50:50 혼합 + UnsharpMask(1.6, 40%, 2). 픽셀 업스케일만, 확산 재생성 없음.',
        'date': '2026-10-06', 'runs': []}
    for f in files:
        e = upscale(f)
        rec['runs'] = [x for x in rec['runs'] if x['source'] != e['source']] + [e]
        recp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
        print('UPSCALED', e['output'], e['size'], e['elapsed_seconds'], 's', flush=True)
    print('ALL DONE', flush=True)
