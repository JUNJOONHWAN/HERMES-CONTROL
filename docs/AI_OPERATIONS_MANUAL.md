# HERMES-CONTROL AI operations manual

## 1. System boundary

HERMES-CONTROL has three separate locations:

- distribution repository: installer, compatibility manifests, patches, documentation;
- managed runtime: a patched official Hermes source and isolated Python environment under `~/.hermes-control/releases/<release>`;
- operator state: configuration, cards, receipts, adapters, Timeline DB, plugins and logs under `HERMES_HOME` (default `~/.hermes`).

Never confuse these layers. Source upgrades must not copy operator state. State backups must not become public source artifacts.

## 2. Installation state machine

`host-check -> clone-baseline -> verify-commit -> verify-patch-hash -> git-apply-check -> apply -> verify-file-checksums -> create-venv -> install-runtime -> import-probe -> write-receipt -> activate`

Only the last step changes the active release pointer. An error before activation leaves the prior release untouched.

## 3. Runtime architecture

The root Hermes process is a governance plane. It accepts the user objective, creates or updates cards, selects a role shell and adapter binding, validates completion receipts, and returns validated outputs. It is not a universal worker with every MCP exposed.

A role shell is a durable policy contract. It defines allowed task classes, preferred executor adapter, MCP/tool catalog, capacity, receipt requirements and escalation behavior. A binding connects a shell to an adapter. An override changes that relation once, temporarily or permanently while preserving an audit record.

Adapters are replaceable execution edges. OpenCode is the default because its free model catalog can be used without making OpenRouter mandatory. Codex CLI, Grok, and generic command adapters remain supported when the operator registers credentials and health checks. Pagent and qagent are not architectural dependencies; they are examples of optional adapters that can be attached through the same interface.

## 4. Card and receipt contract

A card is the authoritative work unit. It contains objective, role, dependencies, status, acceptance criteria, assigned adapter and output expectations. Completion must include a structured receipt whose required fields and artifacts are validated in the same storage transaction as the status transition. A prose-only `done` is not completion.

The gateway sends results from validated receipt state. It does not treat an unverified worker message as final delivery evidence.

Project and card graph changes are controller operations, not adapter work. Use the same native service through `supervisor_project` (chat, Telegram, CLI root) or the Kanban Project/Card API (web UI). A subscribed card's `claimed` event must emit one Telegram working notification containing both `project_id` and `task_id`; cursor advancement is the deduplication boundary:

- `start_project`: create Project metadata and its first self-rooted card;
- `add_project_card`: create a new independent root-card thread in an existing active Project;
- `continue_card`: create a `follows` card in the same root thread;
- `request_direction_change`: pause the Project, stop/archive the source run, checkpoint Git when applicable, and create only a `pa_*` non-blocking successor proposal;
- `split_card`: create parallel `references` cards without waiting on the container card;
- `verify_card`: create a `reviews` card gated on source completion;
- `recover_card`: create a non-blocking `recovers` card and recovery-source provenance;
- `pause_project` / `reopen_project`: stop or resume card creation; pause refuses running cards and clears the active pointer;
- `propose_project_card`: create a durable `pa_*` request for code work without creating a Kanban card;
- `approve_project_card` / `reject_project_card`: resolve a pending proposal; only approval creates exactly one `t_*` card;
- `setup_project_repository`: register `none`, `existing`, `init_local`, or `github` repository mode;
- `commit_project_card` / `push_project_card`: checkpoint and publish a card branch while denying direct default-branch push;
- `close_project`: terminal project transition; it refuses open cards and pending approvals;
- `list_projects`: return every visible Project with status, path, card/thread counts, and status counts;
- `inspect_card`, `inspect_project`, and `locate_card`: reconstruct old work without rewriting completed cards.

Natural-language surfaces should map requests such as "show project list" or "프로젝트 목록 보여줘" to `list_projects`; they must not synthesize a list from conversation memory. Web project filters and Telegram therefore render the same controller payload.

Typed link semantics are part of the storage contract. `depends_on`, `follows`, and `reviews` are blocking. `recovers` and `references` are lineage only. Never emulate these operations by asking an adapter to issue raw SQL or by editing a completed card.

Workspace selection is also a controller invariant, not an adapter guess:

- no Project `primary_path`: controller-managed `scratch`;
- a non-Git Project path: durable `dir` for code, browser, research, operations, and verification cards;
- a Git-backed Project path plus the `code` shell: one linked `worktree` per card;
- an explicit `worktree` request: validate an absolute Git anchor before creating the card;
- an explicit recovery override: pass `workspace_kind` and `workspace_path` through either `supervisor_project` or the Web recovery endpoint.

If workspace resolution fails after an older card was created, leave that failed card blocked and issue `recover_card`. The recovery is immediately runnable because `recovers` is non-blocking. Successful receipt commit archives the blocked source attempt but preserves its runs, errors, comments, provenance, and lineage. Do not initialize Git, move the Project, or mutate the failed card merely to make dispatch succeed unless the operator separately authorizes that repository change.

Project and execution state are separate ledgers. `projects.db` owns `p_*`
identity, phase, milestone, next action, `pa_*` approvals, repository state and
Git events. `kanban.db` owns executable `t_*` cards, links, runs, receipts and
notification cursors. Never repair one by editing the other directly.

