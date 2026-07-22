# HERMES-CONTROL

[English](README_EN.md) | [한국어](README.md)

[![Compatibility](https://github.com/JUNJOONHWAN/HERMES-CONTROL/actions/workflows/compatibility.yml/badge.svg)](https://github.com/JUNJOONHWAN/HERMES-CONTROL/actions/workflows/compatibility.yml)
[![Python 3.11–3.13](https://img.shields.io/badge/python-3.11--3.13-3776AB.svg)](https://www.python.org/)
[![Hermes Agent 0.18.0](https://img.shields.io/badge/Hermes_Agent-0.18.0-6f42c1.svg)](https://github.com/NousResearch/hermes-agent)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**A version-gated governance and orchestration layer for Nous Hermes Agent.**

HERMES-CONTROL is an independent distribution that adds role shells, card contracts, replaceable AI adapters, Timeline Code Map, NeuralLink, and a structured heartbeat to the official Hermes Agent.

> [!IMPORTANT]
> HERMES-CONTROL is not an official Nous Research project. It does not redistribute a full fork of Hermes Agent. The installer fetches one verified upstream commit and applies a cryptographically pinned compatibility patch.

## What is actually included

HERMES-CONTROL is not just a small installer. The installer reproduces the following **complete operating architecture** on top of a pinned Hermes baseline.

| Area | Included capability |
|---|---|
| Kanban web UI | Drag-and-drop cards, eight status columns, task drawer, comments, dependencies, run history, attachments, diagnostics, and live WebSocket updates |
| Multiple boards | Isolated SQLite DB, workspace, logs, and attachments per project; dashboard board switcher; board-pinned workers |
| Card execution kernel | Durable tasks, atomic claims, dependency promotion, idempotent creation, crash/stale reclaim, circuit breaker, and structured completion |
| Root Controller | Controls status, automation, roles, delegation, and adapters through five supervisor tools with no domain MCP attached |
| Seven Role Shells | `code`, `market`, `browser-research`, `operations`, `report`, `verification`, and `tool-management` |
| Adapter Control Plane | Separate controller and worker axes, many-to-many Bindings, capacity/health/capability gates, and task/shell/all overrides |
| Multitool and MCP management | Per-profile MCP, skill, plugin, toolset, and callable-tool inventory/search; minimal assignment, backup, probes, and rollback |
| Evidence and completion | Atomic shell/executor/binding provenance at claim time and a Receipt Gate backed by Timeline evidence |
| Memory and code impact | Profile memory, Timeline Code Map, NeuralLink recall, typed Roadmap, and cross-host delta sync |
| Operational state | Three-layer heartbeat for `configuration`, `service_schedule`, and `artifacts`, including artifact freshness |

The distribution retains the standard Hermes profile, gateway, Kanban, and dashboard capabilities, then adds Role Shells, Bindings, Overrides, Receipts, a zero-domain-MCP root, and evidence gates.

## Kanban board and web UI

Kanban is not an optional visualization. It is the authoritative task state machine shared by people, AI workers, CLI automation, cron, and the dashboard.

```bash
# The gateway hosts the embedded dispatcher on a 15-second interval
hermes-control run -- gateway start

# Run the dashboard in another terminal
hermes-control run -- dashboard
```

Open `http://127.0.0.1:9119/kanban`. The dashboard binds to localhost by default. Use SSH port forwarding for a remote host.

```bash
ssh -L 9119:127.0.0.1:9119 user@remote-host
```

The web board provides:

- status columns: `triage → todo → scheduled → ready → running → blocked → review → done`;
- drag-and-drop cards with validated state transitions;
- task creation, editing, and archival with assignee/profile, role shell, priority, and tenant data;
- parent/child dependencies and automatic `todo → ready` promotion after parents complete;
- a durable comment thread shared by humans and agents;
- run history with the actual `role_shell_id`, `executor_id`, `binding_id`, `adapter_override_id`, and `receipt_id`;
- PDF, image, and source-document attachments delivered to workers as absolute paths;
- diagnostics for stale runs, hallucinated task references, and receipt problems;
- authenticated WebSocket updates from the append-only task event stream;
- board creation, switching, and archival with isolated DB, workspace, logs, and attachments per board.

Cards are stored in `~/.hermes/kanban.db` or, for a named board, `~/.hermes/kanban/boards/<slug>/kanban.db`. Each task chooses a workspace policy.

| Workspace | Use | After completion |
|---|---|---|
| `scratch` | Temporary research and transformation | Deleted |
| `dir:/absolute/path` | Existing shared directory | Preserved |
| `worktree` / `worktree:<path>` | Isolated code work | Preserved |

Workers do not shell out to `hermes kanban`. The dispatcher pins `HERMES_KANBAN_TASK` and the board in the worker process. The model uses `kanban_show`, `kanban_list`, `kanban_create`, `kanban_link`, `kanban_comment`, `kanban_heartbeat`, `kanban_complete`, `kanban_block`, and `kanban_unblock` against the same DB.

```bash
# Human and automation CLI surface
hermes-control run -- kanban init
hermes-control run -- kanban create "Review authentication flow" --assignee hermes-worker-general
hermes-control run -- kanban watch
hermes-control run -- kanban stats

# Project-specific board
hermes-control run -- kanban boards create api-service --name "API Service" --switch
hermes-control run -- kanban --board api-service list
```

### Card execution, provenance, and the Receipt Gate

The dispatcher does more than change `ready` to `running`. Inside one `BEGIN IMMEDIATE` transaction it rechecks dependencies and overrides, reserves capacity on an eligible Binding, compare-and-swaps the task state, and stamps `shell/executor/binding/override` provenance into `task_runs`. This closes the TOCTOU window in which two dispatchers could select the same capacity-one executor.

A worker cannot close a card with one line of natural language. A canonical Receipt includes at least:

```text
trusted task/run/shell/executor/binding/override ids
terminal status: completed | blocked | failed
Timeline goal, context-loaded flag, slice ids, action/output node ids
verify_all result
artifact paths and test commands/results
known limitations
```

The terminal transition is rejected if submitted provenance differs from the live DB run, a code shell has no stored slice, or required Timeline/output evidence is missing. In the same transaction that accepts a Receipt, the kernel stores it, closes the card and run, and consumes a task-scoped `once` override. Crashed, stale-PID, and timed-out runs are reclaimed; repeated spawn or block loops are escalated by a circuit breaker instead of thrashing indefinitely.

## Core idea

A standard Hermes profile groups prompts, tools, and skills. HERMES-CONTROL adds an explicit **execution-governance contract** above that layer.

- **Root Hermes is the control plane.** It turns objectives into cards, selects a role shell and adapter, validates receipts, and delivers validated results.
- **A role shell is a durable policy boundary.** It declares allowed task classes, tool/MCP scope, concurrency, completion criteria, and escalation behavior.
- **An adapter is a replaceable execution edge.** OpenCode is the default worker path, while Codex CLI, Grok, and generic command adapters can use the same contract.
- **Cards and receipts define completion.** A worker saying “done” is insufficient; structured evidence and artifacts must be validated in the same storage transaction as the status change.
- **Timeline Code Map is the shared evidence graph.** It stores context, code slices, actions, decisions, outputs, and their relations as append-only evidence.
- **NeuralLink recalls bounded historical context.** It injects Timeline candidates before an LLM call without claiming perfect semantic retrieval.
- **Heartbeat reports exactly three public layers:** `configuration`, `service_schedule`, and `artifacts`.

The differentiator is not an unverified benchmark claim. It is the ability to reproduce **who ran what, under which authority, and which evidence justified completion**. The design prioritizes manual control and auditability over fully automatic provider routing.

## Architecture at a glance

```text
Chat / CLI / Cron / Kanban Web UI
                 │
                 ▼
   Root Controller (5 control tools, zero domain MCP)
                 │ create/delegate/inspect/switch
                 ▼
      Kanban DB + Event Stream ◄────► Dashboard API / WebSocket
                 │ atomic claim
                 ▼
 Immutable Role Shell ──► Binding / Override ──► Eligible Executor
        │                         │                       │
        │ policy                  │ provenance            ├─ Hermes profile
        │                         │                       ├─ OpenCode
        │                         │                       ├─ Codex CLI
        │                         │                       └─ generic command
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

HERMES-CONTROL keeps three boundaries separate.

| Boundary | Default location | Contents |
|---|---|---|
| Distribution repository | This Git repository | Installer, compatibility manifest, patch, tests, and documentation |
| Managed runtime | `~/.hermes-control/releases/<release>` | Verified Hermes source and an isolated Python environment |
| Operator state | `~/.hermes` or `HERMES_HOME` | Configuration, cards, receipts, adapters, Timeline DB, plugins, and logs |

Source upgrades never copy operator state. Private know-how databases, API keys, personal schedules, and an existing Hermes state are not included in this repository.

## Compatibility

| Item | Current contract |
|---|---|
| HERMES-CONTROL | `0.1.2` (Alpha) |
| Nous Hermes Agent | `0.18.0` |
| Pinned upstream commit | `5445e42b87b9918d5b1bfa9f4eadd8e4bb10ff37` |
| Python | `>=3.11,<3.14` |
| OS | Linux and macOS |
| Default path | OpenCode free-model controller/worker after health gates pass |
| Optional controllers | Grok, OpenRouter Gemma, local OpenAI-compatible/vLLM |
| Optional workers | Codex CLI, generic command adapter, additional OpenCode adapters |

The installer refuses to patch an unsupported upstream version. Activation requires the exact baseline commit, patch SHA-256, a successful `git apply --check`, post-patch SHA-256 verification for 151 files, required paths, and runtime import probes.

`0.1.2` preserves the historical `0.1.0` and `0.1.1` bundles and adds live progress visibility plus preservation of the direct final answer.

## Installation

Requirements: Git, Python 3.11–3.13, and Linux or macOS. OpenRouter is not a default requirement.

```bash
git clone https://github.com/JUNJOONHWAN/HERMES-CONTROL.git
cd HERMES-CONTROL

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

Materialize a verified runtime, complete the base Hermes configuration, and then bootstrap the HERMES-CONTROL layer.

```bash
hermes-control install
hermes-control doctor

# First run: configure the upstream Hermes provider and base settings
hermes-control run -- setup

# Inspect the shell, adapter, and Timeline plan before applying it
hermes-control setup --dry-run
hermes-control setup

# Run the managed Hermes CLI
hermes-control run -- --help

# Run card dispatch and the web board
hermes-control run -- gateway start
hermes-control run -- dashboard
```

The installer shallow-fetches only the exact upstream commit in the compatibility contract. It does not clone full Git history and never modifies an existing Hermes checkout.

### Fully separated paths

```bash
hermes-control --root /opt/hermes-control install
HERMES_HOME=/srv/hermes-state \
  hermes-control --root /opt/hermes-control run -- setup
hermes-control --root /opt/hermes-control \
  setup --hermes-home /srv/hermes-state
```

Use an audited local mirror or offline upstream checkout by specifying the source explicitly.

```bash
hermes-control install --source /path/to/hermes-agent
```

## CLI

| Command | Purpose |
|---|---|
| `hermes-control info` | Print the bundled upstream, patch, platform, and Python contract |
| `hermes-control install [--dry-run]` | Verify the pinned baseline and build a managed runtime |
| `hermes-control doctor` | Check the host, source, patched files, virtual environment, and imports |
| `hermes-control run -- <args>` | Run the Hermes CLI from the active managed runtime |
| `hermes-control setup [--dry-run]` | Bootstrap role shells, adapters, Timeline, NeuralLink, and OpenCode |
| `hermes-control rollback` | Atomically reactivate the preceding verified release |

Commands return JSON so that human operators, AI maintainers, and automation read the same state contract.

## Root Controller and seven Role Shells

Root Hermes is not a general-purpose worker. Its MCP catalog is empty, and it operates through five control tools.

```text
supervisor_status      service, worker, schedule, and artifact state
supervisor_automation  cron/job failures and recovery flows
supervisor_roles       active shells and route availability
supervisor_delegate    card creation and delegation under a shell contract
supervisor_adapter     controller/executor/binding/override/tool-catalog control
```

Domain work must pass through one of seven immutable, versioned Role Shells.

| Role Shell | Responsibility | Required capability summary | Key boundary |
|---|---|---|---|
| `code` | Source changes and tests | file, terminal, kanban, Timeline | Stored code slice required; deployment is separate |
| `market` | Public market and finance research | web, kanban, Timeline | No trading/account writes; no private DB bundled |
| `browser-research` | Authenticated and dynamic-page research | browser, kanban, Timeline | No access-control bypass or unrelated writes |
| `operations` | Services, cron, and watchdogs | file, terminal, kanban, Timeline | Exact unit/PID and desired-state verification |
| `report` | Report assembly from upstream receipts | file, kanban, Timeline | Intermediate artifacts cannot become completion |
| `verification` | Independent regression and final gates | file, terminal, kanban, Timeline | Separates baseline failures from new regressions |
| `tool-management` | MCP, skill, plugin, and toolset lifecycle | file, terminal, skills, kanban, Timeline | Minimal assignment with backup, probes, and rollback |

SQLite triggers reject updates and deletes of Role Shell rows. Policy changes require a new version and contract hash under the same `shell_key`, preserving the exact contract used by historical cards.

## Executors and the Adapter Control Plane

A Role Shell defines what may be done and what must be proven. An Executor defines what actually runs. The default profile pool is:

| Executor profile | Default responsibility | Capacity | Public default MCP |
|---|---|---:|---|
| `hermes-worker-general` | code, operations, report, verification | 3 | Timeline |
| `hermes-worker-market` | market | 2 | Timeline; market MCPs are added per role |
| `hermes-worker-browser` | browser research | 2 | Timeline; browser MCPs are added per role |
| `hermes-worker-universal` | low-priority provider-neutral fallback | 4 | Timeline |
| `hermes-worker-multitool` | MCP/skill/plugin/toolset management | 1 | Timeline |

Controller adapters and worker executors are separate axes.

| Integration | Supported position | Activation gate |
|---|---|---|
| OpenCode | Default controller/worker path | Free-model catalog and tool-call health gate |
| Codex CLI | Optional command worker | Existing Codex authentication plus binary/version probe |
| Grok | Optional controller candidate | `XAI_API_KEY` plus catalog/tool-call probe |
| OpenRouter Gemma | Disabled controller candidate | Operator configuration and health gate; not a default |
| Local OpenAI-compatible/vLLM | Disabled controller candidate | Endpoint and model probe |
| Generic command | Arbitrary CLI worker | `shell=false`, argv/prompt placeholder, capability/MCP probes |

A Binding is a many-to-many Shell-to-Executor relation carrying priority, weight, capacity, and a capability cap. Effective authority cannot exceed this intersection:

```text
effective capabilities
  = Role Shell allowed
  ∩ Executor capabilities
  ∩ Binding capability cap
```

Only candidates that pass health, heartbeat TTL, capacity, and required MCP/tool probes may claim work. Override precedence is `task > shell > all > default`, with `once`, `temporary`, and `permanent` lifetimes. If a forced target becomes ineligible, selection fails closed instead of silently using another healthy candidate.

To add a command adapter:

1. Declare a unique id, argv, `{prompt_file}`, capabilities, and health/tool probes in a JSON descriptor.
2. Register it as a candidate with `scripts/register_external_adapter.py`.
3. Pass live health and required MCP/tool probes.
4. Create Bindings to one or more Role Shells with capacity and capability caps.
5. Validate end to end with a card that requires a real artifact and Receipt.
6. Promote through `once → temporary → permanent`, retaining audit events at every step.

Pagent and qagent are not architectural dependencies. They can be attached as optional command adapters if desired.

## Multitool, MCP, skill, and plugin management

HERMES-CONTROL does not attach every MCP to root. Root remains zero-domain-MCP. A `tool-management` card runs on the capacity-one `hermes-worker-multitool` executor and owns the tool lifecycle.

The tool catalog reports the complete inventory **by name and assignment** without exposing credentials or raw MCP definitions:

- per-profile `mcp_servers`;
- installed skills and plugins;
- Hermes toolsets and expanded built-in callable tools;
- capabilities declared by each executor;
- reverse ownership indexes for MCPs, skills, toolsets, and callable tools;
- profile configuration parse errors and catalog health.

The conversational control action `supervisor_adapter(action="tools", query="...")` searches the full catalog for a missing capability. Installation or reassignment is performed through a separate `tool-management` card with this lifecycle:

```text
inventory/search
→ provenance and compatibility check
→ exact target-profile configuration backup
→ assign only the minimum MCP/skill/plugin/toolset set
→ health and declared-tool probes
→ record before/after assignments and Receipt
→ rollback or hand off to code/operations repair on failure
```

Running model contexts are never hot-mutated. Changes become effective in a new worker session. Browser-login discovery moves to `browser-research`; source modification moves to `code`; service restarts and secret expansion move to `operations` or a repair card. This provides a central tool view while preserving profile isolation and limiting blast radius.

Operational inspection examples:

```bash
hermes-control run -- supervisor shell list --active --json
hermes-control run -- supervisor executor list --json
hermes-control run -- supervisor binding list --json
hermes-control run -- supervisor adapter list --json
hermes-control run -- supervisor heartbeat --json
```

See “Adding an adapter” and “Adding a shell” in the [AI operations manual](docs/AI_OPERATIONS_MANUAL.md).

## Memory, Timeline Code Map, NeuralLink, and Roadmap

“Memory” is composed of four distinct layers.

| Layer | Purpose | Sharing boundary |
|---|---|---|
| Profile `MEMORY.md` / `USER.md` | Curated snapshot injected into a later session | Profile-isolated |
| Optional MemoryProvider | Per-turn external prefetch and synchronization | Provider-specific |
| Timeline | Durable evidence graph for context, decisions, actions, outputs, and relations | Shared by shells and workers |
| NeuralLink | Lexical/metadata candidate recall over Timeline | Current root `pre_llm_call` path |

Profile memory becomes a frozen snapshot when a session starts. This prevents in-turn self-modification, but a memory written now enters the prompt in a later session. Workers do not automatically share root's `MEMORY.md`; common state is carried by card provenance and Timeline evidence.

Timeline contains a node/edge hash chain and a repository code index. The default code-task gate is:

```text
load context
→ query and store a code slice
→ read target source, tests, and configuration directly
→ record and link action and output nodes
→ rerun the same query to check impact drift
→ verify_all
→ include goal, slices, nodes, tests, and outputs in the Receipt
```

A code slice returns relevant and affected files, symbols, relationship flow, watchpoints, patch checkpoints, freshness, and a durable `slice_id`. `verify_all` proves structural hash-chain integrity; it does not prove that node content is true or that tests passed.

NeuralLink is a `pre_llm_call` recall adapter, not a replacement vector database. It indexes workflow, entity, concept, title, token, and metadata features, then applies TTL, recency, association edges, and multi-hop activation. It needs no embedding server or GPU, but its limitations are explicit:

- Abstract semantic similarity depends on indexed concepts and aliases.
- Missing metadata synonyms can cause recall misses.
- A character cap can omit evidence from large cross-goal contexts.
- The plugin is fail-open, so recall failure does not stop the agent itself.
- Final relevance depends partly on the called model's candidate reranking.

The project therefore does not claim to have “solved memory.” It removes embedding-service operations at the cost of semantic-miss risk, while preserving source evidence in Timeline.

Temporal policy no longer treats every node containing a market-related word as a one-day memory. Only live quotes, bars, order books, and snapshots default to one-day `market_live`; service status, health, probes, and heartbeats default to seven-day `runtime_state`. Reports, analyses, actions, and reviews are `episodic`; policies, contracts, decisions, architecture, playbooks, runbooks, and know-how are `durable`. `memory_descriptor.temporal_scope` or `freshness_class` overrides heuristic classification.

Explicit historical cues can include expired nodes, but every such candidate is labelled `STALE/EXPIRED` and must be revalidated before it is used as a current quote or current service state. After an upgrade, the versioned NeuralLink backfill reclassifies existing features without deleting Timeline evidence.

Typed Roadmap separates planning events from their current projection. It stores entity versions, idempotent event ids, dependencies, and schedule intent, then rebuilds projections by replay. Time-based work can preserve both user intent and scheduler representation, such as `KST intent / UTC-stored RRULE`.

## Heartbeat

The public heartbeat has exactly three layers:

1. `configuration`: shells, bindings, adapters, controllers, and policy consistency
2. `service_schedule`: desired state, scheduler, and last/next-run evidence
3. `artifacts`: expected outputs, freshness, paths, and health

A missing layer is reported as `absent`; it is never silently treated as healthy.

## Safety and upgrades

- Installation completes in a new release directory and changes the active pointer only at the final step.
- A failure before activation leaves the current release untouched.
- `doctor` revalidates file checksums and runtime imports.
- An upstream upgrade requires a regenerated patch, full checksums, fresh materialization, and regression tests—not just a version-number edit.
- Operator secrets and state must never be committed to the distribution repository.
- `hermes-control rollback` reactivates the preceding verified release.

See the [upstream compatibility contract](docs/UPSTREAM_COMPATIBILITY.md) for the version-upgrade procedure and fail-closed behavior.

## Validation

The 0.1.0 public release passed these gates before publication:

- HERMES-CONTROL unit suite: 19 passed
- Linux offline materialize/doctor/reinstall/rollback integration: 1 passed
- macOS ARM with Python 3.12 unit suite: 19 passed
- Focused HERMES-CONTROL runtime suite: 151 passed
- Timeline extension suite: 40 passed
- Full materialized upstream regression: 38,314 passed, 0 failed
- Ruff, wheel-content, privacy, and clean-worktree gates: passed

GitHub Actions continuously tests compatibility paths across Linux/macOS and Python 3.11/3.12/3.13.

Basic development checks:

```bash
python -m pip install -e '.[test]'
python -m pip install ruff
ruff check src tests scripts
pytest -q
```

## Documentation

- [AI operations manual](docs/AI_OPERATIONS_MANUAL.md): installation state machine, cards and receipts, shell and adapter extension, and release gate
- [Architecture overview](docs/ARCHITECTURE_KO.md): component and execution-flow summary
- [Upstream compatibility contract](docs/UPSTREAM_COMPATIBILITY.md): baseline updates and fail-closed policy
- [Current patch include paths](src/hermes_control/compatibility/hermes-agent-0.18.0-control-0.1.2/include-paths.txt): extraction scope of the overlay bundle

## Out of scope

The public distribution does not contain a private know-how database, API credentials, user-specific MCP configuration, private schedules, or existing card and Timeline data. Market memory provides only an empty schema and tooling frame; operators can add their own observations manually to private state.

## License

HERMES-CONTROL is released under the [MIT License](LICENSE). The original Nous Hermes Agent and modifications applied to it retain the upstream MIT notice. See [NOTICE.md](NOTICE.md) for details.
