# 프롬프트 입력 형식과 설정

프롬프트 버전: v2 — 사용자 제공 Qwen Prompting Guide의 큰 틀을 적용.

아래의 Mode / Aspect ratio는 실행 안내다. 실제 모델에 붙여 넣는 본문은 각 `.txt` 파일의 내용만 사용한다. GPT 데스크톱 앱과 Qwen의 긍정 프롬프트에 같은 본문을 넣는다.

| 파일 | Mode | Aspect ratio | Prompt |
| --- | --- | --- | --- |
| 00_NEUTRAL_T2I.txt | Text-to-image | 16:9; Qwen 제안 크기 1536 × 864 | 해당 파일 전체 |
| 01_TEARS_EDIT.txt | Edit | 기준 이미지의 원래 화면비와 구도 유지 | 해당 파일 전체 |
| 02_SMILE_EDIT.txt | Edit | 기준 이미지의 원래 화면비와 구도 유지 | 해당 파일 전체 |
| 03_TEAR_FALL_EDIT.txt | Edit | 기준 이미지의 원래 화면비와 구도 유지 | 해당 파일 전체 |

숫자형 화면비·해상도, 모드 표시, 파일명은 생성 본문에 넣지 않는다. GPT 앱에 크기 선택 기능이 없거나 서로 다른 크기가 출력되면 실제 크기 차이를 기록한다. 정밀한 눈·눈물 비교 전에 이미지를 잘라 구도를 맞추지 않는다. 비교 표시용 축소가 필요하면 원본도 유지한다.

## Qwen 테스트 사본

`workflows/Qwen_Emotion_AB_00_T2I.json`은 사용자가 제공한 원본에서 중립 T2I 테스트용으로 만든 사본이다. 원본 파일은 수정하지 않았다.

읽은 원본의 SHA-256: `959701D670DF6531D51ED86A8D38C41FC5F34388B195BD5E64437C2DA9113FF3`. 사본 저장 후 원본 해시가 같음을 확인했다.

- 모델, 인코더, VAE, 노드 연결과 원래 Prompting Guide는 유지.
- node 16 `TextEncodeQwenImage21.prompt`: 00_NEUTRAL_T2I.txt의 본문.
- node 16 `negative_prompt`: 빈 문자열.
- node 10 `DenoResolutionSetup`: Manual Input, width 1536, height 864. 연결된 node 4·11의 저장된 크기도 일치시킴.
- node 20 `KSampler`: 원본 seed 303617254009935를 유지하고 생성 후 변경은 fixed로 설정. steps 40, CFG 1, euler, simple, denoise 1은 원본 그대로.
- node 22 `SaveImage`: 출력 접두사 `emotional_acting_01/B_00_neutral`.
- node 7 `LoadImage`: 원본의 mode 4 유지. 중립 T2I에서는 참조 이미지가 의도에 포함되지 않음.

1536 × 864는 정확한 16:9이며 각 변이 32의 배수다. 원문 가이드의 16:9 예시 1344 × 768은 정확히는 7:4라서, 테스트 목적에 맞춰 크기를 조정했다. 설정값과 실제 생성 크기는 생성 후 대조한다.

## Edit 실행 시 확인

기준 이미지가 아직 없으므로 Edit 워크플로우 사본은 만들지 않았다. T2I 사본을 그대로 실행하면 감정 편집이 되는 것으로 취급하지 않는다.

원본 JSON에는 node 7 `LoadImage`의 IMAGE가 node 16 `TextEncodeQwenImage21`의 `images.image_1`에 연결돼 있다. Edit 시 실제 기준 파일을 node 7에 선택하고 해당 노드의 우회 상태를 해제해 입력이 전달되는지 확인한다. 현재 저장된 `reference_1.png`가 실제 기준 이미지라고 가정하지 않는다.

node 20의 latent 입력은 node 11 `EmptyLatentImage`에 연결돼 있고 node 16의 latent 출력에는 연결이 없다. 이 연결은 원본 설계로 보존한다. 프롬프트 수정 과정에서 임의로 img2img 방식으로 재배선하지 않는다. 실제 Edit 동작은 생성 결과로 확인해야 한다.

Edit에서는 node 10의 출력 크기를 기준 이미지에 맞추고, node 16의 `resolution`(원본 1024)은 출력 캔버스 크기와 별도 값으로 기록한다. 해당 노드 내부 구현과 실제 전처리는 아직 검수하지 않았다. 가이드의 다중 이미지 지원 설명과 달리 이 JSON에 보이는 이미지 입력 슬롯은 두 개이며, 이번 테스트는 한 개만 사용한다.
