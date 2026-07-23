from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_compat_bundle.py"
SPEC = importlib.util.spec_from_file_location("build_compat_bundle", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
validate_include_paths = MODULE.validate_include_paths


def test_include_paths_accept_tracked_files_and_directories():
    validate_include_paths(
        ["README.md", "hermes_cli"],
        {
            "README.md",
            "hermes_cli/supervisor_bootstrap.py",
        },
    )


def test_include_paths_fail_closed_when_required_source_is_missing():
    with pytest.raises(
        SystemExit,
        match=r"required include path\(s\) missing from source head: "
        r"hermes_cli/capability_leases.py",
    ):
        validate_include_paths(
            ["README.md", "hermes_cli/capability_leases.py"],
            {"README.md"},
        )


@pytest.mark.parametrize("path", ["/absolute/path", "../outside"])
def test_include_paths_reject_unsafe_entries(path):
    with pytest.raises(SystemExit, match="unsafe include path"):
        validate_include_paths([path], set())
