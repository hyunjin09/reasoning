"""One Slurm-bound native worker; technical gate precedes the census batch."""
import argparse
import gc
import hashlib
import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import torch

from visual_reasoning.stage0.modeling import generate_once, load_runtime, runtime_environment
from visual_reasoning.stage8a.protocol import termination_status
from visual_reasoning.stage8b.single_execution import runtime_rank, assigned_rows, NativeProgress
from visual_reasoning.stage8b.v2_protocol import generation_parameters, prepared_input, completion_status
from visual_reasoning.stage8b.passive import PassiveRecorder


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,value):
    if path.exists():raise FileExistsError(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    tmp.replace(path)


def technical_check(model,processor,prepared,metadata,probe,seed):
    logs=[]
    def capture(_module,_args,output):
        raw=output[0,-1].detach().float().cpu().numpy().tobytes()
        logs.append(hashlib.sha256(raw).hexdigest())
    handle=model.lm_head.register_forward_hook(capture)
    try:
        baseline=generate_once(model,processor,prepared,128,recorder=None,generation_kwargs=generation_parameters(),seed=seed,collect_predictive_metrics=False)
        native_hashes=list(logs);logs.clear()
        with NativeProgress(model,"technical_preflight"), PassiveRecorder(visual=metadata["visual_token_indices"],prompt_length=metadata["prompt_token_count"],model=probe,reference_check=True) as observer:
            observed=generate_once(model,processor,prepared,128,recorder=None,generation_kwargs=generation_parameters(),seed=seed,collect_predictive_metrics=False)
        assert baseline["generated_token_ids"]==observed["generated_token_ids"],"Observer changed native tokens"
        assert native_hashes==logs,"Observer changed native raw logits"
        arrays=observer.arrays()
        assert len(arrays["retrieval_score"])==len(observed["generated_token_ids"])
        assert np.isnan(arrays["retrieval_score"][0]) and np.isfinite(arrays["retrieval_score"][1:]).all()
        assert observer.reference_rows==4*(len(observed["generated_token_ids"])-1)
        return dict(pass_checks=True,tokens=len(logs),raw_logit_sha256=logs,
            native_token_ids=baseline["generated_token_ids"],observer_tokens_identical=True,
            observer_logits_identical=True,stage8a_per_head_statistics_exact=True,
            reference_layer_queries=observer.reference_rows,
            native_runtime=baseline["runtime"],observed_runtime=observed["runtime"],
            first_prediction_R_unavailable=True)
    finally:
        handle.remove()


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",required=True);ap.add_argument("--phase",choices=["preflight","census"],required=True)
    args=ap.parse_args();cp=Path(args.config);cfg=json.loads(cp.read_text())
    assert cfg["generation_parameters"]==generation_parameters() and cfg["presence_penalty"]==0.0
    allocation=os.environ.get("SLURM_JOB_ID")
    assert allocation and socket.gethostname().split('.')[0]=="node02","Only scheduled node02 execution is authorized"
    rank=runtime_rank(os.environ,visible_devices=torch.cuda.device_count(),allocation=allocation)
    torch.cuda.set_device(0)
    for path,expected in cfg["source_sha256"].items():assert digest(path)==expected,path
    manifest=Path(cfg["manifest"]);assert digest(manifest)==cfg["manifest_sha256"]
    rows=assigned_rows([json.loads(line) for line in manifest.read_text().splitlines()], rank=rank)
    output=Path(cfg["output_dir"]);worker=output/args.phase/f"worker{rank}"
    assert not (worker/"environment.json").exists(),"Immutable run already started; use explicit continuation"
    freeze=Path(cfg["detector_freeze"]);assert digest(freeze)==cfg["detector_freeze_sha256"]
    rule=json.loads(freeze.read_text());assert digest(rule["retrieval"]["models"])==rule["retrieval"]["models_sha256"]
    fitted=joblib.load(rule["retrieval"]["models"])["joint"]
    assert fitted["spec"]==rule["retrieval"]["spec"] and fitted["threshold"]==rule["retrieval"]["tau_R"]
    if args.phase=="census":
        for i in range(1):assert json.loads((output/"preflight"/f"worker{i}"/"checks.json").read_text())["pass_checks"]
    processor,model=load_runtime(Path(cfg["model_checkpoint"]),device="cuda:0")
    assert str(next(model.parameters()).dtype)=="torch.bfloat16"
    env=runtime_environment(Path(cfg["model_checkpoint"]),model,cfg["max_new_tokens"])
    assert (env["language_layers"],env["attention_heads"],env["kv_heads"])==(28,16,8)
    assert "6000" in env["gpu_name"]
    env.update(rank=rank,slurm_job_id=allocation,slurm_step_id=os.environ.get("SLURM_STEP_ID"),
        hostname=socket.gethostname(),gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),
        config_sha256=digest(cp),generation_parameters=generation_parameters(),presence_penalty=0.0,seed=cfg["seed"],tmux_used=False)
    save(worker/"environment.json",env)
    if args.phase=="preflight":
        prepared,metadata=prepared_input(processor,rows[0])
        print(json.dumps(dict(event="technical_start",rank=rank,item_id=rows[0]["item_id"])),flush=True)
        result=technical_check(model,processor,prepared,metadata,fitted["model"],cfg["seed"])
        result.update(item_id=rows[0]["item_id"],rank=rank,at=datetime.now(timezone.utc).isoformat())
        save(worker/"checks.json",result)
        print(json.dumps(dict(event="technical_pass",rank=rank,tokens=result["tokens"],reference_rows=result["reference_layer_queries"])),flush=True)
        return
    eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
    completed=[]
    for row in rows:
        dest=output/"examples"/row["item_id"];assert not dest.exists(),dest
        prepared,metadata=prepared_input(processor,row)
        save(dest/"input.json",metadata);save(dest/"manifest_row.json",row)
        print(json.dumps(dict(event="start_example",rank=rank,item_id=row["item_id"],at=datetime.now(timezone.utc).isoformat())),flush=True)
        with NativeProgress(model,row["item_id"]), PassiveRecorder(visual=metadata["visual_token_indices"],prompt_length=metadata["prompt_token_count"],model=fitted["model"]) as observer:
            generated=generate_once(model,processor,prepared,cfg["max_new_tokens"],recorder=None,
                generation_kwargs=generation_parameters(),seed=cfg["seed"],collect_predictive_metrics=False)
        arrays=observer.arrays();assert len(arrays["features"])==len(generated["generated_token_ids"])
        assert np.isfinite(arrays["retrieval_score"][1:]).all()
        tokens=generated.pop("token_rows");generated.pop("attention_arrays",None)
        status=termination_status(generated["generated_token_ids"],eos_ids=eos,cap=cfg["max_new_tokens"])
        completion=completion_status(generated["raw_decoded_response"],normal_eos=status["normal_eos"],at_length_cap=status["at_length_cap"],tokens=status["tokens"])
        status.update(completion)
        save(dest/"generation.json",dict(generated,**status,seed=cfg["seed"],model_revision=cfg["model_revision"],instrumentation="passive original-eager observation"))
        with (dest/"tokens.jsonl").open("x") as stream:
            for token in tokens:stream.write(json.dumps(token,ensure_ascii=False)+"\n")
        np.savez_compressed(dest/"passive.npz",**arrays)
        result=dict(item_id=row["item_id"],family_id=row["family_id"],rank=rank,seed=cfg["seed"],**status,
            artifact_dir=str(dest),finished_at=datetime.now(timezone.utc).isoformat(),
            runtime=generated["runtime"],observation_rows=len(arrays["features"]),
            provenance_sha256={str(dest/name):digest(dest/name) for name in ["input.json","manifest_row.json","generation.json","tokens.jsonl","passive.npz"]})
        save(dest/"result.json",result);completed.append(row["item_id"])
        with (worker/"progress.jsonl").open("a") as stream:stream.write(json.dumps(result)+"\n")
        # No scientific scores displayed before semantic transfer annotation.
        print(json.dumps(dict(event="complete_example",rank=rank,item_id=row["item_id"],tokens=status["tokens"],normal_eos=status["normal_eos"])),flush=True)
        del prepared,generated,tokens,observer,arrays;gc.collect();torch.cuda.empty_cache()
    save(worker/"completed.json",dict(completed=True,items=completed,rank=rank,at=datetime.now(timezone.utc).isoformat()))


if __name__=="__main__":main()
