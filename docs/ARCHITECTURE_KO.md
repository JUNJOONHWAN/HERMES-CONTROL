# HERMES-CONTROL 구조 요약

```text
User / Gateway / CLI
          |
          v
  Root governance plane
  - card lifecycle
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

표준 Hermes profile은 주로 모델·프롬프트·도구 구성을 묶습니다. HERMES-CONTROL은 그 위에 실행 책임의 경계와 상태 전이 계약을 추가합니다. 차별점은 단순히 provider를 많이 붙이는 것이 아니라, 누가 어떤 정책으로 일을 맡았고 무엇을 근거로 완료됐는지를 카드·receipt·Timeline에서 감사할 수 있다는 점입니다.

자동 provider routing 시스템과 비교하면 HERMES-CONTROL은 수동 승격과 명시적 통제를 더 중시합니다. 따라서 자동 최적화 자체가 우월하다고 주장하지 않습니다. 장점은 재현성과 감사 가능성이고, 단점은 정책과 binding 운영 비용입니다.

NeuralLink는 메모리 문제를 완전히 해소하지 않습니다. embedding 서버 의존 없이 가볍게 공유 기억을 주입하지만, 추상 의미 유사성·fail-open 관측성·문맥 길이 cap이라는 한계가 남습니다. 이 한계를 숨기지 않고 Timeline 원장과 heartbeat 상태를 분리해 검증하는 것이 설계의 일부입니다.

시간 정책은 원본 삭제와 recall 노출을 분리합니다. Timeline 원본은 보존하고 live quote와 runtime state만 TTL로 일반 recall에서 제외합니다. report와 완료 작업은 `episodic`, 정책·계약·판단·노하우는 `durable`입니다. 명시적 과거 회상에서 만료 증거를 다시 노출할 때는 `STALE/EXPIRED` 표시와 현재 데이터 재검증을 강제합니다.
