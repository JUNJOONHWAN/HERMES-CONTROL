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

## 이 프로젝트에 실제로 들어 있는 것

HERMES-CONTROL은 작은 installer만 제공하는 프로젝트가 아닙니다. installer가 고정된 Hermes baseline 위에 다음의 **전체 운영 구조**를 재현합니다.

| 영역 | 제공 기능 |
|---|---|
| 칸반 웹 UI | drag-and-drop 카드, 8개 상태 열, task drawer, 댓글, dependency, run 이력, attachment, 진단 경고, 실시간 WebSocket 갱신 |
| 멀티보드 | 프로젝트별 독립 SQLite DB·workspace·log·attachment, dashboard board switcher, worker의 board 격리 |
| 카드 실행 커널 | durable task, atomic claim, dependency promotion, idempotent create, crash/stale reclaim, circuit breaker, structured completion |
| Root Controller | 도메인 MCP 없이 여섯 supervisor 도구로 상태·자동화·역할·위임·프로젝트/카드·adapter를 통제 |
| Project/Card Controller | 별도 Project DB, `p_*`/`t_*` 이중 ID, `pa_*` 승인, 실행 중 stop/checkpoint 방향 전환, pause/reopen, typed relation, 신규·후속·분할·검증·복구를 웹·텔레그램 공통 경로에서 관리 |
| 프로젝트 Git 관리 | existing/init-local/GitHub 저장소 등록, private/public 선택, 카드 branch checkpoint commit/push와 default-branch 직접 push 차단 |
| 8개 Role Shell | `code`, `market`, `browser-research`, `operations`, `report`, `verification`, `tool-management`, `hermes-repair` |
| Adapter Control Plane | controller와 worker executor 분리, 다대다 Binding, capacity/health/capability gate, task/shell/all override |
| 멀티툴·MCP 관리 | profile별 MCP·skill·plugin·toolset·callable tool inventory/search, 최소 배치, backup, probe, rollback |
| 증거·완료 | 카드 claim과 shell/executor/binding provenance 원자적 고정, Timeline 증거를 검사하는 Receipt Gate |
| 기억·코드 영향 | profile memory, Timeline Code Map, NeuralLink recall, typed Roadmap와 host 간 delta sync |
| 운영 상태 | `configuration`, `service_schedule`, `artifacts`의 3층 heartbeat와 산출물 freshness |

표준 Hermes의 profile·gateway·Kanban·dashboard를 그대로 포함하면서, HERMES-CONTROL은 그 위에 Role Shell, Binding, Override, Receipt, zero-domain-MCP root와 증거 게이트를 추가합니다.

## 칸반 보드와 웹 UI

칸반은 부가 화면이 아니라 작업의 authoritative state machine입니다. 사람, AI worker, CLI, cron, dashboard가 모두 같은 board DB를 읽고 씁니다.

```bash
# gateway가 15초 간격의 embedded dispatcher를 실행
hermes-control run -- gateway start

# 별도 터미널에서 dashboard 실행
hermes-control run -- dashboard
```

브라우저에서 `http://127.0.0.1:9119/kanban`을 엽니다. 기본 bind는 localhost이며 원격 서버는 SSH port forwarding을 사용합니다.

```bash
ssh -L 9119:127.0.0.1:9119 user@remote-host
```

웹 보드는 다음을 제공합니다.

- 상태 열: `triage → todo → scheduled → ready → running → blocked → review → done`
- 카드 drag-and-drop과 상태 전이 검증
- 카드 생성·수정·archive, assignee/profile, role shell, 우선순위와 tenant
- parent/child dependency와 부모 완료 후 `todo → ready` 자동 승격
- 사람과 agent가 함께 쓰는 durable comment thread
- run history와 실제 `role_shell_id`, `executor_id`, `binding_id`, `adapter_override_id`, `receipt_id`
- PDF·이미지·소스 문서 attachment 업로드/다운로드와 worker 절대경로 전달
- stale run, hallucinated task reference, receipt 문제를 보여주는 diagnostics
- append-only task event를 tail하는 인증된 WebSocket live update
- 여러 board의 생성·전환·archive와 board별 DB/workspace/log/attachment 완전 분리
- 프로젝트 필터, 프로젝트 시작·종료·재개와 `New root card`·`Follow-up`·`Change direction`·`Split`·`Verify`·`Recover` 동작

