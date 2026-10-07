"""CHAR_01 서윤 Typecast 목소리 후보 테스트 v02.

v01 6명은 사용자가 전부 '서윤의 외모·분위기·성격과 맞지 않음'으로 판정(2026-10-07).
v02는 미리듣기 밝기(스펙트럼 중심)가 낮고 F0가 중간 이하인 후보로 다시 고른다.
후보 8명 × 대사 3줄, ssfm-v30, smart 감정(앞뒤 대사 문맥), seed 11, target_lufs -20(음량 맞춤).
결과: 같은 폴더의 wav, MANIFEST.json, index.html (듣기용).
실행: python 삭제된_11초/audio/voice_casting_v02/CHAR_01_서윤/run_casting.py
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools" / "typecast"))
import typecast_api as tc  # noqa: E402

MODEL, SEED, LUFS = "ssfm-v30", 11, -20.0

# 한국어 이름 여성 성인 120명 미리듣기 측정 중 밝기 ≤1000Hz, F0 ≤216Hz. 근거는 RESULTS.md.
# V7·V8은 Typecast 분류 middle_age — 32세보다 나이 들게 들릴 수 있어 방향 비교용.
CANDIDATES = [
    ("V1", "서현", "tc_69f2e455ea79fd197aa0476f"),
    ("V2", "인혜", "tc_66c6ce360614b40f9fe13439"),
    ("V3", "주영", "tc_66f4ecb5b1a24ceec9f6ccf0"),
    ("V4", "이현", "tc_68ddea1e462b169ddd20b74d"),
    ("V5", "예슬", "tc_66ab0e26ec23f325b7ad51df"),
    ("V6", "연서", "tc_64b0eede22ce103fdc1d9f78"),
    ("V7", "윤정", "tc_65bb39f30c9fdc33ad4c5a7b"),
    ("V8", "미소", "tc_677f2ac4934cbfb52bee8a9c"),
]

# 감정 곡선의 세 지점: 평소처럼 보이려는 노력 → 대면 → 마지막 낮은 종료.
LINES = [
    ("L1", "S#3", "그날 내 차 점검받았잖아.",
     "그러니까. 괜히 돈 쓰지 말고 새로 사자.", "응.",
     "삼키기 어려운 죽을 한 숟갈 먹은 직후. 평소 말투를 유지하려 하지만 확인하려는 질문."),
    ("L2", "S#5", "기억 안 나는 거랑 귀 안 들리는 거랑 달라.",
     "서윤아. 네가 지금 사고 때문에—", "내가 병원에서 며칠을 잤어.",
     "도현의 말을 끊고 들어간다. 고성 없이 문장이 짧고 분명해지는 지점."),
    ("L3", "S#7", "그러니까 무서워.",
     "나 네 옆에 있었잖아.", "",
     "한동안 바라본 뒤. 울음·고성보다 남편을 보며 낮게 끝내는 방향(설정집 제안)."),
]


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return round(float(out.stdout.strip() or 0), 3)


def main() -> None:
    records = []
    for vid_key, name, voice_id in CANDIDATES:
        for line_key, scene, text, prev, nxt, intent in LINES:
            out = HERE / f"{vid_key}_{name}_{line_key}.wav"
            payload = {"voice_id": voice_id, "text": text, "model": MODEL, "language": "kor",
                       "prompt": {"emotion_type": "smart", "previous_text": prev,
                                  **({"next_text": nxt} if nxt else {})},
                       "output": {"audio_format": "wav", "audio_tempo": 1.0, "target_lufs": LUFS},
                       "seed": SEED}
            if not out.exists():
                audio, ctype = tc.request("POST", "/v1/text-to-speech", body=payload)
                if not audio or ctype.startswith("application/json"):
                    raise tc.TypecastError(f"오디오가 아닌 응답: {ctype}")
                out.write_bytes(audio)
                print(f"합성: {out.name}")
            else:
                print(f"기존 파일 사용: {out.name}")
            data = out.read_bytes()
            records.append({"candidate": vid_key, "voice_name": name, "voice_id": voice_id,
                            "line": line_key, "scene": scene, "text": text, "intent": intent,
                            "file": out.name, "sha256": hashlib.sha256(data).hexdigest(),
                            "duration_sec": duration(out), "payload": payload})

    manifest = {"character": "CHAR_01 한서윤", "test": "voice_casting_v02",
                "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "status": "후보 테스트. 사용자 청취·선택 전.",
                "model": MODEL, "seed": SEED, "records": records}
    (HERE / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    write_html(records)
    print("완료: MANIFEST.json, index.html")


def write_html(records) -> None:
    rows = []
    for vid_key, name, voice_id in CANDIDATES:
        cells = []
        for line_key, scene, text, *_ in LINES:
            r = next(x for x in records if x["candidate"] == vid_key and x["line"] == line_key)
            cells.append(f'<td><audio controls preload="none" src="{r["file"]}"></audio>'
                         f'<div class="d">{r["duration_sec"]:.2f}s</div></td>')
        rows.append(f"<tr><th>{vid_key} {name}<div class='d'>{voice_id}</div></th>{''.join(cells)}</tr>")
    head = "".join(f"<th>{k} · {s}<div class='t'>{t}</div></th>" for k, s, t, *_ in LINES)
    html = f"""<!doctype html><html lang="ko"><meta charset="utf-8">
<title>서윤 목소리 후보 v02</title>
<style>
body{{font-family:system-ui,'Malgun Gothic',sans-serif;margin:24px;background:#fafafa;color:#222}}
table{{border-collapse:collapse;background:#fff}} th,td{{border:1px solid #ddd;padding:10px;vertical-align:top;text-align:left}}
.d{{font-size:12px;color:#888;margin-top:4px}} .t{{font-weight:normal;font-size:14px;margin-top:4px}}
audio{{width:220px}}
</style>
<h1>CHAR_01 서윤 — Typecast 목소리 후보 v02</h1>
<p>ssfm-v30 · smart 감정(앞뒤 대사 문맥) · seed {SEED} · 속도 1.0 · 음량 {LUFS:g} LUFS · 후보 테스트, 사용자 선택 전</p>
<table><tr><th>후보</th>{head}</tr>{''.join(rows)}</table>
</html>"""
    (HERE / "index.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except tc.TypecastError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
