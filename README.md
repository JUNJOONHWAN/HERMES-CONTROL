# HERMES-CONTROL

HERMES-CONTROL은 Nous Hermes Agent 전체 소스를 복제해서 배포하지 않습니다. 검증된 공식 upstream 커밋을 설치 시 가져온 뒤, HERMES-CONTROL의 역할 셸·카드 계약·어댑터 라우팅·Timeline Code Map·NeuralLink·구조화 heartbeat만 적용하는 **버전 고정 호환 레이어**입니다.

## 무엇이 달라지는가

- root Hermes는 카드 생성·검증·배정·수신만 담당합니다.
- 실제 작업은 역할 셸에 바인딩된 OpenCode, Codex CLI, Grok 또는 범용 command adapter가 담당합니다.
- adapter는 부속품입니다. 특정 provider를 코어에 고정하지 않고 등록/승격/비활성화할 수 있습니다.
- 카드 완료는 텍스트 선언이 아니라 구조화 receipt와 원자적 저장 검증을 통과해야 합니다.
- Timeline Code Map은 작업 맥락·코드 영향·산출물을 공유 증거 그래프로 남깁니다.
- NeuralLink는 그 그래프에서 필요한 과거 맥락을 `pre_llm_call` 시 제한된 크기로 회수합니다.
- heartbeat는 `configuration`, `service_schedule`, `artifacts` 세 층을 분리해 보고합니다.

## 빠른 설치

요구사항: macOS 또는 Linux, Python 3.11~3.13, Git. 기본 작업 adapter인 OpenCode는 `setup` 과정에서 설치할 수 있습니다.

```bash
python3 -m pip install .
hermes-control install
hermes-control doctor
hermes-control run -- setup
hermes-control setup --dry-run
hermes-control setup
```

기존 Hermes checkout은 수정하지 않습니다. 기본 관리 경로는 `~/.hermes-control`, Hermes 상태 경로는 `~/.hermes`입니다. 경로를 분리하려면:

```bash
hermes-control --root /opt/hermes-control install
HERMES_HOME=/srv/hermes-state hermes-control --root /opt/hermes-control run -- setup
hermes-control --root /opt/hermes-control setup --hermes-home /srv/hermes-state
```

지원되지 않는 upstream 버전에는 패치를 시도하지 않습니다. 정확한 baseline commit, patch SHA-256, 적용 후 파일별 SHA-256이 모두 맞아야 설치가 활성화됩니다.
설치기는 전체 Git 이력을 복제하지 않고, 호환 계약에 고정된 단일 upstream commit만 shallow fetch합니다.

## 운영 및 확장

- AI 운영자용 전체 절차: `docs/AI_OPERATIONS_MANUAL.md`
- 구조 설명: `docs/ARCHITECTURE_KO.md`
- 버전업 절차: `docs/UPSTREAM_COMPATIBILITY.md`
- patch에 포함되는 파일: `src/hermes_control/compatibility/hermes-agent-0.18.0/include-paths.txt`

## 라이선스

MIT. 설치 시 취득하는 Nous Hermes Agent 원본과 그에 적용되는 수정에는 upstream MIT 고지가 함께 적용됩니다. `NOTICE.md`를 참조하십시오.
