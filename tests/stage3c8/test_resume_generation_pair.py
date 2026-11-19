from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/stage3c8/resume_generation_pair.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("stage3c8_resume_generation_pair", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_resume_dispatch_does_not_depend_on_an_expired_allocation(monkeypatch):
    module = _load_module()
    calls: list[list[str]] = []

    def fake_run(command, *args, **kwargs):
        command = [str(part) for part in command]
        calls.append(command)
        if command[0] == "squeue":
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setenv("SLURM_PROCID", "0")
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    module.main()

    assert calls
    assert calls[0][0].endswith(".venv/bin/python")
    assert "run_prospective_generation.py" in calls[0][1]
    assert any(part.endswith("generation_shard_00.jsonl") for part in calls[0])
