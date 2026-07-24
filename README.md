# HERMES-CONTROL

**English** | [한국어](README_KO.md)

[![Compatibility](https://github.com/JUNJOONHWAN/HERMES-CONTROL/actions/workflows/compatibility.yml/badge.svg)](https://github.com/JUNJOONHWAN/HERMES-CONTROL/actions/workflows/compatibility.yml)
[![Release v0.1.16 Alpha](https://img.shields.io/badge/release-v0.1.16_alpha-f59e0b.svg)](https://github.com/JUNJOONHWAN/HERMES-CONTROL/releases/tag/v0.1.16)
[![Python 3.11–3.13](https://img.shields.io/badge/python-3.11--3.13-3776AB.svg)](https://www.python.org/)
[![Hermes Agent 0.18.0](https://img.shields.io/badge/Hermes_Agent-0.18.0-6f42c1.svg)](https://github.com/NousResearch/hermes-agent)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**A version-gated governance and orchestration layer for Nous Hermes Agent.**

HERMES-CONTROL is an independent distribution that adds role shells, card contracts, replaceable AI adapters, a central Multitool capability catalog, card-scoped leases, Timeline Code Map, NeuralLink, and a structured heartbeat to the official Hermes Agent.

> [!IMPORTANT]
> HERMES-CONTROL is not an official Nous Research project. It does not redistribute a full fork of Hermes Agent. The installer fetches one verified upstream commit and applies a cryptographically pinned compatibility patch.

**Current public release:** [HERMES-CONTROL v0.1.16 (Alpha)](https://github.com/JUNJOONHWAN/HERMES-CONTROL/releases/tag/v0.1.16), built for Nous Hermes Agent `0.18.0`.

## What HERMES-CONTROL is

HERMES-CONTROL is not merely a model router or a collection of prompts. It is a governed orchestration control plane that turns an operator request into a durable project/card contract, assigns that contract to an immutable Role Shell, selects an eligible execution adapter, and accepts completion only with structured evidence.

The controller, policy, executor, and proof layers are separate. That separation lets an operator replace the AI that performs a task without silently changing the task's authority, tools, acceptance criteria, or audit trail.

## Why this orchestration is powerful

Its strength is architectural, not an unverified claim that one bundled model wins every benchmark.

- **Stable authority, replaceable compute.** Role Shells define what may be done; adapters define who runs it. Changing a model does not rewrite the operating contract.
- **Strong models where failure is expensive.** Seven ordinary roles can use low-cost or free executors. Hermes self-maintenance is isolated in `hermes-repair`, defaults to `gpt-5.6-sol/high`, and requires a separate evaluation plus operator approval before replacement.
- **Live free-model routing without pretending availability is static.** OpenRouter strict-free and OpenCode free refresh eligible models, reject paid or unhealthy candidates, and build a strongest-first fallback chain for ordinary roles.
- **Fail-closed overrides.** A forced task, shell, or global adapter does not silently fall back to another executor when the selected target is ineligible.
- **Durable work instead of disposable chat.** Projects, cards, relations, approvals, runs, checkpoints, and receipts survive individual model sessions.
- **Evidence-gated completion.** A worker saying “done” is insufficient. Provenance, artifacts, tests, Timeline nodes, and Code Map verification must agree before a terminal transition is accepted.
- **One operating truth across surfaces.** Telegram, CLI, automation, and the supplementary web UI operate on the same Project and Kanban state instead of creating separate task histories.

## Orchestration flow

```text
Operator
  ├─ Telegram / CLI (recommended)
  ├─ Cron / automation
  └─ Kanban Web UI (supplementary)
              │
              ▼
Root Controller — six control tools, zero domain MCP
              │ creates, delegates, inspects, switches
              ▼
Project/Card Controller + durable Kanban/Event ledger
              │ atomic claim and immutable provenance
              ▼
Versioned Role Shell
              │ policy ∩ capabilities ∩ health ∩ capacity
              ▼
Binding / explicit Override
              │
              ▼
Eligible Executor Adapter
  ├─ OpenCode free / OpenRouter strict-free
  ├─ Hermes profile / Codex CLI / generic command
  └─ hermes-repair → certification gate → gpt-5.6-sol/high default
              │
              ▼
Artifacts + tests → Timeline / Code Map → Receipt Gate → terminal state
```

The Root Controller coordinates work but does not perform domain work itself. The eight Role Shells are `code`, `market`, `browser-research`, `operations`, `report`, `verification`, `tool-management`, and `hermes-repair`. A many-to-many Binding connects each shell to eligible executors; an explicit Override can change the choice for one task, one shell, or all shells without mutating the shell contract.

## Recommended operating surfaces: Telegram and CLI

Version `0.1.16` is documented and released as **Telegram/CLI-first**. Telegram is the conversational operator surface; the CLI is the exact inspection, installation, and recovery surface.

Example Telegram requests:

```text
Show the current project, card, Role Shell, adapter, and health.
Stop card t_12345678 and preserve its checkpoint. Do not disable unrelated automation.
Create a linked continuation for card t_12345678 under the same project.
Run only this card with the OpenRouter free adapter.
Evaluate maintainer candidate X, but do not replace hermes-repair until the gate passes.
```

Equivalent inspection and lifecycle entry points:

```bash
hermes-control info
hermes-control doctor
hermes-control run -- supervisor heartbeat --json
hermes-control run -- supervisor shell list --active --json
hermes-control run -- supervisor adapter list --json
hermes-control run -- kanban watch
```

> [!CAUTION]
> The Kanban Web UI is included as a supplementary control surface. The `v0.1.16` release gate did **not** claim a comprehensive browser/device matrix covering every button, drag-and-drop path, WebSocket recovery path, and mobile layout. Use Telegram and CLI as the recommended operating surfaces until that acceptance matrix is completed.

Other explicit limits: free-model availability and quality can change at any time; NeuralLink recall can miss semantically related history; a valid Receipt proves recorded contract checks, not that an AI judgment is universally correct; and the public distribution does not include private credentials, operator state, or private know-how databases.

Timeline Code Map source remains in its standalone DGX repository. CONTROL carries only a checksum-pinned wheel built from the exact source commit recorded in the compatibility manifest. At runtime Multitool owns the MCP catalog and every worker receives the minimum card-scoped lease; no worker profile or Hermes source tree contains a copied Timeline source.

## What is actually included

HERMES-CONTROL is not just a small installer. The installer reproduces the following **complete operating architecture** on top of a pinned Hermes baseline.

| Area | Included capability |
|---|---|
| Kanban web UI | Drag-and-drop cards, eight status columns, task drawer, comments, dependencies, run history, attachments, diagnostics, and live WebSocket updates |
| Multiple boards | Isolated SQLite DB, workspace, logs, and attachments per project; dashboard board switcher; board-pinned workers |
| Card execution kernel | Durable tasks with default acceptance criteria/input lineage, atomic claims, dependency promotion, idempotent creation, same-card terminal-contract recovery, circuit breaker, and structured completion |
| Root Controller | Uses the same fixed six-tool Supervisor surface for every controller-capable model/provider; explanatory questions require no tool, while live reads and mutations remain fail-closed |
| Project/Card Controller | Separate Project DB, dual `p_*`/`t_*` identity, `pa_*` approval, stop/checkpoint direction changes, pause/reopen, typed relations, and shared web/Telegram actions |
| Project Git management | Existing/init-local/GitHub repository setup, private/public selection, card-branch checkpoint commit/push, and default-branch push denial |
| Eight Role Shells | `code`, `market`, `browser-research`, `operations`, `report`, `verification`, `tool-management`, and `hermes-repair` |
| Adapter Control Plane | Separate controller and worker axes, many-to-many Bindings, capacity/health/capability gates, and task/shell/all overrides |
| Multitool and MCP management | Card-scoped least-privilege rentals across the central MCP/skill/plugin/toolset catalog, simple/advanced/deep search classes, TTL return, health probes, backup, and rollback |
| Evidence and completion | Atomic shell/executor/binding provenance, explicit review lineage, PASS/REWORK/NEED_MORE_CAPABILITY verdicts, reasoning-tier reissue, and a Timeline-backed Receipt Gate |
| Memory and code impact | Profile memory, Timeline Code Map, NeuralLink recall, typed Roadmap, and cross-host delta sync |
| Operational state | Three-layer heartbeat for `configuration`, `service_schedule`, and `artifacts`, including artifact freshness |

The distribution retains the standard Hermes profile, gateway, Kanban, and dashboard capabilities, then adds Role Shells, Bindings, Overrides, Receipts, a zero-domain-MCP root, and evidence gates.

## Kanban state machine and supplementary web UI

The Kanban ledger is not an optional visualization: it is the authoritative task state machine shared by people, AI workers, CLI automation, cron, and the dashboard. The browser UI is one supplementary view and control surface over that state; Telegram and CLI remain the recommended operator paths for `v0.1.16`.

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
- project filtering, project start/close/reopen, and `New root card`, `Follow-up`, `Change direction`, `Split`, `Verify`, and `Recover` actions.

### Project/Card Controller

Project management is not delegated to a worker adapter. `supervisor_project` and the Kanban API call the same deterministic controller service, and only that service commits project state and the card relation graph. Adapters execute the resulting cards under their Role Shell contracts.

- A Project supports `active ↔ paused` and `active → completed → active`; pause is rejected while a card runs, and close is rejected while cards or approvals remain open.
- A code-card request does not immediately create `t_*`. It stores only a `pa_*` request and pauses the Project; a later operator action must approve it before exactly one card is created. Duplicate proposals are deduplicated.
- When scope, deliverable, Role Shell, or acceptance criteria materially changes mid-run, `Change direction` stops and archives the source, checkpoints its Git workspace, and stores only a `pa_*` successor draft. No successor `t_*` exists or dispatches before a separate approval; once approved, it retains non-blocking `references` lineage to the preserved source.
- The first card points `root_task_id` to itself. Follow-ups, splits, reviews, and recoveries inherit the same thread root.
- Relations are typed as `depends_on`, `follows`, `reviews`, `recovers`, or `references`. The first three gate execution; the last two preserve recovery/parallel lineage without blocking work.
- Every card stores explicit `acceptance_criteria` and `input_refs`.
- The controller classifies the workspace before a card becomes dispatchable: no Project path uses `scratch`, a normal folder uses a durable `dir` for every role, and a `code` card backed by a Git repository uses an isolated `worktree`. An explicit worktree without a Git anchor is rejected before dispatch.
- Recovery never rewrites the failed card. `Recover` creates a new card with `recovers` lineage; once that card passes the Receipt Gate, the blocked source attempt is archived with its audit history intact. Both Web and Telegram may explicitly override the recovery workspace.
- Completed cards are immutable. Months later, the operator can locate the card ID and issue a linked follow-up or create a new root card.
- The web UI and Telegram/Supervisor do not maintain separate state; both use the same Project DB and board DB.
- Project Git supports `none`, `existing`, `init_local`, and `github` modes. Only card worktree branches may be committed or pushed; direct pushes to `main`, `master`, or the default branch are rejected.
- Telegram and the dashboard always show Project `p_*` and Card `t_*` together. On an actual claim, Telegram emits one `🔄 작업중 · <title>` (working) notification with both IDs; completion, pause, and failure messages retain the same dual identity. New subscriptions start at the current event cursor so old failures are not replayed.

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
- **Free worker routing is automatic only for ordinary roles.** OpenRouter strict-free and OpenCode free refresh the live catalog before execution, skip removed, exhausted, or no-longer-free candidates, and incorporate newly eligible free models.
- **Hermes repair has a separate quality boundary.** The eighth `hermes-repair` Role Shell defaults to `gpt-5.6-sol/high`; another execution adapter can replace it only after a separate `hermes-repair-v1` performance and safety evaluation plus explicit operator approval.
- **Cards and receipts define completion.** A worker saying “done” is insufficient; structured evidence and artifacts must be validated in the same storage transaction as the status change.
- **Timeline Code Map is the shared evidence graph.** It stores context, code slices, actions, decisions, outputs, and their relations as append-only evidence.
- **NeuralLink recalls bounded historical context.** It injects Timeline candidates before an LLM call without claiming perfect semantic retrieval.
- **Heartbeat reports exactly three public layers:** `configuration`, `service_schedule`, and `artifacts`.

The differentiator is not an unverified benchmark claim. It is the ability to reproduce **who ran what, under which authority, and which evidence justified completion**. The design prioritizes manual control and auditability over fully automatic provider routing.

## Architecture at a glance

```text
Telegram / CLI / Cron / supplementary Kanban Web UI
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
| HERMES-CONTROL | `0.1.16` (Alpha) |
| Nous Hermes Agent | `0.18.0` |
| Pinned upstream commit | `5445e42b87b9918d5b1bfa9f4eadd8e4bb10ff37` |
| Python | `>=3.11,<3.14` |
| OS | Linux and macOS |
| Default path | OpenCode free-model controller/worker after health gates pass |
| Optional controllers | OpenRouter strict-free, Grok, OpenRouter Gemma, local OpenAI-compatible/vLLM |
| Optional workers | OpenRouter strict-free, OpenCode free, Codex CLI, generic command adapters |

The installer refuses to patch an unsupported upstream version. Activation requires the exact baseline commit, patch SHA-256, a successful `git apply --check`, SHA-256 verification of every file declared by the manifest, required paths, and runtime import probes.

`0.1.16` preserves every historical bundle and packages the audited DGX LIVE
release as a new immutable overlay. It keeps the `0.1.15` shell-rental contract
and adds a terminal-contract respawn guard: a clean worker exit without
`kanban_complete` or `kanban_block` keeps the same card blocked until an
explicit unblock instead of immediately reissuing the run. Installation still
fetches only the official Nous `0.18.0` baseline and never requires access to a
personal checkout or a retired repository.

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

# Run card dispatch; start the supplementary web board if needed
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

## Root Controller and eight Role Shells

Root Hermes is not a general-purpose worker. Its MCP catalog is empty, and it operates through six control tools.

```text
supervisor_status      service, worker, schedule, and artifact state
supervisor_automation  cron/job failures and recovery flows
supervisor_roles       active shells and route availability
supervisor_delegate    card creation and delegation under a shell contract
supervisor_project     project/card lifecycle, independent roots, follow-up, split, verify, and recover
supervisor_adapter     controller/executor/binding/override/tool-catalog control
```

Domain work must pass through one of eight immutable, versioned Role Shells.

| Role Shell | Responsibility | Required capability summary | Key boundary |
|---|---|---|---|
| `code` | Source changes and tests | file, terminal, kanban, Timeline | Stored code slice required; deployment is separate |
| `market` | Public market and finance research | web, kanban, Timeline | No trading/account writes; no private DB bundled |
| `browser-research` | Authenticated and dynamic-page research | browser, kanban, Timeline | No access-control bypass or unrelated writes |
| `operations` | Services, cron, and watchdogs | file, terminal, kanban, Timeline | Exact unit/PID and desired-state verification |
| `report` | Report assembly from upstream receipts | file, kanban, Timeline | Intermediate artifacts cannot become completion |
| `verification` | Independent regression and final gates | file, terminal, kanban, Timeline | Separates baseline failures from new regressions |
| `tool-management` | MCP, skill, plugin, and toolset lifecycle | file, terminal, skills, kanban, Timeline | Minimal assignment with backup, probes, and rollback |
| `hermes-repair` | Hermes control-plane, adapter, shell, router, and configuration maintenance | file, terminal, kanban, Timeline | No ordinary project coding; default `gpt-5.6-sol/high`, certified replacements only |

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
| `hermes-worker-opencode-free` | Dynamic free candidate for seven ordinary roles | 2 | Tools permitted by the Role Shell |
| `hermes-worker-openrouter-free` | Strict-free candidate for seven ordinary roles | 2 | Tools permitted by the Role Shell |
| `hermes-worker-hermes-maintainer` | Hermes self-maintenance only | 1 | file, terminal, kanban, Timeline |

Controller adapters and worker executors are separate axes.

| Integration | Supported position | Activation gate |
|---|---|---|
| OpenCode free | Default controller plus ordinary worker candidate | Per-task live free catalog and tool-call health gate |
| OpenRouter strict-free | Optional controller plus ordinary worker candidate | Zero-price, tool, and context filters with ordered `models` fallback |
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

A candidate for `hermes-repair` needs more than this normal adapter flow. Its
launch configuration must carry a `hermes-repair-v1` artifact, performance and
safety metrics for that exact executor, and explicit operator approval. Free
worker adapters are never bound to this shell automatically.

Natural-language examples:

```text
Run only card t_12345678 with the OpenRouter free execution adapter.
Switch the code role to the OpenCode free execution adapter for one hour.
Show the current live model order and health for the free execution adapters.
Evaluate maintainer candidate X with hermes-repair-v1, but do not assign it yet.
If its artifact and approval are valid, permanently assign candidate X to Hermes repair.
```

Pagent and qagent are not architectural dependencies. They can be attached as optional command adapters if desired.

## Multitool, MCP, skill, and plugin management

HERMES-CONTROL does not attach every MCP to root. Root remains zero-domain-MCP. A `tool-management` card runs on the capacity-one `hermes-worker-multitool` executor and owns the tool lifecycle.

Each Role Shell decides its default MCP rentals once at shell setup. An approved
default is attached atomically to the original card and shown as an automatic
default rental; it does not create a second card or add a model turn. A
capability outside that approved set is normalized to an exact MCP, skill, or
toolset request and receives a separate Multitool dependency card. Changing any
required, allowed, or default capability membership creates a versioned full
impact report covering open cards, active leases, other shells, catalog owners,
runtime projections, notifications, and Linux/macOS distribution surfaces.

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

The following numbers are the existing 0.1.5 validation record. Version 0.1.16
is validated separately through its new immutable bundle and DGX full
regression; GitHub Actions status is reported separately for the release.

- HERMES-CONTROL unit suite: 19 passed
- Official-upstream source-backed installer module: 2 passed
- Linux clean materialize/doctor: 164/164 patched files verified
- Focused HERMES-CONTROL runtime suite: 175 passed
- Timeline extension suite: 44 passed
- Full materialized upstream regression: 1,844 files, 38,275 passed, 0 failed
- macOS ARM Python 3.11/3.12/3.13 unit suites: 19 passed on each version
- Linux setup dry-run: 7 role shells, empty Root MCP, Timeline/NeuralLink plan verified (0.1.5 record)
- Ruff, sdist/wheel build, wheel-install smoke, privacy, README-link, and `git diff --check` gates: passed

### Historical 0.1.0 validation record

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
- [Current patch include paths](src/hermes_control/compatibility/hermes-agent-0.18.0-control-0.1.16/include-paths.txt): extraction scope of the overlay bundle

## Out of scope

The public distribution does not contain a private know-how database, API credentials, user-specific MCP configuration, private schedules, or existing card and Timeline data. Market memory provides only an empty schema and tooling frame; operators can add their own observations manually to private state.

## License

HERMES-CONTROL is released under the [MIT License](LICENSE). The original Nous Hermes Agent and modifications applied to it retain the upstream MIT notice. See [NOTICE.md](NOTICE.md) for details.
