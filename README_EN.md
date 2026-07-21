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
| HERMES-CONTROL | `0.1.0` (Alpha) |
| Nous Hermes Agent | `0.18.0` |
| Pinned upstream commit | `5445e42b87b9918d5b1bfa9f4eadd8e4bb10ff37` |
| Python | `>=3.11,<3.14` |
| OS | Linux and macOS |
| Default worker adapter | OpenCode (optional installation) |
| Optional adapters | Codex CLI, Grok, generic command adapter |

The installer refuses to patch an unsupported upstream version. Activation requires the exact baseline commit, patch SHA-256, a successful `git apply --check`, post-patch SHA-256 verification for 151 files, required paths, and runtime import probes.

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

## Extending role shells and adapters

OpenCode is the default path because it can use free models, but it is not a core dependency. Codex CLI, Grok, or any command-line worker can be added while preserving the same contract.

1. Declare a unique adapter id, execution type, capability tags, and health command.
2. Run a live health check after registration; registration alone is not readiness.
3. Bind the adapter to one role shell with an explicit capacity and receipt policy.
4. Validate the path end to end with a card that requires a real artifact.
5. Promote an override through `once → temporary → permanent`, preserving evidence at each step.
6. Restore the previous binding if health or receipt validation fails.

A new role shell must define its responsibility, allowed and prohibited tools, concurrency, queue behavior, receipt schema, and artifact requirements. Pagent and qagent are not architectural dependencies. They are optional accessories that can be attached through the same adapter interface.

See “Adding an adapter” and “Adding a shell” in the [AI operations manual](docs/AI_OPERATIONS_MANUAL.md).

## Timeline Code Map and NeuralLink

Meaningful code work follows this evidence lifecycle:

```text
load context → query code slice → act → record/link → query again → verify
```

NeuralLink is a `pre_llm_call` recall adapter over Timeline, not a separate replacement memory database. The current implementation uses bounded lexical and metadata retrieval, so its limitations are explicit:

- Abstract semantic similarity depends on indexed concepts and alias quality.
- A character cap can omit evidence from large cross-goal contexts.
- The plugin is fail-open, so recall failure does not stop the agent itself.
- Final relevance also depends on the called model's candidate reranking.

The project therefore does not claim to have “solved memory.” It changes the failure mode: source evidence stays in Timeline, while recall and index health can be monitored separately.

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
- [Patch include paths](src/hermes_control/compatibility/hermes-agent-0.18.0/include-paths.txt): extraction scope of the overlay bundle

## Out of scope

The public distribution does not contain a private know-how database, API credentials, user-specific MCP configuration, private schedules, or existing card and Timeline data. Market memory provides only an empty schema and tooling frame; operators can add their own observations manually to private state.

## License

HERMES-CONTROL is released under the [MIT License](LICENSE). The original Nous Hermes Agent and modifications applied to it retain the upstream MIT notice. See [NOTICE.md](NOTICE.md) for details.
