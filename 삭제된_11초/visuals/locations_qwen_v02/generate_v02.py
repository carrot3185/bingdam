"""삭제된 11초 — 로케이션 v02 (집 내부 4뷰).

v01 파이프라인(generate_locations.py)의 업로드·제출 함수를 재사용한다.
변경: 2560x1440, 60 steps, 마감·디테일 프롬프트(사용자 레퍼런스: haanong.com project7-sr).
레퍼런스 사진은 모델에 입력하지 않고, 관찰한 마감 요소를 텍스트로만 옮겼다.

사용: python generate_v02.py HOME_MASTER [--seed N] [--ref outputs/HOME_MASTER.png] [--tag a]
"""
from pathlib import Path
import sys, json, hashlib, struct, time, uuid, urllib.request, urllib.parse, argparse

ROOT = Path(__file__).resolve().parent
V01 = ROOT.parent / 'locations_qwen_v01'
sys.path.insert(0, str(V01))
import generate_locations as g  # noqa: E402

for sub in ['outputs', 'prompts', 'workflows', 'api', 'references']:
    (ROOT / sub).mkdir(parents=True, exist_ok=True)

W, H, STEPS = 2560, 1440, 60
EDIT_ENCODER_RES = 1536  # v01과 동일; 편집 참조 처리 크기 (출력 해상도와 별개)

PHOTO = ('Professional interior-design portfolio photograph: full-frame camera with a wide rectilinear lens at adult eye height, '
         'perfectly vertical walls and clean two-point perspective, balanced high-dynamic-range exposure so the window and the darker corners both hold detail, '
         'crisp micro-detail in wood grain, fabric weave, stone veining and painted wall texture. ')

COMMON = (' Empty unoccupied location, no people, no family photographs, no captions, readable text or watermark. '
          'Realistic architectural proportions without fisheye distortion. A carefully finished, attainable mid-sized Korean apartment, '
          'tasteful and well kept but not a penthouse: single-height ceiling, no double-height void, no staircase, no stacked-stone feature wall, '
          'no glossy marble showroom floor.')

MATERIALS = ('Finishes: wide-plank natural pale oak floor with visible grain, fine board seams and a matte finish; ivory walls with flush shadow-gap baseboards; '
             'a flat ivory ceiling with a recessed perimeter cove emitting soft warm indirect light, a few small recessed downlights and one slim linear air-conditioner diffuser. ')

