"""COSTUME_01B v7c — v7b 왼쪽 측면 소매 끝 왼쪽 모서리의 작은 턱(약 10px) 정리.

방법:
  - 가이드(PIL, 픽셀 복사만): 소매 가장자리 띠 (874,700)-(892,713)을 (874,735)에 복사해 소매 끝선을 y≈748로 맞춤.
    이 띠는 보호대(x≥899) 밖이다.
  - ComfyUI/Qwen: (868,724)-(904,758) 국소 인페인팅 denoise 0.45.
"""
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fix_v3 as f  # noqa: E402
import fix_v7 as v7  # noqa: E402

V7B = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v7b.png'


def make_guide():
    im = Image.open(V7B).convert('RGB')
    im.paste(im.crop((874, 700, 892, 713)), (874, 735))
    p = ROOT / 'inpaint' / 'guide_v7c_profL_cuff.png'
    im.save(p)
    return p


f.SRC = V7B
f.OUT_NAME = 'CHAR_01_서윤_COSTUME_01B_turnaround_v7c'
f.make_guide = make_guide
f.REGIONS = [dict(tag='v7c_cuff_corner_profL', px=640, rect=(868, 724, 904, 758), blur=3, denoise=0.45, seed=2026100697, prompt=v7.PROMPT, ref2=None)]

if __name__ == '__main__':
    f.main()
