#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "infra"))

from gpu_scheduler import HarnessError, plan_jobs, sbatch_args, validate_add_memory_request


def queued_job(**overrides):
    job = {
        "id": "test_job",
        "exp_id": "test_job",
        "command": "true",
        "priority": "medium",
        "status": "queued",
        "gpu_type": "a100",
        "gpus": 1,
        "partition": "",
        "node": "",
        "exclude_nodes": [],
        "allow_slurm_pending": False,
        "mem": "16G",
        "cpus": 4,
        "tmux_session": "",
        "slurm_job_name": "test_job",
        "log_path": "runs/test_job/slurm.log",
        "result_path": "",
        "shell_mode": "login",
        "owner_agent": "test",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
        "notes": "",
    }
    job.update(overrides)
    return job


def scheduler_status():
    return {
        "remaining_user_slots": 8,
        "available_gpus": {"a100": 1, "a4000": 1, "a5000": 1, "a6000": 4},
        "available_node_gpus": {
            "node01": {"gpu_type": "a100", "available": 1, "capacity": 8, "allocated": 0},
            "node02": {"gpu_type": "a6000", "available": 1, "capacity": 10, "allocated": 0},
            "node03": {"gpu_type": "a6000", "available": 1, "capacity": 10, "allocated": 0},
            "node06": {"gpu_type": "a6000", "available": 1, "capacity": 8, "allocated": 0},
            "node07": {"gpu_type": "a6000", "available": 1, "capacity": 8, "allocated": 0},
        },
    }


class GpuSchedulerMemoryCapTest(unittest.TestCase):
    def test_plan_rejects_mem_over_single_gpu_node_cap(self) -> None:
        queue = {"jobs": [queued_job(gpu_type="a100", mem="96G")]}
        with self.assertRaisesRegex(HarnessError, "node01.*60G.*96G"):
            plan_jobs(queue, scheduler_status())

    def test_add_rejects_impossible_mem_request(self) -> None:
        with self.assertRaisesRegex(HarnessError, "node01.*60G"):
            validate_add_memory_request(queued_job(gpu_type="a100", mem="96G"))

    def test_plan_allows_mem_at_single_gpu_node_cap(self) -> None:
        queue = {"jobs": [queued_job(gpu_type="a100", mem="60G")]}
        planned = plan_jobs(queue, scheduler_status())
        self.assertEqual(len(planned), 1)
        self.assertEqual(planned[0]["node"], "node01")
        self.assertEqual(planned[0]["mem"], "60G")

    def test_plan_picks_a6000_node_that_satisfies_requested_memory(self) -> None:
        queue = {"jobs": [queued_job(gpu_type="a6000", mem="60G")]}
        planned = plan_jobs(queue, scheduler_status())
        self.assertEqual(len(planned), 1)
        self.assertEqual(planned[0]["node"], "node07")

    def test_cpu_only_auto_tries_larger_node_caps(self) -> None:
        queue = {"jobs": [queued_job(gpu_type="auto", gpus=0, mem="60G")]}
        planned = plan_jobs(queue, scheduler_status())
        self.assertEqual(len(planned), 1)
        self.assertEqual(planned[0]["gpu_type"], "a6000")
        self.assertEqual(planned[0]["node"], "node07")

    def test_sbatch_args_rejects_manual_over_cap_job(self) -> None:
        job = queued_job(gpu_type="a100", partition="a100", node="node01", mem="96G")
        with self.assertRaisesRegex(HarnessError, "node01.*60G.*96G"):
            sbatch_args(REPO, job)

    def test_pending_a6000_job_can_exclude_node_without_nodelist(self) -> None:
        status = scheduler_status()
        status["available_gpus"]["a6000"] = 0
        for node in ("node02", "node03", "node06", "node07"):
            status["available_node_gpus"][node]["available"] = 0
        queue = {
            "jobs": [
                queued_job(
                    gpu_type="a6000",
                    partition="a6000",
                    mem="30G",
                    exclude_nodes=["node03"],
                    allow_slurm_pending=True,
                )
            ]
        }
        planned = plan_jobs(queue, status)
        self.assertEqual(len(planned), 1)
        self.assertEqual(planned[0]["node"], "")
        args = sbatch_args(REPO, planned[0])
        self.assertIn("--exclude=node03", args)
        self.assertFalse(any(value.startswith("--nodelist=") for value in args))

    def test_normal_planning_never_selects_excluded_node(self) -> None:
        status = scheduler_status()
        status["available_node_gpus"]["node03"]["available"] = 8
        queue = {"jobs": [queued_job(gpu_type="a6000", exclude_nodes=["node03"])]}
        planned = plan_jobs(queue, status)
        self.assertEqual(len(planned), 1)
        self.assertNotEqual(planned[0]["node"], "node03")


if __name__ == "__main__":
    unittest.main()
