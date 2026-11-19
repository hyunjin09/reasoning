#!/usr/bin/env python3
"""Run A6000 internal replay and full-versus-bounded calibration assays."""

from __future__ import annotations

import argparse
import copy
import gc
import json
import os
import time
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.a6000_calibration.metrics import compare_scores
from visual_reasoning.a6000_calibration.runtime import (
    replace_selected_cache_positions,
    tensor_pair_max_abs_delta,
)
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b0.cache import clone_cache
from visual_reasoning.stage3c5.carriers import select_captured_positions
from visual_reasoning.stage3c7.runtime import (
    CANDIDATES,
    capture_native_or_suppressed_states,
    score_suppressed_with_rescue,
)
from visual_reasoning.stage3c9.streaming import (
    clone_streaming_state,
    prefill_streaming_state,
    roll_streaming_prefix,
    score_preference_from_streaming_state,
    snapshot_cache_positions,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/a6000_calibration"
CONDITIONS = ("O", "C")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bases", nargs="*", default=[])
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--controls", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def condition_paths(base: str) -> dict[str, Path]:
    metadata = read_json(ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json")
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Image validation failed for base {base}")
    return {condition: ROOT / metadata["paths"][condition] for condition in CONDITIONS}


def evidence_sequences(event: dict[str, Any], state_index: int) -> tuple[list[int], list[int], list[int], list[int]]:
    context = [int(value) for value in event["history_before_ed_token_ids"]]
    ed = int(event["ed_generated_index"])
    index = int(state_index)
    if not 1 <= index <= ed == len(context):
        raise ValueError("Frozen target state is outside evidence history")
    return (
        context[:index], context[index:ed],
        [int(value) for value in event["original_divergent_suffix_ids"]],
        [int(value) for value in event["counterfactual_divergent_suffix_ids"]],
    )


def cache_snapshot(states: dict[str, Any], absolute_position: int) -> dict[int, tuple[torch.Tensor, torch.Tensor]]:
    candidate = CANDIDATES[0]
    return select_captured_positions(
        states[candidate]["cache"],
        captured_positions=states[candidate]["cache_positions"],
        selected_positions=[absolute_position],
    )


def residual_snapshot(states: dict[str, Any], *, layer: int, boundary: str) -> torch.Tensor:
    return states[CANDIDATES[0]]["residual"][boundary][layer].detach().clone()


def score_triplet(
    *, model: Any, prepared: dict[str, Any], prefix: list[int], bridge: list[int],
    suffix_o: list[int], suffix_c: list[int], current: int, tpre: int,
    layers: list[int], residual_layer: int, residual_boundary: str,
    target_positions: list[int], heads: list[int], visual_positions: list[int], seed: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    common = dict(
        model=model, prepared=prepared, prefix_token_ids=prefix, bridge_token_ids=bridge,
        original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
        current_generated_index=current, tpre_generated_index=tpre,
        cache_layers=layers, residual_layer=residual_layer,
        suppression_layers=layers, source_positions=target_positions,
        selected_heads=heads, seed=seed,
    )
    native, native_states = capture_native_or_suppressed_states(**common, suppression_enabled=False)
    suppressed, suppressed_states = capture_native_or_suppressed_states(**common, suppression_enabled=True)
    rescue = score_suppressed_with_rescue(
        model=model, prepared=prepared, prefix_token_ids=prefix, bridge_token_ids=bridge,
        original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
        current_generated_index=current, tpre_generated_index=tpre,
        suppression_layers=layers, source_positions=target_positions,
        selected_heads=heads, native_states=native_states,
        cache_layers=layers, cache_mode="KV", residual_layer=None,
        residual_boundary=None, visual_positions=visual_positions, seed=seed,
        suppression_enabled=True,
    )
    return {
        "native": native,
        "suppressed": suppressed,
        "kv_rescue": rescue,
    }, native_states, suppressed_states


def patch_streaming_selected(
    recipient: Any, *, donor: Any, generated_positions: list[int],
    selected_layers: list[int], visual_positions: list[int],
) -> tuple[Any, dict[str, Any]]:
    patched = clone_streaming_state(recipient)
    absolute = [int(patched.prompt_length) + int(index) for index in generated_positions]
    recipient_layers = [(layer.keys, layer.values) for layer in patched.cache.layers]
    donor_layers = [(layer.keys, layer.values) for layer in donor.cache.layers]
    audits = replace_selected_cache_positions(
        recipient_layers, donor_layers, absolute_positions=absolute,
        selected_layers=selected_layers, visual_positions=visual_positions,
    )
    return patched, {
        "patch_generated_indices": generated_positions,
        "patch_absolute_positions": absolute,
        "selected_layers": selected_layers,
        "layer_audits": audits,
        "first_downstream_absolute_query": int(patched.prompt_length) + int(patched.generated_length),
    }


def streaming_triplet(
    *, model: Any, prepared: dict[str, Any], context: list[int], suffix_o: list[int],
    suffix_c: list[int], tpre: int, layers: list[int], target_positions: list[int],
    heads: list[int], visual_positions: list[int], seed: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    prefill, prefill_audit = prefill_streaming_state(model=model, prepared=prepared, seed=seed)
    native_state, native_audit = roll_streaming_prefix(
        model=model, prefill=prefill, prefix_token_ids=context,
        end_generated_index=len(context), seed=seed,
    )
    suppressed_state, suppressed_audit = roll_streaming_prefix(
        model=model, prefill=prefill, prefix_token_ids=context,
        end_generated_index=len(context), seed=seed,
        layers=layers, selected_heads=heads, source_positions=target_positions,
        suppressed_generated_indices=[tpre],
    )
    rescued_state, patch_audit = patch_streaming_selected(
        suppressed_state, donor=native_state, generated_positions=[tpre],
        selected_layers=layers, visual_positions=visual_positions,
    )
    scores = {
        "native": score_preference_from_streaming_state(
            model=model, state=native_state, original_suffix_ids=suffix_o,
            counterfactual_suffix_ids=suffix_c, seed=seed,
        ),
        "suppressed": score_preference_from_streaming_state(
            model=model, state=suppressed_state, original_suffix_ids=suffix_o,
            counterfactual_suffix_ids=suffix_c, seed=seed,
        ),
        "kv_rescue": score_preference_from_streaming_state(
            model=model, state=rescued_state, original_suffix_ids=suffix_o,
            counterfactual_suffix_ids=suffix_c, seed=seed,
        ),
    }
    absolute_tpre = int(prefill.prompt_length) + tpre
    states = {
        "native": native_state,
        "suppressed": suppressed_state,
        "rescued": rescued_state,
    }
    audits = {
        "prefill": prefill_audit,
        "native": native_audit,
        "suppressed": suppressed_audit,
        "patch": patch_audit,
        "absolute_tpre": absolute_tpre,
        "native_snapshot": snapshot_cache_positions(native_state, absolute_positions=[absolute_tpre]),
        "suppressed_snapshot": snapshot_cache_positions(suppressed_state, absolute_positions=[absolute_tpre]),
        "states": states,
    }
    return scores, audits


def self_patch_controls(
    *, model: Any, prepared: dict[str, Any], prefix: list[int], bridge: list[int],
    suffix_o: list[int], suffix_c: list[int], current: int, tpre: int,
    layers: list[int], residual_layer: int, residual_boundary: str,
    target_positions: list[int], heads: list[int], visual_positions: list[int], seed: int,
    native_score: dict[str, Any], suppressed_score: dict[str, Any],
    native_states: dict[str, Any], suppressed_states: dict[str, Any],
    streaming_native: Any, streaming_suppressed: Any, tolerance: float,
) -> dict[str, Any]:
    common = dict(
        model=model, prepared=prepared, prefix_token_ids=prefix, bridge_token_ids=bridge,
        original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
        current_generated_index=current, tpre_generated_index=tpre,
        suppression_layers=layers, source_positions=target_positions,
        selected_heads=heads, visual_positions=visual_positions, seed=seed,
    )
    controls: dict[str, Any] = {}
    for mode in ("K", "V", "KV"):
        native_self = score_suppressed_with_rescue(
            **common, native_states=native_states, cache_layers=layers,
            cache_mode=mode, residual_layer=None, residual_boundary=None,
            suppression_enabled=False,
        )
        suppressed_self = score_suppressed_with_rescue(
            **common, native_states=suppressed_states, cache_layers=layers,
            cache_mode=mode, residual_layer=None, residual_boundary=None,
            suppression_enabled=True,
        )
        controls[mode] = {
            "native_to_native": compare_scores(native_score, native_self, tolerance=tolerance),
            "suppressed_to_suppressed": compare_scores(suppressed_score, suppressed_self, tolerance=tolerance),
            "native_patch_audits": native_self["cache_patch_audits"],
            "suppressed_patch_audits": suppressed_self["cache_patch_audits"],
        }
    native_residual = score_suppressed_with_rescue(
        **common, native_states=native_states, cache_layers=[], cache_mode=None,
        residual_layer=residual_layer, residual_boundary=residual_boundary,
        suppression_enabled=False,
    )
    suppressed_residual = score_suppressed_with_rescue(
        **common, native_states=suppressed_states, cache_layers=[], cache_mode=None,
        residual_layer=residual_layer, residual_boundary=residual_boundary,
        suppression_enabled=True,
    )
    controls["residual"] = {
        "native_to_native": compare_scores(native_score, native_residual, tolerance=tolerance),
        "suppressed_to_suppressed": compare_scores(suppressed_score, suppressed_residual, tolerance=tolerance),
        "native_patch_audits": native_residual["residual_patch_audits"],
        "suppressed_patch_audits": suppressed_residual["residual_patch_audits"],
    }
    span = list(range(max(0, len(prefix) + len(bridge) - 4), len(prefix) + len(bridge)))
    stream_scores = {}
    for name, state in (("native", streaming_native), ("suppressed", streaming_suppressed)):
        patched, audit = patch_streaming_selected(
            state, donor=state, generated_positions=span,
            selected_layers=list(range(36)), visual_positions=visual_positions,
        )
        scored = score_preference_from_streaming_state(
            model=model, state=patched, original_suffix_ids=suffix_o,
            counterfactual_suffix_ids=suffix_c, seed=seed,
        )
        reference = native_score if name == "native" else suppressed_score
        stream_scores[name] = {
            "comparison_to_full_recipient": compare_scores(reference, scored, tolerance=tolerance),
            "patch_audit": audit,
        }
    controls["event_span"] = stream_scores
    return controls


def finite_score(score: dict[str, Any]) -> bool:
    return bool(score["finite"] and all(score[candidate]["finite"] for candidate in CANDIDATES))


def main() -> None:
    args = parse_args()
    if args.repeats < 3:
        raise ValueError("Calibration requires at least three deterministic replays")
    output = args.output_dir.resolve()
    output.relative_to(OUT.resolve())
    cohort = read_json(OUT / "config/calibration_cohort.json")
    selected = list(cohort["cells"])
    if args.bases:
        requested = {str(value) for value in args.bases}
        selected = [cell for cell in selected if str(cell["base_problem_id"]) in requested]
        missing = requested - {str(cell["base_problem_id"]) for cell in selected}
        if missing:
            raise ValueError(f"Requested bases are outside the frozen cohort: {sorted(missing)}")
    selected = selected[args.shard_index::args.shard_count]
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "run_config.json", {
        "base_problem_ids": [str(cell["base_problem_id"]) for cell in selected],
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "repeats": args.repeats,
        "controls": args.controls,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "full_execution": "native full-prefix eager attention",
        "bounded_execution": "native eager DynamicCache, 128-query chunks",
    })
    c7 = read_json(ROOT / "outputs/stage3c7/config/stage3c7_config.json")
    tolerances = read_json(OUT / "config/tolerances.json")
    tolerance = float(tolerances["aggregate_D_max_abs_delta"])
    manifests = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3c7/cohort/primary_manifest.jsonl")}
    events = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")}
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(Path(c7["dataset_root"]))}
    processor, model = load_runtime(Path(c7["model_checkpoint"]), device="cuda")
    environment = runtime_environment(Path(c7["model_checkpoint"]), model, 40_960)
    if "A6000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected A6000, observed {environment['gpu_name']}")
    architecture = {
        "language_layers": int(model.config.text_config.num_hidden_layers),
        "logical_query_heads": int(model.config.text_config.num_attention_heads),
        "kv_heads": int(model.config.text_config.num_key_value_heads),
        "query_heads_per_kv_group": int(model.config.text_config.num_attention_heads // model.config.text_config.num_key_value_heads),
        "head_dimension": int(model.config.text_config.head_dim),
    }
    if architecture != c7["architecture_expected"]:
        raise RuntimeError(f"Architecture mismatch: {architecture}")
    write_json(output / "environment.json", {**environment, "architecture_observed": architecture})
    layers = [int(value) for value in c7["cache_scope"]["layers"]]
    heads = list(range(architecture["logical_query_heads"]))
    torch.cuda.reset_peak_memory_stats()
    run_started = time.perf_counter()
    completed = 0
    for cell in selected:
        base = str(cell["base_problem_id"])
        path = output / "examples" / base / "result.json"
        if path.is_file():
            if not args.resume:
                raise FileExistsError(path)
            completed += 1
            print(f"[{completed}/{len(selected)}] resume base={base}", flush=True)
            continue
        started = time.perf_counter()
        item = manifests[base]
        target = str(cell["target_id"])
        pair = next(row for row in item["state_pairs"] if row["target_id"] == target)
        residual_spec = c7["residual_boundaries"][target]
        current = int(pair["state_R"]["generated_index"])
        tpre = current - 1
        prefix, bridge, suffix_o, suffix_c = evidence_sequences(events[base], current)
        context = prefix + bridge
        prepared, metadata = {}, {}
        for condition, image_path in condition_paths(base).items():
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, dataset[str(item["example_id"])], image_path, device="cuda"
            )
        if metadata["O"]["prompt_token_ids"] != metadata["C"]["prompt_token_ids"] or metadata["O"]["image_grid_thw"] != metadata["C"]["image_grid_thw"]:
            raise RuntimeError(f"O/C layout mismatch for base {base}")
        visual_positions = [int(value) for value in metadata["O"]["visual_token_indices"]]
        target_positions = [int(value) for value in rois[base]["absolute_source_groups"]["V_target"]]
        if visual_positions != [int(value) for value in rois[base]["absolute_source_groups"]["V_all"]]:
            raise RuntimeError(f"Visual layout mismatch for base {base}")
        condition_results = {}
        all_finite = True
        for condition in CONDITIONS:
            replay_scores, replay_caches, replay_residuals = [], [], []
            first_native_states = first_suppressed_states = None
            for repeat in range(args.repeats):
                scores, native_states, suppressed_states = score_triplet(
                    model=model, prepared=prepared[condition], prefix=prefix, bridge=bridge,
                    suffix_o=suffix_o, suffix_c=suffix_c, current=current, tpre=tpre,
                    layers=layers, residual_layer=int(residual_spec["layer"]),
                    residual_boundary=str(residual_spec["boundary"]),
                    target_positions=target_positions, heads=heads,
                    visual_positions=visual_positions, seed=int(c7["seed"]),
                )
                replay_scores.append(scores)
                absolute_tpre = int(scores["native"]["tpre_absolute_position"])
                replay_caches.append({
                    "native": cache_snapshot(native_states, absolute_tpre),
                    "suppressed": cache_snapshot(suppressed_states, absolute_tpre),
                })
                replay_residuals.append({
                    "native": residual_snapshot(native_states, layer=int(residual_spec["layer"]), boundary=str(residual_spec["boundary"])),
                    "suppressed": residual_snapshot(suppressed_states, layer=int(residual_spec["layer"]), boundary=str(residual_spec["boundary"])),
                })
                if repeat == 0:
                    first_native_states, first_suppressed_states = native_states, suppressed_states
                else:
                    del native_states, suppressed_states
            assert first_native_states is not None and first_suppressed_states is not None
            deterministic_rows = []
            for repeat in range(1, args.repeats):
                score_deltas = {
                    name: compare_scores(replay_scores[0][name], replay_scores[repeat][name], tolerance=tolerance)
                    for name in ("native", "suppressed", "kv_rescue")
                }
                cache_deltas = {
                    name: tensor_pair_max_abs_delta(replay_caches[0][name], replay_caches[repeat][name])
                    for name in ("native", "suppressed")
                }
                residual_deltas = {
                    name: float((replay_residuals[0][name] - replay_residuals[repeat][name]).float().abs().max().item())
                    for name in ("native", "suppressed")
                }
                deterministic_rows.append({
                    "repeat_index": repeat,
                    "score_deltas": score_deltas,
                    "cache_deltas": cache_deltas,
                    "residual_max_abs_deltas": residual_deltas,
                    "passed": bool(
                        all(row["passed"] for row in score_deltas.values())
                        and all(row["maximum_abs_delta"] <= tolerance for row in cache_deltas.values())
                        and all(value <= tolerance for value in residual_deltas.values())
                    ),
                })
            bounded_scores, bounded = streaming_triplet(
                model=model, prepared=prepared[condition], context=context,
                suffix_o=suffix_o, suffix_c=suffix_c, tpre=tpre, layers=layers,
                target_positions=target_positions, heads=heads,
                visual_positions=visual_positions, seed=int(c7["seed"]),
            )
            parity = {
                name: compare_scores(replay_scores[0][name], bounded_scores[name], tolerance=tolerance)
                for name in ("native", "suppressed", "kv_rescue")
            }
            full_cache = {
                "native": replay_caches[0]["native"],
                "suppressed": replay_caches[0]["suppressed"],
            }
            bounded_cache = {
                "native": {layer: bounded["native_snapshot"][layer] for layer in layers},
                "suppressed": {layer: bounded["suppressed_snapshot"][layer] for layer in layers},
            }
            cache_parity = {
                name: tensor_pair_max_abs_delta(full_cache[name], bounded_cache[name])
                for name in ("native", "suppressed")
            }
            residual_rescue = score_suppressed_with_rescue(
                model=model, prepared=prepared[condition], prefix_token_ids=prefix,
                bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                counterfactual_suffix_ids=suffix_c, current_generated_index=current,
                tpre_generated_index=tpre, suppression_layers=layers,
                source_positions=target_positions, selected_heads=heads,
                native_states=first_native_states, cache_layers=[], cache_mode=None,
                residual_layer=int(residual_spec["layer"]),
                residual_boundary=str(residual_spec["boundary"]),
                visual_positions=visual_positions, seed=int(c7["seed"]),
                suppression_enabled=True,
            )
            controls = None
            if args.controls:
                controls = self_patch_controls(
                    model=model, prepared=prepared[condition], prefix=prefix, bridge=bridge,
                    suffix_o=suffix_o, suffix_c=suffix_c, current=current, tpre=tpre,
                    layers=layers, residual_layer=int(residual_spec["layer"]),
                    residual_boundary=str(residual_spec["boundary"]),
                    target_positions=target_positions, heads=heads,
                    visual_positions=visual_positions, seed=int(c7["seed"]),
                    native_score=replay_scores[0]["native"],
                    suppressed_score=replay_scores[0]["suppressed"],
                    native_states=first_native_states, suppressed_states=first_suppressed_states,
                    streaming_native=bounded["states"]["native"],
                    streaming_suppressed=bounded["states"]["suppressed"],
                    tolerance=tolerance,
                )
            all_finite &= all(finite_score(score) for score in [
                *replay_scores[0].values(), *bounded_scores.values(), residual_rescue,
            ])
            condition_results[condition] = {
                "full_scores": replay_scores[0],
                "bounded_scores": bounded_scores,
                "residual_rescue": residual_rescue,
                "deterministic_replay": deterministic_rows,
                "full_vs_bounded": parity,
                "full_vs_bounded_cache": cache_parity,
                "bounded_audits": {key: value for key, value in bounded.items() if key not in {"states", "native_snapshot", "suppressed_snapshot"}},
                "self_patch_controls": controls,
                "suppression_audits": {
                    candidate: first_suppressed_states[candidate]["suppression_audit"]
                    for candidate in CANDIDATES
                },
            }
            del first_native_states, first_suppressed_states, bounded
            gc.collect()
            torch.cuda.empty_cache()
        result = {
            "base_problem_id": base,
            "example_id": str(cell["example_id"]),
            "target_id": target,
            "effect_stratum": cell["effect_stratum"],
            "conditions": condition_results,
            "prefix_length": len(context),
            "prompt_length": len(metadata["O"]["prompt_token_ids"]),
            "visual_token_count": len(visual_positions),
            "target_position_count": len(target_positions),
            "architecture": architecture,
            "all_scores_finite": all_finite,
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(path, result)
        completed += 1
        print(f"[{completed}/{len(selected)}] base={base} target={target} seconds={result['runtime_seconds']:.1f}", flush=True)
        del prepared
        gc.collect()
        torch.cuda.empty_cache()
    torch.cuda.synchronize()
    write_json(output / "run_summary.json", {
        "completed": completed,
        "expected": len(selected),
        "runtime_seconds": time.perf_counter() - run_started,
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_gpu_reserved_bytes": int(torch.cuda.max_memory_reserved()),
    })


if __name__ == "__main__":
    main()
