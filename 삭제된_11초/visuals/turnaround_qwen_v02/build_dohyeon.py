from pathlib import Path
import json
import shutil

base = Path(__file__).resolve().parent
old = base.parent / 'turnaround_qwen_v01'
cid = 'CHAR_02'
w = json.loads((base/'workflows/CHAR_03_turnaround_HQ.json').read_text(encoding='utf-8'))
n = {x['id']:x for x in w['nodes']}
common = n[16]['widgets_values'][0].split("Preserve the original man's",1)[0]
details = '''Preserve the original man's exact short black naturally parted hairstyle with loose forehead strands, clean-shaven face, calm restrained expression and original slender adult physique. Keep the muted slate-blue cotton button-down shirt: original color, fine fabric texture, plain collar, original open upper buttons, button placket, sleeve folds and sleeves rolled to the forearms. Keep the shirt tucked into the same deep navy tailored trousers, preserving their waistband, pocket shape, fit and original soft creases. Preserve the plain black leather lace-up shoes with the original toe shape, leather texture, laces and sole edge. Keep exactly one original dark round wristwatch with its original metal case and dark band, on anatomical LEFT wrist only. It is on the image-right wrist in front, the image-left wrist from behind and the near wrist in the left-facing profile. Show that watch clearly in the front, left-facing profile and rear views; keep the anatomical right wrist bare. The watch may be naturally hidden in the opposite side profile. Keep both hands in trouser pockets as in the selected original, without changing the body build or clothing design. Do not add an outer jacket, tie, shirt pocket, jewelry, beard or new accessories.'''
prompt = common + details
n[7]['widgets_values'] = ['D11_CHAR_02_FINAL.png','image']
n[16]['widgets_values'] = [prompt,'',0]
n[20]['widgets_values'][0] = 2026100502
n[22]['widgets_values'] = ['deleted_11s_turnaround/CHAR_02_v02_HQ']
shutil.copy2(old/'references/D11_CHAR_02_FINAL.png',base/'references/D11_CHAR_02_FINAL.png')
(base/'workflows/CHAR_02_turnaround_HQ.json').write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
(base/'prompts/CHAR_02.txt').write_text(prompt,encoding='utf-8')
changes=json.loads((base/'CHANGES.json').read_text(encoding='utf-8'))
if not any(x['id']==cid for x in changes):
    entry=json.loads(json.dumps(changes[1]))
    entry.update(id=cid,selected_source='D11_CHAR_02_FINAL.png',seed=2026100502,status='prepared, not yet generated')
    changes.append(entry)
    (base/'CHANGES.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print('CHAR_02 HQ prepared; earlier CHAR_01 and CHAR_03 workflows/results preserved.')
