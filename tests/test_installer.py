from __future__ import annotations

import json
import os
from types import SimpleNamespace

import pytest

from hermes_control import installer
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


def test_setup_falls_back_to_current_supervisor_installer(tmp_path, monkeypatch):
    root = tmp_path / "managed"
    release = root / "releases" / "release-v011"
    source = release / "source"
    python = release / "venv" / "bin" / "python"
    home = tmp_path / "hermes-home"
    source.mkdir(parents=True)
    python.parent.mkdir(parents=True)
    python.touch()
    home.mkdir()
    (home / "config.yaml").write_text("{}\n", encoding="utf-8")
    (release / "receipt.json").write_text(
        json.dumps(
            {
                "release_path": str(release),
                "venv_path": str(release / "venv"),
            }
        ),
        encoding="utf-8",
    )
    root.mkdir(exist_ok=True)
    (root / "current.json").write_text(
        json.dumps(
            {
                "schema": installer.CURRENT_SCHEMA,
                "release_id": "release-v011",
                "release_path": str(release),
            }
        ),
        encoding="utf-8",
    )
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs.get("env")
        return SimpleNamespace(stdout=json.dumps({"dry_run": True}))

    monkeypatch.setattr(installer, "_run", fake_run)
    result = installer.setup_public(
        root=root,
        hermes_home=home,
        dry_run=True,
    )

    assert result == {"dry_run": True}
    assert captured["command"] == [
        str(python),
        "-m",
        "hermes_cli.main",
        "supervisor",
        "install",
        "--repo-root",
        str(source),
        "--dry-run",
    ]
    assert captured["env"]["HERMES_HOME"] == str(home)
