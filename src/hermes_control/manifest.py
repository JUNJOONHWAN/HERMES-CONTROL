"""Strict compatibility contract for an HERMES-CONTROL overlay release."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import json
from pathlib import Path
from typing import Any


SCHEMA = "hermes-control.compatibility.v1"


class ManifestError(ValueError):
    """Raised when a compatibility manifest is incomplete or unsafe."""


@dataclass(frozen=True)
class CompatibilityManifest:
    schema: str
    overlay_version: str
    upstream_name: str
    upstream_url: str
    upstream_version: str
    baseline_commit: str
    python_min: tuple[int, int]
    python_max_exclusive: tuple[int, int]
    platforms: tuple[str, ...]
    patch_file: str
    patch_sha256: str
    checksums_file: str
    checksums_sha256: str
    patched_file_count: int
    required_paths: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CompatibilityManifest":
        required = {
            "schema",
            "overlay_version",
            "upstream",
            "python",
            "platforms",
            "bundle",
            "required_paths",
        }
        missing = sorted(required - payload.keys())
        if missing:
            raise ManifestError(f"manifest fields missing: {', '.join(missing)}")
        if payload["schema"] != SCHEMA:
            raise ManifestError(f"unsupported manifest schema: {payload['schema']!r}")

        upstream = payload["upstream"]
        python = payload["python"]
        bundle = payload["bundle"]
        baseline = str(upstream["baseline_commit"])
        if len(baseline) != 40 or any(ch not in "0123456789abcdef" for ch in baseline):
            raise ManifestError("baseline_commit must be a full lowercase git SHA-1")

        manifest = cls(
            schema=payload["schema"],
            overlay_version=str(payload["overlay_version"]),
            upstream_name=str(upstream["name"]),
            upstream_url=str(upstream["url"]),
            upstream_version=str(upstream["version"]),
            baseline_commit=baseline,
            python_min=_version_pair(python["min_inclusive"]),
            python_max_exclusive=_version_pair(python["max_exclusive"]),
            platforms=tuple(str(item).lower() for item in payload["platforms"]),
            patch_file=str(bundle["patch_file"]),
            patch_sha256=_sha256(bundle["patch_sha256"], "patch_sha256"),
            checksums_file=str(bundle["checksums_file"]),
            checksums_sha256=_sha256(bundle["checksums_sha256"], "checksums_sha256"),
            patched_file_count=int(bundle["patched_file_count"]),
            required_paths=tuple(str(path) for path in payload["required_paths"]),
        )
        if not manifest.platforms:
            raise ManifestError("platforms cannot be empty")
        for path in (*manifest.required_paths, manifest.patch_file, manifest.checksums_file):
            _safe_relative_path(path)
        return manifest

    @classmethod
    def load(cls, path: Path) -> "CompatibilityManifest":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "overlay_version": self.overlay_version,
            "upstream": {
                "name": self.upstream_name,
                "url": self.upstream_url,
                "version": self.upstream_version,
                "baseline_commit": self.baseline_commit,
            },
            "python": {
                "min_inclusive": ".".join(map(str, self.python_min)),
                "max_exclusive": ".".join(map(str, self.python_max_exclusive)),
            },
            "platforms": list(self.platforms),
            "bundle": {
                "patch_sha256": self.patch_sha256,
                "checksums_sha256": self.checksums_sha256,
                "patched_file_count": self.patched_file_count,
            },
            "required_paths": list(self.required_paths),
        }


def bundled_manifest() -> CompatibilityManifest:
    resource = files("hermes_control").joinpath(
        "compatibility/hermes-agent-0.18.0-control-0.1.8/manifest.json"
    )
    return CompatibilityManifest.from_dict(json.loads(resource.read_text(encoding="utf-8")))


def bundle_resource(relative_path: str):
    _safe_relative_path(relative_path)
    return files("hermes_control").joinpath(relative_path)


def _version_pair(value: Any) -> tuple[int, int]:
    parts = str(value).split(".")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ManifestError(f"invalid major.minor version: {value!r}")
    return int(parts[0]), int(parts[1])


def _sha256(value: Any, field: str) -> str:
    token = str(value).lower()
    if len(token) != 64 or any(ch not in "0123456789abcdef" for ch in token):
        raise ManifestError(f"{field} must be a lowercase SHA-256")
    return token


def _safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not value or ".." in path.parts:
        raise ManifestError(f"unsafe bundle path: {value!r}")
    return path
