"""Gate0 native-path and all-layer intervention checks on both allocated GPUs."""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import _reset_generation_state, load_runtime, prepare_example, runtime_environment
from visual_reasoning.stage3c9.streaming import advance_streaming_state, clone_streaming_state, prefill_streaming_state
from visual_reasoning.stage8a.instrumentation import AttentionAssay, js_divergence
from visual_reasoning.stage8a.protocol import generation_parameters, runtime_rank


def save(path, record):
    assert not path.exists(), path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")


def equal_cache(left, right):
    return all(torch.equal(a.keys, b.keys) and torch.equal(a.values, b.values)
               for a, b in zip(left.layers, right.layers))


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config_path = Path(args.config)
    config = json.loads(config_path.read_text())
    rank = runtime_rank(os.environ, visible_devices=torch.cuda.device_count(), allocation=config["slurm_allocation"])
    torch.cuda.set_device(0)
    for name, digest in config["source_sha256"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
    manifest = Path(config["manifest"])
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == config["manifest_sha256"]
    records = [json.loads(s) for s in manifest.read_text().splitlines()]
    record = records[rank]
    row = next(r for r in load_mathverse_rows(Path(config["dataset_root"])) if str(r["sample_index"]) == record["example_id"])
    out = Path(config["output_dir"]) / f"worker{rank}"
    assert not out.exists()
    started = time.monotonic()
    processor, model = load_runtime(Path(config["model_checkpoint"]), "cuda:0")
    env = runtime_environment(Path(config["model_checkpoint"]), model, 128)
    assert (env["language_layers"], env["attention_heads"], env["kv_heads"]) == (28, 16, 8)
    env.update(rank=rank, slurm_job_id=os.environ["SLURM_JOB_ID"], slurm_step_id=os.environ.get("SLURM_STEP_ID"),
               gpu_uuid=str(torch.cuda.get_device_properties(0).uuid), config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest())
    save(out / "environment.json", env)
    prepared, metadata, image = prepare_example(processor, row, Path(config["dataset_root"]), "cuda:0")
    assert image.resolve() == Path(record["image"]).resolve()
    assert hashlib.sha256(image.read_bytes()).hexdigest() == record["image_sha256"]
    save(out / "input.json", metadata)
    _reset_generation_state(model, seed=config["seed"])
    generated = model.generate(**prepared, **generation_parameters(), max_new_tokens=128,
                               use_cache=True, return_dict_in_generate=True, output_logits=True)
    ids = generated.sequences[0, prepared["input_ids"].shape[1]:].tolist()
    reference = [x[0].detach().clone() for x in generated.logits]
    previous = json.loads((Path(config["native_output_dir"]) / f"worker{rank}/native_repeat128.json").read_text())
    assert previous["base_id"] == record["base_id"] and previous["pass"]
    assert ids == previous["token_ids"][0]
    assert len(ids) == 128, "Calibration comparison needs 128 native steps"
    del generated
    state, prefill_audit = prefill_streaming_state(model=model, prepared=prepared, seed=config["seed"])
    checks = []
    for index in range(128):
        # Every raw next-token logit, not merely the sampled token, must match HF.
        delta = float((state.last_logits.float()-reference[index].float()).abs().max())
        checks.append({"generated_prefix_length": index, "exact": delta == 0., "max_abs_error": delta})
        if index == 126:
            checkpoint = clone_streaming_state(state)
        if index < 127:
            advance_streaming_state(model=model, state=state, token_ids=[ids[index]], seed=config["seed"], chunk_size=1)
    save(out / "native_streaming_parity.json", {"pass": all(c["exact"] for c in checks), "checks": checks,
         "accepted_path": "native multimodal prefill then one-token cached queries", "prefill": prefill_audit})
    assert all(c["exact"] for c in checks), "Native one-token streaming logit parity failed"
    saved_cache = clone_streaming_state(checkpoint)
    layers = list(range(env["language_layers"]))
    visual = metadata["visual_token_indices"]
    prompt = metadata["prompt_token_count"]
    capture_state = clone_streaming_state(checkpoint)
    with AttentionAssay(model, layers=layers, visual=visual, prompt_length=prompt) as capture:
        advance_streaming_state(model=model, state=capture_state, token_ids=[ids[126]], seed=config["seed"], chunk_size=1)
    capture_exact = torch.equal(capture_state.last_logits, reference[127])
    cache_exact = equal_cache(capture_state.cache, state.cache)
    reconstruction = max(r["attention_reconstruction_max_abs_error"] for r in capture.records.values())
    save(out / "capture.json", {"logits_exact": capture_exact, "cache_exact": cache_exact,
         "attention_reconstruction_max_abs_error": reconstruction, "layers": capture.records})
    assert capture_exact and cache_exact and reconstruction == 0., "Attention capture changes native execution"
    self_state = clone_streaming_state(checkpoint)
    with AttentionAssay(model, layers=layers, visual=visual, prompt_length=prompt, frozen=capture.states,
                        donor_values={l: s["value"] for l, s in capture.states.items()}, positions=visual) as self_patch:
        advance_streaming_state(model=model, state=self_state, token_ids=[ids[126]], seed=config["seed"], chunk_size=1)
    self_exact = torch.equal(self_state.last_logits, reference[127]) and equal_cache(self_state.cache, state.cache)
    assert self_exact, "Fixed-routing self Value patch is not an exact no-op"
    # Synthetic offset is a technical operation check, never a semantic result.
    donor = {l: s["value"].clone() for l, s in capture.states.items()}
    for values in donor.values():
        values[:, :, visual] += .125
    changed_state = clone_streaming_state(checkpoint)
    with AttentionAssay(model, layers=layers, visual=visual, prompt_length=prompt, frozen=capture.states,
                        donor_values=donor, positions=visual) as changed:
        advance_streaming_state(model=model, state=changed_state, token_ids=[ids[126]], seed=config["seed"], chunk_size=1)
    changed_js = js_divergence(reference[127], changed_state.last_logits)
    routing_exact = all(r["routing_max_abs_delta"] == 0. for r in changed.records.values())
    assert routing_exact and changed_js > 0. and equal_cache(changed_state.cache, state.cache)
    off_state = clone_streaming_state(checkpoint)
    with AttentionAssay(model, layers=layers, visual=visual, prompt_length=prompt, mode="off"):
        advance_streaming_state(model=model, state=off_state, token_ids=[ids[126]], seed=config["seed"], chunk_size=1)
    off_js = js_divergence(reference[127], off_state.last_logits)
    assert torch.isfinite(off_state.last_logits).all() and off_js > 0.
    assert equal_cache(checkpoint.cache, saved_cache.cache), "An arm mutated its shared native checkpoint"
    save(out / "completed.json", {"completed": True, "rank": rank, "base_id": record["base_id"],
        "native_generation_repeat_exact": True, "native_streaming_128_logits_exact": True,
        "all_28_layer_capture_exact": capture_exact, "all_layer_cache_exact": cache_exact,
        "fixed_route_self_exact": self_exact, "fixed_routing_exact": routing_exact,
        "synthetic_value_offset_js": changed_js, "visual_off_js": off_js,
        "cache_isolation_exact": True, "runtime_seconds": time.monotonic()-started,
        "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(),
        "scope": "Technical checks only. Functional localization and ten normal-EOS examples remain separate Gate0 requirements."})
    print(json.dumps({"event": "mechanics_complete", "rank": rank}), flush=True)


if __name__ == "__main__":
    main()
