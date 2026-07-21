from __future__ import annotations

import json
import os

import pytest

from hermes_control.installer import doctor, install, rollback


def test_dry_run_has_no_side_effects(tmp_path):
    root = tmp_path / "managed"
    result = install(root=root, dry_run=True, install_dependencies=False)
    assert result["dry_run"] is True
    assert result["isolation"].startswith("managed release")
    assert result["fetch_strategy"] == "single exact upstream commit"
    assert not root.exists()


@pytest.mark.integration
def test_offline_materialize_doctor_and_rollback(tmp_path):
    source = os.environ.get("HERMES_CONTROL_SOURCE_REPO")
    if not source:
        pytest.skip("set HERMES_CONTROL_SOURCE_REPO to a git repo containing the baseline")
    root = tmp_path / "managed"
    first = install(root=root, source=source, install_dependencies=False)
    assert first["verified"] is True
    first_doctor = doctor(root=root)
    assert first_doctor["ok"], first_doctor
    assert first_doctor["warnings"] == ["dependencies were intentionally not installed"]

    second = install(root=root, source=source, install_dependencies=False)
    assert second["previous_release"] == first["release_id"]
    rolled = rollback(root=root)
    assert rolled["to_release"] == first["release_id"]
    current = json.loads((root / "current.json").read_text(encoding="utf-8"))
    assert current["release_id"] == first["release_id"]
