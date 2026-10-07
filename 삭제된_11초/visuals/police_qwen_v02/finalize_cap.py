"""repair_cap.py 결과(capfix)의 후처리 (Python 픽셀 처리, 생성 없음).

관찰된 문제 두 가지를 고친다.
1. Qwen이 모자 원단을 A보다 밝고 푸른 남색(중앙값 약 RGB 41,50,74)으로 바꿨다. A 모자 원단의 실측 중앙값은 약 RGB 34,36,40이다.
   → capfix의 모자 원단 픽셀(푸른 기가 도는 어두운 픽셀)만 골라 A 모자 원단의 채널별 평균·표준편차에 맞춘다.
      금색 자수·피부·머리카락·배경은 푸른 기가 없으므로 대상에서 빠진다.
2. 편집 박스 안의 배경 밝기가 원본보다 약 4~7 낮아져 사각 경계가 보였다.
   → 박스 마스크 ∩ 비배경(원본 또는 수정본에서 밝은 연회색이 아닌 픽셀, 4px 확장)만 수정본을 쓰고 나머지는 원본 픽셀을 유지한다.
"""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
spec = __import__('repair_cap')
PANELS, FEATHER = spec.PANELS, spec.FEATHER

L = lambda f: np.asarray(Image.open(f).convert('RGB')).astype(np.float64)
A = L(OUT / 'CHAR_06_turnaround_v02.png')
B0 = L(OUT / 'CHAR_07_turnaround_v02_patchfix.png')
B = L(OUT / 'CHAR_07_turnaround_v02_capfix.png')
H, W, _ = B.shape


def box_mask(cx, cy, mw, mh, mx, my):
    m = np.zeros((H, W), np.float64)
    m[cy + my:cy + my + mh, cx + mx:cx + mx + mw] = 1
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(FEATHER / 2))) / 255


def fabric(img):
    lum = img.mean(2)
    return ((img[..., 2] - img[..., 0]) > 8) & (lum < 120)


def a_fabric_pixels(cx, cy, mw, mh, mx, my):
    sl = (slice(cy + my, cy + my + mh), slice(cx + mx, cx + mx + mw))
    r = A[sl].reshape(-1, 3)
    lum = r.mean(1)
    return r[(lum < 70) & ((r[:, 2] - r[:, 0]) >= 0)]


result = B.copy()
stats = {}
for view, p in PANELS.items():
    cx, cy, mw, mh, mx, my = p
    sl = (slice(cy + my, cy + my + mh), slice(cx + mx, cx + mx + mw))
    sub = result[sl]
    fm = fabric(sub)
    src = sub[fm]
    ref = a_fabric_pixels(*p)
    mapped = (src - src.mean(0)) / (src.std(0) + 1e-6) * ref.std(0) + ref.mean(0)
    sub[fm] = np.clip(mapped, 0, 255)
    result[sl] = sub
    stats[view] = {'fabric_pixels': int(fm.sum()), 'before_mean': src.mean(0).round(1).tolist(), 'A_ref_mean': ref.mean(0).round(1).tolist(),
                   'after_mean': sub[fm].mean(0).round(1).tolist()}

bg = lambda img: (img.mean(2) > 185) & ((img.max(2) - img.min(2)) < 30)
nonbg = ~(bg(B0) & bg(result))
nonbg = np.asarray(Image.fromarray((nonbg * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.5))) / 255
boxes = np.clip(sum(box_mask(*p) for p in PANELS.values()), 0, 1)
mask = (boxes * nonbg)[..., None]
final = B0 * (1 - mask) + result * mask
out = OUT / 'CHAR_07_turnaround_v02_capfix_final.png'
Image.fromarray(np.clip(final.round(), 0, 255).astype(np.uint8)).save(out)

rec_p = ROOT / 'GENERATION_RECORD.json'
rec = json.loads(rec_p.read_text(encoding='utf-8'))
rec['runs'].append({'id': 'CHAR_07_turnaround_v02_capfix_final', 'character': 'CHAR_07', 'stage': 'Python post-process of capfix (no generation)',
                    'script': 'finalize_cap.py', 'inputs': ['outputs/CHAR_07_turnaround_v02_patchfix.png', 'outputs/CHAR_07_turnaround_v02_capfix.png', 'outputs/CHAR_06_turnaround_v02.png'],
                    'fabric_color_transfer': stats, 'output': 'outputs/' + out.name, 'sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
                    'status': 'generated', 'visual_review': 'pending'})
rec_p.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(stats, indent=1))