PROMPTS = {
 'HOME_MASTER': PHOTO + '''The image shows the connected kitchen, dining area and living room of a lived-in modern Korean apartment at blue-hour evening. The camera stands just inside the short entrance passage, looking diagonally across the space, with the room filling the frame.
On the near left edge, a partial ivory passage wall and a small patch of large-format pale gray porcelain entry tile frame the view.
On the left midground is an open L-shaped kitchen: flush handleless matte ivory cabinetry with fine vertical reveals, a warm light-gray stone-look countertop with a thin edge, a honed pale stone backsplash with subtle veining, an integrated slim hood and plain built-in appliances. There is no high island.
In front of the kitchen stands one solid natural oak rectangular dining table with softened edges and exactly four chairs, two on each long side, each with a slim oak frame and a charcoal fabric seat. One slim matte cream pendant hangs low above the table. A closed plain silver laptop and one clear water glass sit on the table; nothing else.
On the right midground, a low deep slate-gray woven-fabric sofa faces inward, with one dusty-blue and one oatmeal cushion and a folded throw. In front of it is a small round coffee table with a dark-veined stone top on a slim black metal base, over a low-pile warm gray rug. Against the right wall beside the sofa, a slim dark bronze metal open shelf holds a few books and two matte ceramic vases, next to a small olive tree in a matte ceramic planter.
At the far end, a broad window spans most of the wall, with layered sheer ivory curtains and heavier warm-gray linen drapes hung from a recessed ceiling curtain pocket, showing deep blue evening sky and distant apartment-block lights.
''' + MATERIALS + '''A clear continuous floor path runs from the near entrance beside the dining table into the living room, wide enough for two actors. Overlapping wall edges, furniture at distinct distances and floorboards converging toward the far window create readable foreground, middle distance and background. Layered lighting: the warm pendant and warm ceiling cove glow against the cool blue window light, gentle falloff, soft realistic shadows, nothing blown out. The palette is ivory, natural oak, slate gray and muted charcoal; calm and carefully kept, with a quiet hint of tension.''' + COMMON,

 'HOME_REVERSE': PHOTO + '''Using the apartment in the image as the actual architecture, materials, furniture and lighting, generate a new photographic reverse view from near the far living-room window looking back toward the entrance. Rotate the viewpoint inside the same physical apartment; preserve the room topology and every furniture design, material and color.
The camera is at adult eye height and the room fills the frame. The slate-gray sofa with its cushions and the round stone coffee table now occupy the near left side. The oak dining table with exactly four charcoal-seat chairs, the closed silver laptop, the water glass and the slim cream pendant stand to the right of the central walkway, with the flush ivory kitchen behind them on the right.
At the back center, the walkway leads into a short entry passage that ends in a recessed shoe-removal vestibule of pale gray porcelain tile. The single gray apartment entrance door is centered on the rear wall of that vestibule, directly at the end of the walkway, with its handle and interior digital lock mounted on the door leaf. A flush matte ivory shoe cabinet lines the left side of the vestibule. There is exactly one entrance door and no other door beside the vestibule.
''' + MATERIALS + '''Foreground sofa and coffee table, middle-distance dining chairs and kitchen, and the far recessed entry form three distinct distance layers. The path from the table to the door is continuous and free of furniture. Warm pendant and cove light, with cool evening window light falling from behind the camera, belong to the same evening as the reference. This is the same apartment seen from the opposite end, not a mirrored duplicate or a redesigned home.''' + COMMON,

 'LOC_02_KITCHEN': PHOTO + '''Using the apartment in the image as the actual room, generate a genuinely different camera position from inside its left-side kitchen, looking out across the counter toward the dining table and the far living room. Preserve the layout, materials, furniture designs and evening light; only move the camera.
The camera stands at adult eye height behind the kitchen worktop, looking diagonally right. In the lower-left foreground are the warm light-gray stone-look countertop, one undermount stainless sink with a single matte faucet and one plain saucepan; this is the only sink in the kitchen. At the near left edge, part of the flush handleless ivory cabinetry with fine reveals and the honed stone backsplash.
In the middle distance, the oak dining table with exactly four charcoal-seat chairs, the closed silver laptop, the water glass and the slim cream pendant are fully visible through the open kitchen; the counter is low and never blocks the sightline to a person seated at the entry-side short end of the table. Farther back, smaller with distance, the slate-gray sofa, round stone coffee table, olive tree and the broad curtained blue-evening window. The entry-side end of the table has a visible free path toward the entrance passage.
''' + MATERIALS + '''Near worktop, middle-distance dining area and far living room stay individually readable and in architectural focus. Warm pendant and cove light with weak cool window light, matching the reference.''' + COMMON,

 'LOC_03_ENTRY': PHOTO + '''Using the apartment in the image as the architecture, materials and lighting reference, generate a photographic view from the dining-side passage toward the recessed shoe-removal vestibule and the gray entrance door.
The camera is at adult eye height several steps back from the door, framing the passage and the full vestibule with enough floor for two adults to stand and one to reach the handle. In the near foreground, the edge of the oak dining table and one charcoal-seat oak chair partly enter the frame.
The wide-plank oak walkway recedes and meets a slim metal threshold strip at the large-format pale gray porcelain entry tiles. At the back, one plain warm-gray metal apartment door with a slim frame, a single lever handle and a black interior digital lock mounted directly on the door leaf, not on the wall. Along one side of the vestibule stands a tall flush matte ivory shoe cabinet with handleless doors and a recessed open niche lit by a thin warm LED strip. Two pairs of simple shoes rest tidily beside it, out of the central path. A small recessed ceiling downlight above the vestibule. The door is closed; it opens outward into the communal corridor. No bag or loose props.
''' + MATERIALS + '''Warm living-room light comes from behind the camera while the soft neutral vestibule downlight keeps the lock and surrounding wall readable. Overlapping table edge, passage walls and recessed door create connected depth without turning the entry into a spacious lobby.''' + COMMON,
}

TITLES = {'HOME_MASTER': '집 전체 · 현관에서 거실', 'HOME_REVERSE': '집 역방향 · 거실에서 현관',
          'LOC_02_KITCHEN': '주방에서 식탁·거실', 'LOC_03_ENTRY': '현관과 출구'}
