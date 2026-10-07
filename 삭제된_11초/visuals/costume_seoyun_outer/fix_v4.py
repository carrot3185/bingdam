"""COSTUME_01B v4 — v3 재검수 잔여 문제 국소 수정.

v3 검수(2026-10-06): 얼굴 3면 확정 v02와 픽셀 동일, 후면 보호대·코트 밑단 길이 해결.
남은 문제:
  1) 밑단을 늘린 구간 끝(밑단+48px)에서 배경 바닥에 가로 명암 경계(늘린 배경 그라데이션과 원래 배경의 불연속).
  2) 정면 양어깨 위쪽 띠: 마스크 시작선(300)이 어깨선(약 290)보다 아래라 v02의 오트밀 니트 어깨가 코트 어깨 위에 옅게 남음.
방법:
  - 가이드(PIL, 픽셀 선택만): v3에서 늘린 구간(밑단-300 ~ 밑단+50)의 배경 픽셀만 v2_a_brace1의 원래 배경으로 되돌린다
    (두 이미지 모두 배경색인 픽셀만, 저채도·밝기 150 초과 픽셀 기준).
  - ComfyUI/Qwen: 경계 띠(패널 전체 폭) denoise 0.4, 정면 어깨 띠 denoise 0.65. fix_v3와 같은 패널 단위 연쇄 합성.
  - 후면 보호대 영역과 얼굴은 마스크 밖.
"""
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fix_v3 as f  # noqa: E402

V3 = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v3.png'
ORIG = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v2_a_brace1.png'

SEAM_PROMPT = ("Image one is one view of a woman in a long camel wool coat, charcoal trousers and white sneakers in a photo studio. In the marked horizontal band, "
               "make the pale warm-gray studio floor and backdrop one smooth continuous surface with no horizontal line or tone step, and keep the coat hem, the soft shadow "
               "under it, the trousers and the sneakers exactly as they are. No text or watermark.")
SHOULDER_PROMPT = ("Image one is the front view of a woman wearing a long open camel wool coat over an oatmeal cotton round-neck top, with long black hair falling over her "
                   "image-left shoulder. In the marked band across her shoulders, the camel wool coat covers both shoulders completely up to the natural shoulder line, with its "
                   "collar sitting around the base of the neck; no pale knit fabric shows on top of the coat shoulders. Her long black hair strands fall naturally over the coat "
                   "on the image-left shoulder. The oatmeal round neckline stays visible only at the center between the lapels. Keep the face, neck skin, lapels, lighting and "
                   "background unchanged. No text or watermark.")


def make_guide():
    a = np.asarray(Image.open(V3).convert('RGB')).astype(int)
    o = np.asarray(Image.open(ORIG).convert('RGB')).astype(int)

    def is_bg(x):
        mx, mn = x.max(2), x.min(2)
        return (mx - mn < 18) & (x.mean(2) > 150)
    sel = np.zeros(a.shape[:2], bool)
    for i, (hem, xa, xb) in f.HEMS.items():
        y0, y1 = hem - f.BAND, hem + f.DELTA + 6
        band = np.zeros_like(sel)
        band[y0:y1, i * 640:(i + 1) * 640] = True
        sel |= band
    keep = sel & is_bg(a) & is_bg(o)
    out = a.copy()
    out[keep] = o[keep]
    p = ROOT / 'inpaint' / 'guide_v4_bg_restore.png'
    Image.fromarray(out.astype(np.uint8)).save(p)
    return p


f.SRC = V3
f.OUT_NAME = 'CHAR_01_서윤_COSTUME_01B_turnaround_v4'
f.make_guide = make_guide
f.REGIONS = [dict(tag=f'v4_seam{i}', px=i * 640, rect=(i * 640, hem + f.DELTA - 22, i * 640 + 639, hem + f.DELTA + 26), blur=6, denoise=0.4,
                  seed=2026100660 + i, prompt=SEAM_PROMPT, ref2=None) for i, (hem, xa, xb) in f.HEMS.items()]
f.REGIONS.append(dict(tag='v4_shoulders_front', px=0, rect=(140, 280, 520, 330), blur=4, denoise=0.65, seed=2026100665, prompt=SHOULDER_PROMPT, ref2=None))

if __name__ == '__main__':
    f.main()
