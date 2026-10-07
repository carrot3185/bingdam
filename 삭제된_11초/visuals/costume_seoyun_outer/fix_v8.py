"""COSTUME_01B v8 — 왼쪽 측면 보호대를 소매 안으로(원래 비스듬한 소매 끝선 유지), v5b에서 다시 시작.

v6~v7c 경과: 수평 사각형으로 소매 질감을 붙여 보호대를 덮었으나, v5b의 실제 소매 끝선은 팔 기울기를 따라
(878,738)→(968,755)로 비스듬해 왼쪽 모서리에 턱·꺾인 선이 반복 발생. 사용자 "다시 시도" 요청.
방법:
  - 가이드(numpy, 픽셀 복사만): v5b에서 원래 소매 끝선 위·소매 좌우선 사이 다각형 = 보호대 윗부분이 소매를 덮고 있던 영역만 선택.
    각 픽셀을 소매 기울기 방향으로 (dx=+12, dy=-66) 떨어진 소매 픽셀로 채운다(원본 소매만 참조, 보호대 상단 y≥695 미참조).
    소매 끝선은 원래 선을 그대로 사용한다.
  - ComfyUI/Qwen: (888,682)-(966,762) 국소 인페인팅 denoise 0.4로 질감·끝선 그림자만 다듬는다.
  v8(첫 시도): 다각형 왼쪽 경계가 실제 소매 가장자리 띠(x877~893)와 겹쳐 그림자선이 이중으로 생김 → v8b에서 다각형을 보호대 범위로 좁힘.
"""
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fix_v3 as f  # noqa: E402
import fix_v5 as v5  # noqa: E402

V5B = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v5b.png'
POLY = [(892, 688), (958, 688), (958, 753), (886, 740)]  # 보호대가 소매를 덮던 범위만(원래 소매 좌우 가장자리 띠 제외), 아래 변 = 원래 비스듬한 소매 끝선
DX, DY = 13, -66  # 소매 축 기울기(측정: 가장자리 x가 y 1px당 약 0.2 감소)를 따른 이동


def make_guide():
    a = np.asarray(Image.open(V5B).convert('RGB')).copy()
    m = Image.new('L', (a.shape[1], a.shape[0]), 0)
    ImageDraw.Draw(m).polygon(POLY, fill=255)
    ys, xs = np.nonzero(np.asarray(m))
    a[ys, xs] = a[ys + DY, xs + DX]
    p = ROOT / 'inpaint' / 'guide_v8_profL_sleeve_poly.png'
    Image.fromarray(a).save(p)
    return p


f.SRC = V5B
f.OUT_NAME = 'CHAR_01_서윤_COSTUME_01B_turnaround_v8b'
f.make_guide = make_guide
f.REGIONS = [dict(tag='v8b_brace_tuck_profL', px=640, rect=(888, 682, 966, 762), blur=3, denoise=0.4, seed=2026100699, prompt=v5.BRACE, ref2=None)]

if __name__ == '__main__':
    f.main()
