"""COSTUME_01B v5 — 사용자 지적(2026-10-06) 수정: 보호대를 코트 소매 안으로, 어깨·깃 윗선의 허연 번짐 제거.

사용자 지적: "손목보호대가 코트 안으로 들어가야 하지 않아? 어깨 부분에 허옇게 뜨는 것 수정."
확대 확인(v4):
  - 보호대 3면 모두 소매 끝 바깥에 덧댄 모양. 왼쪽 측면은 보호대 윗부분이 소매를 덮음.
  - 허연 번짐: 정면 오른쪽 깃 윗부분, 양측면 목 쪽 깃 윗선, 후면 왼쪽 어깨 윗선.
    원인: v2 인페인팅의 부드러운 마스크 경계에서 원래 니트·배경과 새 코트가 반투명하게 섞임.
방법: fix_v3와 같은 패널 단위 국소 인페인팅(ComfyUI/Qwen). 소스는 v4 그대로(가이드 전처리 없음).
  깃·어깨 마스크는 위쪽 경계를 목·머리·배경(확정본과 같은 내용)에, 아래쪽 경계를 코트 안쪽에 둬 반투명 혼합이 다시 생기지 않게 한다.
  얼굴은 마스크 밖(정면 턱 약 262, 측면 턱 약 232).
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fix_v3 as f  # noqa: E402

V4 = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v4.png'

COLLAR = ("Image one is one view of a woman wearing a long camel wool coat over an oatmeal cotton top, with long black hair. In the marked area around the base of her neck "
          "and the top of her shoulders, the camel coat collar and shoulders are solid, opaque brushed camel wool with crisp clean top edges and a natural soft shadow where the "
          "collar meets the neck. Remove any translucent pale whitish haze or glow along the collar and shoulder line. The skin of the neck, the hair strands and the background "
          "stay natural and unchanged. Keep the face, the lapel shape and the lighting unchanged. No text or watermark.")
BRACE = ("Image one is one view of a woman in a long camel wool coat with a gray structured wrist brace on her anatomical LEFT wrist. In the marked area, the coat sleeve "
         "is worn OVER the brace: the camel cuff edge overlaps and hides the upper end of the brace, so the brace emerges from inside the sleeve. The brace is slimmer than the "
         "sleeve opening, with a small soft shadow under the cuff edge. Below the cuff, the lower part of the gray brace with its straps and thumb opening remains clearly "
         "visible over the wrist and the base of the hand. The hand and fingers stay natural and unchanged. No text or watermark.")

REG = [  # tag, panel x, rect, blur, denoise, prompt
    ('collar_front', 0, (330, 276, 520, 335), 5, 0.7, COLLAR),
    ('collar_profL', 640, (880, 252, 1060, 310), 5, 0.7, COLLAR),
    ('shoulders_rear', 1280, (1410, 262, 1810, 318), 5, 0.6, COLLAR),
    ('collar_profR', 1920, (2170, 252, 2340, 315), 5, 0.7, COLLAR),
    ('brace_front', 0, (440, 630, 560, 735), 5, 0.75, BRACE),
    ('brace_profL', 640, (868, 668, 992, 772), 5, 0.75, BRACE),
    ('brace_rear', 1280, (1368, 612, 1497, 722), 5, 0.75, BRACE),
]


def run(tag, seed_base):
    f.SRC = V4
    f.OUT_NAME = f'CHAR_01_서윤_COSTUME_01B_turnaround_v5{tag}'
    f.make_guide = lambda: V4
    f.REGIONS = [dict(tag=f'v5{tag}_{t}', px=px, rect=rect, blur=bl, denoise=dn, seed=seed_base + k, prompt=pr, ref2=None)
                 for k, (t, px, rect, bl, dn, pr) in enumerate(REG)]
    f.main()


if __name__ == '__main__':
    run('a', 2026100670)
    run('b', 2026100680)
