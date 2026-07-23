"""Materialize and operate an isolated, version-gated HERMES-CONTROL runtime."""

from __future__ import annotations

from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterable
from uuid import uuid4

from .manifest import CompatibilityManifest, bundle_resource, bundled_manifest


INSTALL_SCHEMA = "hermes-control.install-receipt.v1"
CURRENT_SCHEMA = "hermes-control.current.v1"


class InstallError(RuntimeError):
    """A fail-closed install, setup, or validation error."""


def default_root() -> Path:
    configured = os.environ.get("HERMES_CONTROL_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".hermes-control"


def check_host(
    manifest: CompatibilityManifest,
    *,
    system: str | None = None,
    version: tuple[int, int] | None = None,
) -> dict[str, Any]:
    system_name = (system or platform.system()).lower()
    python_version = version or (sys.version_info.major, sys.version_info.minor)
    errors: list[str] = []
    if system_name not in manifest.platforms:
        errors.append(
            f"unsupported platform {system_name!r}; supported: {', '.join(manifest.platforms)}"
        )
    if not (manifest.python_min <= python_version < manifest.python_max_exclusive):
        errors.append(
            "unsupported Python "
            f"{python_version[0]}.{python_version[1]}; required >="
            f"{manifest.python_min[0]}.{manifest.python_min[1]}, <"
            f"{manifest.python_max_exclusive[0]}.{manifest.python_max_exclusive[1]}"
        )
    return {
        "ok": not errors,
        "platform": system_name,
        "python": f"{python_version[0]}.{python_version[1]}",
        "errors": errors,
    }


def install(
    *,
    root: Path | None = None,
    source: str | None = None,
    install_dependencies: bool = True,
    dry_run: bool = False,
    manifest: CompatibilityManifest | None = None,
) -> dict[str, Any]:
    manifest = manifest or bundled_manifest()
    host = check_host(manifest)
    if not host["ok"]:
        raise InstallError("; ".join(host["errors"]))
    root = (root or default_root()).expanduser().resolve()
    source_value = source or manifest.upstream_url
    plan = {
        "schema": INSTALL_SCHEMA,
        "dry_run": dry_run,
        "root": str(root),
        "source": source_value,
        "upstream_commit": manifest.baseline_commit,
        "overlay_version": manifest.overlay_version,
        "timeline_package": manifest.timeline_package,
        "timeline_version": manifest.timeline_version,
        "timeline_source_repository": manifest.timeline_source_repository,
        "timeline_source_commit": manifest.timeline_source_commit,
        "install_dependencies": install_dependencies,
        "host": host,
        "isolation": "managed release; existing Hermes checkouts are not modified",
        "fetch_strategy": "single exact upstream commit",
    }
    if dry_run:
        return plan

    root.mkdir(parents=True, exist_ok=True)
    releases = root / "releases"
    releases.mkdir(exist_ok=True)
    release_id = _release_id(manifest)
    final_release = releases / release_id
    stage = Path(tempfile.mkdtemp(prefix=".stage-", dir=root))
    source_tree = stage / "source"
    previous = _read_current(root, required=False)
    moved = False
    try:
        source_tree.mkdir(parents=True)
        _run(["git", "init", "-q", str(source_tree)])
        _run(["git", "remote", "add", "origin", source_value], cwd=source_tree)
        _run(
            [
                "git",
                "fetch",
                "--depth",
                "1",
                "--no-tags",
                "origin",
                manifest.baseline_commit,
            ],
            cwd=source_tree,
        )
        _run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=source_tree)
        actual_commit = _capture(["git", "rev-parse", "HEAD"], cwd=source_tree)
        if actual_commit != manifest.baseline_commit:
            raise InstallError(
                f"upstream commit mismatch: expected {manifest.baseline_commit}, got {actual_commit}"
            )

        patch_bytes = bundle_resource(manifest.patch_file).read_bytes()
        _verify_bytes(patch_bytes, manifest.patch_sha256, "patch bundle")
        try:
            patch = gzip.decompress(patch_bytes)
        except (gzip.BadGzipFile, OSError) as exc:
            raise InstallError(f"invalid gzip patch bundle: {exc}") from exc
        _run(
            ["git", "apply", "--check", "--binary", "--whitespace=nowarn", "-"],
            cwd=source_tree,
            input_bytes=patch,
        )
        _run(
            ["git", "apply", "--binary", "--whitespace=nowarn", "-"],
            cwd=source_tree,
            input_bytes=patch,
        )
        checksum_result = verify_overlay_tree(source_tree, manifest)
        if not checksum_result["ok"]:
            raise InstallError("patched tree checksum failure: " + "; ".join(checksum_result["errors"]))

        stage.rename(final_release)
        moved = True
        source_tree = final_release / "source"
        venv_dir = final_release / "venv"
        timeline_extension = "not_installed"
        if install_dependencies:
            _run([sys.executable, "-m", "venv", str(venv_dir)])
            python = _venv_python(venv_dir)
            _run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "-e",
                    f"{source_tree}[mcp]",
                ]
            )
            timeline_wheel = bundle_resource(manifest.timeline_wheel)
            timeline_bytes = timeline_wheel.read_bytes()
            _verify_bytes(
                timeline_bytes,
                manifest.timeline_wheel_sha256,
                "standalone Timeline wheel",
            )
            _run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    str(timeline_wheel),
                ]
            )
            runtime_imports = (
                "import hermes_cli.supervisor_bootstrap, "
                "hermes_cli.supervisor_registry, hermes_timeline_code_map"
            )
            timeline_extension = "standalone_pinned_wheel"
            _run(
                [
                    str(python),
                    "-c",
                    runtime_imports,
                ]
            )

        receipt = {
            **plan,
            "dry_run": False,
            "release_id": release_id,
            "release_path": str(final_release),
            "source_path": str(source_tree),
            "venv_path": str(venv_dir) if install_dependencies else None,
            "timeline_extension": timeline_extension,
            "timeline_package": manifest.timeline_package,
            "timeline_version": manifest.timeline_version,
            "timeline_wheel_sha256": manifest.timeline_wheel_sha256,
            "timeline_source_repository": manifest.timeline_source_repository,
            "timeline_source_commit": manifest.timeline_source_commit,
            "installed_at_utc": datetime.now(timezone.utc).isoformat(),
            "previous_release": previous.get("release_id") if previous else None,
            "patch_sha256": manifest.patch_sha256,
            "checksums_sha256": manifest.checksums_sha256,
            "patched_file_count": manifest.patched_file_count,
            "verified": True,
        }
        _atomic_json(final_release / "receipt.json", receipt)
        _activate(root, receipt)
        return receipt
    except Exception:
        if moved and final_release.exists():
            shutil.rmtree(final_release)
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def verify_overlay_tree(
    source_tree: Path, manifest: CompatibilityManifest | None = None
) -> dict[str, Any]:
    manifest = manifest or bundled_manifest()
    checksums_bytes = bundle_resource(manifest.checksums_file).read_bytes()
    _verify_bytes(checksums_bytes, manifest.checksums_sha256, "checksums manifest")
    entries = parse_checksums(checksums_bytes.decode("utf-8"))
    errors: list[str] = []
    if len(entries) != manifest.patched_file_count:
        errors.append(
            f"file count mismatch: expected {manifest.patched_file_count}, manifest has {len(entries)}"
        )
    for relative, expected in entries:
        candidate = source_tree / relative
        if not candidate.is_file():
            errors.append(f"missing: {relative}")
            continue
        actual = _sha256_file(candidate)
        if actual != expected:
            errors.append(f"checksum mismatch: {relative}")
    for required in manifest.required_paths:
        if not (source_tree / required).exists():
            errors.append(f"required path missing: {required}")
    return {"ok": not errors, "checked": len(entries), "errors": errors}


