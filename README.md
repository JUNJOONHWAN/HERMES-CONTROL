# HERMES-CONTROL

[한국어](README.md) | [English](README_EN.md)

[![Compatibility](https://github.com/JUNJOONHWAN/HERMES-CONTROL/actions/workflows/compatibility.yml/badge.svg)](https://github.com/JUNJOONHWAN/HERMES-CONTROL/actions/workflows/compatibility.yml)
[![Python 3.11–3.13](https://img.shields.io/badge/python-3.11--3.13-3776AB.svg)](https://www.python.org/)
[![Hermes Agent 0.18.0](https://img.shields.io/badge/Hermes_Agent-0.18.0-6f42c1.svg)](https://github.com/NousResearch/hermes-agent)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**A version-gated governance and orchestration layer for Nous Hermes Agent.**

공식 Hermes Agent 위에 역할 셸, 카드 계약, 교체 가능한 AI 어댑터, Timeline Code Map, NeuralLink, 구조화 heartbeat를 더하는 독립 배포판입니다.

> [!IMPORTANT]
> HERMES-CONTROL은 Nous Research의 공식 프로젝트가 아닙니다. 전체 Hermes 소스를 포크해 재배포하지 않고, 검증된 공식 upstream 커밋을 설치 시 가져와 해시가 고정된 호환 패치를 적용합니다.

## 핵심 아이디어

일반적인 Hermes profile이 프롬프트·도구·스킬을 묶는다면, HERMES-CONTROL은 그 위에 **실행 거버넌스 계약**을 둡니다.

- **Root Hermes는 통제면**입니다. 목표를 카드로 만들고, 역할 셸과 어댑터를 선택하며, receipt를 검증한 뒤 결과를 전달합니다.
- **역할 셸은 지속적인 정책 단위**입니다. 허용 작업, 도구/MCP 범위, 동시 실행 수, 완료 조건과 에스컬레이션을 선언합니다.
- **어댑터는 교체 가능한 실행 경계**입니다. OpenCode를 기본 작업 경로로 쓰되 Codex CLI, Grok, 기타 command adapter를 같은 계약으로 연결할 수 있습니다.
- **카드와 receipt가 완료의 기준**입니다. 작업자의 “완료” 문장만으로 상태를 바꾸지 않고, 구조화된 증거와 산출물을 같은 저장 트랜잭션에서 검증합니다.
- **Timeline Code Map이 공유 증거 그래프**를 만듭니다. 맥락, 코드 슬라이스, 실행, 판단, 산출물과 관계를 append-only로 기록합니다.
- **NeuralLink가 필요한 과거 맥락을 회수**합니다. LLM 호출 직전에 Timeline 후보를 제한된 크기로 주입하되, 의미 검색의 완전성을 주장하지 않습니다.
- **Heartbeat는 세 층만 보고**합니다: `configuration`, `service_schedule`, `artifacts`.

이 구조의 장점은 특정 모델의 벤치마크 우위가 아니라, **누가·어떤 권한으로·무엇을 실행했고·어떤 증거로 완료됐는지 재현할 수 있다는 것**입니다. 자동 provider 라우팅보다 수동 통제와 감사 가능성을 우선하는 설계입니다.

## 구조 한눈에 보기

```text
User / Gateway
      │ objective
      ▼
Root Hermes ── creates/validates ──► Card Store
      │                                  │
      │ selects                          │ acceptance contract
      ▼                                  ▼
Role Shell ── binding/override ──► Adapter ──► Worker AI / CLI
      │                                  │
      │ policy                           │ artifact + receipt
      └──────────────────────────────────┘
                         │
                         ▼
             Receipt validation + atomic status
                         │
               ┌─────────┴─────────┐
               ▼                   ▼
       Timeline Code Map       Validated delivery
               │
               └── NeuralLink recall before later LLM calls
```

HERMES-CONTROL은 세 경계를 분리합니다.

| 경계 | 기본 위치 | 내용 |
|---|---|---|
| 배포 저장소 | 이 Git 저장소 | 설치기, 호환 manifest, patch, 테스트, 문서 |
| 관리 runtime | `~/.hermes-control/releases/<release>` | 검증된 Hermes 소스와 격리된 Python 환경 |
| 운영자 state | `~/.hermes` 또는 `HERMES_HOME` | 설정, 카드, receipt, adapter, Timeline DB, 플러그인, 로그 |

소스 업그레이드와 운영자 데이터는 서로 복사하지 않습니다. 개인 노하우 DB, API 키, 사용자 일정과 기존 Hermes 상태는 이 저장소에 포함되지 않습니다.

## 호환 범위

| 항목 | 현재 계약 |
|---|---|
| HERMES-CONTROL | `0.1.0` (Alpha) |
| Nous Hermes Agent | `0.18.0` |
| 고정 upstream commit | `5445e42b87b9918d5b1bfa9f4eadd8e4bb10ff37` |
| Python | `>=3.11,<3.14` |
| OS | Linux, macOS |
| 기본 작업 adapter | OpenCode (설치 선택 가능) |
| 선택 adapter | Codex CLI, Grok, generic command adapter |

지원되지 않는 upstream 버전에는 패치를 시도하지 않습니다. baseline commit, patch SHA-256, `git apply --check`, 적용 후 151개 파일의 SHA-256, 필수 경로와 import probe가 모두 맞아야 runtime이 활성화됩니다.

## 설치

요구사항은 Git, Python 3.11~3.13, macOS 또는 Linux입니다. OpenRouter는 기본 요구사항이 아닙니다.

```bash
git clone https://github.com/JUNJOONHWAN/HERMES-CONTROL.git
cd HERMES-CONTROL

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

검증된 runtime을 만들고 기본 Hermes 설정을 완료한 뒤 HERMES-CONTROL 계층을 부트스트랩합니다.

```bash
hermes-control install
hermes-control doctor

# 최초 1회: upstream Hermes의 provider/기본 설정
hermes-control run -- setup

# 생성될 셸·어댑터·Timeline 설정을 먼저 확인
hermes-control setup --dry-run
hermes-control setup

# 관리 runtime에서 Hermes 실행
hermes-control run -- --help
```

설치기는 전체 Git 이력을 복제하지 않고 호환 계약에 고정된 단일 upstream commit만 shallow fetch합니다. 기존 Hermes checkout은 수정하지 않습니다.

### 경로를 완전히 분리하는 설치

```bash
hermes-control --root /opt/hermes-control install
HERMES_HOME=/srv/hermes-state \
  hermes-control --root /opt/hermes-control run -- setup
hermes-control --root /opt/hermes-control \
  setup --hermes-home /srv/hermes-state
```

감사된 로컬 mirror나 오프라인 upstream checkout을 사용하려면 다음처럼 source를 명시합니다.

```bash
hermes-control install --source /path/to/hermes-agent
```

## CLI

| 명령 | 역할 |
|---|---|
| `hermes-control info` | 내장된 upstream/patch/플랫폼 호환 계약 출력 |
| `hermes-control install [--dry-run]` | 고정 baseline을 검증하고 관리 runtime 생성 |
| `hermes-control doctor` | host, source, patch 결과, venv와 import 상태 검사 |
| `hermes-control run -- <args>` | 활성화된 관리 runtime의 Hermes CLI 실행 |
| `hermes-control setup [--dry-run]` | 역할 셸, adapter, Timeline, NeuralLink, OpenCode 부트스트랩 |
| `hermes-control rollback` | 직전 검증 release로 active pointer 원자적 복구 |

모든 명령은 JSON 결과를 반환하므로 사람뿐 아니라 AI 운영자와 자동화가 동일한 상태 계약을 읽을 수 있습니다.

## 역할 셸과 어댑터 확장

OpenCode는 무료 모델을 활용할 수 있는 기본 경로지만 코어 의존성이 아닙니다. Codex CLI, Grok 또는 임의 CLI를 추가할 때는 다음 계약을 유지합니다.

1. 고유 adapter id, 실행 방식, capability tag, health command를 선언합니다.
2. 등록 후 실제 health check를 통과시킵니다. 등록만으로 준비 완료로 보지 않습니다.
3. 하나의 역할 셸에 capacity와 receipt policy를 포함해 binding합니다.
4. 실제 산출물을 요구하는 테스트 카드로 end-to-end 검증합니다.
5. override는 `once → temporary → permanent` 순서로 증거를 남기며 승격합니다.
6. health 또는 receipt 검증 실패 시 이전 binding으로 되돌립니다.

새 역할 셸은 책임, 허용/금지 도구, 동시 실행 수, 큐 동작, receipt schema, 산출물 조건을 명시해야 합니다. Pagent와 qagent는 필수 구성요소가 아니며, 필요하다면 같은 adapter 인터페이스로 붙일 수 있는 선택 부속품입니다.

자세한 AI 운영 절차는 [AI 운영 매뉴얼](docs/AI_OPERATIONS_MANUAL.md)의 “Adding an adapter”와 “Adding a shell”을 따르십시오.

## Timeline Code Map과 NeuralLink

의미 있는 코드 작업의 기본 흐름은 다음과 같습니다.

```text
load context → query code slice → act → record/link → query again → verify
```

NeuralLink는 Timeline을 대체하는 별도 메모리 DB가 아니라 `pre_llm_call` recall adapter입니다. 현재 구현은 bounded lexical/metadata retrieval이므로 다음 한계를 의도적으로 공개합니다.

- 추상적인 의미 유사성은 indexed concept와 alias 품질에 영향을 받습니다.
- character cap 때문에 큰 교차 목표의 일부 증거가 잘릴 수 있습니다.
- plugin은 fail-open이므로 recall 실패가 작업 자체를 막지는 않습니다.
- 최종 관련성은 호출된 AI의 후보 재랭킹 품질에도 의존합니다.

따라서 “메모리 문제를 완전히 해결”한다고 주장하지 않습니다. 대신 recall 실패를 관측 가능한 plugin/index health로 분리하고, 원본 증거는 Timeline 그래프에 보존합니다.

## Heartbeat

Heartbeat의 공개 출력은 정확히 세 층입니다.

1. `configuration`: shell, binding, adapter, controller, policy consistency
2. `service_schedule`: desired state, scheduler, last/next run evidence
3. `artifacts`: expected output, freshness, path, health

없는 층은 건강한 것으로 추정하지 않고 `absent`로 보고합니다.

## 안전성과 업그레이드

- 설치는 새 release 디렉터리에서 완료된 뒤 마지막 단계에서만 active pointer를 바꿉니다.
- 중간 실패는 현재 활성 release를 건드리지 않습니다.
- `doctor`가 파일 checksum과 runtime import를 다시 확인합니다.
- upstream 버전업은 manifest 숫자만 바꾸는 방식이 아닙니다. patch 재생성, 전체 checksum, materialization, 회귀 테스트가 모두 필요합니다.
- 운영자 secret과 state는 distribution repository에 커밋하지 않습니다.
- 문제가 생기면 `hermes-control rollback`으로 직전 검증 release를 활성화합니다.

버전업 절차와 실패 동작은 [Upstream compatibility contract](docs/UPSTREAM_COMPATIBILITY.md)에 정리되어 있습니다.

## 검증

0.1.0 공개 전 다음 게이트를 통과했습니다.

- HERMES-CONTROL unit: 19 passed
- Linux offline materialize/doctor/reinstall/rollback integration: 1 passed
- macOS ARM, Python 3.12 unit: 19 passed
- HERMES-CONTROL focused runtime: 151 passed
- Timeline extension: 40 passed
- 전체 materialized upstream regression: 38,314 passed, 0 failed
- Ruff, wheel contents, privacy scan, clean-worktree gate: passed

GitHub Actions는 Linux/macOS와 Python 3.11/3.12/3.13 조합에서 호환 경로를 계속 검사합니다.

개발 환경의 기본 검사는 다음과 같습니다.

```bash
python -m pip install -e '.[test]'
python -m pip install ruff
ruff check src tests scripts
pytest -q
```

## 문서

- [AI 운영 매뉴얼](docs/AI_OPERATIONS_MANUAL.md): 설치 상태 머신, 카드/receipt, 셸·adapter 추가, release gate
- [구조 설명](docs/ARCHITECTURE_KO.md): 구성요소와 실행 흐름 요약
- [Upstream 호환 계약](docs/UPSTREAM_COMPATIBILITY.md): baseline 갱신과 fail-closed 정책
- [패치 포함 경로](src/hermes_control/compatibility/hermes-agent-0.18.0/include-paths.txt): overlay bundle의 추출 범위

## 범위 밖

이 공개판에는 개인 노하우 DB, API credential, 사용자별 MCP 설정, 사설 일정, 기존 카드/Timeline 데이터가 포함되지 않습니다. 시장 메모리는 빈 schema와 도구 frame만 제공하며, 운영자가 자신의 state에 수동으로 추가할 수 있습니다.

## 라이선스

HERMES-CONTROL은 [MIT License](LICENSE)로 배포됩니다. 설치 시 취득하는 Nous Hermes Agent 원본과 그에 적용되는 수정에는 upstream MIT 고지가 함께 적용됩니다. 자세한 내용은 [NOTICE.md](NOTICE.md)를 참조하십시오.
