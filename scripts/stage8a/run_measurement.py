"""Extract passive R and causal/native G on frozen reviewed main events."""
import argparse
import gc
import gzip
import hashlib
import json
import os
import time
from collections import defaultdict
from pathlib import Path

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, prepare_example, runtime_environment
from visual_reasoning.stage3c9.streaming import advance_streaming_state, clone_streaming_state, prefill_streaming_state
from visual_reasoning.stage8a.instrumentation import AttentionAssay, js_divergence
from visual_reasoning.stage8a.measurement import MeasurementAssay, feature_vector
from visual_reasoning.stage8a.protocol import runtime_rank
from visual_reasoning.stage8a.schedule import query_schedule


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    assert not path.exists(),path
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False,ensure_ascii=False)+"\n")
    temporary.replace(path)


def advance(model,state,ids,seed):
    return advance_streaming_state(model=model,state=state,token_ids=ids,seed=seed,chunk_size=1)


def branch(model,checkpoint,token,seed,assay=None):
    state = clone_streaming_state(checkpoint)
    if assay is None:
        advance(model,state,[token],seed)
    else:
        with assay:
            advance(model,state,[token],seed)
    return state


@torch.inference_mode()
def measure_base(model,processor,row,requests,config,output):
    started = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    request_by_id = {r["event_id"]:r for r in requests}
    native = Path(requests[0]["native_dir"])
    tokens = json.loads((native/"generation.json").read_text())["generated_token_ids"]
    for r in requests:
        assert r["native_dir"] == str(native)
        assert digest(r["annotation"]) == r["annotation_sha256"]
        assert digest(native/"input.json") == r["input_sha256"]
        assert digest(r["images"]["O"]) == r["image_sha256"]["O"]
    schedule = query_schedule(requests,tokens,past_window=32)
    prepared,meta,actual_image = prepare_example(processor,row,Path(config["dataset_root"]),"cuda:0")
    assert actual_image.resolve() == Path(requests[0]["images"]["O"]).resolve()
    native_meta = json.loads((native/"input.json").read_text())
    assert meta["question"] == native_meta["question"]
    assert meta["generation_query"] == native_meta["generation_query"]
    assert meta["visual_token_indices"] == requests[0]["visual_positions"]
    assert meta["prompt_token_count"] == requests[0]["prompt_length"]
    assert meta["image_grid_thw"] == requests[0]["image_grid_thw"]
    state,_ = prefill_streaming_state(model=model,prepared=prepared,seed=config["seed"])
    del prepared
    layers = config["layers"]
    kwargs = dict(model=model,layers=layers,visual=meta["visual_token_indices"],prompt_length=meta["prompt_token_count"])
    passive, event_first = {}, {}
    raw = {r["event_id"]:dict(native=[],visual_off=[],target_off=[],irrelevant_off=[]) for r in requests}
    distributions = {}
    max_query = schedule["last_query"]
    index = 0
    while index <= max_query:
        targets = schedule["readout"].get(index,[])
        need_capture = index in schedule["passive"] or bool(targets)
        if not need_capture:
            end = index+1
            while end <= max_query and end not in schedule["passive"] and end not in schedule["readout"]:
                end += 1
            advance(model,state,tokens[index:end],config["seed"])
            index = end
            continue
        checkpoint = clone_streaming_state(state) if targets else None
        capture = MeasurementAssay(**kwargs)
        with capture:
            advance(model,state,[tokens[index]],config["seed"])
        if index in schedule["passive"]:
            passive[index] = capture.records
        if targets:
            baseline = state.last_logits.clone()
            reference = branch(model,checkpoint,tokens[index],config["seed"])
            assert torch.equal(reference.last_logits,baseline), "Main event capture is not exact"
            del reference
            self_assay = AttentionAssay(**kwargs,frozen=capture.states,
                donor_values={l:capture.states[l]["value"] for l in layers})
            self_state = branch(model,checkpoint,tokens[index],config["seed"],self_assay)
            assert torch.equal(self_state.last_logits,baseline), "Main event self/no-op is not exact"
            assert all(v["routing_max_abs_delta"] == 0 for v in self_assay.records.values())
            del self_assay,self_state
            for event_id,offset in targets:
                r = request_by_id[event_id]
                target_token = r["original_token_ids"][offset]
                assert target_token == tokens[index+1]
                raw[event_id]["native"].append(float(baseline.float().log_softmax(-1)[target_token]))
                if offset == 0:
                    event_first[event_id] = dict(records=capture.records,shallow_state=capture.shallow_state)
                    assert capture.shallow_state is not None
                    distributions[event_id] = {}
                for arm,positions in (("visual_off",r["visual_positions"]),("target_off",r["target_positions"]),("irrelevant_off",r["irrelevant_positions"])):
                    if positions is None:
                        continue
                    off = AttentionAssay(**kwargs,mode="off",positions=positions)
                    changed = branch(model,checkpoint,tokens[index],config["seed"],off)
                    assert torch.isfinite(changed.last_logits).all()
                    raw[event_id][arm].append(float(changed.last_logits.float().log_softmax(-1)[target_token]))
                    if offset == 0:
                        distributions[event_id][arm] = js_divergence(baseline,changed.last_logits)
                    del changed,off
            del checkpoint,baseline
        del capture
        index += 1
    events = []
    for r in requests:
        event_id = r["event_id"]
        query = len(r["prefix_token_ids"])-1
        current = event_first[event_id]
        past = [passive[q] for q in range(max(0,query-32),query)]
        features = {f"{a}_k{k}":feature_vector(current["records"],past,aggregation=a,window=k)
                    for a in ("median","trimmed_mean","max") for k in (4,16,32)}
        means = {arm:sum(values)/len(values) if values else None for arm,values in raw[event_id].items()}
        ce = {arm:means["native"]-mean if mean is not None else None for arm,mean in means.items() if arm != "native"}
        vsd = ce["target_off"]-ce["irrelevant_off"] if ce["target_off"] is not None and ce["irrelevant_off"] is not None else None
        source_role = r.get("source_role","demanded_source")  # Calibration smoke has certified sources.
        result = dict(event_id=event_id,base_id=r["base_id"],family_id=r["family_id"],split=r["split"],label=r["label"],
                      prefix_length=len(r["prefix_token_ids"]),prompt_length=r["prompt_length"],visual_token_count=len(r["visual_positions"]),
                      literal_query_boundary=True,features=features,passive_current=current["records"],
                      shallow_state=current["shallow_state"],lexical_prefix_last32=r["lexical_prefix_last32"],
                      strict_past_query_count=len(past),raw_token_log_probabilities=raw[event_id],ce_effect=ce,
                      first_query_js=distributions[event_id],roi_relative_vsd=vsd,
                      target_relative_vsd=vsd if source_role=="demanded_source" else None,source_role=source_role,
                      semantic_eligible=r["semantic_eligible"],semantic_unavailable_reason=r["semantic_unavailable_reason"],
                      source_id=r["source_id"],local_claim_correct=r["local_claim_correct"],capture_exact=True,self_noop_exact=True,
                      scope="Passive R and native transport G only; no semantic Value outcome used",completed=True)
        save(output/"events"/(event_id+".json"),result)
        events.append(event_id)
    raw_path = output/"bases"/(str(row["problem_index"])+"_passive_queries.json.gz")
    raw_path.parent.mkdir(parents=True,exist_ok=True)
    assert not raw_path.exists()
    with gzip.open(raw_path,"wt",encoding="utf-8") as f:
        json.dump({str(k):v for k,v in passive.items()},f,allow_nan=False)
    summary = dict(base_id=str(row["problem_index"]),events=events,completed=True,last_native_query=max_query,
                   runtime_seconds=time.monotonic()-started,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
                   passive_queries=str(raw_path),passive_queries_sha256=digest(raw_path))
    save(output/"bases"/(str(row["problem_index"])+".json"),summary)
    del state,passive,event_first
    gc.collect();torch.cuda.empty_cache()
    return summary


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config",required=True)
    args = parser.parse_args()
    config_path = Path(args.config)
    config = json.loads(config_path.read_text())
    rank = runtime_rank(os.environ,visible_devices=torch.cuda.device_count(),allocation=config["slurm_allocation"])
    torch.cuda.set_device(0)
    for p,h in config["source_sha256"].items():
        assert digest(p) == h,p
    assert digest(config["requests"]) == config["requests_sha256"]
    frozen = json.loads(Path(config["requests"]).read_text())
    assert not frozen["preflight_only"] and not frozen["missing_reviews"]
    assert digest(frozen["protocol"]) == frozen["protocol_sha256"]
    assert digest(config["gate0"]) == config["gate0_sha256"]
    assert json.loads(Path(config["gate0"]).read_text())["status"] == "PASS"
    if frozen["split"] == "confirmation":
        assert digest(config["discovery_freeze"]) == config["discovery_freeze_sha256"]
        assert json.loads(Path(config["discovery_freeze"]).read_text())["frozen"]
    assert config["layers"] == [19,20,21,22]
    out = Path(config["output_dir"])/f"worker{rank}"
    assert not out.exists()
    processor,model = load_runtime(Path(config["model_checkpoint"]),"cuda:0")
    env = runtime_environment(Path(config["model_checkpoint"]),model,40960)
    assert (env["language_layers"],env["attention_heads"],env["kv_heads"]) == (28,16,8)
    env.update(rank=rank,slurm_job_id=os.environ["SLURM_JOB_ID"],slurm_step_id=os.environ.get("SLURM_STEP_ID"),
               gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),config_sha256=digest(config_path))
    save(out/"environment.json",env)
    dataset = {str(r["sample_index"]):r for r in load_mathverse_rows(Path(config["dataset_root"]))}
    grouped = defaultdict(list)
    for r in frozen["requests"]:
        grouped[r["base_id"]].append(r)
    completed = []
    for base,requests in list(grouped.items())[rank::2]:
        print(json.dumps(dict(event="measurement_start",base_id=base,rank=rank)),flush=True)
        result = measure_base(model,processor,dataset[requests[0]["example_id"]],requests,config,out)
        completed.append(result)
        print(json.dumps(dict(event="measurement_complete",**result)),flush=True)
    save(out/"completed.json",dict(completed=True,rank=rank,bases=completed,events=sum(len(r["events"]) for r in completed)))


if __name__ == "__main__":
    main()
