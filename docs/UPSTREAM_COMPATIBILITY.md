# Upstream compatibility contract

## Principle

Compatibility is explicit, versioned, and fail-closed. `latest` is never treated as compatible merely because a patch happens to apply.

Each supported upstream line owns these immutable artifacts:

1. a full 40-character upstream baseline commit;
2. a deterministic gzip binary patch;
3. SHA-256 of the compressed patch;
4. a complete post-patch file checksum list;
5. required architectural anchor paths;
6. supported Python and operating-system bounds.

## Upgrade procedure for an AI maintainer

1. Fetch the new official upstream commit without changing a live checkout.
2. Create a temporary worktree from that commit.
3. Port HERMES-CONTROL changes by subsystem: contract, Project/Card Controller and typed-link storage, card/receipt storage, root enforcement, adapters, gateway delivery, heartbeat/artifacts, Timeline, NeuralLink, dashboard.
4. Generate a new patch bundle. Do not modify or delete an old bundle.
5. Materialize the patch into a second clean checkout with `hermes-control install --no-deps --source <audited-repo>`.
6. Run `hermes-control doctor` and compare every listed file checksum.
7. Install dependencies in a clean venv and run import probes.
8. Run focused HERMES-CONTROL tests, Timeline tests, upstream full regression, privacy scan, Linux matrix, and macOS matrix.
9. Run public setup against a temporary Hermes home. Confirm 7 role shells, bindings, six root control tools including `supervisor_project`, Project/Card web API, Timeline MCP, NeuralLink plugin, OpenCode adapter/controller, and three heartbeat layers.
10. Record the new compatibility manifest only after all gates are green.

## Why a core patch still exists

Timeline and NeuralLink are independently packageable, and adapters can be registered externally. The current upstream plugin API cannot atomically enforce all HERMES-CONTROL guarantees: Project/Card lifecycle and typed relation semantics shared across chat and dashboard, card receipt validation at storage time, root tool-schema hiding, conversation-loop failback, and gateway delivery from validated receipts. Those guarantees remain a small version-gated core patch until upstream exposes equivalent enforcement hooks.

## Failure behavior

- wrong commit: stop before patching;
- wrong patch hash: stop before decompression;
- `git apply --check` conflict: stop before modification;
- post-patch checksum mismatch: do not activate;
- dependency/import failure: do not update `current.json`;
- failed upgrade after a valid release: keep the previous release active;
- bad newly activated release: `hermes-control rollback` reactivates the preceding verified release.