### Project/Card Controller

프로젝트 관리는 worker adapter에 위임되지 않습니다. `supervisor_project`와 Kanban API가 같은 결정적 컨트롤러 서비스를 호출하고, 그 서비스만 프로젝트 상태와 카드 관계 그래프를 기록합니다. adapter는 컨트롤러가 만든 카드의 Role Shell 계약 안에서 실행할 뿐입니다.

- Project는 `active ↔ paused`와 `active → completed → active` 생명주기를 가지며, 실행 카드가 있으면 pause가, 열린 카드나 pending 승인이 있으면 종료가 거절됩니다.
- 코드 카드 요청은 즉시 `t_*`를 만들지 않습니다. 먼저 `pa_*` 승인 요청만 저장하고 Project를 `paused`로 바꾸며, 다음 운영자 동작에서 승인해야 정확히 한 카드가 생성됩니다. 같은 제안은 중복 생성되지 않습니다.
- 실행 중 범위·산출물·Role Shell·완료 조건이 크게 바뀌면 `Change direction`이 원본을 중지·archive하고 Git 작업공간을 checkpoint한 뒤 `pa_*` 후속 초안만 만듭니다. 운영자가 별도 승인하기 전에는 후속 `t_*`가 존재하거나 실행되지 않으며, 승인된 후속은 원본과 비차단 `references`로 연결됩니다.
- 첫 카드는 자기 자신을 `root_task_id`로 갖고, 모든 후속·분할·검증·복구 카드는 같은 thread root를 상속합니다.
- 관계는 `depends_on`, `follows`, `reviews`, `recovers`, `references`로 구분됩니다. 앞의 세 가지는 실행을 막는 dependency이고, 뒤의 두 가지는 실패 복구와 병렬 분할을 막지 않는 lineage입니다.
- 각 카드에는 명시적 `acceptance_criteria`와 `input_refs`가 저장됩니다.
- 컨트롤러가 카드 생성 전에 workspace를 판정합니다. Project 경로가 없으면 `scratch`, 일반 폴더면 모든 역할에 보존형 `dir`, Git 저장소의 `code` 카드면 격리 `worktree`를 사용합니다. Git 기준점이 없는 명시적 worktree 요청은 디스패치 전에 거절됩니다.
- 실패 복구는 원본 카드를 덮어쓰지 않습니다. `Recover`가 새 카드와 `recovers` 계보를 만들고, 복구 카드가 Receipt Gate를 통과하면 막힌 원본 실행을 감사 이력과 함께 archive합니다. Web과 Telegram 모두 복구 workspace를 명시적으로 바꿀 수도 있습니다.
- 완료 카드는 다시 쓰지 않습니다. 수개월 뒤에도 카드 ID를 찾아 새 follow-up 또는 새 root card를 발행합니다.
- 웹 UI와 Telegram/Supervisor는 별도 상태를 만들지 않고 같은 Project DB와 board DB를 사용합니다.
- 프로젝트 Git은 `none`, `existing`, `init_local`, `github` mode를 지원합니다. 카드별 worktree branch만 commit/push할 수 있고 `main`, `master`, default branch 직접 push는 거부됩니다.
- Telegram과 웹 UI는 항상 Project `p_*`와 Card `t_*`를 함께 표시합니다. 실제 claim이 발생하면 Telegram은 `🔄 작업중 · <제목>` 아래에 두 ID를 한 번 표시하고, 완료·중단·실패 알림도 같은 이중 ID를 유지합니다. 새 알림 구독은 현재 event cursor에서 시작해 과거 실패를 재전송하지 않습니다.

