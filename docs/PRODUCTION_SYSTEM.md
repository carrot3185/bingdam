# 제작 시스템 설정

## 이미지 생성 도구

상태: 사용자 확정 (2026-10-05). 사용자가 지정한 도구 이름을 그대로 기록한다.

| 도구 | 사용 환경 |
| --- | --- |
| OpenAI GPT Image 2.5 | 사용자 지정 데스크톱 앱에서 실행 |
| Deno Qwen-Image 2.1 T2I + Edit | ComfyUI Desktop 내 워크플로우로 실행 |

이 프로젝트의 이미지 제작 제안과 프롬프트는 위 두 도구를 기준으로 작성한다. 외부 사례에서 사용한 이미지 모델을 이 프로젝트의 확정 도구로 대체 기록하지 않는다.

실행 환경은 사용자 확인 사항이다. GPT 데스크톱 앱의 상세 입력 방식·실제 모델 ID는 확인하지 않았다. 2차 감정 연기 테스트는 사용자의 요청으로 이 대화의 내장 이미지 도구에서 실행했으며 정확한 모델 버전은 노출되지 않았다. 따라서 그 결과를 GPT Image 2.5 확인 결과로 취급하지 않는다.

## 사용자 제공 Qwen 워크플로우

- 경로: `D:/Comfy-Desktop/ComfyUI-Installs/KSH/ComfyUI/user/default/workflows/Deno Qwen-Image 2.1 T2I + Edit.json`
- 2026-10-05에 JSON의 노드 구성·저장된 설정·node 33의 Prompting Guide를 확인했다. 원본은 보존했다.
- 2026-10-05에 ComfyUI Desktop 설치본의 로컬 서버에서 2차 감정 연기 테스트 사본 4개를 검증·실행하고 실제 출력 4장을 확인했다. 프롬프트·시드·입력 대응은 출력 메타데이터와 입력 파일 해시로 대조했다. 노드 내부 알고리즘을 별도로 검증한 것은 아니다.
- 감정 표현 A/B 테스트에서는 가이드의 큰 틀을 적용하되 사용자가 강조한 테스트 목적을 우선한다. 적용 내용은 `experiments/emotional_acting_01/TEST_PLAN.md`와 `PROMPT_SETTINGS.md`에 기록했다.
- 2차 실행·검수 기록: `_테스트/1. 인물/1. 감정연기/2차_톤질감보존/RESULTS.md`와 `GENERATION_RECORD.json`.

## 영상 생성 도구

상태: 사용자 지정 (2026-10-07). 로컬 ComfyUI에서 생성하며 유료 API는 현재 고려하지 않는다.

