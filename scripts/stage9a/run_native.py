"""Slurm-only arm-aware native runner; frozen Stage8 instrumentation is reused."""
import argparse
import gc
import json
import os
import socket
import traceback
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import torch

from scripts.stage8c.prepare import save, sha
from scripts.stage8b.run_native_v2_shared import technical_check
from visual_reasoning.stage0.modeling import generate_once, load_runtime, runtime_environment
from visual_reasoning.stage8a.protocol import termination_status
from visual_reasoning.stage8b.passive import PassiveRecorder
from visual_reasoning.stage8b.single_execution import NativeProgress
from visual_reasoning.stage8b.v2_protocol import generation_parameters, prepared_input
from visual_reasoning.stage9a.protocol import ARMS, reasoning_span


def now():
    return datetime.now(timezone.utc).isoformat()


def inputs(processor, row):
    assert "answer" not in row and "ground_truth_answer" not in row
    prepared, meta = prepared_input(processor, dict(row, answer=None))
    assert meta.pop("ground_truth_answer") is None
    return prepared, meta


def claim(rows, root, arm, worker):
    for row in rows:
        if row["arm"] != arm:
            continue
        path = root/"native"/"claims"/row["task_id"]
        try:
            path.mkdir(parents=False)
        except FileExistsError:
            continue
        save(path/"owner.json",dict(worker=worker,slurm_job_id=os.environ["SLURM_JOB_ID"],at=now()))
        return row
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config",default="outputs/stage9a/v1/stage9a_generation_config.json")
    ap.add_argument("--preflight",action="store_true")
    ap.add_argument("--preferred",choices=ARMS,default="thinking")
    args = ap.parse_args()
    cp=Path(args.config);cfg=json.loads(cp.read_text());root=Path(cfg["root"])
    assert os.environ.get("SLURM_JOB_ID"), "GPU computation requires Slurm"
    assert socket.gethostname().split(".")[0] in cfg["allowed_nodes"]
    assert torch.cuda.device_count()==1, "Request a single GPU for each independent worker"
    torch.cuda.set_device(0)
    assert cfg["generation_parameters"]==generation_parameters()
    for path,expected in cfg["source_sha256"].items():
        assert sha(path)==expected, path
    assert sha(cfg["native_tasks"])==cfg["native_tasks_sha256"]
    tasks=json.loads(Path(cfg["native_tasks"]).read_text())["rows"]
    assert len(tasks)==384 and len({r["task_id"] for r in tasks})==384
    assert sha(cfg["detector_freeze"])==cfg["detector_freeze_sha256"]
    rule=json.loads(Path(cfg["detector_freeze"]).read_text())
    assert sha(rule["retrieval"]["models"])==rule["retrieval"]["models_sha256"]
    fitted=joblib.load(rule["retrieval"]["models"])["joint"]
    assert fitted["spec"]==rule["retrieval"]["spec"] and fitted["threshold"]==cfg["threshold"]
    worker="slurm_"+os.environ["SLURM_JOB_ID"]
    worker_dir=root/"native"/"workers"/worker
    if not args.preflight:
        gate=json.loads((root/"audit/preflight/complete.json").read_text())
        assert gate["pass"] and gate["config_sha256"]==sha(cp)
        for path,expected in gate["checks_sha256"].items():
            assert sha(path)==expected
        (root/"native/claims").mkdir(parents=True,exist_ok=True)
    model=processor=None;current=None;completed=[]
    order=list(ARMS) if args.preflight else [args.preferred]+[a for a in ARMS if a!=args.preferred]
    preflight_paths=[]
    for arm in order:
        row=next(r for r in tasks if r["arm"]==arm) if args.preflight else claim(tasks,root,arm,worker)
        if row is None:
            continue
        model_key="thinking" if arm=="thinking" else "instruct"
        if current!=model_key:
            if model is not None:
                del model,processor;gc.collect();torch.cuda.empty_cache()
            info=cfg["models"][model_key];checkpoint=Path(info["checkpoint"])
            for filename,expected in info["files_sha256"].items():
                assert sha(checkpoint/filename)==expected, filename
            processor,model=load_runtime(checkpoint,"cuda:0");current=model_key
            assert str(next(model.parameters()).dtype)=="torch.bfloat16"
            env=runtime_environment(checkpoint,model,cfg["max_new_tokens"])
            assert (env["language_layers"],env["attention_heads"],env["kv_heads"])==(28,16,8)
            assert "6000" in env["gpu_name"]
            env.update(at=now(),slurm_job_id=os.environ["SLURM_JOB_ID"],hostname=socket.gethostname(),
                       gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),config_sha256=sha(cp),
                       model_revision=info["revision"],tmux_used=False,preflight=args.preflight)
            save(worker_dir/(model_key+"_environment.json"),env)
        if args.preflight:
            prepared,metadata=inputs(processor,row)
            save(root/"audit/preflight"/(arm+"_input.json"),metadata)
            print(json.dumps(dict(event="preflight_start",arm=arm,at=now())),flush=True)
            result=technical_check(model,processor,prepared,metadata,fitted["model"],row["seed"])
            result.update(arm=arm,task_id=row["task_id"],at=now())
            dest=root/"audit/preflight"/(arm+"_checks.json");save(dest,result);preflight_paths.append(dest)
            print(json.dumps(dict(event="preflight_pass",arm=arm,tokens=result["tokens"])),flush=True)
            del prepared
            continue
        eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
        while row is not None:
            dest=root/"native/examples"/row["task_id"]
            assert not dest.exists(), "Partial attempts require an explicit continuation"
            try:
                prepared,metadata=inputs(processor,row)
                save(dest/"input.json",metadata);save(dest/"manifest_row.json",row)
                print(json.dumps(dict(event="start_example",arm=arm,task_id=row["task_id"],at=now())),flush=True)
                with NativeProgress(model,row["task_id"]), PassiveRecorder(
                    visual=metadata["visual_token_indices"],prompt_length=metadata["prompt_token_count"],model=fitted["model"]) as observer:
                    generated=generate_once(model,processor,prepared,cfg["max_new_tokens"],recorder=None,
                        generation_kwargs=generation_parameters(),seed=row["seed"],collect_predictive_metrics=False)
                arrays=observer.arrays()
                assert len(arrays["features"])==len(generated["generated_token_ids"])
                assert np.isfinite(arrays["retrieval_score"][1:]).all()
                tokens=generated.pop("token_rows");generated.pop("attention_arrays",None)
                assert generated["incremental_decode_alignment"]
                status=termination_status(generated["generated_token_ids"],eos_ids=eos,cap=cfg["max_new_tokens"])
                status["completion"]=("normal completed" if status["normal_eos"] and (arm!="thinking" or "</think>" in generated["raw_decoded_response"])
                    else "capped" if status["at_length_cap"] else "other abnormal stop")
                status["reasoning_span"]=reasoning_span(tokens,arm)
                save(dest/"generation.json",dict(generated,**status,arm=arm,seed=row["seed"],model_revision=cfg["models"][model_key]["revision"]))
                with (dest/"tokens.jsonl").open("x") as stream:
                    for token in tokens:
                        stream.write(json.dumps(token,ensure_ascii=False)+"\n")
                np.savez_compressed(dest/"passive.npz",**arrays)
                result=dict(task_id=row["task_id"],item_id=row["item_id"],family_id=row["family_id"],arm=arm,
                    **status,finished_at=now(),runtime=generated["runtime"],worker=worker,
                    artifact_dir=str(dest),config_sha256=sha(cp),
                    provenance_sha256={str(dest/name):sha(dest/name) for name in ["input.json","manifest_row.json","generation.json","tokens.jsonl","passive.npz"]})
                save(dest/"result.json",result);completed.append(row["task_id"])
                with (worker_dir/"progress.jsonl").open("a") as stream:
                    stream.write(json.dumps(result)+"\n")
                print(json.dumps(dict(event="complete_example",task_id=row["task_id"],tokens=status["tokens"],normal_eos=status["normal_eos"],elapsed_seconds=generated["runtime"]["elapsed_seconds"],at=now())),flush=True)
                del prepared,generated,tokens,observer,arrays;gc.collect();torch.cuda.empty_cache()
            except Exception as exc:
                save(dest/"failure.json",dict(at=now(),error=repr(exc),traceback=traceback.format_exc(),worker=worker,task_id=row["task_id"]))
                raise
            row=claim(tasks,root,arm,worker)
    if args.preflight:
        a1=json.loads((root/"audit/preflight/instruct_direct_input.json").read_text())
        a2=json.loads((root/"audit/preflight/instruct_cot_input.json").read_text())
        a3=json.loads((root/"audit/preflight/thinking_input.json").read_text())
        assert a1["pixel_values_sha256"]==a2["pixel_values_sha256"]==a3["pixel_values_sha256"]
        assert a1["chat_prompt"].endswith("<|im_start|>assistant\n")
        assert a3["chat_prompt"].endswith("<|im_start|>assistant\n<think>\n")
        save(root/"audit/preflight/complete.json",{"pass":True,"at":now(),"config_sha256":sha(cp),
            "checks_sha256":{str(p):sha(p) for p in preflight_paths},"native_template_difference_recorded":True,"image_preprocessing_identical":True})
    save(worker_dir/"completed.json",dict(at=now(),completed=completed,preflight=args.preflight))


if __name__=="__main__":
    main()
