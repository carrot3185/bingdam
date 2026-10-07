from pathlib import Path
import json
import copy
import shutil

base = Path(__file__).resolve().parent
old = base / 'turnaround_qwen_v01'
out = base / 'turnaround_qwen_v02'
for sub in ['workflows', 'prompts', 'references', 'outputs']:
    (out / sub).mkdir(parents=True, exist_ok=True)

common = '''Using image one as the exact full-body identity and costume reference and image two as a close crop of that SAME original person's head, generate a photographic turnaround of that same person. Image two only reinforces the original face and hair; it does not introduce another person or a new design. Show exactly four separate full-body views in one horizontal row: front, strict profile facing the left edge, straight rear, strict profile facing the right edge. Keep every head and foot inside the frame, views evenly spaced on the same floor baseline, same body scale and natural proportions as image one. The front-view facial geometry, eye spacing and shape, nose, lips, jaw, head size, hairline, bangs and skin tone must match the original, without beautifying, slimming, recasting or changing age. Keep the original soft studio lighting and pale warm-gray backdrop. Preserve individual hair strands, natural skin texture, subtle fabric weave, garment seams, folds, fastenings and footwear edges, with clear focused detail and without painterly smoothing or artificial sharpening. Rotate the same original person and clothes; do not reinterpret their design. No text or watermark. '''
details = {
    'CHAR_01': '''Preserve the original woman's long black loose hair, thin wispy bangs, exact natural wave pattern and volume, and hair length reaching the lower chest from the front and the middle back from behind. Preserve the oatmeal soft thin cotton round-neck top, its loose comfortable fit and original hem height, with sleeves pushed to the forearms. Preserve the charcoal soft relaxed trousers: same loose straight silhouette, generous original hip and leg widths, softly draped wrinkled fabric and original waistband details. Do not change them into fitted formal suit trousers or introduce sharp pressed creases. Keep her original torso and hip proportions. She is barefoot. The gray wrist brace is the original structured soft orthosis with its original fastening straps and thumb opening, not a gauze wrap, glove or cast. It stays on anatomical LEFT wrist only: image-right in front, image-left from behind and the near arm in the left-facing profile. Keep the other wrist bare. Arms rest alongside the body as in the original, hands visible. Keep rear trouser hems just clear of the floor so both bare heels can be seen. Preserve the calm original face.''',
    'CHAR_03': '''Preserve the original man's short black side-parted hair, clean-shaven face, exact subtle friendly expression and original sturdy physique. Keep the dark olive cotton jacket's original color, collar, chest seam, zipper, elastic cuffs and waist hem, worn open over the same plain ivory round-neck cotton T-shirt. Preserve the indigo jeans' original straight fit, denim grain, stitching and soft creases. Keep the original dark low-top sneakers and off-white rubber soles with clear lace and sole detail. Preserve the SAME small black crossbody bag with original rectangular shape, zipper and strap buckle. One continuous strap starts on anatomical LEFT shoulder and runs to the bag at anatomical RIGHT hip: image-right shoulder to image-left hip in front, image-left shoulder to image-right hip at the rear. In side views rotate that same strap and bag naturally without shifting it to the other hip or redesigning it. Keep his hands in pockets as in the source reference.'''
}
changes = []
for cid in details:
    w = json.loads((old / 'workflows' / f'{cid}_turnaround.json').read_text(encoding='utf-8-sig'))
    n = {x['id']: x for x in w['nodes']}
    ref = f'D11_{cid}_FINAL.png'
    shutil.copy2(old / 'references' / ref, out / 'references' / ref)
    prompt = common + details[cid]
    n[10]['widgets_values'] = ['Manual Input', '3:2', 3.93, 2560, 1536, '32', 'Center Crop (Fill)', 'lanczos', .5, .5, 1]
    n[11]['widgets_values'] = [2560, 1536, 1]
    n[4]['widgets_values'][2:] = [2560, 1536]
    n[3]['widgets_values'] = ['cpu', 'default']
    n[16]['widgets_values'] = [prompt, '', 0]
    n[20]['widgets_values'][2] = 60
    n[22]['widgets_values'] = [f'deleted_11s_turnaround/{cid}_v02_HQ']
    # ComfyUI performs the crop. The source image itself is never edited.
    link_in = max(x[0] for x in w['links']) + 1
    link_out = link_in + 1
    n[7]['outputs'][0]['links'].append(link_in)
    image_two = next(x for x in n[16]['inputs'] if x['name'] == 'images.image_2')
    image_two['link'] = link_out
    crop = {'id':34,'type':'ImageCrop','pos':[440,560],'size':[280,200],'flags':{},'order':12,'mode':0,
        'title':'Original face detail reference (same person)',
        'inputs':[{'name':'image','type':'IMAGE','link':link_in},
            *[{'name':x,'type':'INT','widget':{'name':x},'link':None} for x in ['width','height','x','y']]],
        'outputs':[{'name':'IMAGE','type':'IMAGE','links':[link_out]}],
        'properties':{'Node name for S&R':'ImageCrop'},'widgets_values':[384,384,320,0]}
    w['nodes'].append(crop)
    w['links'].extend([[link_in,7,0,34,0,'IMAGE'],[link_out,34,0,16,2,'IMAGE']])
    w['last_node_id'] = max(w.get('last_node_id',0),34)
    w['last_link_id'] = link_out
    (out / 'workflows' / f'{cid}_turnaround_HQ.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
    (out / 'prompts' / f'{cid}.txt').write_text(prompt,encoding='utf-8')
    changes.append({'id':cid,'selected_source':ref,'seed':n[20]['widgets_values'][0],
        'options':{'DenoResolutionSetup':[2560,1536],'TextEncodeQwenImage21.resolution':0,'KSampler.steps':60,'QwenImage21Cache':['cpu','default']},
        'added_node':{'id':34,'type':'ImageCrop','source':[7,0],'crop':[384,384,320,0],'destination':'16 images.image_2'},
        'unchanged':{'model':n[1]['widgets_values'][0],'CFG':1,'sampler':'euler','scheduler':'simple','denoise':1},
        'status':'prepared, not yet generated'})
(out/'CHANGES.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print(out)
