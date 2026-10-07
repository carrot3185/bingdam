"""COSTUME_01B v7b — v6 왼쪽 측면 소매 가장자리의 꺾인 선 제거(가이드 복원 방식).

v7(denoise 0.8 인페인팅)로도 x≈874, y 690~750의 꺾인 선이 남음: Qwen 편집이 image_1의 구조를 다시 그림.
방법:
  - 가이드(PIL, 픽셀 복사만): v6에서 (864,680)-(890,748) 띠를 v5b 원래 픽셀로 되돌림.
    이 띠에는 원래 소매 가장자리·몸판·주머니선만 있고 보호대(x≥899)는 없다.
  - ComfyUI/Qwen: (862,676)-(902,752) 국소 인페인팅 denoise 0.45로 복원 띠와 붙인 소매 질감의 경계만 다듬는다.
"""
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fix_v3 as f  # noqa: E402
import fix_v7 as v7  # noqa: E402

V6 = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v6.png'
V5B = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v5b.png'
STRIP = (864, 680, 890, 748)


def make_guide():
    im = Image.open(V6).convert('RGB')
    im.paste(Image.open(V5B).convert('RGB').crop(STRIP), STRIP[:2])
    p = ROOT / 'inpaint' / 'guide_v7b_profL_edge.png'
    im.save(p)
    return p


f.SRC = V6
f.OUT_NAME = 'CHAR_01_서윤_COSTUME_01B_turnaround_v7b'
f.make_guide = make_guide
f.REGIONS = [dict(tag='v7b_sleeve_edge_profL', px=640, rect=(862, 676, 902, 752), blur=4, denoise=0.45, seed=2026100696, prompt=v7.PROMPT, ref2=None)]

if __name__ == '__main__':
    f.main()