카드는 `~/.hermes/kanban.db` 또는 named board의 `~/.hermes/kanban/boards/<slug>/kanban.db`에 남습니다. workspace는 목적에 따라 선택합니다.

| workspace | 용도 | 완료 후 |
|---|---|---|
| `scratch` | 임시 조사·변환 | 삭제 |
| `dir:/absolute/path` | 기존 공유 디렉터리 | 보존 |
| `worktree` / `worktree:<path>` | 격리된 코드 작업 | 보존 |

worker는 shell로 `hermes kanban`을 호출하지 않습니다. dispatcher가 `HERMES_KANBAN_TASK`와 board를 고정해 프로세스를 띄우고, 모델은 `kanban_show`, `kanban_list`, `kanban_create`, `kanban_link`, `kanban_comment`, `kanban_heartbeat`, `kanban_complete`, `kanban_block`, `kanban_unblock` 도구로 같은 DB를 직접 다룹니다.

```bash
# 사람/자동화용 CLI 표면
hermes-control run -- kanban init
hermes-control run -- kanban create "Review authentication flow" --assignee hermes-worker-general
hermes-control run -- kanban watch
hermes-control run -- kanban stats

# 프로젝트별 board
hermes-control run -- kanban boards create api-service --name "API Service" --switch
hermes-control run -- kanban --board api-service list
```

### 카드 실행, provenance, Receipt Gate

dispatcher는 단순히 `ready`를 `running`으로 바꾸지 않습니다. 한 `BEGIN IMMEDIATE` transaction에서 dependency와 override를 다시 확인하고, eligible Binding의 capacity를 예약하고, 상태를 compare-and-swap한 뒤 `task_runs`에 `shell/executor/binding/override` provenance를 고정합니다. 이 방식은 capacity 1 실행기를 두 dispatcher가 동시에 잡는 TOCTOU를 막습니다.

worker 종료도 자연어 한 줄로 닫히지 않습니다. canonical Receipt에는 최소한 다음이 들어갑니다.

```text
trusted task/run/shell/executor/binding/override ids
terminal status: completed | blocked | failed
Timeline goal, context-loaded flag, slice ids, action/output node ids
verify_all result
artifact paths and test commands/results
known limitations
```

DB의 현재 run과 제출 provenance가 다르거나, code shell에 slice가 없거나, 필요한 Timeline/output 증거가 없으면 terminal transition을 거절합니다. Receipt가 통과한 같은 transaction에서 receipt 저장, card/run 종료, task-scoped `once` override 소비가 이루어집니다. crash·stale PID·timeout run은 reclaim되고, 반복 spawn/block은 circuit breaker가 triage/blocked로 올려 thrashing을 막습니다.

## 핵심 아이디어

일반적인 Hermes profile이 프롬프트·도구·스킬을 묶는다면, HERMES-CONTROL은 그 위에 **실행 거버넌스 계약**을 둡니다.

- **Root Hermes는 통제면**입니다. 목표를 카드로 만들고, 역할 셸과 어댑터를 선택하며, receipt를 검증한 뒤 결과를 전달합니다.
- **역할 셸은 지속적인 정책 단위**입니다. 허용 작업, 도구/MCP 범위, 동시 실행 수, 완료 조건과 에스컬레이션을 선언합니다.
- **어댑터는 교체 가능한 실행 경계**입니다. OpenCode를 기본 작업 경로로 쓰되 Codex CLI, Grok, 기타 command adapter를 같은 계약으로 연결할 수 있습니다.
- **무료 실행 라우팅은 일반 역할에만 자동 배치**됩니다. OpenRouter strict-free와 OpenCode free는 실행 전 live catalog를 다시 읽어 종료·유료 전환·사용량 소진 후보를 넘기고, 새 무료 후보를 반영합니다.
- **Hermes 수선은 별도 품질 경계**입니다. 여덟 번째 `hermes-repair` Role Shell은 `gpt-5.6-sol/high`가 기본이며, 다른 실행 어댑터는 별도 `hermes-repair-v1` 성능·안전 시험과 운영자 승인을 통과해야만 교체할 수 있습니다.
- **카드와 receipt가 완료의 기준**입니다. 작업자의 “완료” 문장만으로 상태를 바꾸지 않고, 구조화된 증거와 산출물을 같은 저장 트랜잭션에서 검증합니다.
- **Timeline Code Map이 공유 증거 그래프**를 만듭니다. 맥락, 코드 슬라이스, 실행, 판단, 산출물과 관계를 append-only로 기록합니다.
- **NeuralLink가 필요한 과거 맥락을 회수**합니다. LLM 호출 직전에 Timeline 후보를 제한된 크기로 주입하되, 의미 검색의 완전성을 주장하지 않습니다.
- **Heartbeat는 세 층만 보고**합니다: `configuration`, `service_schedule`, `artifacts`.

