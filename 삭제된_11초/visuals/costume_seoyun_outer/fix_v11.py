"""COSTUME_01B v11 — v10a 후면 왼팔 소매 연장부의 안쪽선 들쭉날쭉함·위쪽 턱 수정.

v10 검수(2026-10-06): v10a 채택 기준(정면 두 소매 깨끗, 후면 보호대 버클 스트랩 자연스러움, v10b 후면 보호대는 각진 플라스틱 느낌).
남은 문제: 후면 소매 안쪽선(x≈1460)에 들쭉날쭉한 세로선과 위쪽 턱.
원인(측정): v10의 안쪽선 직선 R(y)=1472-0.11(y-550)이 실제(1472@540 → 1466@652, 기울기 약 -0.055)보다 가팔라 약 5px 어긋남.
방법:
  - 가이드(numpy): v10a를 바탕으로 후면 행 641~747만, v8b 소스에서 수정한 R(y)=1472-0.055(y-550)로 같은 가장자리 정렬 복사.
    v10a의 후면 보호대(y≥748)와 정면은 그대로.
  - ComfyUI/Qwen: (1384,634)-(1480,750) denoise 0.4.
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
V10A = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v10a.png'
L = lambda y: 1408 - 0.09 * (y - 550)   # noqa: E731
R = lambda y: 1472 - 0.055 * (y - 550)  # noqa: E731
C, N, PAD, PAD_L = 661, 745, 2, 6  # 바깥(왼쪽) 여백 6px: v10a의 이전 연장부 가장자리까지 덮음


def make_guide():
    src = np.asarray(Image.open(V8B).convert('RGB'))
    out = np.asarray(Image.open(V10A).convert('RGB')).copy()
    d = N - C
    for y in range(C - 20, N + 3):
        ys = y - d
        l, r = L(y) - PAD_L, R(y) + PAD
        ls, rs = L(ys) - PAD_L, R(ys) + PAD
        xs = np.arange(int(np.floor(l)), int(np.ceil(r)) + 1)
        t = (xs - l) / (r - l)
        sx = np.rint(ls + t * (rs - ls)).astype(int)
        out[y, xs] = src[ys, sx]
    p = ROOT / 'inpaint' / 'guide_v11_rear_sleeve.png'
    Image.fromarray(out).save(p)
    return p


def run(tag, seed):
    f.SRC = V10A
    f.OUT_NAME = f'CHAR_01_서윤_COSTUME_01B_turnaround_v11{tag}'
    f.make_guide = make_guide
    f.REGIONS = [dict(tag=f'v11{tag}_ext_rear_imgL', px=1280, rect=(1384, 634, 1480, 750), blur=4, denoise=0.4, seed=seed, prompt=v9.EXT, ref2=None)]
    f.main()


if __name__ == '__main__':
    run('a', 2026100740)
    run('b', 2026100741)
