"""COSTUME_01B v7 — v6 왼쪽 측면 소매 가장자리의 가이드 윤곽선 제거.

v6 검수(2026-10-06): 왼쪽 측면 보호대가 소매 끝 아래에서 나오는 형태로 수정됨.
남은 문제: 소매 질감을 붙인 가이드의 왼쪽 경계(x≈874, y 690~750)에 사각형 윤곽선이 희미하게 남음.
방법: (864,676)-(902,748) 국소 인페인팅 denoise 0.8. 보호대(y≥750)와 얼굴은 마스크 밖.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fix_v3 as f  # noqa: E402

V6 = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v6.png'
PROMPT = ("Image one is a left-facing profile of a woman in a long camel wool coat. In the marked narrow area, the camel coat sleeve hangs straight down with one clean, "
          "continuous outer edge from the elbow to the cuff, lying over the coat body behind it with a soft natural shadow along the edge. No rectangular outline, no step, "
          "no horizontal line across the sleeve. Same brushed camel wool texture and lighting as the surroundings. No text or watermark.")
f.SRC = V6
f.OUT_NAME = 'CHAR_01_서윤_COSTUME_01B_turnaround_v7'
f.make_guide = lambda: V6
f.REGIONS = [dict(tag='v7_sleeve_edge_profL', px=640, rect=(864, 676, 902, 748), blur=4, denoise=0.8, seed=2026100695, prompt=PROMPT, ref2=None)]

if __name__ == '__main__':
    f.main()
