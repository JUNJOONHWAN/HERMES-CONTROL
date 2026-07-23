from __future__ import annotations

from importlib.resources import files

import pytest

from hermes_control.installer import InstallError, check_host, parse_checksums
from hermes_control.manifest import ManifestError, bundled_manifest


def test_bundled_manifest_is_strict_and_complete():
    manifest = bundled_manifest()
    assert manifest.schema == "hermes-control.compatibility.v1"
    assert manifest.overlay_version == "0.1.13"
    assert manifest.baseline_commit == "5445e42b87b9918d5b1bfa9f4eadd8e4bb10ff37"
    assert manifest.source_basis == (
        "DGX LIVE 0.1.13 central Multitool MCP catalog and card-scoped leases"
    )
    assert manifest.timeline_package == "hermes-timeline-code-map"
    assert manifest.timeline_version == "0.1.1"
    assert manifest.timeline_source_commit == "3a66a36fef96468705e5cc2d22645ba6f605e704"
    assert manifest.timeline_wheel.endswith(".whl")
    assert manifest.platforms == ("linux", "darwin")
    assert manifest.patched_file_count > 50
    assert "distribution/release.json" in manifest.required_paths


def test_current_bundle_has_no_team_or_timeline_cli_dependency():
    manifest = bundled_manifest()
    include_paths = files("hermes_control").joinpath(
        "compatibility/hermes-agent-0.18.0-control-0.1.13/include-paths.txt"
    ).read_text(encoding="utf-8")
    contract_text = "\n".join(
        (
            include_paths,
            manifest.patch_file,
            manifest.checksums_file,
            *manifest.required_paths,
        )
    ).lower()

    assert "hermes-team" not in contract_text
    assert "hermes_team" not in contract_text
    assert "scripts/hermes_timeline_cli.py" not in contract_text
    assert "extensions/hermes-timeline-code-map" not in contract_text


@pytest.mark.parametrize("system", ["linux", "darwin", "Linux", "Darwin"])
@pytest.mark.parametrize("version", [(3, 11), (3, 12), (3, 13)])
def test_supported_host_matrix(system, version):
    assert check_host(bundled_manifest(), system=system, version=version)["ok"]


@pytest.mark.parametrize(
    ("system", "version"),
    [("windows", (3, 12)), ("linux", (3, 10)), ("darwin", (3, 14))],
)
def test_unsupported_hosts_fail_closed(system, version):
    result = check_host(bundled_manifest(), system=system, version=version)
    assert not result["ok"]
    assert result["errors"]


def test_checksum_parser_rejects_traversal_and_duplicates():
    digest = "a" * 64
    with pytest.raises(InstallError, match="unsafe path"):
        parse_checksums(f"{digest}  ../outside\n")
    with pytest.raises(InstallError, match="duplicate"):
        parse_checksums(f"{digest}  safe.txt\n{digest}  safe.txt\n")


def test_manifest_rejects_short_baseline():
    payload = {
        "schema": "hermes-control.compatibility.v1",
        "overlay_version": "x",
        "upstream": {"name": "x", "url": "x", "version": "x", "baseline_commit": "abc"},
        "python": {"min_inclusive": "3.11", "max_exclusive": "3.14"},
        "platforms": ["linux"],
        "bundle": {
            "patch_file": "patches/x.gz",
            "patch_sha256": "a" * 64,
            "checksums_file": "compatibility/x.sha256",
            "checksums_sha256": "b" * 64,
            "patched_file_count": 1,
        },
        "timeline": {
            "package": "hermes-timeline-code-map",
            "version": "0.1.1",
            "wheel": "artifacts/timeline.whl",
            "wheel_sha256": "c" * 64,
            "source_repository": "git@example/timeline.git",
            "source_commit": "d" * 40,
        },
        "required_paths": ["safe"],
    }
    with pytest.raises(ManifestError, match="baseline_commit"):
        type(bundled_manifest()).from_dict(payload)