def parse_checksums(text: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            digest, relative = raw.split("  ", 1)
        except ValueError as exc:
            raise InstallError(f"invalid checksums line {number}") from exc
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise InstallError(f"invalid SHA-256 on checksums line {number}")
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not relative:
            raise InstallError(f"unsafe path on checksums line {number}: {relative!r}")
        if relative in seen:
            raise InstallError(f"duplicate checksums path: {relative}")
        seen.add(relative)
        result.append((relative, digest))
    return result


def doctor(*, root: Path | None = None) -> dict[str, Any]:
    root = (root or default_root()).expanduser().resolve()
    manifest = bundled_manifest()
    host = check_host(manifest)
    errors = list(host["errors"])
    warnings: list[str] = []
    try:
        current = _read_current(root, required=True)
        release = Path(current["release_path"])
        receipt = json.loads((release / "receipt.json").read_text(encoding="utf-8"))
        source_tree = release / "source"
        actual_commit = _capture(["git", "rev-parse", "HEAD"], cwd=source_tree)
        if actual_commit != manifest.baseline_commit:
            errors.append(
                f"baseline drift: expected {manifest.baseline_commit}, got {actual_commit}"
            )
        tree = verify_overlay_tree(source_tree, manifest)
        errors.extend(tree["errors"])
        venv_value = receipt.get("venv_path")
        if venv_value:
            python = _venv_python(Path(venv_value))
            if not python.is_file():
                errors.append(f"managed Python missing: {python}")
            else:
                runtime_imports = (
                    "import hermes_cli.supervisor_bootstrap, "
                    "hermes_cli.supervisor_registry, hermes_timeline_code_map"
                )
                if receipt.get("timeline_extension") != "standalone_pinned_wheel":
                    errors.append(
                        "Timeline installation provenance is not the pinned "
                        "standalone wheel"
                    )
                if receipt.get("timeline_source_commit") != manifest.timeline_source_commit:
                    errors.append(
                        "Timeline source commit drift: expected "
                        f"{manifest.timeline_source_commit}, got "
                        f"{receipt.get('timeline_source_commit')}"
                    )
                probe = subprocess.run(
                    [
                        str(python),
                        "-c",
                        runtime_imports,
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if probe.returncode:
                    errors.append("runtime import probe failed: " + probe.stderr.strip())
        else:
            warnings.append("dependencies were intentionally not installed")
        return {
            "schema": "hermes-control.doctor.v1",
            "ok": not errors,
            "root": str(root),
            "release_id": current.get("release_id"),
            "host": host,
            "checked_files": tree["checked"],
            "errors": errors,
            "warnings": warnings,
        }
    except (OSError, KeyError, ValueError, InstallError, subprocess.SubprocessError) as exc:
        errors.append(str(exc))
        return {
            "schema": "hermes-control.doctor.v1",
            "ok": False,
            "root": str(root),
            "host": host,
            "errors": errors,
            "warnings": warnings,
        }


def setup_public(
    *,
    root: Path | None = None,
    hermes_home: Path | None = None,
    dry_run: bool = False,
    skip_opencode_install: bool = False,
    skip_timeline_install: bool = False,
    skip_live_health: bool = False,
) -> dict[str, Any]:
    root = (root or default_root()).expanduser().resolve()
    current = _read_current(root, required=True)
    release = Path(current["release_path"])
    receipt = json.loads((release / "receipt.json").read_text(encoding="utf-8"))
    if not receipt.get("venv_path"):
        raise InstallError("setup requires an install with dependencies")
    python = _venv_python(Path(receipt["venv_path"]))
    home = (hermes_home or Path.home() / ".hermes").expanduser().resolve()
    if not (home / "config.yaml").is_file():
        prefix = f"HERMES_HOME={home} " if hermes_home else ""
        raise InstallError(
            f"Hermes state is not initialized at {home}. "
            f"Run `{prefix}hermes-control --root {root} run -- setup` first."
        )
    source = release / "source"
    legacy_setup = source / "scripts" / "setup_public_edition.py"
    if legacy_setup.is_file():
        command = [
            str(python),
            str(legacy_setup),
            "--home",
            str(home),
            "--repo-root",
            str(source),
        ]
        if dry_run:
            command.append("--dry-run")
        if skip_opencode_install:
            command.append("--skip-opencode-install")
        if skip_timeline_install:
            command.append("--skip-timeline-install")
        if skip_live_health:
            command.append("--skip-live-health")
    else:
        unsupported = [
            name
            for name, enabled in (
                ("--skip-opencode-install", skip_opencode_install),
                ("--skip-timeline-install", skip_timeline_install),
                ("--skip-live-health", skip_live_health),
            )
            if enabled
        ]
        if unsupported:
            raise InstallError(
                "this source uses `hermes supervisor install`; unsupported "
                "legacy setup option(s): " + ", ".join(unsupported)
            )
        command = [
            str(python),
            "-m",
            "hermes_cli.main",
            "supervisor",
            "install",
            "--repo-root",
            str(source),
        ]
        if dry_run:
            command.append("--dry-run")
    runtime_env = dict(os.environ)
    runtime_env["HERMES_HOME"] = str(home)
    completed = _run(command, capture=True, env=runtime_env)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise InstallError("public setup returned non-JSON output") from exc


def run_hermes(arguments: Iterable[str], *, root: Path | None = None) -> int:
    root = (root or default_root()).expanduser().resolve()
    current = _read_current(root, required=True)
    receipt = json.loads(
        (Path(current["release_path"]) / "receipt.json").read_text(encoding="utf-8")
    )
    if not receipt.get("venv_path"):
        raise InstallError("run requires an install with dependencies")
    executable = Path(receipt["venv_path"]) / "bin" / "hermes"
    if not executable.is_file():
        raise InstallError(f"Hermes executable missing: {executable}")
    return subprocess.call([str(executable), *arguments])


def rollback(*, root: Path | None = None) -> dict[str, Any]:
    root = (root or default_root()).expanduser().resolve()
    current = _read_current(root, required=True)
    receipt = json.loads(
        (Path(current["release_path"]) / "receipt.json").read_text(encoding="utf-8")
    )
    previous_id = receipt.get("previous_release")
    if not previous_id:
        raise InstallError("no previous managed release is recorded")
    previous_release = root / "releases" / previous_id
    previous_receipt = json.loads(
        (previous_release / "receipt.json").read_text(encoding="utf-8")
    )
    tree = verify_overlay_tree(previous_release / "source")
    if not tree["ok"]:
        raise InstallError("previous release is invalid: " + "; ".join(tree["errors"]))
    _activate(root, previous_receipt)
    return {
        "schema": "hermes-control.rollback.v1",
        "ok": True,
        "from_release": current["release_id"],
        "to_release": previous_id,
    }


def _activate(root: Path, receipt: dict[str, Any]) -> None:
    current = {
        "schema": CURRENT_SCHEMA,
        "release_id": receipt["release_id"],
        "release_path": receipt["release_path"],
        "activated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _atomic_json(root / "current.json", current)
    link = root / "current"
    temporary = root / f".current-{uuid4().hex}"
    temporary.symlink_to(Path(receipt["release_path"]), target_is_directory=True)
    os.replace(temporary, link)


def _read_current(root: Path, *, required: bool) -> dict[str, Any] | None:
    path = root / "current.json"
    if not path.is_file():
        if required:
            raise InstallError(f"no managed HERMES-CONTROL install at {root}")
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != CURRENT_SCHEMA:
        raise InstallError(f"unsupported current pointer schema at {path}")
    release = Path(payload["release_path"]).resolve()
    expected_parent = (root / "releases").resolve()
    if release.parent != expected_parent:
        raise InstallError("current release escapes the managed releases directory")
    return payload


def _release_id(manifest: CompatibilityManifest) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{manifest.upstream_version}-{manifest.overlay_version}-{stamp}-{uuid4().hex[:8]}"


def _venv_python(venv: Path) -> Path:
    return venv / "bin" / "python"


def _verify_bytes(value: bytes, expected: str, label: str) -> None:
    actual = hashlib.sha256(value).hexdigest()
    if actual != expected:
        raise InstallError(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    input_bytes: bytes | None = None,
    capture: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            input=input_bytes,
            capture_output=capture,
            check=True,
            text=False if input_bytes is not None else capture,
            env=env,
        )
    except FileNotFoundError as exc:
        raise InstallError(f"required command not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        detail = (stderr or "").strip()
        raise InstallError(
            f"command failed ({exc.returncode}): {' '.join(command)}"
            + (f"\n{detail}" if detail else "")
        ) from exc


def _capture(command: list[str], *, cwd: Path) -> str:
    completed = _run(command, cwd=cwd, capture=True)
    stdout = completed.stdout
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8")
    return stdout.strip()
