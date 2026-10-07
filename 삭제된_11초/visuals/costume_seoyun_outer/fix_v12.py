"""COSTUME_01B v12 — 후면 소매단 박음선 중복 제거 + 정면 안쪽 가장자리 작은 점 정리.

v11 검수(2026-10-06): v11a 후면 안쪽선 정리됨. 남은 문제:
  1) 후면 연장부 위쪽 y≈641 가로줄 = 원래 소매 끝 위 약 20px의 소매단 박음선. 채우기를 소매끝-20에서 시작해 옛 박음선이 남고
     새 소매 끝에도 복사돼 두 줄이 됨. → 시작 행을 소매끝-30(631)으로 올려 다시 채움(v10a 바탕, fix_v11과 같은 가장자리 정렬).
  2) 정면 채우기 시작 행의 안쪽 가장자리 작은 어두운 점 2곳(약 3x6px): (187,692), (476,665). → 국소 인페인팅 denoise 0.6.
"""
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fix_v3 as f  # noqa: E402
import fix_v9 as v9  # noqa: E402
import fix_v11 as v11  # noqa: E402

START = 30
NOTCH = ("Image one is the front view of a woman in a long camel wool coat. In the marked tiny area at the inner edge of the coat sleeve, the sleeve edge continues as one "
         "smooth straight line with the same soft shading as above and below it; no dark spot or notch. Same camel wool texture and lighting. No text or watermark.")


def make_guide():
    src = np.asarray(Image.open(v11.V8B).convert('RGB'))
    out = np.asarray(Image.open(v11.V10A).convert('RGB')).copy()
    d = v11.N - v11.C
    for y in range(v11.C - START, v11.N + 3):
        ys = y - d
        l, r = v11.L(y) - v11.PAD_L, v11.R(y) + v11.PAD
        ls, rs = v11.L(ys) - v11.PAD_L, v11.R(ys) + v11.PAD
        xs = np.arange(int(np.floor(l)), int(np.ceil(r)) + 1)
        t = (xs - l) / (r - l)
        out[y, xs] = src[ys, np.rint(ls + t * (rs - ls)).astype(int)]
    p = ROOT / 'inpaint' / 'guide_v12_rear_sleeve.png'
    Image.fromarray(out).save(p)
    return p


def run(tag, seed):
    f.SRC = v11.V10A
    f.OUT_NAME = f'CHAR_01_서윤_COSTUME_01B_turnaround_v12{tag}'
    f.make_guide = make_guide
    f.REGIONS = [
        dict(tag=f'v12{tag}_ext_rear_imgL', px=1280, rect=(1384, 622, 1480, 750), blur=4, denoise=0.4, seed=seed, prompt=v9.EXT, ref2=None),
        dict(tag=f'v12{tag}_notch_front_imgL', px=0, rect=(180, 684, 196, 702), blur=2, denoise=0.6, seed=seed + 1, prompt=NOTCH, ref2=None),
        dict(tag=f'v12{tag}_notch_front_imgR', px=0, rect=(469, 656, 485, 674), blur=2, denoise=0.6, seed=seed + 2, prompt=NOTCH, ref2=None),
    ]
    f.main()


if __name__ == '__main__':
    run('a', 2026100740)
    run('b', 2026100750)
