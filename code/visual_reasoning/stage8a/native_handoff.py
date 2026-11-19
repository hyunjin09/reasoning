"""Guard the one user-authorized native tail handoff without overwriting data."""
import hashlib
import json
from pathlib import Path


def claim_destination(destination, handoff_path):
    destination, handoff_path = Path(destination), Path(handoff_path)
    handoff = json.loads(handoff_path.read_text())
    if destination.exists():
        if str(destination) != handoff["reservation"]:
            raise FileExistsError(destination)
        marker = destination / "handoff_reserved.json"
        if {p.name for p in destination.iterdir()} != {marker.name}:
            raise FileExistsError("Reserved destination already contains native artifacts")
        expected = hashlib.sha256(handoff_path.read_bytes()).hexdigest()
        if json.loads(marker.read_text())["handoff_sha256"] != expected:
            raise ValueError("Reservation does not match the frozen handoff")
    else:
        destination.mkdir(parents=True)


def boundary_complete(handoff):
    root = Path(handoff["canonical_output_dir"])
    if not (root / "wrapper.json").exists():
        return False
    original = json.loads((root / "wrapper.json").read_text())
    assert not original["completed"] and original["exit_code"] != 0
    assert (root / "worker0/examples" / handoff["current_untouched"] / "result.json").exists()
    log = Path("runs/stage8a/main_v1_worker_0.log").read_text()
    assert "AssertionError: " + handoff["reservation"] in log
    starts = [json.loads(line)["base_id"] for line in log.splitlines()
              if line.startswith('{"event": "start_example"')]
    assert not set(starts) & set(handoff["pending"]), "A reassigned sample started on the original worker"
    return True
