"""COSTUME_01B v6 — v5b의 왼쪽 측면 보호대를 소매 안으로.

v5 검수(2026-10-06): v5b가 깃·어깨 번짐 제거와 정면·후면 보호대 소매 안 처리를 모두 만족.
왼쪽 측면만 두 시드 모두 보호대 윗부분(y≈695~755)이 소매 위에 덧대어진 채 남음 → 텍스트 지시만으로 바뀌지 않음.
방법:
  - 가이드(PIL, 픽셀 복사만): 소매 영역(x 885~975)의 y 632~690 소매 질감을 소매 기울기에 맞춰 왼쪽 11px 옮겨 y 690~748에 복사해,
    원래 소매 끝(≈750)이 보호대 윗부분을 덮는 형태를 만든다. 소매 길이는 바꾸지 않는다.
  - ComfyUI/Qwen: (870,680)-(985,770) 국소 인페인팅 denoise 0.55로 소매 끝 그림자와 보호대 노출부를 자연스럽게 다듬는다.
"""
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fix_v3 as f  # noqa: E402
import fix_v5 as v5  # noqa: E402

V5B = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v5b.png'
X0, X1, SRC_Y, DST_Y, H, SHIFT = 885, 975, 632, 690, 58, -11


def make_guide():
    im = Image.open(V5B).convert('RGB')
    im.paste(im.crop((X0, SRC_Y, X1, SRC_Y + H)), (X0 + SHIFT, DST_Y))
    p = ROOT / 'inpaint' / 'guide_v6_profL_sleeve.png'
    im.save(p)
    return p


f.SRC = V5B
f.OUT_NAME = 'CHAR_01_서윤_COSTUME_01B_turnaround_v6'
f.make_guide = make_guide
f.REGIONS = [dict(tag='v6_brace_profL', px=640, rect=(870, 680, 985, 770), blur=5, denoise=0.55, seed=2026100690, prompt=v5.BRACE, ref2=None)]

if __name__ == '__main__':
    f.main()
