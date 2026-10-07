"""Build seeded MiniMax H3 R2V workflows (UI + API) from the project base workflow.

Run from a test/production folder that has prompts/<shot>_<ver>.txt; writes workflows/.
Usage:
  OI=<object_info.json> python build_h3.py <shot> <ver> "<img1>|<img2>|..." <seed1,seed2> <seconds>
Image paths are relative to the ComfyUI input directory (e.g. D11_h3/CHAR_02_....png).
object_info: curl http://127.0.0.1:8188/object_info -o object_info.json
"""
import copy
import json
import os
import sys

sys.path.insert(0, r"C:/Users/commz/AppData/Roaming/Python/Python314/site-packages")
from comfy_cli.workflow_to_api import convert_ui_to_api

BASE = os.environ.get("H3_BASE", "D:/work/Youtube/New_롱폼/tools/h3/D11_H3_R2V_BASE_v01.json")

shot, ver, images, seeds, secs = (
    sys.argv[1], sys.argv[2], sys.argv[3].split("|"),
    [int(s) for s in sys.argv[4].split(",")], float(sys.argv[5]),
)
oi = json.load(open(os.environ["OI"], encoding="utf-8"))
src = json.load(open(BASE, encoding="utf-8"))
prompt = open(f"prompts/{shot}_{ver}.txt", encoding="utf-8").read().strip()
os.makedirs("workflows", exist_ok=True)

for seed in seeds:
    w = copy.deepcopy(src)
    for n in w["nodes"]:
        if n["id"] == 186:
            n["widgets_values"] = [prompt]
        if n["id"] == 142:
            n["widgets_values"] = ["\n".join(images), "", n["widgets_values"][2]]
        if n["id"] == 132:
            n["widgets_values"] = [secs]
        if n["id"] == 129:
            n["widgets_values"] = [seed, "fixed"]
        if n["id"] == 144:
            n["widgets_values"]["filename_prefix"] = f"D11_h3/{shot}_{ver}_s{seed}"
    base = f"workflows/D11_{shot}_{ver}_s{seed}"
    json.dump(w, open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    api = convert_ui_to_api(w, oi)
    up = api["197"]["inputs"]
    # Guard: the base fixes node 197's widget order; fail loudly if conversion drifts again.
    assert up["force_unload"] is True and up["device"] == "cuda" and up["precision"] == "bf16", up
    # Optional reference audio (<Audio 1>, <Audio 2>, ... in this order): files in the ComfyUI input root.
    for i, name in enumerate(a for a in os.environ.get("AUDIO", "").split("|") if a):
        node_id = str(900 + i)
        api[node_id] = {"class_type": "LoadAudio", "inputs": {"audio": name}}
        api["141"]["inputs"][f"ref_audios.ref_audio_{i}"] = [node_id, 0]
    json.dump(api, open(base + "_api.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(base + "_api.json")
