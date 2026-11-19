"""Release only115046 after all approved Stage8A GPU artifacts pass validation."""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from harness_state import mutate_gpu_queue


def main():
    proof = json.loads(Path("outputs/stage8a/audit/gpu_work_complete_v1.json").read_text())
    assert proof["completed"] and proof["required_gpu_work_complete"] and proof["release_authorized"]
    assert proof["slurm_job_id"] == "115046"
    before = subprocess.run(["squeue","-h","-j","115046","-o","%i %T %N"],capture_output=True,text=True,check=True).stdout
    cancelled = subprocess.run(["scancel","115046"],capture_output=True,text=True,check=True)
    after = None
    for _ in range(30):
        after = subprocess.run(["squeue","-h","-j","115046","-o","%i %T %N"],capture_output=True,text=True,check=True).stdout
        if not after.strip():
            break
        time.sleep(1)
    record = dict(at=datetime.now(timezone.utc).isoformat(), slurm_job_id="115046", allocation_released=not bool(after.strip()),
                  before=before, after=after, scancel_returncode=cancelled.returncode,
                  reason="User requested immediate release as soon as Stage8A no longer needs GPUs; all native, measurement and Value artifacts verified. Final analysis/report are CPU-only.",
                  gpu_completion_receipt="outputs/stage8a/audit/gpu_work_complete_v1.json")
    target = Path("outputs/stage8a/audit/allocation_released_v1.json")
    assert not target.exists()
    target.write_text(json.dumps(record,indent=2)+"\n")
    def update(queue):
        job = next(j for j in queue["jobs"] if j["id"] == "interactive_node02_2gpu_20260916")
        job.update(status="cancelled" if record["allocation_released"] else "running",
                   finished_at=record["at"], notes=record["reason"], release_receipt=str(target))
    mutate_gpu_queue(Path.cwd(),update)
    print(json.dumps(record),flush=True)
    assert record["allocation_released"], "Release requested but Slurm allocation still visible; inspect status"


if __name__ == "__main__":
    main()
