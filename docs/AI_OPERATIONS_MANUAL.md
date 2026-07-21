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

Do not report a release complete unless bundle hashes, fresh materialization, doctor, setup dry-run, focused tests, Timeline tests, full upstream regression, privacy scan, macOS/Linux validation and rollback all pass. If any one is missing, name the missing gate.