- 워크플로우: `D:/Comfy-Desktop/ComfyUI-Installs/KSH/ComfyUI/user/default/workflows/Deno_minimax_final_R2V_7+1_memopt_Sol.json` (원본 보존, 사본 사용).
- 2026-10-07 JSON 확인 내용(실행 검증 아님): MiniMax H3 reference-to-video(ref2va). 모델 `Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8`, 텍스트 인코더 `qwen3vl_32b_minimax_h3_int8_convrot`, LoRA `minimax_h3_dmd_ref2va_8step_turbo_pruned`(작성자 표기 실험적)와 `Camera_Control`(강도 1). euler/simple 8스텝을 7+1로 나눠 7스텝 후 잠재 공간 ×2 업스케일, 마지막 1스텝은 H3 Memory Optimization. 저장된 설정은 16:9 0.51MP 1단계, 12초, `ref_image_size=match`, 참조 이미지 로더 3칸. **참조 오디오 입력은 연결돼 있지 않다.** 음성은 H3가 영상과 함께 생성해 디코딩한다.
- 실행 환경: RTX 4070 12GB, RAM 96GB, i7-14700KF.
- 2026-10-07 첫 실행: 기준 목소리 후보 테스트 6클립(도현 S2-14 ×3, 서윤 S3-17 ×3). 사본 워크플로우·프롬프트·참조 해시·관찰은 `삭제된_11초/visuals/video_h3_voice_test/GENERATION_RECORD.json`. 실측: 1920×1088, 5.875초, 클립당 약 5분. 저장된 UI 파일의 `MinimaxH3LatentUpscaler3D` 설정값이 한 칸씩 어긋나 있어 API 변환 시 force_unload=True·device=cuda·precision=bf16으로 보정했다. 목소리 적합성은 사용자 청취 전. 음성 고정 방식(참조 오디오 연결 여부)은 미정.
- **2026-10-07 사용자 승인 — 본 작업 생성 기준 조건**: 위 테스트의 연기·대사 자연스러움, 영상 톤앤매너, 카메라 연출, 배경 포커스 아웃을 사용자가 좋다고 평가하고 이 조건으로 본 작업을 진행하기로 했다. 기준 조건은 다음과 같다.
  - 워크플로우: 사용자 원본 설정 그대로(7+1, Camera_Control LoRA 1.0, 터보 LoRA, ×2 업스케일, 메모리 최적화, `match`, 16:9 0.51MP → 1920×1088). 업스케일러 노드값만 보정한 기준 파일 `tools/h3/D11_H3_R2V_BASE_v01.json`(sha256 `b1a44c7d…`). 빌드 스크립트 `tools/h3/build_h3.py`는 테스트 때 실행한 API 그래프를 그대로 재현함을 확인했다.
  - 참조: 확정 인물 시트(<Picture 1>) + 확정 배경 원본(<Picture 2>).
  - 프롬프트 구조: `video_h3_voice_test/prompts/`의 4필드 형식(참조 역할·정체성 고정 → 시간순 샷 설명과 `<d>[Korean] …</d>` 대사 → 환경음 → 음악 N/A).
  - 승인 범위가 아닌 것: 인물별 목소리 선택·고정(미정), 발화 타이밍 제어, MCU/CU 화면 크기 준수(테스트에서 MS로 넓어짐).
- **목소리 고정 방식 사용자 확정 (2026-10-07)**: 인물별 기준 음성(`삭제된_11초/visuals/voice_anchor/`)을 `ref_audios.ref_audio_0`에 넣는다(`build_h3.py`의 `AUDIO` 환경변수). 사용자 청취 결과 새 대사에서도 기준 목소리와 거의 비슷하게 들림. 도현·서윤 기준 음성 확보, 다른 인물은 미확보.
- **프롬프트 규칙 (2026-10-07 테스트에서 확인)**:
  - 화면에 상대 인물의 일부(OTS 어깨·뒤통수 등)가 나올 수 있는 샷은 상대의 확정 시트를 참조 이미지로 함께 넣고, 전경 인물이 누구인지·얼굴 비노출을 프롬프트에 명시한다. 넣지 않으면 상대 의상이 임의로 바뀐다(v01 분홍 상의 → v02 확정 의상으로 해결).
  - 참조 오디오를 쓸 때 상대 대사를 따옴표로 인용하지 않는다. 인용하면 그 대사가 소리로 생성된다. 상황만 서술하고 상대는 무음이라고 명시한다.

## 음성: Typecast API 연결 도구

상태: 연결 도구만 추가했다(2026-10-07, 사용자 요청). 이 작품의 음성 방식·인물별 voice_id·감정 방식은 아직 미정이며, shorts 프로젝트의 목소리 배정을 가져오지 않는다.

- 스크립트: `tools/typecast/typecast_api.py` (`check` / `voices` / `synth`, 표준 라이브러리만 사용).
- 키: 환경변수 `TYPECAST_API_KEY` 또는 프로젝트 루트 `.env` (`.env.example` 참고).
- 합성할 때마다 `tools/typecast/SYNTH_LOG.jsonl`에 요청 본문(키 제외)·출력 경로·SHA-256을 남긴다.
- 2026-10-07: 사용자가 `.env`에 키를 등록했다. `check`(GET `/v1/users/me/subscription`)는 성공했다. 결과는 free 요금제, 15,000크레딧 중 240 사용, 동시 처리 2. `voices`(GET `/v3/voices`, ssfm-v30)는 608개를 돌려줬다. 음성 합성(`synth`)은 아직 실행하지 않았다.
- 2026-10-07 사용자 의견: Typecast 목소리는 인물과 잘 붙지 않는다. 이 작품 대사의 주 음성 방식으로 전제하지 않는다. 대안(영상 모델 자체 음성, 음성 변환 등)은 미정.
