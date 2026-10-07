"""COSTUME_01B v13 — 후면 연장부 경계 단차·정면 작은 점을 가이드 단계에서 제거(v10a 바탕).

v12 검수(2026-10-06, 명암 1.8배 확대): 후면 가로줄은 박음선이 아니라 채우기 시작 행(631) 자체의 명암 단차.
Qwen 편집이 denoise 0.4에서 image_1 구조를 보존해 단차가 남음. 정면 점은 denoise 0.6으로도 남음
(소매 옆 주머니 입구 끝부분이 복사된 것).
방법:
  - 후면: fix_v12와 같은 가장자리 정렬 채움(행 631~747) + 시작 16행(631~646)은 원본과 선형 크로스페이드.
  - 정면 점: (183,684)-(197,702) ← 바로 아래 (183,704)-(197,722) 픽셀, (473,661)-(481,673) ← 바로 위 (473,647)-(481,659) 픽셀(처음 18x20 범위는 밝은 사각형이 생겨 축소)(같은 열의 소매 가장자리).
  - ComfyUI/Qwen: 후면 (1384,622)-(1480,750) denoise 0.4, 정면 점 주변 denoise 0.4.
"""
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fix_v3 as f  # noqa: E402
import fix_v11 as v11  # noqa: E402
import fix_v12 as v12  # noqa: E402
import fix_v9 as v9  # noqa: E402

FADE = 16
PATCHES = [((183, 684, 197, 702), (183, 704)), ((473, 661, 481, 673), (473, 647))]


def make_guide():
    src = np.asarray(Image.open(v11.V8B).convert('RGB')).astype(float)
    base = np.asarray(Image.open(v11.V10A).convert('RGB'))
    out = base.astype(float)
    d = v11.N - v11.C
    y0 = v11.C - v12.START
    for y in range(y0, v11.N + 3):
        ys = y - d
        l, r = v11.L(y) - v11.PAD_L, v11.R(y) + v11.PAD
        ls, rs = v11.L(ys) - v11.PAD_L, v11.R(ys) + v11.PAD
        xs = np.arange(int(np.floor(l)), int(np.ceil(r)) + 1)
        t = (xs - l) / (r - l)
        fill = src[ys, np.rint(ls + t * (rs - ls)).astype(int)]
        a = min(1.0, (y - y0 + 1) / FADE)
        out[y, xs] = a * fill + (1 - a) * out[y, xs]
    out = np.clip(np.rint(out), 0, 255).astype(np.uint8)
    for (x0, ya, x1, yb), (sx, sy) in PATCHES:
        out[ya:yb, x0:x1] = out[sy:sy + (yb - ya), sx:sx + (x1 - x0)]
    p = ROOT / 'inpaint' / 'guide_v13.png'
    Image.fromarray(out).save(p)
    return p


def run(tag, seed):
    f.SRC = v11.V10A
    f.OUT_NAME = f'CHAR_01_서윤_COSTUME_01B_turnaround_v13{tag}'
    f.make_guide = make_guide
    f.REGIONS = [
        dict(tag=f'v13{tag}_ext_rear_imgL', px=1280, rect=(1384, 622, 1480, 750), blur=4, denoise=0.4, seed=seed, prompt=v9.EXT, ref2=None),
        dict(tag=f'v13{tag}_patch_front_imgL', px=0, rect=(178, 680, 200, 706), blur=3, denoise=0.4, seed=seed + 1, prompt=v12.NOTCH, ref2=None),
        dict(tag=f'v13{tag}_patch_front_imgR', px=0, rect=(468, 656, 486, 678), blur=3, denoise=0.4, seed=seed + 2, prompt=v12.NOTCH, ref2=None),
    ]
    f.main()


if __name__ == '__main__':
    run('a', 2026100760)
