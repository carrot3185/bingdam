"""COSTUME_01B v9 — 정면·후면 소매 길이를 측면과 맞춤(사용자 지적 2026-10-06).

측정(v8b): 손끝 높이는 모든 면이 약 y830. 소매 끝 → 손끝 거리: 측면 약 90~95, 후면 오른팔 약 80인데
정면 오른팔 약 125(소매 끝 705), 정면 왼팔(보호대) 약 150(682), 후면 왼팔(보호대) 약 175(655)로 짧다.
기준: 소매 끝 = 손끝 위 약 90px(손목). 정면 양쪽 → 약 740, 후면 왼팔 → 약 745.
방법:
  - 가이드(PIL, 픽셀 복사만): 각 소매의 (x0, 소매끝-K-Δ)~(x1, 소매끝+3) 띠를 Δ만큼 아래로 옮겨 붙여 소매 끝선을 내린다(K=30).
  - ComfyUI/Qwen 국소 인페인팅: 붙인 띠 전체(위쪽 경계 포함)와 소매 끝 그림자 denoise 0.5.
    후면 왼팔은 소매를 내리면 보호대가 거의 가려지므로, 측면과 같이 소매 아래 손등 아랫부분을 덮는 보호대 끝부분을
    확정 v02 후면 보호대 크롭(image_2)을 참조로 denoise 0.9로 그린다.
  - 얼굴은 마스크 밖.
"""
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fix_v3 as f  # noqa: E402

V8B = ROOT / 'outputs/CHAR_01_서윤_COSTUME_01B_turnaround_v8b.png'
K = 30
# 이름: (x0, x1, 현재 소매 끝 y, 새 소매 끝 y)
SLEEVES = {
    'front_imgL_right': (112, 188, 705, 740),       # 소매 폭만(안쪽 몸판 주머니선 x≈192~202 제외)
    'front_imgR_left_brace': (476, 534, 682, 740),  # 소매 폭만(안쪽 몸판 가장자리 x≈465~475 제외)
    'rear_imgL_left_brace': (1399, 1462, 656, 745),  # 소매 폭만(바깥 배경 제외)
}

EXT = ("Image one is one view of a woman in a long camel wool coat. In the marked area, the camel coat sleeve continues straight down to the wrist and ends in one clean cuff "
       "edge at the wrist, with a soft shadow under the cuff, like a normal full-length coat sleeve. Below the cuff the hand stays natural; if a gray wrist brace is there, "
       "only its lower end shows below the cuff. No seam line or step across the sleeve. Same brushed camel wool texture and lighting. No text or watermark.")
REAR_BRACE = ("Image one is a straight rear-view photograph of a woman in a long camel wool coat, and image two is a close detail of her gray structured wrist brace seen from "
              "behind. On the wrist at the LEFT SIDE OF THE IMAGE, her anatomical LEFT wrist, the camel coat sleeve covers the forearm and the upper part of the brace; "
              "right below the cuff edge, the lower end of the matching gray brace is clearly visible, wrapping the wrist and the back of the base of the hand, with the edge of "
              "a fastening strap and the thumb wrap at the side, exactly in the material and color of image two. Below it, the natural relaxed hand with fingers pointing down. "
              "The wrist on the right side of the image stays bare. Keep the coat sleeve, cuff, coat body, lighting and background unchanged. No text or watermark.")


def make_guide():
    im = Image.open(V8B).convert('RGB')
    for x0, x1, c, n in SLEEVES.values():
        d = n - c
        im.paste(im.crop((x0, c - K - d, x1, c + 3)), (x0, c - K))
    p = ROOT / 'inpaint' / 'guide_v9_sleeves.png'
    im.save(p)
    return p


def regions(seed):
    return [
        dict(tag='v9_ext_front_imgL', px=0, rect=(104, 667, 196, 762), blur=4, denoise=0.5, seed=seed, prompt=EXT, ref2=None),
        dict(tag='v9_ext_front_imgR', px=0, rect=(468, 644, 542, 762), blur=4, denoise=0.5, seed=seed + 1, prompt=EXT, ref2=None),
        dict(tag='v9_ext_rear_imgL', px=1280, rect=(1391, 618, 1470, 760), blur=4, denoise=0.5, seed=seed + 2, prompt=EXT, ref2=None),
        dict(tag='v9_brace_rear_hand', px=1280, rect=(1382, 738, 1478, 800), blur=4, denoise=0.9, seed=seed + 3, prompt=REAR_BRACE, ref2=(1390, 600, 160, 240)),
    ]


def run(tag, seed):
    f.SRC = V8B
    f.OUT_NAME = f'CHAR_01_서윤_COSTUME_01B_turnaround_v9{tag}'
    f.make_guide = make_guide
    f.REGIONS = regions(seed)
    f.main()


if __name__ == '__main__':
    run('a', 2026100700)
    run('b', 2026100710)
