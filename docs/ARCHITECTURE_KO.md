# HERMES-CONTROL 구조 요약

```text
User / Gateway / CLI
          |
          v
  Root governance plane
  - Project/Card lifecycle (controller-owned)
  - root-card thread + typed relations
  - shell selection
  - binding/override
  - receipt validation
          |
          v
  Role Shell policy boundary
          |
          v
  Executor Adapter
  - OpenCode (default)
  - Codex CLI
  - Grok
  - generic command
  - optional external adapters
          |
          v
  Structured receipt + artifacts
          |
          +----> Kanban atomic state
          +----> Gateway delivery
          +----> Timeline Code Map

Timeline Code Map --bounded recall--> NeuralLink pre_llm_call
Heartbeat --------------------------> configuration / service_schedule / artifacts
```

Project/Card Controller는 여기에 별도 worker를 하나 더 넣는 구조가 아니다. Root governance plane의 결정적 상태 기계이며, 웹 UI와 Telegram의 `supervisor_project`가 같은 서비스 함수를 호출한다. Project는 장기 팀 작업의 컨테이너이고, Board는 그 카드를 보여주고 실행하는 저장·뷰 경계다.

카드 관계는 실행 의미를 가진다. `depends_on`, `follows`, `reviews`는 부모가 끝날 때까지 자식을 막고, `references`, `recovers`는 병렬 분할과 실패 복구가 즉시 실행되도록 lineage만 보존한다. 후속 작업은 기존 `root_task_id`를 상속하고, 독립 신규 작업은 같은 Project 안에서 자기 자신을 root로 갖는 새 thread를 연다. 완료 카드는 수정하지 않고 새 카드를 연결하므로 수개월 뒤 재개해도 과거 receipt와 adapter provenance가 유지된다.

workspace도 컨트롤러가 카드 생성 전에 결정한다. Project 경로가 없으면 관리형 `scratch`, 일반 디렉터리면 역할과 무관하게 보존형 `dir`, Git 저장소에서 실행하는 `code` 카드면 카드별 linked `worktree`다. 따라서 비-Git 프로젝트를 worktree로 잘못 예약해 실행 단계에서 반복 실패시키지 않는다. 명시적 worktree는 절대경로와 Git anchor를 선검증하며, 실패 복구는 원본을 수정하지 않고 workspace를 교정한 `recovers` 카드를 발행한다. 복구 Receipt가 완료되면 원본 blocked 시도만 archive되고 실행·오류·계보 증거는 보존된다.

표준 Hermes profile은 주로 모델·프롬프트·도구 구성을 묶습니다. HERMES-CONTROL은 그 위에 실행 책임의 경계와 상태 전이 계약을 추가합니다. 차별점은 단순히 provider를 많이 붙이는 것이 아니라, 누가 어떤 정책으로 일을 맡았고 무엇을 근거로 완료됐는지를 카드·receipt·Timeline에서 감사할 수 있다는 점입니다.

자동 provider routing 시스템과 비교하면 HERMES-CONTROL은 수동 승격과 명시적 통제를 더 중시합니다. 따라서 자동 최적화 자체가 우월하다고 주장하지 않습니다. 장점은 재현성과 감사 가능성이고, 단점은 정책과 binding 운영 비용입니다.

NeuralLink는 메모리 문제를 완전히 해소하지 않습니다. embedding 서버 의존 없이 가볍게 공유 기억을 주입하지만, 추상 의미 유사성·fail-open 관측성·문맥 길이 cap이라는 한계가 남습니다. 이 한계를 숨기지 않고 Timeline 원장과 heartbeat 상태를 분리해 검증하는 것이 설계의 일부입니다.

시간 정책은 원본 삭제와 recall 노출을 분리합니다. Timeline 원본은 보존하고 live quote와 runtime state만 TTL로 일반 recall에서 제외합니다. report와 완료 작업은 `episodic`, 정책·계약·판단·노하우는 `durable`입니다. 명시적 과거 회상에서 만료 증거를 다시 노출할 때는 `STALE/EXPIRED` 표시와 현재 데이터 재검증을 강제합니다.
