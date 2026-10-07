"""v02 관찰 오류 보정. 원본 출력은 보존하고 새 이름으로 저장한다.

- LOC_03_ENTRY_flip: 픽셀 좌우 반전(후처리, 모델 미사용). 식탁·신발장·도어록 좌우를 HOME_REVERSE와 일치시킴.
- HOME_REVERSE_v02: 현관 쪽 벽에 생긴 창·커튼·올리브나무 제거 (Qwen Edit).
- LOC_03_ENTRY_v02: 반전본에서 문 안쪽 경첩 제거 → 바깥여닫이로 읽히게 (Qwen Edit).
"""
from pathlib import Path
import json, hashlib, sys
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import generate_v02 as v  # noqa: E402

EDITS = {
 'HOME_REVERSE_v02': ('HOME_REVERSE', 'outputs/HOME_REVERSE.png', '''Remove only the exterior window on the rear wall at the left of the entry passage, together with its gray drapes, sheer curtain and the potted olive tree standing in front of it. Fill that whole section with continuous plain ivory wall matching the surrounding wall, with the same flush shadow-gap baseboard and the same warm cove light washing down from the ceiling. The only exterior window of this apartment is behind the camera, so the wall around the entrance has no window. Keep everything else identical: the camera view, the slate-gray sofa with cushions, round stone coffee table and gray rug on the left, the oak dining table with four charcoal chairs, laptop, glass and pendant on the right, the ivory kitchen, the recessed tiled vestibule and the gray entrance door with its digital lock, the oak floor, ceiling cove, downlights, air-conditioner diffuser and evening lighting. A local architectural correction, not a camera move or redesign. No people, captions or watermark.'''),
 'LOC_03_ENTRY_v02': ('LOC_03_ENTRY', 'outputs/LOC_03_ENTRY_flip.png', '''Remove only the visible hinge barrels on the interior side of the gray entrance door frame, so the door reads as an outward-opening apartment door whose hinges are on the corridor side: leave a clean slim door frame and a thin even gap along that edge. Keep everything else identical: the camera view, the door leaf, its lever handle and black digital lock on the door leaf, the tall ivory shoe cabinet with its lit niche, the two pairs of shoes, the pale gray porcelain tiles and metal threshold strip, the oak floor, the dining table and chair edges in the foreground, ivory walls, ceiling cove, downlight and air-conditioner diffuser, and the warm evening light. A local detail correction, not a redesign. No people, captions or watermark.'''),
}


def flip_entry():
    src = ROOT / 'outputs/LOC_03_ENTRY.png'
    dst = ROOT / 'outputs/LOC_03_ENTRY_flip.png'
    Image.open(src).transpose(Image.FLIP_LEFT_RIGHT).save(dst)
    rec = v.load_record()
    rec['runs'].append({'id': 'LOC_03_ENTRY_flip', 'view': 'LOC_03_ENTRY', 'type': 'post-process: horizontal flip (PIL), no model',
                        'source': 'outputs/LOC_03_ENTRY.png', 'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
                        'reason': 'HOME_REVERSE에서 현관을 볼 때 식탁·주방이 오른쪽, 신발장·도어록이 왼쪽. 원본 현관 뷰가 반대였음.',
                        'output': 'outputs/LOC_03_ENTRY_flip.png', 'sha256': hashlib.sha256(dst.read_bytes()).hexdigest(), 'status': 'generated'})
    v.save_record(rec)
    print('FLIPPED', flush=True)


if __name__ == '__main__':
    if not (ROOT / 'outputs/LOC_03_ENTRY_flip.png').exists():
        flip_entry()
    for out_name, (view, src, prompt) in EDITS.items():
        if (ROOT / 'outputs' / f'{out_name}.png').exists():
            continue
        v.PROMPTS[out_name] = prompt
        v.TITLES[out_name] = v.TITLES[view] + ' (보정)'
        v.run(out_name, 202610052200 + list(EDITS).index(out_name), src)
