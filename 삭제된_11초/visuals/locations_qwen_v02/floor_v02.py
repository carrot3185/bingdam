"""삭제된 11초 — 로케이션 v02: 복도·엘리베이터(디테일 상향), 지하주차장(레퍼런스 디벨롭).

사용자 지시(2026-10-05): 집 내부 4뷰 확정. 복도·엘리베이터는 구조 유지·디테일만 상향.
지하주차장은 사용자 제공 레퍼런스(references/USER_REF_GARAGE.webp)로 디벨롭.
주차장 레퍼런스는 모델에 입력하지 않고 마감 요소를 텍스트로 옮겼다(실차 로고·번호판 복제 방지).

사용: python floor_v02.py [ID ...]   (기본: 정의 순서대로 전부, 이미 출력이 있으면 건너뜀)
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import generate_v02 as v  # noqa: E402

V01 = '../locations_qwen_v01/outputs/'
PHOTO = v.PHOTO
EMPTY = ' The space is empty and unoccupied: no people, no readable text, signage, logos or watermark.'

JOBS = {
 'LOC_04_CORRIDOR_v02': dict(view='복도와 엘리베이터 동선 (디테일 상향)', seed=202610052300,
  ref=V01 + 'LOC_04_CORRIDOR.png', ref2='outputs/LOC_03_ENTRY_v02.png', prompt=PHOTO + '''Using the corridor in <image1> as the scene, keep its camera position, framing, corridor length and layout exactly: the apartment doorway on the near left, the short corridor, the side recess on the left and the elevator at the far end. Refinish the whole corridor to the material detail of a well-kept upscale Korean apartment building.
The apartment entrance door is the same door that <image2> shows from inside: a plain warm-gray metal slab door with a slim frame and one fine vertical reveal line. Its corridor-side face carries a slim black digital keypad lock with a lever handle. The door stands open outward into the corridor, its leaf swung toward the camera along the near left wall and hinged on the near edge of the doorway, so the pale gray tiled shoe vestibule and the warm ivory interior light are visible through the opening.
The corridor floor is large-format warm gray porcelain tile with fine joints and a soft satin sheen. The walls are clad in pale greige large-format panels with thin dark reveal lines and slim dark recessed baseboards. The flat ceiling carries one continuous linear LED cove running down the corridor, a few small recessed downlights and one small smoke detector. Beside the door is a small plain unit-number plate with no readable characters.
At the far end, the elevator has hairline brushed stainless steel doors in a slim brushed steel frame, with a small call-button panel on its right.
Even neutral-white ceiling light fills the corridor, with a warm spill from the open apartment onto the floor near the doorway. Only the finishes and lighting detail change; the architecture and camera stay as in <image1>.''' + EMPTY),

 'LOC_06_GARAGE_MASTER': dict(view='지하주차장 기준 뷰 (레퍼런스 디벨롭)', seed=202610052310, prompt=PHOTO + '''The image is a wide architectural photograph of an upscale Korean apartment underground parking garage late at night, with a black linear-baffle ceiling, warm gray granite pavers and dark charcoal columns. The camera stands at adult eye height in the middle of the main driving aisle, looking straight down the aisle toward a far end wall, and the garage fills the frame.
Across the whole ceiling, long parallel matte black metal baffles run along the aisle with deep black voids between them. Long slim linear LED light lines are set into the baffles, some running along the aisle and some across it, and small black dome security cameras hang from the baffles.
The aisle floor is laid with rectangular flamed granite pavers in warm light gray with a fine speckle and thin joints. Dark granite strips separate the aisle from the parking bays on both sides.
On both sides stand square columns finished in matte dark charcoal, each front edge protected by a black-and-yellow striped rubber corner guard. Parking bays sit between the columns.
In the near left bay, a silver mid-size SUV is seen from its rear quarter, cropped by the left edge. Farther along the left wall is a glass-doored elevator lobby vestibule set into the charcoal wall, softly lit from inside.
In the right bays, a row of parked premium sedans and one coupe in black, deep navy, burgundy and white stand nose-in. Every car is plain and unbranded, with blank license plates.
At the far end, the aisle ends at a wall clad in warm horizontal timber slats, outlined by a thin cool blue LED line along its top and sides.
The aisle in the middle distance is completely open and evenly lit, with room for two adults to stand.
Crisp cool-white light falls from the linear LED lines, leaving sharp highlights on the car paint, soft reflections on the granite and slightly darker columns under deep black ceiling voids. The palette is black, charcoal and warm gray granite with a warm timber accent and a touch of cool blue; sleek, quiet, expensive and slightly cold.''' + EMPTY),

 'LOC_05_ELEVATOR_v02': dict(view='엘리베이터 내부 (디테일 상향)', seed=202610052320,
  ref=V01 + 'LOC_05_ELEVATOR.png', ref2='outputs/LOC_04_CORRIDOR_v02.png', prompt=PHOTO + '''Using the open elevator in <image1> as the scene, keep its camera position, head-on framing, door opening size and cabin depth. Refinish it to match the building corridor in <image2>: the corridor floor outside the threshold uses the same large-format warm gray porcelain tile, the walls beside the door use the same pale greige panels with thin dark reveals and slim dark baseboards, and the door frame and doors are the same hairline brushed stainless steel.
Inside the cabin, the side walls are hairline brushed stainless steel panels with fine vertical seams, the rear wall is a warm-gray textured laminate panel with one horizontal brushed steel handrail, the floor is dark gray stone-look tile, and the ceiling is a recessed soft diffused LED panel with a slim perimeter light.
Move the control panel onto the right side wall of the cabin, right next to the doorway at adult hand height, so a person stepping in reaches it with the right hand: a slim vertical brushed steel panel with small round buttons and a tiny dark floor display, without readable characters. The rear wall carries no panel or notice.
There is no large mirror and no reflection of people. Neutral-white cabin light, a little brighter than the corridor.''' + EMPTY),

 'LOC_06_GARAGE_DASHCAM': dict(view='블랙박스 시점 지하주차장 (디벨롭)', seed=202610052330,
  ref='outputs/LOC_06_GARAGE_MASTER.png', prompt='''Using the parking garage in the image as the actual location, generate a fixed dashcam still recorded from inside one car that is reverse-parked in a bay of this garage, so the car's front faces straight across the main driving aisle.
The dashcam is mounted high at the center of the windshield and has a mildly wide dashcam lens. Along the bottom of the frame, a dark dashboard edge and the lower windshield frame occupy a thin band; no steering wheel, rear-view mirror, driver or wiper is visible.
Directly in front of the car is the open granite-paved aisle, bright under the ceiling LED lines, where two adults could stand facing the windshield with their faces fully lit. Beyond the aisle, the opposite row of charcoal columns with black-and-yellow corner guards and parked plain unbranded cars with blank plates stands at middle distance. Above, the black linear baffle ceiling and its LED lines fill the top of the frame and recede to both sides.
Keep the same materials and lighting as the image: warm gray granite pavers, dark granite bay strips, matte charcoal columns, black baffles, cool-white linear light.
The image has subtle dashcam character: slightly limited dynamic range, mild compression softness and a faint highlight bloom around the LED lines, while faces in the open aisle area would still be clearly readable. No timestamp, recording icon or interface overlay, no license plate close-up, no people, no collision or damage, no readable text or logos, no watermark.'''),
 # --- 관찰 오류 보정 ---
 'LOC_04_CORRIDOR_v03': dict(view='복도 (문 바깥여닫이 보정)', seed=202610052340,
  ref='outputs/LOC_04_CORRIDOR_v02.png', prompt='''Change only the open apartment door on the near left of the image so that it opens outward into the corridor. Move its hinges to the near, camera-side edge of the doorway and swing the warm-gray door leaf out into the corridor, so the leaf stands roughly perpendicular to the left wall and projects toward the viewer. Its corridor-side face now turns toward the camera at a steep angle, with the slim black digital keypad lock and lever handle near its free outer edge. The doorway opening itself is unobstructed and shows the pale gray tiled shoe vestibule and warm ivory interior light. Where the old hinges and leaf stood on the far side of the opening, leave a clean slim door frame. This is a local edit: keep the camera, framing, corridor walls, floor tiles, ceiling cove light, elevator and lighting identical to the image. No people, readable text or watermark.'''),

 'LOC_06_GARAGE_DASHCAM_v02': dict(view='블랙박스 시점 지하주차장 (재구도)', seed=202610052350,
  ref='outputs/LOC_06_GARAGE_MASTER.png', prompt='''Using the parking garage in the image as the location and material reference, generate a genuinely different camera position: recompose the entire view as a fixed dashcam still from inside a car that is reverse-parked in one of the left-hand parking bays, its front facing straight across the main aisle. Do not reuse the original view down the aisle.
In this new view, the granite-paved driving aisle runs horizontally across the middle of the frame from left to right, directly in front of the car, open and evenly lit, where two adults could stand facing the windshield. Beyond the aisle, the opposite row of parking bays faces the camera: two or three plain unbranded cars parked nose-in with blank plates, separated by matte charcoal columns with black-and-yellow striped corner guards, with the dark charcoal back wall behind them. The black linear baffle ceiling with its cool-white LED lines and small dome cameras spans the top of the frame, its baffles now running left to right.
The dashcam is mounted high at the center of the windshield with a mildly wide dashcam lens. A thin dark dashboard edge and the lower windshield frame run along the bottom of the frame; no steering wheel, rear-view mirror, driver or wiper is visible.
Keep the materials and light of the image: warm gray granite pavers, dark granite bay strips, charcoal columns, black baffles, cool-white linear light, no timber end wall in view.
The still has subtle dashcam character: slightly limited dynamic range, mild compression softness and faint bloom around the LED lines, while the open aisle area stays clearly readable. No timestamp, recording icon or interface overlay, no license plate close-up, no people, no collision or damage, no readable text or logos, no watermark.'''),
 'LOC_06_GARAGE_DASHCAM_v03': dict(view='블랙박스 시점 지하주차장 (인물 제거)', seed=202610052360,
  ref='outputs/LOC_06_GARAGE_DASHCAM_v02.png', prompt='''Remove the three people standing around the white car in the far left parking bay, and continue the white car's side, the dark charcoal back wall, the parking bay floor and its white lines naturally where they stood. The white car remains parked nose-in, empty, with its doors closed. This is a local edit: keep the dashcam framing, dashboard edge, aisle, every other car, column, corner guard, ceiling baffle and LED line, and the lighting identical to the image. No people anywhere, no readable text or watermark.'''),
}


if __name__ == '__main__':
    todo = sys.argv[1:] or list(JOBS)
    for cid in todo:
        if (ROOT / 'outputs' / f'{cid}.png').exists():
            print('SKIP', cid, flush=True)
            continue
        j = JOBS[cid]
        v.PROMPTS[cid] = j['prompt']
        v.TITLES[cid] = j['view']
        v.run(cid, j['seed'], j.get('ref'), '', j.get('ref2'))
    print('ALL DONE', flush=True)