이 구조의 장점은 특정 모델의 벤치마크 우위가 아니라, **누가·어떤 권한으로·무엇을 실행했고·어떤 증거로 완료됐는지 재현할 수 있다는 것**입니다. 자동 provider 라우팅보다 수동 통제와 감사 가능성을 우선하는 설계입니다.

## 구조 한눈에 보기

```text
Chat / CLI / Cron / Kanban Web UI
                 │
                 ▼
   Root Controller (6 control tools, zero domain MCP)
                 │ create/delegate/inspect/switch
                 ▼
      Kanban DB + Event Stream ◄────► Dashboard API / WebSocket
                 │ atomic claim
                 ▼
 Immutable Role Shell ──► Binding / Override ──► Eligible Executor Adapter
        │                         │                       │
        │ policy                  │ provenance            ├─ Hermes profile
        │                         │                       ├─ OpenCode Free
        │                         │                       ├─ OpenRouter strict-free
        │                         │                       ├─ Codex CLI
        │                         │                       └─ generic command
        │
        └─ hermes-repair ──► hermes-repair-v1 gate ──► Maintainer
                                                     default: gpt-5.6-sol/high
        │                         ▼
        │               capability ∩ health ∩ capacity
        │
        ├─ tool-management ──► MCP / skill / plugin / toolset catalog
        │
        ▼
 Output + tests ──► Timeline / Code Map ──► Receipt Gate
                          │                        │
                          ├─ NeuralLink recall     └─ atomic done/block/fail
                          └─ Typed Roadmap / sync

 Three-layer heartbeat: configuration | service_schedule | artifacts
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
| HERMES-CONTROL | `0.1.8` (Alpha) |
| Nous Hermes Agent | `0.18.0` |
| 고정 upstream commit | `5445e42b87b9918d5b1bfa9f4eadd8e4bb10ff37` |
| Python | `>=3.11,<3.14` |
| OS | Linux, macOS |
| 기본 경로 | health gate를 통과한 OpenCode 무료 model controller/worker |
| 선택 controller | OpenRouter strict-free, Grok, OpenRouter Gemma, local OpenAI-compatible/vLLM |
| 선택 worker | OpenRouter strict-free, OpenCode free, Codex CLI, generic command adapter |

지원되지 않는 upstream 버전에는 패치를 시도하지 않습니다. baseline commit, patch SHA-256, `git apply --check`, manifest의 모든 patched file SHA-256, 필수 경로와 import probe가 모두 맞아야 runtime이 활성화됩니다.

`0.1.8`은 기존 `0.1.0`~`0.1.7` 번들을 보존하고 HERMES-TEAM과 공통 배포 버전 `0.1.8`을 강제합니다. OpenRouter strict-free와 OpenCode free는 컨트롤러뿐 아니라 일반 7개 Role Shell의 낮은 우선순위 실행 후보로 등록되며, 매 작업의 live catalog에서 무료·tool 조건을 확인하고 strongest-first fallback을 구성합니다. 일반 프로젝트 코딩·수선은 `code`/`operations`와 저비용 실행기에 남습니다. Hermes 자체 controller·adapter·Role Shell·router·supervisor 설정만 `hermes-repair`가 담당하며 기본 실행자는 `gpt-5.6-sol/high`입니다. 대체 실행자는 별도 `hermes-repair-v1` 20개 이상 평가, 전체 95%·중요 항목 100%, baseline 점수 95% 이상, 중앙 지연 1.5배 이하, 기본 브랜치 쓰기 0회, Timeline invalid 0, SHA-256 평가 artifact와 운영자 승인을 모두 통과해야 합니다.

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

# 실제 카드 dispatch와 웹 보드
hermes-control run -- gateway start
hermes-control run -- dashboard
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

## Root Controller와 8개 Role Shell

Root Hermes는 일반 worker가 아닙니다. root MCP catalog는 비어 있고 다음 여섯 제어 도구만 사용합니다.

```text
supervisor_status      현재 서비스·worker·schedule·artifact 상태
supervisor_automation  cron/job 실패와 복구 흐름
supervisor_roles       활성 shell과 route 가능성
supervisor_delegate    shell 계약을 가진 카드 생성·위임
supervisor_project     프로젝트·독립 root·후속·방향 전환·분할·검증·복구·종료 관리
supervisor_adapter     controller/executor/binding/override/tool catalog 관리
```

실제 도메인 작업은 다음 불변·버전형 Role Shell 중 하나를 거칩니다.

| Role Shell | 책임 | 주요 필수 capability | 핵심 경계 |
|---|---|---|---|
| `code` | 소스 변경과 테스트 | file, terminal, kanban, Timeline | stored code slice 필수; 배포권은 별도 |
| `market` | 공개 시장·금융 조사 | web, kanban, Timeline | 거래/account write 금지; 개인 DB 미포함 |
| `browser-research` | 로그인·동적 페이지 조사 | browser, kanban, Timeline | 접근 우회·범위 밖 write 금지 |
| `operations` | service, cron, watchdog | file, terminal, kanban, Timeline | 정확한 unit/PID와 desired state 검증 |
| `report` | 상위 receipt 기반 보고서 조립 | file, kanban, Timeline | 중간 산출물을 완료로 승격 금지 |
| `verification` | 독립 회귀·최종 게이트 | file, terminal, kanban, Timeline | baseline failure와 새 regression 분리 |
| `tool-management` | MCP·skill·plugin·toolset lifecycle | file, terminal, skills, kanban, Timeline | 최소 권한 배치, backup/probe/rollback 의무 |
| `hermes-repair` | Hermes 자체 제어면·adapter·shell·router·설정 수선 | file, terminal, kanban, Timeline | 일반 프로젝트 코딩 금지; 기본 `gpt-5.6-sol/high`, 인증 후보로만 교체 |

Role Shell row는 SQLite trigger로 update/delete가 금지됩니다. 정책 변경은 같은 `shell_key`의 새 version과 새 contract hash로만 가능하므로 과거 카드가 어떤 계약 아래 실행됐는지 유지됩니다.

## Executor와 Adapter Control Plane

Role Shell은 “무엇을 할 수 있고 무엇을 증명해야 하는가”이고, Executor는 “실제로 누가 실행하는가”입니다. 기본 profile pool은 다음과 같습니다.

| Executor profile | 기본 역할 | capacity | 공개판 기본 MCP |
|---|---|---:|---|
| `hermes-worker-general` | code, operations, report, verification | 3 | Timeline |
| `hermes-worker-market` | market | 2 | Timeline; 추가 market MCP는 역할별 설치 |
| `hermes-worker-browser` | browser research | 2 | Timeline; browser MCP는 역할별 설치 |
| `hermes-worker-universal` | 낮은 우선순위 provider-neutral fallback | 4 | Timeline |
| `hermes-worker-multitool` | MCP/skill/plugin/toolset 관리 | 1 | Timeline |
| `hermes-worker-opencode-free` | 일반 7개 역할의 동적 무료 후보 | 2 | Role Shell이 허용한 도구 |
| `hermes-worker-openrouter-free` | 일반 7개 역할의 strict-free 후보 | 2 | Role Shell이 허용한 도구 |
| `hermes-worker-hermes-maintainer` | Hermes 자체 수선 전용 | 1 | file, terminal, kanban, Timeline |

controller adapter와 worker executor는 별도 축입니다.

| 통합 | 지원 위치 | 활성화 조건 |
|---|---|---|
| OpenCode free | 기본 controller + 일반 worker 후보 | 매 작업 live 무료 catalog와 tool-call health gate 통과 |
| OpenRouter strict-free | 선택 controller + 일반 worker 후보 | 0가격·tool·context 필터와 ordered `models` fallback |
| Codex CLI | 선택형 command worker | 기존 Codex 로그인 + binary/version probe |
| Grok | 선택형 controller candidate | `XAI_API_KEY` + catalog/tool-call probe |
| OpenRouter Gemma | 비활성 controller candidate | operator 설정 + health gate; 기본값 아님 |
| local OpenAI-compatible/vLLM | 비활성 controller candidate | endpoint와 model probe |
| generic command | 임의 CLI worker | `shell=false`, argv/prompt placeholder, capability/MCP probe |

Binding은 Shell↔Executor 다대다 관계이며 우선순위, weight, capacity, capability cap을 가집니다. 실제 권한은 다음 교집합보다 넓어질 수 없습니다.

```text
effective capabilities
  = Role Shell allowed
  ∩ Executor capabilities
  ∩ Binding capability cap
