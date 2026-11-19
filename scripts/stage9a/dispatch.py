"""Bounded scheduler coordinator; no inference or dataset computation locally.

Launches only Stage9A's preflight and native jobs, on healthy authorized nodes,
as GPU capacity becomes available. Stops on a failed job or after native export;
semantic review/causal selection is never replaced with an automatic heuristic.
"""
import argparse
import fcntl
import json
import os
import subprocess
import time
from datetime import datetime,timezone
from pathlib import Path

import gpu_scheduler as scheduler
from harness_state import load_gpu_queue,mutate_run_state,append_run_history

ROOT=Path("outputs/stage9a/v1")
CFG=ROOT/"stage9a_generation_config_node07.json"
PREFLIGHT="stage9a_preflight_recovery_v1"
NATIVE=[f"stage9a_native_worker{i}_v1" for i in range(4)]
HEALTHY={"node02","node03","node06"}


def now():
    return datetime.now(timezone.utc).isoformat()


def command(*args):
    result=subprocess.run([".venv/bin/python","infra/gpu_scheduler.py",*args,"--project","."],
                          text=True,capture_output=True,check=True)
    print(result.stdout.strip(),flush=True)


def add(job,preflight=False,index=0):
    # Node07 remains user-authorized, but this coordinator cannot certify that
    # its observed filesystem/RPC startup block has been repaired.
    preferred=["thinking","instruct_cot","thinking","instruct_direct"][index]
    cmd=f"bash scripts/stage9a/run_native.sh --config {CFG} "
    cmd += "--preflight" if preflight else f"--preferred {preferred}"
    if not preflight:
        cmd += " && PYTHONPATH=code:.:infra PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/stage9a/export_native.py"
    command("add","--id",job,"--exp-id",job,"--gpu-type","a6000","--gpus","1",
            "--exclude-node","node07","--mem","30G","--cpus","4","--shell-mode","plain",
            "--command",cmd,"--log-path",f"runs/stage9a/v1/{job}_slurm.log",
            "--result-path",str(ROOT/("audit/preflight/complete.json" if preflight else "audit/native_complete.json")))


def status(value):
    value.update(at=now())
    path=ROOT/"audit/dispatcher_status.json";tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value,indent=2)+"\n");tmp.replace(path)


def run(hours):
    project=Path(".").resolve()
    stop=time.monotonic()+hours*3600
    args=argparse.Namespace(squeue_output=None,all_squeue_output=None,scontrol_output=None,
                            available_gpus=None,max_user_gpus=4)
    while time.monotonic()<stop:
        if (ROOT/"audit/STOP_DISPATCH").exists():
            status(dict(state="stopped_by_file",note="Existing Slurm jobs are untouched."));return
        queue=load_gpu_queue(project);jobs={j["id"]:j for j in queue["jobs"]}
        gate=ROOT/"audit/preflight/complete.json"
        if PREFLIGHT not in jobs and not gate.exists():
            add(PREFLIGHT,preflight=True);continue
        live=subprocess.run(["squeue","--me","-h","-o","%i"],text=True,capture_output=True,check=True)
        live_ids=set(live.stdout.split())
        for jid in [PREFLIGHT]+NATIVE:
            job=jobs.get(jid)
            if not job or job["status"]!="running" or str(job.get("slurm_job_id")) in live_ids:
                continue
            sid=str(job["slurm_job_id"])
            receipt=gate if jid==PREFLIGHT else ROOT/"native/workers"/("slurm_"+sid)/"completed.json"
            if not receipt.exists():
                command("update","--id",jid,"--status","failed","--note","Job left Slurm without completion receipt; explicit diagnosis required.")
                status(dict(state="failed",job=jid,slurm_job_id=sid,note="No automatic retry; existing native workers may finish their own queue."));return
            command("update","--id",jid,"--status","succeeded","--note","Completion receipt verified; allocation released.")
        if gate.exists():
            assert json.loads(gate.read_text())["pass"]
            # Wait for preflight allocation to leave Slurm before production.
            pre=jobs.get(PREFLIGHT,{})
            if str(pre.get("slurm_job_id","")) in live_ids:
                time.sleep(30);continue
            for index,jid in enumerate(NATIVE):
                if jid not in jobs:
                    add(jid,index=index)
            if (ROOT/"audit/native_complete.json").exists():
                for jid in NATIVE:
                    if jobs.get(jid,{}).get("status")=="queued":
                        command("update","--id",jid,"--status","cancelled","--note","All384 native tasks already completed; unused worker unnecessary.")
                status(dict(state="native_complete_review_pending",trajectories=384,scientific_stage_complete=False));return
        queue=load_gpu_queue(project)
        capacity=scheduler.gpu_status(args,queue)
        if capacity["warnings"]:
            raise RuntimeError(capacity["warnings"])
        selected={PREFLIGHT} if not gate.exists() else set(NATIVE)
        owned_queue=dict(queue,jobs=[j for j in queue["jobs"] if j["id"] in selected])
        planned=scheduler.plan_jobs(owned_queue,capacity)
        for job in planned:
            assert job["node"] in HEALTHY and job["gpus"]==1
            os.environ["SBATCH_TIMELIMIT"]="01:00:00" if job["id"]==PREFLIGHT else "3-00:00:00"
            scheduler.execute_launch(project,job)
            print(json.dumps(dict(event="launched",job=job["id"],node=job["node"],at=now())),flush=True)
        status(dict(state="preflight_waiting_or_running" if not gate.exists() else "native_waiting_or_running",
                    own_gpus=capacity["own_gpus"],maximum_gpus=4,allowed_healthy_nodes=sorted(HEALTHY),
                    node07="User authorized; withheld after observed startup RPC wait pending evidence of repair.",
                    planned_jobs=[j["id"] for j in planned],deadline_hours=hours,scientific_stage_complete=False))
        time.sleep(30)
    status(dict(state="coordinator_deadline",note="No more submissions; already submitted jobs may continue."))


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--hours",type=float,default=72);a=ap.parse_args()
    lock=(ROOT/"audit/dispatcher.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:
        run(a.hours)
    except Exception as exc:
        status(dict(state="error",error=repr(exc),automatic_retry=False));raise
    finally:
        lock.close()


if __name__=="__main__":
    main()
