"""COSTUME_01B v10 — 정면·후면 소매 길이를 측면과 맞춤(사용자 지적 2026-10-06), 가장자리 정렬 방식.

v9a/b 검수: 소매 띠를 수직으로만 내려 붙여 비스듬한 소매 가장자리가 어긋남 → 띠 위쪽 경계에 계단·세로선. v9a는 후면 보호대도 소실.
방법(v8b에서 성공한 원리를 일반화):
  - 가이드(numpy, 픽셀 복사만): 측정한 소매 좌우 가장자리 직선 L(y), R(y) 사이에서, 대상 행 y∈[소매끝-20, 새 소매끝+2](원래 소매 끝 박음선·그림자보다 위에서 시작)의 각 픽셀을
    소스 행 ys=y-Δ의 같은 상대 위치 t=(x-L(y))/(R(y)-L(y)) 픽셀로 채운다(가장자리 2px 바깥까지 포함).
    가장자리 그림자선과 원래 소매 끝선이 새 위치에 그대로 이어진다.
  - ComfyUI/Qwen: 연장부 이음 denoise 0.4. 후면 왼팔은 소매 아래 보호대 끝부분을 확정 v02 후면 보호대 크롭(image_2) 참조로 denoise 0.9.
측정(v8b, 3배 확대 격자): 소매끝·가장자리는 아래 표.
"""
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fix_v3 as f  # noqa: E402
import fix_v9 as v9  # noqa: E402

V8B = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v8b.png'
# 이름: (L(y) 함수, R(y) 함수, 현재 소매 끝, 새 소매 끝)
SLEEVES = {
    'front_imgL_right': (lambda y: 137 - 0.08 * (y - 550), lambda y: 189.0, 713, 740),
    'front_imgR_left_brace': (lambda y: 474 + 0.044 * (y - 600), lambda y: 527.0, 686, 740),
    'rear_imgL_left_brace': (lambda y: 1408 - 0.09 * (y - 550), lambda y: 1472 - 0.11 * (y - 550), 661, 745),
}
PAD = 2


def make_guide():
    src = np.asarray(Image.open(V8B).convert('RGB'))
    out = src.copy()
    for L, R, c, n in SLEEVES.values():
        d = n - c
        for y in range(c - 20, n + 3):
            ys = y - d
            l, r = L(y) - PAD, R(y) + PAD
            ls, rs = L(ys) - PAD, R(ys) + PAD
            xs = np.arange(int(np.floor(l)), int(np.ceil(r)) + 1)
            t = (xs - l) / (r - l)
            sx = np.clip(np.rint(ls + t * (rs - ls)).astype(int), 0, src.shape[1] - 1)
            out[y, xs] = src[ys, sx]
    p = ROOT / 'inpaint' / 'guide_v10_sleeves.png'
    Image.fromarray(out).save(p)
    return p


def regions(seed):
    return [
        dict(tag='v10_ext_front_imgL', px=0, rect=(112, 686, 198, 752), blur=4, denoise=0.4, seed=seed, prompt=v9.EXT, ref2=None),
        dict(tag='v10_ext_front_imgR', px=0, rect=(466, 660, 536, 752), blur=4, denoise=0.4, seed=seed + 1, prompt=v9.EXT, ref2=None),
        dict(tag='v10_ext_rear_imgL', px=1280, rect=(1384, 634, 1480, 756), blur=4, denoise=0.5, seed=seed + 2, prompt=v9.EXT, ref2=None),
        dict(tag='v10_brace_rear_hand', px=1280, rect=(1382, 742, 1478, 800), blur=4, denoise=0.9, seed=seed + 3, prompt=v9.REAR_BRACE, ref2=(1390, 600, 160, 240)),
    ]


def run(tag, seed):
    f.SRC = V8B
    f.OUT_NAME = f'CHAR_01_서윤_COSTUME_01B_turnaround_v10{tag}'
    f.make_guide = make_guide
    f.REGIONS = regions(seed)
    f.main()


if __name__ == '__main__':
    run('a', 2026100720)
    run('b', 2026100730)
