# AI operator contract

This repository is the slim HERMES-CONTROL distribution, not a full Hermes checkout.

Before changing compatibility data, read `docs/AI_OPERATIONS_MANUAL.md` and `docs/UPSTREAM_COMPATIBILITY.md` completely.

Hard rules:

1. Never patch an arbitrary existing Hermes checkout. Materialize a managed release under an explicit HERMES-CONTROL root.
2. Never relax the exact upstream commit, patch SHA-256, or post-patch file checksum gates to make an upgrade pass.
3. Add a new compatibility manifest and patch for a new upstream line; do not overwrite historical bundles.
4. Verify Linux and macOS, Python 3.11 through 3.13, materialization, doctor, setup dry-run, focused HERMES-CONTROL tests, and rollback before release.
5. Never include a maintainer's private Hermes home, adapter credentials, market know-how database, Timeline database, cards, logs, or receipts.
6. The canonical Git repository is the source of truth. Treat platform-specific checkouts as disposable validation copies.