BASE_SEED = 202610052100


def build(cid, out_name, seed, reference=None, reference2=None):
    text = PROMPTS[cid]
    w = json.loads(g.TEMPLATE.read_text(encoding='utf-8-sig'))
    n = {x['id']: x for x in w['nodes']}
    for node in w['nodes']:
        node.pop('widgets_values_named', None)
    enc_res = EDIT_ENCODER_RES if reference else 1024
    n[3]['widgets_values'] = ['cpu', 'default']
    n[10]['widgets_values'] = ['Manual Input', '16:9', 3.69, W, H, '32', 'Center Crop (Fill)', 'lanczos', .5, .5, 1]
    n[11]['widgets_values'] = [W, H, 1]
    n[4]['widgets_values'][2:] = [W, H]
    n[16]['widgets_values'] = [text, '', enc_res]
    n[20]['widgets_values'] = [seed, 'fixed', STEPS, 1, 'euler', 'simple', 1]
    n[22]['widgets_values'] = ['deleted_11s_locations_v02/' + out_name]
    n[7]['mode'] = 0 if reference else 4
    if reference:
        n[7]['widgets_values'] = [reference, 'image']
    api = {
        '1': {'class_type': 'UNETLoader', 'inputs': {'unet_name': n[1]['widgets_values'][0], 'weight_dtype': 'default'}},
        '3': {'class_type': 'QwenImage21Cache', 'inputs': {'model': ['1', 0], 'device': 'cpu', 'dtype': 'default'}},
        '4': {'class_type': 'ModelSamplingFlux', 'inputs': {'model': ['3', 0], 'max_shift': n[4]['widgets_values'][0], 'base_shift': n[4]['widgets_values'][1], 'width': ['10', 1], 'height': ['10', 2]}},
        '6': {'class_type': 'VAELoader', 'inputs': {'vae_name': n[6]['widgets_values'][0]}},
        '31': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': n[31]['widgets_values'][0], 'type': 'qwen_image', 'device': 'default'}},
        '10': {'class_type': 'DenoResolutionSetup', 'inputs': dict(zip(['mode', 'ratio_preset', 'megapixels', 'width', 'height', 'divisible_by', 'resize_method', 'interpolation', 'crop_x', 'crop_y', 'crop_zoom'], n[10]['widgets_values']))},
        '11': {'class_type': 'EmptyLatentImage', 'inputs': {'width': ['10', 1], 'height': ['10', 2], 'batch_size': 1}},
        '16': {'class_type': 'TextEncodeQwenImage21', 'inputs': {'clip': ['31', 0], 'vae': ['6', 0], 'prompt': text, 'negative_prompt': '', 'resolution': enc_res}},
        '20': {'class_type': 'KSampler', 'inputs': {'model': ['4', 0], 'positive': ['16', 0], 'negative': ['16', 1], 'latent_image': ['11', 0], 'seed': seed, 'steps': STEPS, 'cfg': 1, 'sampler_name': 'euler', 'scheduler': 'simple', 'denoise': 1}},
        '21': {'class_type': 'VAEDecode', 'inputs': {'samples': ['20', 0], 'vae': ['6', 0]}},
        '22': {'class_type': 'SaveImage', 'inputs': {'images': ['21', 0], 'filename_prefix': n[22]['widgets_values'][0]}},
    }
    if reference:
        api['7'] = {'class_type': 'LoadImage', 'inputs': {'image': reference}}
        api['16']['inputs']['images.image_1'] = ['7', 0]
    if reference2:
        # 두 번째 참조는 API 그래프에만 연결된다(UI 워크플로우 사본에는 image_1만 표시).
        api['8'] = {'class_type': 'LoadImage', 'inputs': {'image': reference2}}
        api['16']['inputs']['images.image_2'] = ['8', 0]
    (ROOT / 'prompts' / f'{out_name}.txt').write_text(text, encoding='utf-8')
    (ROOT / 'workflows' / f'{out_name}.json').write_text(json.dumps(w, ensure_ascii=False, indent=2), encoding='utf-8')
    (ROOT / 'api' / f'{out_name}.json').write_text(json.dumps(api, ensure_ascii=False, indent=2), encoding='utf-8')
    return api, w


