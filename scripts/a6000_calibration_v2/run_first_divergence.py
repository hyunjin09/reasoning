#!/usr/bin/env python3
"""Compare earliest matching one-shot and canonical-streaming tensors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.a6000_calibration_v2.protocol import summarize_tensor_pair
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b0.runtime import (
    prefill_condition,
    score_candidate_from_cache,
)
from visual_reasoning.stage3b5.boundaries import CaptureCurrentBlockBoundaries
from visual_reasoning.stage3c5.carriers import CaptureTokenKV
from visual_reasoning.stage3c9.streaming import (
    prefill_streaming_state,
    roll_streaming_prefix,
    score_preference_from_streaming_state,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/a6000_calibration_v2"
CANDIDATES = ("original_candidate", "counterfactual_candidate")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--device-index", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


class LogitCapture:
    def __init__(self, model: Any) -> None:
        self.module = model.lm_head
        self.tensor: torch.Tensor | None = None
        self.handle: Any | None = None

    def _hook(self, module: Any, args: tuple[Any, ...], output: torch.Tensor) -> None:
        if self.tensor is not None:
            raise RuntimeError("Logit capture executed more than once")
        self.tensor = output[:, 0, :].detach().clone()

    def __enter__(self) -> "LogitCapture":
        self.handle = self.module.register_forward_hook(self._hook)
        return self

    def complete(self) -> torch.Tensor:
        if self.tensor is None:
            raise RuntimeError("Logit capture did not execute")
        return self.tensor

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.handle is not None:
            self.handle.remove()
            self.handle = None


def condition_path(base: str) -> Path:
    metadata = read_json(
        ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json"
    )
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Image validation failed for base {base}")
    return ROOT / metadata["paths"]["O"]


def preference(original: dict[str, Any], counterfactual: dict[str, Any]) -> dict[str, Any]:
    lo = float(original["mean_log_probability"])
    lc = float(counterfactual["mean_log_probability"])
    return {
        "L_o": lo,
        "L_c": lc,
        "D": lo - lc,
        "finite": bool(original["finite"] and counterfactual["finite"]),
        CANDIDATES[0]: original,
        CANDIDATES[1]: counterfactual,
    }


def boundary_tensors(capture: CaptureCurrentBlockBoundaries) -> dict[str, dict[int, torch.Tensor]]:
    return capture.complete_states()


def cache_last(cache: Any, position: int) -> dict[int, tuple[torch.Tensor, torch.Tensor]]:
    return {
        index: (
            layer.keys[:, :, position : position + 1, :].detach().clone(),
            layer.values[:, :, position : position + 1, :].detach().clone(),
        )
        for index, layer in enumerate(cache.layers)
    }


def summarize_layers(
    left: dict[int, torch.Tensor], right: dict[int, torch.Tensor]
) -> list[dict[str, Any]]:
    return [
        {"layer": layer, **summarize_tensor_pair(left[layer], right[layer])}
        for layer in sorted(left)
    ]


def summarize_kv(
    left: dict[int, tuple[torch.Tensor, torch.Tensor]],
    right: dict[int, tuple[torch.Tensor, torch.Tensor]],
) -> list[dict[str, Any]]:
    return [
        {
            "layer": layer,
            "post_rope_key": summarize_tensor_pair(left[layer][0], right[layer][0]),
            "projected_value": summarize_tensor_pair(left[layer][1], right[layer][1]),
        }
        for layer in sorted(left)
    ]


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to(OUT.resolve())
    if (output_dir / "result.json").exists():
        raise FileExistsError(output_dir / "result.json")
    torch.cuda.set_device(int(args.device_index))
    device = f"cuda:{int(args.device_index)}"
    environment = read_json(OUT / "config/environment_freeze.json")
    chunking = read_json(OUT / "config/canonical_chunking.json")
    chunk_size = int(chunking["selected_chunk_size"])
    release = bool(chunking["release_allocator_cache_between_chunks"])
    c7 = read_json(ROOT / "outputs/stage3c7/config/stage3c7_config.json")
    cohort = read_json(ROOT / "outputs/a6000_calibration/config/calibration_cohort.json")
    cell = next(row for row in cohort["cells"] if str(row["base_problem_id"]) == str(args.base))
    manifests = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3c7/cohort/primary_manifest.jsonl")
    }
    events = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")
    }
    item = manifests[str(args.base)]
    pair = next(row for row in item["state_pairs"] if row["target_id"] == cell["target_id"])
    event = events[str(args.base)]
    context = [int(value) for value in event["history_before_ed_token_ids"]]
    if len(context) > chunk_size:
        raise ValueError("First-divergence bases must fit one canonical chunk")
    suffix_o = [int(value) for value in event["original_divergent_suffix_ids"]]
    suffix_c = [int(value) for value in event["counterfactual_divergent_suffix_ids"]]
    dataset = {
        str(row["sample_index"]): row
        for row in load_mathverse_rows(Path(environment["dataset_root"]))
    }
    processor, model = load_runtime(Path(environment["model_checkpoint"]), device=device)
    observed = runtime_environment(Path(environment["model_checkpoint"]), model, 40_960)
    layers = list(range(int(model.config.text_config.num_hidden_layers)))
    prepared, metadata = prepare_custom_image(
        processor, dataset[str(item["example_id"])], condition_path(str(args.base)), device=device
    )
    prompt_length = int(prepared["input_ids"].shape[1])

    one_prefill_capture = CaptureCurrentBlockBoundaries(
        model=model, position=prompt_length - 1, layer_indices=layers
    )
    with one_prefill_capture:
        one_cache, one_rope, one_prefill_audit = prefill_condition(
            model=model, prepared=prepared, seed=int(c7["seed"])
        )
    one_prefill_boundaries = boundary_tensors(one_prefill_capture)
    one_prefill_kv = cache_last(one_cache, prompt_length - 1)

    absolute_predictor = prompt_length + len(context) - 1
    one_kv_capture = CaptureTokenKV(
        model=model, positions=[absolute_predictor], selected_layers=layers
    )
    one_boundary_capture = CaptureCurrentBlockBoundaries(
        model=model, position=len(context) - 1, layer_indices=layers
    )
    one_logits_capture = LogitCapture(model)
    with one_kv_capture, one_boundary_capture, one_logits_capture:
        one_original = score_candidate_from_cache(
            model=model, prefill_cache=one_cache, rope_deltas=one_rope,
            prompt_length=prompt_length, visual_token_indices=metadata["visual_token_indices"],
            prefix_token_ids=context, candidate_token_ids=suffix_o,
            seed=int(c7["seed"]), cutoff_enabled=False,
        )
    one_counterfactual = score_candidate_from_cache(
        model=model, prefill_cache=one_cache, rope_deltas=one_rope,
        prompt_length=prompt_length, visual_token_indices=metadata["visual_token_indices"],
        prefix_token_ids=context, candidate_token_ids=suffix_c,
        seed=int(c7["seed"]), cutoff_enabled=False,
    )
    one_boundaries = boundary_tensors(one_boundary_capture)
    one_kv = one_kv_capture.complete()
    one_logits = one_logits_capture.complete()
    one_score = preference(one_original, one_counterfactual)

    stream_prefill_capture = CaptureCurrentBlockBoundaries(
        model=model, position=prompt_length - 1, layer_indices=layers
    )
    with stream_prefill_capture:
        stream_prefill, stream_prefill_audit = prefill_streaming_state(
            model=model, prepared=prepared, seed=int(c7["seed"])
        )
    stream_prefill_boundaries = boundary_tensors(stream_prefill_capture)
    stream_prefill_kv = cache_last(stream_prefill.cache, prompt_length - 1)
    stream_kv_capture = CaptureTokenKV(
        model=model, positions=[absolute_predictor], selected_layers=layers
    )
    stream_boundary_capture = CaptureCurrentBlockBoundaries(
        model=model, position=len(context) - 1, layer_indices=layers
    )
    stream_logits_capture = LogitCapture(model)
    with stream_kv_capture, stream_boundary_capture, stream_logits_capture:
        stream_state, stream_audit = roll_streaming_prefix(
            model=model, prefill=stream_prefill, prefix_token_ids=context,
            end_generated_index=len(context), seed=int(c7["seed"]),
            chunk_size=chunk_size, release_allocator_cache=release,
        )
    stream_boundaries = boundary_tensors(stream_boundary_capture)
    stream_kv = stream_kv_capture.complete()
    stream_logits = stream_logits_capture.complete()
    stream_score = score_preference_from_streaming_state(
        model=model, state=stream_state, original_suffix_ids=suffix_o,
        counterfactual_suffix_ids=suffix_c, seed=int(c7["seed"]),
    )

    tensor_bundle = {
        "one_shot": {
            "prefill_boundaries": one_prefill_boundaries,
            "prefill_kv": one_prefill_kv,
            "predictor_boundaries": one_boundaries,
            "predictor_kv": one_kv,
            "predictor_attention_output": {
                layer: one_boundaries["h_post_attn"][layer].float()
                - one_boundaries["h_pre"][layer].float()
                for layer in layers
            },
            "predictor_logits": one_logits,
        },
        "streaming": {
            "prefill_boundaries": stream_prefill_boundaries,
            "prefill_kv": stream_prefill_kv,
            "predictor_boundaries": stream_boundaries,
            "predictor_kv": stream_kv,
            "predictor_attention_output": {
                layer: stream_boundaries["h_post_attn"][layer].float()
                - stream_boundaries["h_pre"][layer].float()
                for layer in layers
            },
            "predictor_logits": stream_logits,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(tensor_bundle, output_dir / "matching_tensors.pt")
    comparisons = {
        "prefill_residual": {
            boundary: summarize_layers(one_prefill_boundaries[boundary], stream_prefill_boundaries[boundary])
            for boundary in one_prefill_boundaries
        },
        "prefill_kv": summarize_kv(one_prefill_kv, stream_prefill_kv),
        "predictor_residual": {
            boundary: summarize_layers(one_boundaries[boundary], stream_boundaries[boundary])
            for boundary in one_boundaries
        },
        "predictor_kv": summarize_kv(one_kv, stream_kv),
        "predictor_attention_output": summarize_layers(
            tensor_bundle["one_shot"]["predictor_attention_output"],
            tensor_bundle["streaming"]["predictor_attention_output"],
        ),
        "predictor_logits": summarize_tensor_pair(one_logits, stream_logits),
        "candidate_log_probabilities": {
            candidate: {
                "one_shot": one_score[candidate]["token_log_probabilities"],
                "streaming": stream_score[candidate]["token_log_probabilities"],
            }
            for candidate in CANDIDATES
        },
        "D": {
            "one_shot": one_score["D"],
            "streaming": stream_score["D"],
            "delta": one_score["D"] - stream_score["D"],
        },
    }
    result = {
        "base_problem_id": str(args.base),
        "example_id": str(item["example_id"]),
        "condition": "O",
        "context_length": len(context),
        "prompt_length": prompt_length,
        "predictor_absolute_position": absolute_predictor,
        "canonical_chunk_size": chunk_size,
        "release_allocator_cache_between_chunks": release,
        "one_shot_prefill_audit": one_prefill_audit,
        "streaming_prefill_audit": stream_prefill_audit,
        "streaming_audit": stream_audit,
        "one_shot_score": one_score,
        "streaming_score": stream_score,
        "comparisons": comparisons,
        "tensor_bundle": str((output_dir / "matching_tensors.pt").relative_to(ROOT)),
        "environment": {
            **observed,
            "selected_cuda_device_index": int(args.device_index),
            "selected_cuda_device_name": torch.cuda.get_device_name(int(args.device_index)),
        },
    }
    (output_dir / "result.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
