"""Redistribute only the frozen unstarted tail; preserve the native generation path."""
import argparse
import gc
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import generate_once, load_runtime, prepare_example, runtime_environment
from visual_reasoning.stage8a.protocol import generation_parameters, runtime_rank, termination_status
from visual_reasoning.stage8a.native_handoff import claim_destination, boundary_complete


def save(path, value):
    assert not path.exists(), path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config_path = Path(args.config)
    config = json.loads(config_path.read_text())
    rank = runtime_rank(os.environ, visible_devices=torch.cuda.device_count(), allocation=config["slurm_allocation"])
    torch.cuda.set_device(0)
    out = Path(config["output_dir"]) / f"worker{rank}"
    out.mkdir(parents=True, exist_ok=True)
    if (out / "completed.json").exists():
        raise FileExistsError("This frozen worker already completed")
    manifest = Path(config["manifest"])
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == config["manifest_sha256"]
    for path, expected in config["source_sha256"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
    assert json.loads(Path(config["model_integrity"]).read_text())["status"] == "PASS_COMPLETE_LOCAL_MODEL"
    handoff_path = Path(config["handoff"])
    assert hashlib.sha256(handoff_path.read_bytes()).hexdigest() == config["handoff_sha256"]
    handoff = json.loads(handoff_path.read_text())
    assert hashlib.sha256(Path(handoff["original_config"]).read_bytes()).hexdigest() == handoff["original_config_sha256"]
    gpu_uuid = str(torch.cuda.get_device_properties(0).uuid)
    assert gpu_uuid == config["expected_gpu_uuid"][str(rank)], "Slurm binding changed; do not overlap the active worker"
    if rank == 0:
        print(json.dumps(dict(event="waiting_for_safe_boundary",base_id=handoff["current_untouched"])),flush=True)
        while not boundary_complete(handoff):
            time.sleep(2)
    all_records = {r["base_id"]:r for r in [json.loads(s) for s in manifest.read_text().splitlines() if s.strip()]}
    records = [all_records[b] for b in handoff["assignments"][str(rank)]]
    dataset = {str(r["sample_index"]):r for r in load_mathverse_rows(Path(config["dataset_root"]))}
    processor, model = load_runtime(Path(config["model_checkpoint"]), device="cuda:0")
    env = runtime_environment(Path(config["model_checkpoint"]), model, config["max_new_tokens"])
    assert (env["language_layers"], env["attention_heads"], env["kv_heads"]) == (28,16,8)
    assert "A6000" in env["gpu_name"]
    assert str(next(model.parameters()).dtype) == "torch.bfloat16"
    env.update(rank=rank, slurm_job_id=os.environ["SLURM_JOB_ID"], slurm_step_id=os.environ.get("SLURM_STEP_ID"), gpu_uuid=str(torch.cuda.get_device_properties(0).uuid), generation_parameters=generation_parameters(), seed=config["seed"], config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest())
    save(out / "environment.json", env)
    eos = model.generation_config.eos_token_id
    eos_ids = [eos] if isinstance(eos,int) else list(eos)
    results=[]
    for order, record in enumerate(records):
        row=dataset[record["example_id"]]
        assert str(row["problem_index"]) == record["base_id"]
        image=Path(record["image"])
        assert hashlib.sha256(image.read_bytes()).hexdigest() == record["image_sha256"]
        dest=Path(handoff["canonical_output_dir"]) / "worker0" / "examples" / record["base_id"]
        claim_destination(dest, handoff_path)
        prepared, metadata, actual_image = prepare_example(processor,row,Path(config["dataset_root"]),"cuda:0")
        assert actual_image.resolve() == image.resolve()
        save(dest / "input.json", metadata)
        save(dest / "manifest_row.json", record)
        if order == 0:
            repeated=[]
            for _ in range(2):
                repeated.append(generate_once(model,processor,prepared,128,recorder=None,generation_kwargs=generation_parameters(),seed=config["seed"],collect_predictive_metrics=False))
            exact=repeated[0]["generated_token_ids"] == repeated[1]["generated_token_ids"]
            save(out / "native_repeat128.json", {"pass":exact,"base_id":record["base_id"],"token_ids":[r["generated_token_ids"] for r in repeated],"scope":"Native cached generation repeat; streaming/intervention checks remain separate."})
            assert exact, "Native repeatability failed"
            del repeated
        print(json.dumps({"event":"start_example","rank":rank,"base_id":record["base_id"],"at":datetime.now(timezone.utc).isoformat()}),flush=True)
        generated=generate_once(model,processor,prepared,config["max_new_tokens"],recorder=None,generation_kwargs=generation_parameters(),seed=config["seed"],collect_predictive_metrics=False)
        status=termination_status(generated["generated_token_ids"],eos_ids=eos_ids,cap=config["max_new_tokens"])
        tokens=generated.pop("token_rows")
        generated.pop("attention_arrays",None)
        save(dest / "generation.json", {**generated,**status,"seed":config["seed"],"model_revision":config["model_revision"],"instrumentation":False})
        with (dest / "tokens.jsonl").open("x") as f:
            for token in tokens:f.write(json.dumps(token,ensure_ascii=False)+"\n")
        result={"base_id":record["base_id"],"family_id":record["family_id"],"example_id":record["example_id"],"rank":rank,"artifact_dir":str(dest),**status,"finished_at":datetime.now(timezone.utc).isoformat()}
        save(dest / "result.json",result)
        results.append(result)
        with (out / "progress.jsonl").open("a") as f:f.write(json.dumps(result)+"\n")
        print(json.dumps({"event":"complete_example",**result}),flush=True)
        del prepared,generated,tokens
        gc.collect();torch.cuda.empty_cache()
    save(out / "completed.json",{"completed":True,"rank":rank,"examples":len(results),"normal_eos":sum(r["normal_eos"] for r in results),"results":results,"finished_at":datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    main()
