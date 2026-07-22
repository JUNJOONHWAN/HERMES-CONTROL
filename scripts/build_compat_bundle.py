#!/usr/bin/env python3
"""Build a deterministic patch and checksum manifest from an audited source repo."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def capture(command: list[str], *, cwd: Path, text: bool = False):
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=text,
    ).stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--compat-id", default="hermes-agent-0.18.0-control-0.1.2")
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()

    source = args.source_repo.expanduser().resolve()
    project = args.project_root.expanduser().resolve()
    package = project / "src" / "hermes_control"
    compat = package / "compatibility" / args.compat_id
    manifest_path = compat / "manifest.json"
    include_path = compat / "include-paths.txt"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload["upstream"]["baseline_commit"] != args.baseline:
        raise SystemExit("baseline argument does not match manifest")
    paths = [
        line.strip()
        for line in include_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    capture(["git", "cat-file", "-e", f"{args.baseline}^{{commit}}"], cwd=source)
    head = capture(["git", "rev-parse", args.head], cwd=source, text=True).strip()
    command = ["git", "diff", "--binary", args.baseline, head, "--", *paths]
    raw_patch = capture(command, cwd=source)
    if not raw_patch:
        raise SystemExit("selected overlay diff is empty")

    patch_name = payload["bundle"]["patch_file"]
    patch_path = package / patch_name
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    compressed = gzip.compress(raw_patch, compresslevel=9, mtime=0)
    patch_path.write_bytes(compressed)

    changed_text = capture(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=AM",
            args.baseline,
            head,
            "--",
            *paths,
        ],
        cwd=source,
        text=True,
    )
    changed = sorted(path for path in changed_text.splitlines() if path)
    checksum_lines: list[str] = []
    for path in changed:
        content = capture(["git", "show", f"{head}:{path}"], cwd=source)
        checksum_lines.append(f"{hashlib.sha256(content).hexdigest()}  {path}")
    checksum_bytes = ("\n".join(checksum_lines) + "\n").encode()
    checksums_path = package / payload["bundle"]["checksums_file"]
    checksums_path.write_bytes(checksum_bytes)

    payload["bundle"].update(
        {
            "patch_sha256": hashlib.sha256(compressed).hexdigest(),
            "checksums_sha256": hashlib.sha256(checksum_bytes).hexdigest(),
            "patched_file_count": len(changed),
            "source_head": head,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "patch": str(patch_path),
                "patch_bytes": len(compressed),
                "patched_file_count": len(changed),
                "source_head": head,
                "patch_sha256": payload["bundle"]["patch_sha256"],
                "checksums_sha256": payload["bundle"]["checksums_sha256"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