def load_record():
    p = ROOT / 'GENERATION_RECORD.json'
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return {'engine': 'local ComfyUI Desktop / Deno Qwen-Image 2.1 T2I + Edit (workflow copy)', 'date': '2026-10-05',
            'design_status': '검토용 생성 시안; 사용자 확정 전',
            'user_direction': '로케이션 완성도·디테일 상향. 레퍼런스 https://www.haanong.com/portfolio/project7-sr 는 마감·디테일만 반영, 기존 중형 아파트 구조 유지 (사용자 선택 2026-10-05).',
            'reference_usage': '레퍼런스 사진은 모델에 입력하지 않음. 관찰한 마감 요소(간접조명 코브, 넓은 원목 마루, 무손잡이 수납, 석재 상판, 다크 메탈 선반, 화분, 레이어드 커튼, 건축 사진 노출)를 텍스트로 번역.',
            'settings': {'width': W, 'height': H, 'steps': STEPS, 'cfg': 1, 'sampler': 'euler', 'scheduler': 'simple', 'cache': 'cpu/default',
                         'edit_encoder_resolution': EDIT_ENCODER_RES},
            'runs': []}


def save_record(rec):
    (ROOT / 'GENERATION_RECORD.json').write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding='utf-8')


def _prep_ref(ref_path):
    ref_path = Path(ref_path)
    if not ref_path.is_absolute():
        ref_path = ROOT / ref_path
    target = ROOT / 'references' / ref_path.name
    if target.resolve() != ref_path.resolve():
        target.write_bytes(ref_path.read_bytes())
    return ref_path, g.upload(ref_path)


def _ref_entry(ref_path, uploaded, slot):
    return {'source': str(ref_path.relative_to(ROOT)) if ref_path.is_relative_to(ROOT) else str(ref_path), 'uploaded_name': uploaded,
            'sha256': hashlib.sha256(ref_path.read_bytes()).hexdigest(), 'destination': f'16 images.{slot}'}


def run(cid, seed, ref_path=None, tag='', ref2_path=None):
    out_name = cid + (f'_{tag}' if tag else '')
    rec = load_record()
    ref = ref2 = None
    if ref_path:
        ref_path, ref = _prep_ref(ref_path)
    if ref2_path:
        ref2_path, ref2 = _prep_ref(ref2_path)
    api, w = build(cid, out_name, seed, ref, ref2)
    r = g.post('/prompt', {'prompt': api, 'client_id': 'd11-loc-v02-' + uuid.uuid4().hex, 'extra_data': {'extra_pnginfo': {'workflow': w}}})
    entry = {'id': out_name, 'view': cid, 'title': TITLES[cid], 'seed': seed, 'prompt_id': r['prompt_id'], 'node_errors': r.get('node_errors', {}),
             'reference': _ref_entry(ref_path, ref, 'image_1') if ref_path else None,
             'reference2': _ref_entry(ref2_path, ref2, 'image_2') if ref2_path else None,
             'status': 'queued', 'visual_review': 'pending'}
    rec['runs'].append(entry)
    save_record(rec)
    print('QUEUED', out_name, r['prompt_id'], flush=True)
    t0 = time.monotonic()
    while True:
        h = g.get('/history/' + r['prompt_id']).get(r['prompt_id'])
        if h:
            if h.get('status', {}).get('status_str') == 'error':
                entry['status'] = 'failed'
                entry['error'] = h.get('status')
                save_record(rec)
                raise RuntimeError(entry['error'])
            imgs = h.get('outputs', {}).get('22', {}).get('images', [])
            if imgs:
                blob = urllib.request.urlopen(g.BASE + '/view?' + urllib.parse.urlencode(imgs[0]), timeout=120).read()
                out = ROOT / 'outputs' / f'{out_name}.png'
                out.write_bytes(blob)
                entry.update(status='generated', output=f'outputs/{out_name}.png', actual_size=list(struct.unpack('>II', blob[16:24])),
                             elapsed_seconds=round(time.monotonic() - t0, 1), sha256=hashlib.sha256(blob).hexdigest())
                save_record(rec)
                print('SAVED', out_name, entry['actual_size'], entry['elapsed_seconds'], 's', flush=True)
                return entry
        time.sleep(5)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('views', nargs='+')
    ap.add_argument('--seed', type=int)
    ap.add_argument('--ref')
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    for v in a.views:
        run(v, a.seed if a.seed is not None else BASE_SEED + list(PROMPTS).index(v), a.ref, a.tag)
