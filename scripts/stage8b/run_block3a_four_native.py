"""Block3A fixed item/seed rollouts continuation on four Slurm-bound node02 GPUs."""
import argparse
import gc
import hashlib
import json
import os
import socket
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import torch

from visual_reasoning.stage0.modeling import generate_once, load_runtime, runtime_environment
from visual_reasoning.stage8a.protocol import termination_status
from visual_reasoning.stage8b.single_execution import NativeProgress
from visual_reasoning.stage8b.block3a_resume import runtime_rank
from scripts.stage8b.run_native_v2_shared import technical_check
from visual_reasoning.stage8b.v2_protocol import generation_parameters, prepared_input, completion_status
from visual_reasoning.stage8b.passive import PassiveRecorder


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def save(path,value):
    if path.exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    tmp.replace(path)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",required=True);ap.add_argument("--phase",choices=["census"],required=True)
    ap.add_argument("--lane",type=int,required=True);ap.add_argument("--workers-per-gpu",type=int,choices=[1,2],required=True)
    args=ap.parse_args();cp=Path(args.config);cfg=json.loads(cp.read_text())
    assert cfg["generation_parameters"]==generation_parameters() and cfg["presence_penalty"]==0.0
    allocation=os.environ.get("SLURM_JOB_ID")
    assert allocation and socket.gethostname().split('.')[0]=="node02","Only scheduled node02 execution is authorized"
    rank=runtime_rank(os.environ,visible_devices=torch.cuda.device_count(),allocation=allocation,lane=args.lane,workers_per_gpu=args.workers_per_gpu)
    workers=4*args.workers_per_gpu
    torch.cuda.set_device(0)
    for path,expected in cfg["source_sha256"].items():assert digest(path)==expected,path
    assert cfg["worker_count"]==8 and cfg["gpus"]==4
    for path,expected in cfg["reused_receipt_sha256"].items():assert digest(path)==expected,path
    manifest=Path(cfg["manifest"]);assert digest(manifest)==cfg["manifest_sha256"]
    rows=[r for r in map(json.loads,manifest.read_text().splitlines()) if r["assigned_rank"]==rank]
    output=Path(cfg["output_dir"]);worker=output/args.phase/f"worker{rank}"
    assert not (worker/"environment.json").exists(),"Immutable run already started; use explicit continuation"
    freeze=Path(cfg["detector_freeze"]);assert digest(freeze)==cfg["detector_freeze_sha256"]
    rule=json.loads(freeze.read_text());assert digest(rule["retrieval"]["models"])==rule["retrieval"]["models_sha256"]
    fitted=joblib.load(rule["retrieval"]["models"])["joint"]
    assert fitted["spec"]==rule["retrieval"]["spec"] and fitted["threshold"]==rule["retrieval"]["tau_R"]
    decision=json.loads(Path(cfg["layout_decision"]).read_text())
    assert decision["workers_per_gpu"]==args.workers_per_gpu==2 and decision["exact_parity"]
    processor,model=load_runtime(Path(cfg["model_checkpoint"]),device="cuda:0")
    assert str(next(model.parameters()).dtype)=="torch.bfloat16"
    env=runtime_environment(Path(cfg["model_checkpoint"]),model,cfg["max_new_tokens"])
    assert (env["language_layers"],env["attention_heads"],env["kv_heads"])==(28,16,8)
    assert "6000" in env["gpu_name"]
    env.update(rank=rank,slurm_job_id=allocation,slurm_step_id=os.environ.get("SLURM_STEP_ID"),
        hostname=socket.gethostname(),gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),
        config_sha256=digest(cp),generation_parameters=generation_parameters(),presence_penalty=0.0,seeds=cfg["seeds"],tmux_used=False)
    env.update(workers_per_gpu=args.workers_per_gpu,slurm_parent_rank=int(os.environ["SLURM_PROCID"]))
    save(worker/"environment.json",env)
    # Same-node per-GPU layout was measured; validate every new worker and GPU.
    prepared,metadata=prepared_input(processor,cfg["technical_probe_row"])
    check=technical_check(model,processor,prepared,metadata,fitted["model"],cfg["seed"])
    reference=json.loads(Path(cfg["technical_reference"]).read_text())
    for key in ["native_token_ids","raw_logit_sha256"]:
        assert check[key]==reference[key], f"Continuation differs from preserved technical reference: {key}"
    check.update(rank=rank,reference_exact=True,reference_sha256=digest(cfg["technical_reference"]))
    save(worker/"checks.json",check)
    print(json.dumps(dict(event="technical_pass",rank=rank,tokens=check["tokens"],reference_exact=True)),flush=True)
    del prepared;gc.collect();torch.cuda.empty_cache()
    deadline=time.monotonic()+300
    while not all((output/"census"/f"worker{i}"/"checks.json").exists() for i in range(workers)):
        if time.monotonic()>deadline:raise TimeoutError("Eight-worker parity barrier timed out")
        time.sleep(.2)
    environments=[json.loads((output/"census"/f"worker{i}"/"environment.json").read_text()) for i in range(workers)]
    counts=Counter(e["gpu_uuid"] for e in environments)
    assert len(counts)==4 and set(counts.values())=={2}
    assert all(e["slurm_job_id"]==allocation and e["hostname"].split('.')[0]=="node02" for e in environments)
    assert decision["conservative_double_reserved_gib"]<=.9*min(e["gpu_total_memory_bytes"]/2**30 for e in environments)
    for i in range(workers):
        peer=json.loads((output/"census"/f"worker{i}"/"checks.json").read_text())
        assert peer["pass_checks"] and peer["reference_exact"]
    eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
    completed=[]
    for row in rows:
        dest=output/"examples"/row["task_id"];assert not dest.exists(),dest
        prepared,metadata=prepared_input(processor,row)
        assert digest(row["reference_input"])==row["reference_input_sha256"]
        native_metadata=json.loads(Path(row["reference_input"]).read_text())
        for key in ["prompt_ids_sha256","pixel_values_sha256","visual_token_indices","prompt_token_count","image_grid_thw","preprocessing"]:
            assert metadata[key]==native_metadata[key], key
        save(dest/"input.json",metadata);save(dest/"manifest_row.json",row)
        print(json.dumps(dict(event="start_example",rank=rank,item_id=row["item_id"],task_id=row["task_id"],seed=row["seed"],at=datetime.now(timezone.utc).isoformat())),flush=True)
        with NativeProgress(model,row["task_id"]), PassiveRecorder(visual=metadata["visual_token_indices"],prompt_length=metadata["prompt_token_count"],model=fitted["model"]) as observer:
            generated=generate_once(model,processor,prepared,cfg["max_new_tokens"],recorder=None,
                generation_kwargs=generation_parameters(),seed=row["seed"],collect_predictive_metrics=False)
        arrays=observer.arrays();assert len(arrays["features"])==len(generated["generated_token_ids"])
        assert np.isfinite(arrays["retrieval_score"][1:]).all()
        tokens=generated.pop("token_rows");generated.pop("attention_arrays",None)
        status=termination_status(generated["generated_token_ids"],eos_ids=eos,cap=cfg["max_new_tokens"])
        completion=completion_status(generated["raw_decoded_response"],normal_eos=status["normal_eos"],at_length_cap=status["at_length_cap"],tokens=status["tokens"])
        status.update(completion)
        save(dest/"generation.json",dict(generated,**status,seed=row["seed"],model_revision=cfg["model_revision"],instrumentation="passive original-eager observation"))
        with (dest/"tokens.jsonl").open("x") as stream:
            for token in tokens:stream.write(json.dumps(token,ensure_ascii=False)+"\n")
        np.savez_compressed(dest/"passive.npz",**arrays)
        result=dict(item_id=row["item_id"],family_id=row["family_id"],rank=rank,seed=row["seed"],task_id=row["task_id"],**status,
            artifact_dir=str(dest),finished_at=datetime.now(timezone.utc).isoformat(),
            runtime=generated["runtime"],observation_rows=len(arrays["features"]),
            provenance_sha256={str(dest/name):digest(dest/name) for name in ["input.json","manifest_row.json","generation.json","tokens.jsonl","passive.npz"]})
        save(dest/"result.json",result);completed.append(row["task_id"])
        with (worker/"progress.jsonl").open("a") as stream:stream.write(json.dumps(result)+"\n")
        # No scientific scores displayed before semantic transfer annotation.
        print(json.dumps(dict(event="complete_example",rank=rank,item_id=row["item_id"],task_id=row["task_id"],seed=row["seed"],tokens=status["tokens"],normal_eos=status["normal_eos"])),flush=True)
        del prepared,generated,tokens,observer,arrays;gc.collect();torch.cuda.empty_cache()
    save(worker/"completed.json",dict(completed=True,items=completed,rank=rank,at=datetime.now(timezone.utc).isoformat()))


if __name__=="__main__":main()
