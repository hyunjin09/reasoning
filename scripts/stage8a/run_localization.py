"""Calibrate the2B layer window using frozen native events and source controls."""
import argparse
import gc
import hashlib
import json
import os
import time
from pathlib import Path

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, prepare_example, runtime_environment
from visual_reasoning.stage3c9.streaming import advance_streaming_state, clone_streaming_state, prefill_streaming_state
from visual_reasoning.stage8a.instrumentation import AttentionAssay, js_divergence
from visual_reasoning.stage8a.assays import summarize_control_scores
from visual_reasoning.stage8a.protocol import runtime_rank


def save(path, data):
    assert not path.exists(), path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False)+"\n")
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def logp(logits, token):
    return float(logits.float().log_softmax(-1)[int(token)])


def run_query(model, checkpoint, token, seed, assay=None):
    state = clone_streaming_state(checkpoint)
    if assay is None:
        advance_streaming_state(model=model, state=state, token_ids=[token], seed=seed, chunk_size=1)
    else:
        with assay:
            advance_streaming_state(model=model, state=state, token_ids=[token], seed=seed, chunk_size=1)
    return state


@torch.inference_mode()
def score_event(model, processor, row, request, config, layer_sets, out):
    started = time.monotonic()
    assert digest(request["annotation"]) == request["annotation_sha256"]
    assert digest(Path(request["native_dir"])/"input.json") == request["input_sha256"]
    states, inputs = {}, {}
    for condition, path in request["images"].items():
        assert digest(path) == request["image_sha256"][condition]
        prepared, meta, _ = prepare_example(processor, {**row, "image": path}, Path(config["dataset_root"]), "cuda:0")
        assert meta["visual_token_indices"] == request["visual_positions"]
        assert meta["prompt_token_count"] == request["prompt_length"]
        assert meta["image_grid_thw"] == request["image_grid_thw"]
        inputs[condition] = prepared["input_ids"].clone()
        states[condition], _ = prefill_streaming_state(model=model, prepared=prepared, seed=config["seed"])
        del prepared
    assert torch.equal(inputs["O"], inputs["C"]) and torch.equal(inputs["O"], inputs["S"])
    assert torch.equal(states["O"].rope_deltas, states["C"].rope_deltas)
    assert torch.equal(states["O"].rope_deltas, states["S"].rope_deltas)
    visual, target = request["visual_positions"], request["target_positions"]
    prefix = request["prefix_token_ids"]
    assert prefix
    checkpoint = clone_streaming_state(states["O"])
    advance_streaming_state(model=model, state=checkpoint, token_ids=prefix[:-1], seed=config["seed"], chunk_size=1)
    all_layers = list(range(model.config.text_config.num_hidden_layers))
    arms = ["native", "self", "semantic", "sham", "roi_semantic", "roi_sham", "target_off", "irrelevant_off"]
    scores = {label: {arm: {candidate: [] for candidate in ["original", "counterfactual"]} for arm in arms}
              for label in layer_sets}
    distributions = {label: {} for label in layer_sets}
    passive = None
    for candidate in ["original", "counterfactual"]:
        candidate_ids = request[candidate+"_token_ids"]
        branch_checkpoint = clone_streaming_state(checkpoint)
        query_token = prefix[-1]
        for index, target_token in enumerate(candidate_ids):
            capture = AttentionAssay(model, layers=all_layers, visual=visual, prompt_length=request["prompt_length"])
            native = run_query(model, branch_checkpoint, query_token, config["seed"], capture)
            baseline = native.last_logits.clone()
            reference = run_query(model, branch_checkpoint, query_token, config["seed"])
            assert torch.equal(reference.last_logits, baseline), "Event-specific capture no-op failed"
            del reference
            if candidate == "original" and index == 0:
                passive = capture.records
            donor = {condition: {} for condition in ["C", "S"]}
            for condition in donor:
                for layer, state in capture.states.items():
                    values = state["value"].clone()
                    values[:, :, visual] = states[condition].cache.layers[layer].values[:, :, visual]
                    donor[condition][layer] = values
            for label, layers in layer_sets.items():
                scores[label]["native"][candidate].append(logp(baseline, target_token))
                for arm in arms[1:]:
                    kwargs = dict(model=model, layers=layers, visual=visual, prompt_length=request["prompt_length"])
                    if arm in {"self", "semantic", "sham", "roi_semantic", "roi_sham"}:
                        values = {l: capture.states[l]["value"] for l in layers} if arm == "self" else donor["C" if arm.endswith("semantic") else "S"]
                        positions = target if arm.startswith("roi_") else visual
                        assay = AttentionAssay(**kwargs, frozen=capture.states, donor_values=values, positions=positions)
                    else:
                        positions = target if arm == "target_off" else request["irrelevant_positions"]
                        assay = AttentionAssay(**kwargs, mode="off", positions=positions)
                    changed = run_query(model, branch_checkpoint, query_token, config["seed"], assay)
                    if arm == "self":
                        assert torch.equal(changed.last_logits, baseline), "Event-specific self Value no-op failed"
                    if arm in {"self", "semantic", "sham", "roi_semantic", "roi_sham"}:
                        assert all(r["routing_max_abs_delta"] == 0. for r in assay.records.values())
                    assert torch.isfinite(changed.last_logits).all()
                    scores[label][arm][candidate].append(logp(changed.last_logits, target_token))
                    if candidate == "original" and index == 0:
                        distributions[label][arm] = js_divergence(baseline, changed.last_logits)
                    del changed, assay
            # Every suffix query has a native, isolated history. No arm is reused here.
            branch_checkpoint = native
            query_token = target_token
            del donor, capture, baseline
        del branch_checkpoint
    results = []
    for label, layers in layer_sets.items():
        results.append(dict(label=label, layers=layers, **summarize_control_scores(scores[label]),
            first_query_js=distributions[label], self_noop_exact=True, selected_routing_fixed=True))
        print(json.dumps(dict(event="localization_layer_complete", event_id=request["event_id"], label=label)), flush=True)
    result = dict(event_id=request["event_id"], base_id=request["base_id"], family_id=request["family_id"],
                  source_id=request["source_id"], results=results, passive_first_query=passive,
                  runtime_seconds=time.monotonic()-started, peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
                  distribution_definition="Raw model logits before sampling temperature/top-k/top-p; log-probabilities and JS in nats",
                  semantic_scope="Calibration only; no discovery/confirmation conclusion", completed=True)
    save(out, result)
    del states, checkpoint
    gc.collect()
    torch.cuda.empty_cache()
    return result


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config_path = Path(args.config)
    config = json.loads(config_path.read_text())
    rank = runtime_rank(os.environ, visible_devices=torch.cuda.device_count(), allocation=config["slurm_allocation"])
    torch.cuda.set_device(0)
    for path, expected in config["source_sha256"].items():
        assert digest(path) == expected, path
    assert digest(config["requests"]) == config["requests_sha256"]
    frozen = json.loads(Path(config["requests"]).read_text())
    assert digest(frozen["protocol"]) == frozen["protocol_sha256"]
    native_wrapper = json.loads(Path(config["native_wrapper"]).read_text())
    mechanics_wrapper = json.loads(Path(config["mechanics_wrapper"]).read_text())
    assert native_wrapper["completed"] and mechanics_wrapper["completed"]
    native_out = Path(config["native_wrapper"]).parent
    assert sum(json.loads((native_out/f"worker{r}/completed.json").read_text())["normal_eos"] for r in range(2)) >= 10
    out = Path(config["output_dir"])/f"worker{rank}"
    assert not out.exists()
    processor, model = load_runtime(Path(config["model_checkpoint"]), "cuda:0")
    env = runtime_environment(Path(config["model_checkpoint"]), model, 40960)
    assert (env["language_layers"], env["attention_heads"], env["kv_heads"]) == (28, 16, 8)
    env.update(rank=rank, slurm_job_id=os.environ["SLURM_JOB_ID"], slurm_step_id=os.environ.get("SLURM_STEP_ID"),
               gpu_uuid=str(torch.cuda.get_device_properties(0).uuid), config_sha256=digest(config_path))
    save(out/"environment.json", env)
    dataset = {str(r["sample_index"]): r for r in load_mathverse_rows(Path(config["dataset_root"]))}
    layer_sets = config["layer_sets"]
    completed = []
    for request in frozen["requests"][rank::2]:
        print(json.dumps(dict(event="start_localization", event_id=request["event_id"], rank=rank)), flush=True)
        result = score_event(model, processor, dataset[request["example_id"]], request, config, layer_sets,
                             out/"events"/(request["event_id"]+".json"))
        completed.append(dict(event_id=result["event_id"], runtime_seconds=result["runtime_seconds"]))
    save(out/"completed.json", dict(completed=True, events=completed, rank=rank))


if __name__ == "__main__":
    main()