Code proposals are a hard two-turn boundary. The proposing turn may create
only `pa_*` and must leave the Project `paused`. Approval must be a later,
explicit operator action; neither the controller nor a worker may approve the
proposal in the same turn. Repeated identical proposals return the existing
pending approval. Rejection creates no card, and card-creation failure restores
the pending approval and paused state.

Material mid-card direction changes are a hard stop/checkpoint/approval
boundary, not live prompt injection. Validate the successor contract first,
then pause the Project, archive the source card so its process group cannot be
redispatched, and record the current Git worktree as a direction-change
checkpoint. A non-Git workspace is preserved with `not_applicable` checkpoint
status. Store only a `pa_*` proposal and show Project ID, source Card ID,
checkpoint status/SHA, and approval ID. A later `approve_project_card` creates
one successor with non-blocking `references` lineage; rejection creates none
and leaves the archived source evidence intact. Never request and approve the
successor in the same turn. Small corrections that keep the deliverable and
acceptance criteria unchanged may use the normal same-card comment/retry path.

A repository write is also controller-owned. Card work uses its isolated
worktree branch. Checkpoint commit and optional push are recorded in
`project_git_events`; direct push of `main`, `master`, or the configured
default branch is rejected. Repository creation and visibility are explicit
operator choices and credentials stay in operator state.

## 5. Timeline Code Map and NeuralLink

Timeline Code Map stores append-only context, code slices, actions, outputs and relations. A meaningful code task follows `load context -> query slice -> act -> record/link -> query again -> verify`.

NeuralLink is a bounded recall adapter installed as a Hermes `pre_llm_call` plugin. It injects relevant historical candidates from Timeline. It does not replace the graph and it does not prove semantic equivalence. Recall remains limited by indexed concepts, lexical/metadata matches, configured character caps, and the final model's ranking. Failure is fail-open so agent execution can continue; doctor and heartbeat must therefore report plugin/index health separately.

Temporal retention is evidence-type based. Live quotes, bars, order books and snapshots default to one-day `market_live`; runtime health, probes and heartbeats default to seven-day `runtime_state`; reports and completed work are `episodic`; policy, contracts, decisions, architecture and know-how are `durable`. An explicit `memory_descriptor.temporal_scope` or `freshness_class` overrides heuristics. Historical cues may include expired evidence only with a `STALE/EXPIRED` label and a current-data revalidation requirement. Run the versioned NeuralLink backfill once after an upgrade so existing feature rows are reclassified without deleting Timeline nodes.

## 6. Heartbeat

Heartbeat has exactly three public layers:

1. `configuration`: shells, bindings, adapters, controllers and policy consistency;
2. `service_schedule`: managed services, desired state, scheduler and next/last run evidence;
3. `artifacts`: expected outputs, freshness, path and health.

An absent layer is reported as absent, not silently treated as healthy.

## 7. Common commands

```bash
hermes-control info
hermes-control install --dry-run
hermes-control install
hermes-control doctor
hermes-control run -- setup
hermes-control setup --dry-run
hermes-control setup
hermes-control run -- --help
hermes-control rollback
```

For a test or multi-tenant install, always set both boundaries:

```bash
hermes-control --root /tmp/control-runtime install
hermes-control --root /tmp/control-runtime setup --hermes-home /tmp/control-state
```

## 8. Adding an adapter

1. Create an adapter descriptor containing a unique id, command/provider type, capability tags and health command.
2. Register it with the supervisor registry or the supplied generic adapter script.
3. Run live health. Registration alone is not readiness.
4. Bind it to one role shell with capacity and receipt policy.
5. Test a card whose acceptance criteria require a real artifact.
6. Promote `once -> temporary -> permanent` only with receipt evidence.
7. Roll back the binding if health or receipt validation fails.

Secrets belong in operator state or environment variables, never in the descriptor committed here.

An adapter may execute a Project card or propose a follow-up. It must not directly commit Project status, `root_task_id`, or typed card relations; those writes return through the native controller.

## 9. Adding a shell

1. Define a stable shell id and narrow responsibility.
2. Declare tool/MCP catalog and prohibited capabilities.
3. Declare concurrency capacity and queue behavior.
4. Declare accepted receipt schema and artifact requirements.
5. Attach a healthy adapter binding.
6. Add contract tests for allowed, denied and unavailable-adapter cases.
7. Verify root cannot bypass the shell by directly exposing the worker's tool catalog.

## 10. Market memory

The public edition includes only the schema and tooling frame. A private know-how database is never bundled. An operator may add market observations manually to their own state with `scripts/market_memory.py`. Shell policy should require querying that state before market collection when the operator enables it.

## 11. Release gate

Do not report a release complete unless bundle hashes, fresh materialization, doctor, setup dry-run, focused tests, Timeline tests, full upstream regression, privacy scan, macOS/Linux validation and rollback all pass. Project approval tests must prove that proposing code creates no `t_*`, approval creates one, pause blocks writes, a direction change archives/checkpoints the source and creates no successor before separate approval, the approved successor uses non-blocking lineage, direct default-branch push is denied, a `claimed` event sends exactly one working notification with both IDs, and notification subscriptions do not replay old events. If any one is missing, name the missing gate.