```

health, heartbeat TTL, capacity와 required MCP/tool probe까지 통과한 후보만 claim할 수 있습니다. Override 우선순위는 `task > shell > all > default`이고 수명은 `once`, `temporary`, `permanent`입니다. 강제한 대상이 부적격이면 건강한 다른 후보로 몰래 폴백하지 않고 fail-closed합니다.

새 command adapter를 추가하는 절차:

1. 고유 id, argv, `{prompt_file}`, capability, health/tool probe를 JSON descriptor로 선언합니다.
2. `scripts/register_external_adapter.py`로 candidate를 등록합니다.
3. 실제 health와 required MCP/tool probe를 통과시킵니다.
4. 하나 이상의 Role Shell에 capacity와 capability cap을 가진 Binding을 만듭니다.
5. 실제 산출물과 Receipt를 요구하는 카드로 end-to-end 검증합니다.
6. `once → temporary → permanent` 순으로 감사 이벤트를 남기며 승격합니다.

`hermes-repair`에 연결할 후보는 위 절차만으로 부족합니다. 실행기 설정에 동일 실행기를
대상으로 한 `hermes-repair-v1` 평가 artifact와 성능·안전 지표, 명시적 운영자 승인을
기록해야 합니다. 일반 무료 실행 어댑터는 이 Shell에 자동 바인딩되지 않습니다.

자연어 사용 예:

```text
이번 카드 t_12345678만 OpenRouter 무료 실행 어댑터로 실행해.
코드 역할을 OpenCode 무료 실행 어댑터로 1시간 임시 전환해.
현재 무료 실행 어댑터의 실제 모델 순서와 health를 보여줘.
Hermes 수선 후보 X의 hermes-repair-v1 성능 평가만 실행해. 아직 배정하지 마.
평가 artifact와 승인 기록이 유효하면 Hermes 수선 역할을 후보 X로 영구 전환해.
```

Pagent와 qagent는 필수 구성요소가 아닙니다. 필요하면 같은 command adapter 경계에 붙일 수 있는 선택 부속품입니다.

## 멀티툴, MCP, skill, plugin 관리

HERMES-CONTROL은 모든 MCP를 root에 꽂는 방식이 아닙니다. root는 zero-domain-MCP 상태를 유지하고, `tool-management` 카드가 capacity 1의 `hermes-worker-multitool`에서 도구 lifecycle을 담당합니다.

도구 catalog는 다음 전체 inventory를 **이름과 assignment 중심으로** 보여주며 credential이나 MCP 정의 원문은 노출하지 않습니다.

- profile별 `mcp_servers`
- 설치된 skills와 plugins
- Hermes toolsets와 확장된 built-in callable tools
- 각 executor가 선언한 capabilities
- MCP/skill/toolset/callable tool의 profile별 owner 역색인
- profile config parse 오류와 catalog health

대화 제어면의 `supervisor_adapter(action="tools", query="...")`는 누락된 capability 후보를 catalog 전체에서 검색합니다. 실제 설치·이동은 별도 `tool-management` 카드로 수행하며 다음 순서를 강제합니다.

```text
inventory/search
→ provenance·compatibility 확인
→ 대상 profile의 정확한 config backup
→ 최소 MCP/skill/plugin/toolset만 배치
→ health + declared tool probe
→ before/after assignment와 receipt 기록
→ 실패 시 rollback 또는 code/operations repair로 handoff
```

실행 중인 model context는 hot-mutate하지 않습니다. 변경은 새 worker session부터 적용됩니다. 브라우저 로그인 탐색은 `browser-research`, source 수정은 `code`, service restart·secret 확대는 `operations`/repair 카드로 분리됩니다. 이 구조는 도구 관리를 중앙에서 볼 수 있게 하면서도 profile 격리와 blast radius 제한을 유지합니다.

운영 상태 확인 예:

```bash
hermes-control run -- supervisor shell list --active --json
hermes-control run -- supervisor executor list --json
hermes-control run -- supervisor binding list --json
hermes-control run -- supervisor adapter list --json
hermes-control run -- supervisor heartbeat --json
```

자세한 AI 운영 절차는 [AI 운영 매뉴얼](docs/AI_OPERATIONS_MANUAL.md)의 “Adding an adapter”와 “Adding a shell”을 따르십시오.

## 메모리, Timeline Code Map, NeuralLink, Roadmap

“메모리”는 하나의 DB가 아니라 네 층입니다.

| 층 | 역할 | 공유 범위 |
|---|---|---|
| profile `MEMORY.md` / `USER.md` | 다음 session에 들어가는 curated memory snapshot | profile 격리 |
| optional MemoryProvider | turn별 external prefetch/sync | 설치한 provider 범위 |
| Timeline | context·판단·action·output·관계의 durable evidence graph | shell/worker가 공유 |
| NeuralLink | Timeline 위 lexical/metadata candidate recall | 현재 root `pre_llm_call` |

profile memory는 session 시작 시 frozen snapshot이 되므로 현재 turn의 자기변조를 막지만, 방금 쓴 memory는 다음 session부터 prompt에 반영됩니다. worker가 root의 `MEMORY.md`를 자동 공유하지는 않습니다. 공통으로 공유되는 것은 카드 provenance와 Timeline evidence입니다.

Timeline은 node/edge hash chain뿐 아니라 repository code index도 가집니다. code task의 기본 게이트는 다음과 같습니다.

```text
load context
→ query/store code slice
→ target source/test/config 직접 읽기
→ action과 output node 기록·연결
→ 같은 query로 영향 drift 재검사
→ verify_all
→ Receipt에 goal/slice/node/test/output 포함
```

code slice는 relevant/affected files, symbols, relationship flow, watchpoints, patch checkpoints, freshness와 `slice_id`를 반환합니다. `verify_all`은 저장된 hash chain의 구조적 무결성을 증명하지만, node 내용의 사실성이나 테스트 성공을 대신하지 않습니다.

NeuralLink는 Timeline을 대체하는 별도 벡터 DB가 아니라 `pre_llm_call` recall adapter입니다. workflow/entity/concept/title/token/metadata를 인덱스하고 TTL, recency, association edge, multi-hop으로 후보를 만듭니다. 별도 embedding server나 GPU가 필요 없지만 다음 한계가 있습니다.

- 추상적인 의미 유사성은 indexed concept와 alias 품질에 영향을 받습니다.
- 동의어가 metadata에 없으면 관련 기억을 놓칠 수 있습니다.
- character cap 때문에 큰 교차 목표의 일부 증거가 잘릴 수 있습니다.
- plugin은 fail-open이므로 recall 실패가 작업 자체를 막지는 않습니다.
- 최종 관련성은 호출된 AI의 후보 재랭킹 품질에도 의존합니다.

따라서 “메모리 문제를 완전히 해결”한다고 주장하지 않습니다. embedding 운영 의존을 줄이는 대신 semantic miss 위험을 받아들였으며, 원본 증거는 Timeline 그래프에 보존합니다.

시간 정책은 노드 전체에 `market`이라는 단어가 있는지만 보지 않습니다. 실시간 quote/bar/orderbook/snapshot만 기본 1일 `market_live`, service status/health/probe/heartbeat만 기본 7일 `runtime_state`로 만료됩니다. report/analysis/action/review는 `episodic`, policy/contract/decision/architecture/playbook/runbook/know-how는 `durable`로 보존됩니다. `memory_descriptor.temporal_scope` 또는 `freshness_class`가 자동 분류보다 우선합니다.

“전에”, “예전”, “과거” 같은 명시적 과거 회상은 만료 노드도 후보로 가져올 수 있지만 반드시 `STALE/EXPIRED`로 표시합니다. 당시 증거는 현재 시세나 현재 서비스 상태로 사용하기 전에 재검증해야 합니다. 업그레이드 후 versioned NeuralLink backfill은 기존 Timeline 노드를 삭제하지 않고 분류만 갱신합니다.

Typed Roadmap은 Kanban과 별개로 계획 event와 projection을 분리합니다. entity version, idempotent event id, dependency, schedule intent를 저장하고 replay로 현재 projection을 재구축합니다. 시간 기반 작업은 `KST intent / UTC-stored RRULE`처럼 의도 시간대와 실행 저장값을 함께 보존할 수 있습니다.

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

0.1.5 배포의 기존 검증 기록은 다음과 같습니다. 0.1.8은 새 immutable bundle과 현재 GitHub Actions에서 별도로 검증합니다.

- HERMES-CONTROL unit: 19 passed
- 공식 upstream source-backed installer: 2 passed
- Linux clean materialize/doctor: 패치 파일 164/164 검증
- HERMES-CONTROL focused runtime: 175 passed
- Timeline extension: 44 passed
- 전체 materialized upstream regression: 1,844 files, 38,275 passed, 0 failed
- macOS ARM Python 3.11/3.12/3.13 unit: 각 19 passed
- Linux setup dry-run: 7 role shells, 빈 Root MCP, Timeline/NeuralLink 계획 검증(0.1.5 기록)
- Ruff, sdist/wheel build, wheel install smoke, privacy scan, README link, `git diff --check`: passed

### 0.1.0 역사적 검증 기록

0.1.0 공개 전에는 다음 게이트를 통과했습니다.

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
- [현재 패치 포함 경로](src/hermes_control/compatibility/hermes-agent-0.18.0-control-0.1.8/include-paths.txt): overlay bundle의 추출 범위

## 범위 밖

이 공개판에는 개인 노하우 DB, API credential, 사용자별 MCP 설정, 사설 일정, 기존 카드/Timeline 데이터가 포함되지 않습니다. 시장 메모리는 빈 schema와 도구 frame만 제공하며, 운영자가 자신의 state에 수동으로 추가할 수 있습니다.

## 라이선스

HERMES-CONTROL은 [MIT License](LICENSE)로 배포됩니다. 설치 시 취득하는 Nous Hermes Agent 원본과 그에 적용되는 수정에는 upstream MIT 고지가 함께 적용됩니다. 자세한 내용은 [NOTICE.md](NOTICE.md)를 참조하십시오.
