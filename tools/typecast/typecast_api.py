"""Typecast TTS API 연결 (New_롱폼 전용, 표준 라이브러리만 사용).

  POST https://api.typecast.ai/v1/text-to-speech      음성 합성 (응답 = 오디오 바이너리)
  GET  https://api.typecast.ai/v3/voices              목소리 목록
  GET  https://api.typecast.ai/v1/users/me/subscription 요금제·크레딧 확인

API 키: 환경변수 TYPECAST_API_KEY → 없으면 프로젝트 루트의 .env (TYPECAST_API_KEY=...).
키 값은 화면·로그·기록 파일에 쓰지 않는다.

사용 예:
  python tools/typecast/typecast_api.py check
  python tools/typecast/typecast_api.py voices --gender female --age young_adult
  python tools/typecast/typecast_api.py synth --voice tc_xxx --text "문 열어." --out _테스트/typecast/test.wav
  python tools/typecast/typecast_api.py synth --voice tc_xxx --text-file line.txt --dry-run

이 스크립트는 연결 도구일 뿐이다. 인물별 목소리(voice_id)·감정 방식·모델은 이 작품에서 아직
사용자 확정 전이며, 다른 프로젝트(shorts 등)의 배정을 가져오지 않는다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.typecast.ai"
KEY_VAR = "TYPECAST_API_KEY"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_FILE = PROJECT_ROOT / "tools" / "typecast" / "SYNTH_LOG.jsonl"
DEFAULT_MODEL = "ssfm-v30"
PRESETS = ("normal", "happy", "sad", "angry", "whisper", "toneup", "tonedown")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


class TypecastError(RuntimeError):
    pass


# ── 키 ──────────────────────────────────────────────────────────

def _dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return out
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip().removeprefix("export ").strip()] = v.strip().strip('"').strip("'")
    return out


def api_key() -> str:
    key = os.environ.get(KEY_VAR, "").strip() or _dotenv(PROJECT_ROOT / ".env").get(KEY_VAR, "").strip()
    if not key:
        raise TypecastError(
            "Typecast API 키가 없습니다.\n"
            "  https://typecast.ai/developers/api 에서 키를 발급한 뒤\n"
            f"  {PROJECT_ROOT / '.env'} 에 한 줄로 적으세요:  {KEY_VAR}=발급받은키\n"
            f"  (또는 환경변수 {KEY_VAR})"
        )
    return key


# ── HTTP ────────────────────────────────────────────────────────

_HINTS = {401: "API 키가 올바르지 않습니다.",
          402: "크레딧이 부족합니다.",
          404: "voice_id 또는 경로를 찾을 수 없습니다.",
          422: "요청 값이 잘못됐습니다(문장·voice_id·모델 조합 확인).",
          429: "요청이 너무 많습니다(동시 처리 한도)."}


def request(method: str, path: str, *, params: dict | None = None, body: dict | None = None) -> tuple[bytes, str]:
    url = f"{API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    headers = {"X-API-KEY": api_key(), "Accept": "*/*"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(5):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read(), resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            if (exc.code == 429 or exc.code >= 500) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise TypecastError(f"Typecast 오류 {exc.code}: {_HINTS.get(exc.code, '')}\n  {detail}") from None
        except urllib.error.URLError as exc:
            if attempt == 4:
                raise TypecastError(f"Typecast 연결 실패: {exc.reason}") from None
            time.sleep(2 ** attempt)
    raise TypecastError("Typecast 요청이 반복해서 실패했습니다.")


def get_json(path: str, **params):
    raw, _ = request("GET", path, params=params)
    return json.loads(raw.decode("utf-8"))


# ── 명령 ────────────────────────────────────────────────────────

def cmd_check(_args) -> None:
    info = get_json("/v1/users/me/subscription")
    print("연결 성공. 구독 정보:")
    print(json.dumps(info, ensure_ascii=False, indent=2))


def _voice_name(v: dict) -> str:
    names = v.get("voice_names") or v.get("voice_name") or {}
    if isinstance(names, dict):
        return names.get("kor") or names.get("ko") or names.get("eng") or names.get("en") or next(iter(names.values()), "")
    return str(names)


def cmd_voices(args) -> None:
    data = get_json("/v3/voices", model=args.model)
    items = data if isinstance(data, list) else data.get("voices", data.get("items", []))
    rows = []
    for v in items:
        gender, age = str(v.get("gender", "")).lower(), str(v.get("age", "")).lower()
        if args.gender and gender != args.gender:
            continue
        if args.age and age != args.age:
            continue
        rows.append(v)
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(rows)}개 저장: {out}")
        return
    for v in rows:
        uses = ",".join(v.get("use_cases") or [])
        print(f"{v.get('voice_id', ''):<28} {_voice_name(v):<14} {v.get('gender', ''):<7} "
              f"{v.get('age', ''):<12} {uses}")
    print(f"\n총 {len(rows)}개 (model={args.model})")


def build_payload(args, text: str) -> dict:
    if args.emotion == "smart":
        prompt: dict = {"emotion_type": "smart"}
        if args.prev:
            prompt["previous_text"] = args.prev[:2000]
        if args.next:
            prompt["next_text"] = args.next[:2000]
    else:
        prompt = {"emotion_type": "preset", "emotion_preset": args.emotion,
                  "emotion_intensity": args.intensity}
    output: dict = {"audio_format": args.format, "audio_tempo": args.tempo}
    if args.pitch:
        output["audio_pitch"] = args.pitch
    if args.volume is not None:
        output["volume"] = args.volume
    if args.lufs is not None:
        output["target_lufs"] = args.lufs
    payload = {"voice_id": args.voice, "text": text, "model": args.model,
               "language": args.language, "prompt": prompt, "output": output}
    if args.seed is not None:
        payload["seed"] = args.seed
    return payload


def cmd_synth(args) -> None:
    text = Path(args.text_file).read_text(encoding="utf-8").strip() if args.text_file else (args.text or "").strip()
    if not text:
        raise TypecastError("--text 또는 --text-file 로 문장을 주세요.")
    if len(text) > 2000:
        raise TypecastError(f"문장이 2000자를 넘습니다({len(text)}자). 나눠서 합성하세요.")
    payload = build_payload(args, text)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    out = Path(args.out) if args.out else PROJECT_ROOT / "_테스트" / "typecast" / \
        f"{datetime.now():%Y%m%d_%H%M%S}_{args.voice}.{args.format}"
    if out.suffix.lstrip(".").lower() != args.format:
        out = out.with_suffix(f".{args.format}")
    if out.exists() and not args.overwrite:
        raise TypecastError(f"이미 있는 파일입니다: {out}  (--overwrite 로 덮어쓰기)")

    audio, ctype = request("POST", "/v1/text-to-speech", body=payload)
    if not audio or ctype.startswith("application/json"):
        raise TypecastError(f"오디오가 아닌 응답: {ctype} {audio[:300]!r}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio)

    record = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "output": str(out.relative_to(PROJECT_ROOT)) if out.is_relative_to(PROJECT_ROOT) else str(out),
              "sha256": hashlib.sha256(audio).hexdigest(), "bytes": len(audio),
              "content_type": ctype, "payload": payload, "note": args.note or ""}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"저장: {out}  ({len(audio):,} bytes)\n기록: {LOG_FILE}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Typecast TTS API (New_롱폼)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="키·연결·크레딧 확인").set_defaults(func=cmd_check)

    v = sub.add_parser("voices", help="목소리 목록")
    v.add_argument("--model", default=DEFAULT_MODEL, choices=("ssfm-v30", "ssfm-v21"))
    v.add_argument("--gender", choices=("male", "female"))
    v.add_argument("--age", choices=("child", "teenager", "young_adult", "middle_age", "elder"))
    v.add_argument("--json", help="필터 결과를 JSON 파일로 저장")
    v.set_defaults(func=cmd_voices)

    s = sub.add_parser("synth", help="한 줄 합성")
    s.add_argument("--voice", required=True, help="voice_id (tc_... / uc_...)")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--text")
    g.add_argument("--text-file")
    s.add_argument("--out", help="저장 경로 (기본: _테스트/typecast/시각_voice.확장자)")
    s.add_argument("--model", default=DEFAULT_MODEL, choices=("ssfm-v30", "ssfm-v21"))
    s.add_argument("--language", default="kor")
    s.add_argument("--emotion", default="smart", choices=("smart",) + PRESETS,
                   help="smart(앞뒤 문맥 추론) 또는 프리셋")
    s.add_argument("--intensity", type=float, default=1.0, help="프리셋 강도 0.0~2.0")
    s.add_argument("--prev", help="smart 모드: 앞 대사")
    s.add_argument("--next", help="smart 모드: 뒤 대사")
    s.add_argument("--tempo", type=float, default=1.0, help="0.5~2.0")
    s.add_argument("--pitch", type=int, default=0, help="-12~12 반음")
    s.add_argument("--volume", type=int, help="0~200")
    s.add_argument("--lufs", type=float, help="목표 라우드니스 -70~0")
    s.add_argument("--format", default="wav", choices=("wav", "mp3"))
    s.add_argument("--seed", type=int)
    s.add_argument("--note", help="기록용 메모 (예: S#3 서윤 대사 테스트)")
    s.add_argument("--overwrite", action="store_true")
    s.add_argument("--dry-run", action="store_true", help="요청 본문만 출력(크레딧 사용 안 함)")
    s.set_defaults(func=cmd_synth)

    args = ap.parse_args(argv)
    try:
        args.func(args)
    except TypecastError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
