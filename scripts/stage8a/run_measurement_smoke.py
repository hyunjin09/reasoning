"""Actual-model validation of main measurement extensions on calibration only."""
import argparse
import json
import os
from pathlib import Path

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage8a.protocol import runtime_rank
from scripts.stage8a.run_measurement import digest, measure_base, save


@torch.inference_mode()
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--config",required=True)
    args=parser.parse_args()
    config_path=Path(args.config)
    config=json.loads(config_path.read_text())
    rank=runtime_rank(os.environ,visible_devices=torch.cuda.device_count(),allocation=config["slurm_allocation"])
    torch.cuda.set_device(0)
    for p,h in config["source_sha256"].items():
        assert digest(p)==h,p
    assert digest(config["requests"])==config["requests_sha256"]
    requests=json.loads(Path(config["requests"]).read_text())["requests"]
    assert len(requests)==2 and all(r["split"]=="calibration" for r in requests)
    out=Path(config["output_dir"])/f"worker{rank}"
    assert not out.exists()
    processor,model=load_runtime(Path(config["model_checkpoint"]),"cuda:0")
    env=runtime_environment(Path(config["model_checkpoint"]),model,40960)
    env.update(rank=rank,slurm_job_id=os.environ["SLURM_JOB_ID"],slurm_step_id=os.environ.get("SLURM_STEP_ID"),
        gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),config_sha256=digest(config_path))
    save(out/"environment.json",env)
    rows={str(r["sample_index"]):r for r in load_mathverse_rows(Path(config["dataset_root"]))}
    request=requests[rank]
    result=measure_base(model,processor,rows[request["example_id"]],[request],config,out)
    event=json.loads((out/"events"/(request["event_id"]+".json")).read_text())
    assert event["capture_exact"] and event["self_noop_exact"]
    assert len(event["shallow_state"])==2048
    assert event["strict_past_query_count"]==32
    assert len(event["features"])==9
    assert event["first_query_js"]["visual_off"]>=0
    save(out/"completed.json",dict(completed=True,rank=rank,base=result,capture_and_self_exact=True,
        shallow_dimensions=2048,temporal_query_count=32,scope="Calibration-only technical extension test; no main-cohort score"))
    print(json.dumps(dict(completed=True,rank=rank,base_id=request["base_id"])),flush=True)


if __name__=="__main__":
    main()
