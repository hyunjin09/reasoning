"""Launch only one named project-scheduler job, with cumulative reservation."""
import argparse
import os
import shlex
import subprocess
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage14d1_pilot.common import *
from scripts.stage14d1_pilot.execution import remaining_budget
from scripts.stage14d1_pilot.accounting import budget_amounts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--node", default="")
    args = parser.parse_args()
    m = load(args.manifest)
    ident = "sava14d1_pilot_" + m["id"]
    receipt = P / "audit/launches" / f"{ident}.json"
    assert not receipt.exists()
    consumed, reservations = [], []
    for p in (P / "audit/launches").glob("*.json"):
        prior = load(p)
        job = prior["job"]["slurm_job_id"]
        raw = subprocess.check_output([
            "sacct", "-j", job, "-X", "-n", "-P",
            "--format=JobID,State,ElapsedRaw,AllocTRES"], text=True)
        charged, reserved = budget_amounts(raw, prior["maximum_gpu_seconds"])
        consumed.append(charged)
        reservations.append(reserved)
    assert remaining_budget(PRIOR_GPU_SECONDS, consumed, reservations) >= m["wall_seconds"]
    if m["mode"] == "main":
        release = load(m["scientific_release"])
        assert release["technical_pass"] and release["source_transport_review_complete"]
    opts = SimpleNamespace(max_user_gpus=8, squeue_output=None, all_squeue_output=None,
                           scontrol_output=None, available_gpus=None)
    status = scheduler.gpu_status(opts, scheduler.load_gpu_queue(Path.cwd()))
    assert status["remaining_user_slots"] >= 1
    command = shlex.join(["env", "VLLM_ENABLE_V1_MULTIPROCESSING=0", "bash",
                         "scripts/stage14d1/run.sh", "-m", "scripts.stage14d1_pilot.main_worker", args.manifest])
    saved = Path("reports/index.md").read_text()
    try:
        add = [".venv/bin/python", "infra/gpu_scheduler.py", "add", "--project", ".",
               "--id", ident, "--exp-id", ident, "--gpu-type", "a6000", "--gpus", "1",
               "--mem", "28G", "--cpus", "1", "--command", command,
               "--log-path", f"runs/stage14d1_pilot/{ident}/slurm.log",
               "--result-path", str(P / "raw" / m["id"])]
        if args.node:
            add += ["--node", args.node]
        else:
            add += ["--allow-slurm-pending"]
        subprocess.run(add, check=True, capture_output=True, text=True)
        selected = [j for j in scheduler.load_gpu_queue(Path.cwd())["jobs"] if j["id"] == ident]
        plans = scheduler.plan_jobs({"jobs": selected}, status)
        assert len(plans) == 1, "No suitable live capacity; do not fall back outside scheduler"
        seconds = m["wall_seconds"]
        os.environ["SBATCH_TIMELIMIT"] = f"{seconds//3600:02}:{seconds//60%60:02}:{seconds%60:02}"
        scheduler.execute_launch(Path.cwd(), plans[0])
        job = next(j for j in scheduler.load_gpu_queue(Path.cwd())["jobs"] if j["id"] == ident)
        save(receipt, dict(at=now(), job=job, manifest_sha256=sha(args.manifest),
                          maximum_gpu_seconds=seconds, prior_stage_gpu_seconds=PRIOR_GPU_SECONDS,
                          prior_new_allocated=consumed, prior_outstanding_reservations=reservations,
                          maximum_cumulative_gpu_seconds=PRIOR_GPU_SECONDS+sum(consumed)+sum(reservations)+seconds,
                          capacity_at_submission=status))
        print("SUBMITTED", job["slurm_job_id"], ident)
    finally:
        Path("reports/index.md").write_text(saved)


if __name__ == "__main__":
    main()
