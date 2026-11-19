#!/usr/bin/env python3
"""Numerically verify that current-residual rescue leaves every past K/V exact."""

from __future__ import annotations

import argparse
import json
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b5.boundaries import CurrentPositionBoundaryPatch
from visual_reasoning.stage3c3.runtime import score_evidence_suffix
from visual_reasoning.stage3c4.runtime import SourceContributionWindowPatch
from visual_reasoning.stage3c5.carriers import CaptureTokenKV
from visual_reasoning.stage3c6.runtime import capture_preference_states


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="141")
    parser.add_argument("--target", default="target_a", choices=("target_a", "target_b"))
    parser.add_argument("--layer", default=29, type=int)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def evidence_sequences(event: dict[str, Any], state_index: int) -> tuple[list[int], list[int], list[int], list[int]]:
    context = [int(value) for value in event["history_before_ed_token_ids"]]
    ed = int(event["ed_generated_index"])
    return context[:state_index], context[state_index:ed], [int(v) for v in event["original_divergent_suffix_ids"]], [int(v) for v in event["counterfactual_divergent_suffix_ids"]]


def run_candidate(
    *, model: Any, prepared: dict[str, Any], prefix: list[int], bridge: list[int], suffix: list[int],
    current_absolute: int, absolute_tpre: int, target_positions: list[int], all_heads: list[int],
    suppression_layers: list[int], capture_positions: list[int], native_states: dict[str, dict[str, dict[int, torch.Tensor]]],
    candidate: str, rescue_layer: int, boundary: str | None, seed: int,
) -> tuple[dict[str, Any], dict[int, tuple[torch.Tensor, torch.Tensor]], dict[str, Any] | None]:
    capture = CaptureTokenKV(model=model, positions=capture_positions, selected_layers=list(range(36)))
    suppression = [
        SourceContributionWindowPatch(
            model=model, layer_index=layer, query_positions=[absolute_tpre], selected_heads=all_heads,
            source_positions=target_positions, gain=0.0,
        )
        for layer in suppression_layers
    ]
    residual = (
        CurrentPositionBoundaryPatch(
            model=model, position=current_absolute, layer_index=rescue_layer, boundary=boundary,
            source_state=native_states[candidate][boundary][rescue_layer],
        )
        if boundary is not None else None
    )
    with ExitStack() as stack:
        stack.enter_context(capture)
        for patch in suppression:
            stack.enter_context(patch)
        if residual is not None:
            stack.enter_context(residual)
        score = score_evidence_suffix(
            model=model, prepared=prepared, prefix_token_ids=prefix, bridge_token_ids=bridge,
            suffix_token_ids=suffix, seed=seed,
        )
    return score, capture.complete(), None if residual is None else {"audit": residual.audit}


def main() -> None:
    args = parse_args()
    config = read_json(OUT / "config/stage3c6_config.json")
    manifest = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/validation_manifest.jsonl")}
    item = manifest[str(args.base)]
    events = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")}
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    edit = read_json(ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / str(args.base) / "edit_metadata.json")
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Stage 3C.6 requires A5000, observed {environment['gpu_name']}")
    prepared, metadata = prepare_custom_image(processor, data[str(item["example_id"])], ROOT / edit["paths"]["O"], device="cuda")
    target_positions = [int(v) for v in rois[str(args.base)]["absolute_source_groups"]["V_target"]]
    state = next(row for row in item["state_pairs"] if row["target_id"] == args.target)
    current = int(state["state_R"]["generated_index"])
    tpre = current - 1
    prompt_length = int(prepared["input_ids"].shape[1])
    current_absolute = prompt_length + current - 1
    absolute_tpre = prompt_length + tpre - 1
    prefix, bridge, suffix_o, suffix_c = evidence_sequences(events[str(args.base)], current)
    all_heads = list(range(32))
    suppression_layers = list(range(16, 36))
    _, native_states = capture_preference_states(
        model=model, prepared=prepared, prefix_token_ids=prefix, bridge_token_ids=bridge,
        original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
        current_generated_index=current, capture_layers=[args.layer], suppression_generated_index=None,
        suppression_layers=[], source_positions=target_positions, selected_heads=all_heads,
        suppression_gain=1.0, seed=int(config["seed"]),
    )
    capture_positions = list(range(current_absolute))
    suffix_by_candidate = {"original_candidate": suffix_o, "counterfactual_candidate": suffix_c}
    output_rows = []
    all_exact = True
    maximum_delta = 0.0
    for candidate, suffix in suffix_by_candidate.items():
        _, baseline, _ = run_candidate(
            model=model, prepared=prepared, prefix=prefix, bridge=bridge, suffix=suffix,
            current_absolute=current_absolute, absolute_tpre=absolute_tpre, target_positions=target_positions,
            all_heads=all_heads, suppression_layers=suppression_layers, capture_positions=capture_positions,
            native_states=native_states, candidate=candidate, rescue_layer=args.layer, boundary=None, seed=int(config["seed"]),
        )
        for boundary in ("h_pre", "h_post_attn", "h_post_block"):
            _, rescued, residual = run_candidate(
                model=model, prepared=prepared, prefix=prefix, bridge=bridge, suffix=suffix,
                current_absolute=current_absolute, absolute_tpre=absolute_tpre, target_positions=target_positions,
                all_heads=all_heads, suppression_layers=suppression_layers, capture_positions=capture_positions,
                native_states=native_states, candidate=candidate, rescue_layer=args.layer, boundary=boundary, seed=int(config["seed"]),
            )
            for layer in range(36):
                key_delta = float((baseline[layer][0].float() - rescued[layer][0].float()).abs().max().item())
                value_delta = float((baseline[layer][1].float() - rescued[layer][1].float()).abs().max().item())
                exact = bool(torch.equal(baseline[layer][0], rescued[layer][0]) and torch.equal(baseline[layer][1], rescued[layer][1]))
                all_exact &= exact
                maximum_delta = max(maximum_delta, key_delta, value_delta)
                output_rows.append({
                    "candidate": candidate, "boundary": boundary, "layer": layer, "past_position_count": len(capture_positions),
                    "past_key_exact": bool(torch.equal(baseline[layer][0], rescued[layer][0])),
                    "past_value_exact": bool(torch.equal(baseline[layer][1], rescued[layer][1])),
                    "past_key_max_abs_delta": key_delta, "past_value_max_abs_delta": value_delta,
                    "visual_positions_included": len(set(metadata["visual_token_indices"]) & set(capture_positions)),
                    "residual_patch_audit": residual,
                })
    result = {
        "status": "PASS" if all_exact else "FAIL", "base_problem_id": str(args.base), "target": args.target,
        "rescue_layer": args.layer, "boundaries": ["h_pre", "h_post_attn", "h_post_block"],
        "candidate_count": 2, "layer_comparison_count": len(output_rows),
        "all_past_post_rope_KV_exact": all_exact, "maximum_absolute_delta": maximum_delta,
        "current_position_excluded": True, "visual_positions_included_in_exact_comparison": True,
        "rows": output_rows,
    }
    write_json(OUT / "audit/past_cache_invariance.json", result)
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))
    if not all_exact:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
