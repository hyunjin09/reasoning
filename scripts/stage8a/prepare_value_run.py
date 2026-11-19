"""Freeze the remaining approved assay and its immediate allocation-release hook."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    request_path = Path("outputs/stage8a/value/requests_v1.json")
    selected = json.loads(request_path.read_text())
    assert selected["frozen_before_value_scores"] and selected["requests"]
    config = json.loads(Path("outputs/stage8a/config/measurement_discovery_v1.json").read_text())
    config.update(frozen_at=datetime.now(timezone.utc).isoformat(), phase="main_value_assays",
                  requests=str(request_path), requests_sha256=digest(request_path),
                  output_dir="outputs/stage8a/value/main_v1", layer_sets={"late_window":[19,20,21,22]},
                  discovery_freeze=selected["discovery_freeze"], discovery_freeze_sha256=selected["discovery_freeze_sha256"])
    for path, sha in config["source_sha256"].items():
        assert digest(path) == sha
    for path in ("scripts/stage8a/run_value_assays.py", "scripts/stage8a/verify_value_completion.py",
                 "scripts/stage8a/release_allocation.py", str(Path(__file__).resolve().relative_to(Path.cwd()))):
        config["source_sha256"][path] = digest(path)
    snapshot = Path("outputs/stage8a/source_snapshots/value_main_v1")
    assert not snapshot.exists()
    for path in config["source_sha256"]:
        target = snapshot/path
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target)
    output = Path("outputs/stage8a/config/value_assays_v1.json")
    assert not output.exists()
    output.write_text(json.dumps(config,indent=2)+"\n")
    shell = Path("scripts/stage8a/run_measurement_discovery_v1_tmux.sh").read_text()
    shell = shell.replace("measurement_discovery_v1", "value_assays_v1").replace("measurement/discovery_v1", "value/main_v1").replace("run_measurement.py", "run_value_assays.py")
    shell = shell.replace('exit "$stage8a_exit"', '''if [[ "$stage8a_exit" -eq 0 ]]; then
    .venv/bin/python scripts/stage8a/verify_value_completion.py
    .venv/bin/python scripts/stage8a/release_allocation.py
fi
exit "$stage8a_exit"''')
    wrapper = Path("scripts/stage8a/run_value_assays_v1_tmux.sh")
    assert not wrapper.exists()
    wrapper.write_text(shell)
    receipt = dict(at=config["frozen_at"], events=len(selected["requests"]),
                   config=str(output),config_sha256=digest(output),wrapper=str(wrapper),wrapper_sha256=digest(wrapper),
                   source_snapshot=str(snapshot), source_sha256=config["source_sha256"],
                   value_scores_seen=False, release_after_verification=True,
                   update_to_review_v1="Verification checks both measured event sets against frozen requests and verifies preserved native completion receipt before release.")
    Path("outputs/stage8a/audit/value_assay_launch_v1.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(dict(events=receipt["events"],config=str(output),release_after_verification=True)))


if __name__ == "__main__":
    main()
