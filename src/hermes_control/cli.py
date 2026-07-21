"""Command-line interface for the HERMES-CONTROL slim distribution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .installer import (
    InstallError,
    doctor,
    install,
    rollback,
    run_hermes,
    setup_public,
)
from .manifest import bundled_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hermes-control",
        description="Install a version-gated HERMES-CONTROL overlay without modifying an existing Hermes checkout.",
    )
    parser.add_argument("--root", type=Path, help="managed install root (default: ~/.hermes-control)")
    sub = parser.add_subparsers(dest="command", required=True)

    install_parser = sub.add_parser("install", help="materialize a verified managed runtime")
    install_parser.add_argument("--source", help="explicit upstream git URL/path for offline or audited installs")
    install_parser.add_argument("--no-deps", action="store_true", help="materialize only; skip runtime virtualenv")
    install_parser.add_argument("--dry-run", action="store_true")

    sub.add_parser("doctor", help="verify host, baseline, overlay files, and runtime imports")
    sub.add_parser("info", help="print the bundled compatibility contract")

    setup_parser = sub.add_parser("setup", help="bootstrap shells, adapters, Timeline, NeuralLink, and OpenCode")
    setup_parser.add_argument("--hermes-home", type=Path, help="Hermes state home (default: ~/.hermes)")
    setup_parser.add_argument("--dry-run", action="store_true")
    setup_parser.add_argument("--skip-opencode-install", action="store_true")
    setup_parser.add_argument("--skip-timeline-install", action="store_true")
    setup_parser.add_argument("--skip-live-health", action="store_true")

    run_parser = sub.add_parser("run", help="run the managed Hermes CLI")
    run_parser.add_argument("args", nargs=argparse.REMAINDER)
    sub.add_parser("rollback", help="atomically reactivate the preceding verified release")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "install":
            result = install(
                root=args.root,
                source=args.source,
                install_dependencies=not args.no_deps,
                dry_run=args.dry_run,
            )
        elif args.command == "doctor":
            result = doctor(root=args.root)
        elif args.command == "info":
            result = bundled_manifest().to_public_dict()
        elif args.command == "setup":
            result = setup_public(
                root=args.root,
                hermes_home=args.hermes_home,
                dry_run=args.dry_run,
                skip_opencode_install=args.skip_opencode_install,
                skip_timeline_install=args.skip_timeline_install,
                skip_live_health=args.skip_live_health,
            )
        elif args.command == "run":
            forwarded = args.args[1:] if args.args[:1] == ["--"] else args.args
            return run_hermes(forwarded, root=args.root)
        elif args.command == "rollback":
            result = rollback(root=args.root)
        else:  # pragma: no cover
            raise InstallError(f"unknown command: {args.command}")
    except InstallError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.command == "doctor" and not result.get("ok"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
