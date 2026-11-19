#!/usr/bin/env python3
"""Run Stage 3C.4 validation and frozen phase scoring."""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from pathlib import Path
from typing import Any, Sequence

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c3.runtime import score_evidence_suffix
from visual_reasoning.stage3c4.protocol import temporal_query_indices
from visual_reasoning.stage3c4.runtime import score_window_preference


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("validation", "phase_a", "phase_b", "phase_c"), required=True)
    parser.add_argument("--config", type=Path, default=OUT / "config/stage3c4_config.json")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-bases", type=int, default=0)
    parser.add_argument("--repeat-first", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def deterministic_view(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: deterministic_view(item) for key, item in value.items() if key != "runtime_seconds"}
    if isinstance(value, list):
        return [deterministic_view(item) for item in value]
    return value


def condition_original_path(base: str) -> Path:
    metadata = read_json(
        ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json"
    )
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Four-condition validation failed for base {base}")
    return ROOT / metadata["paths"]["O"]


def evidence_sequences(
    event: dict[str, Any], state_index: int
) -> tuple[list[int], list[int], list[int], list[int]]:
    context = [int(value) for value in event["history_before_ed_token_ids"]]
    ed = int(event["ed_generated_index"])
    index = int(state_index)
    if not 1 <= index <= ed == len(context):
        raise ValueError("Frozen retrieval-state index is outside the evidence history")
    return (
        context[:index],
        context[index:ed],
        [int(value) for value in event["original_divergent_suffix_ids"]],
        [int(value) for value in event["counterfactual_divergent_suffix_ids"]],
    )


def source_groups(
    *, target: Sequence[int], mention: Sequence[int], irrelevant: Sequence[int]
) -> dict[str, list[int]]:
    groups = {
        "T": sorted({int(value) for value in target}),
        "M": sorted({int(value) for value in mention}),
        "I": sorted({int(value) for value in irrelevant}),
    }
    sets = [set(groups[name]) for name in ("T", "M", "I")]
    if any(not values for values in sets):
        raise ValueError("T/M/I groups must be nonempty")
    if any(sets[left] & sets[right] for left in range(3) for right in range(left + 1, 3)):
        raise ValueError("T/M/I groups must be disjoint")
    return groups


def native_score(
    *, model: Any, prepared: dict[str, Any], event: dict[str, Any], generated_index: int, seed: int
) -> dict[str, Any]:
    prefix, bridge, original, counterfactual = evidence_sequences(event, generated_index)
    candidates = {}
    for name, suffix in (("original_candidate", original), ("counterfactual_candidate", counterfactual)):
        candidates[name] = score_evidence_suffix(
            model=model,
            prepared=prepared,
            prefix_token_ids=prefix,
            bridge_token_ids=bridge,
            suffix_token_ids=suffix,
            seed=seed,
        )
    lo = float(candidates["original_candidate"]["mean_log_probability"])
    lc = float(candidates["counterfactual_candidate"]["mean_log_probability"])
    return {"L_o": lo, "L_c": lc, "D": lo - lc, "finite": True, **candidates}


def score_arm(
    *,
    model: Any,
    prepared: dict[str, Any],
    event: dict[str, Any],
    current_generated_index: int,
    query_generated_indices: Sequence[int],
    layer_indices: Sequence[int],
    source_positions: Sequence[int],
    all_heads: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    prefix, bridge, original, counterfactual = evidence_sequences(event, current_generated_index)
    return score_window_preference(
        model=model,
        prepared=prepared,
        prefix_token_ids=prefix,
        bridge_token_ids=bridge,
        original_suffix_ids=original,
        counterfactual_suffix_ids=counterfactual,
        query_generated_indices=query_generated_indices,
        layer_indices=layer_indices,
        source_positions=source_positions,
        selected_heads=all_heads,
        gain=0.0,
        seed=seed,
    )


def arms_for_mode(
    *,
    mode: str,
    current: int,
    target_layer: int,
    layers: dict[str, list[int]],
    temporal: dict[str, int],
    interactions: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if mode == "validation":
        return [
            {"arm_id": "single_target_layer_current", "layers": [int(target_layer)], "backward": 0, "source": "T"},
            {"arm_id": "L0_current", "layers": layers["L0"], "backward": 0, "source": "T"},
            {"arm_id": "L4_current", "layers": layers["L4"], "backward": 0, "source": "T"},
            {"arm_id": "L4_last4", "layers": layers["L4"], "backward": 4, "source": "T"},
            {"arm_id": "late_last4", "layers": layers["L2"], "backward": 4, "source": "T"},
        ]
    if mode == "phase_a":
        return [
            {"arm_id": label, "layers": selected, "backward": 0, "source": "T"}
            for label, selected in layers.items()
        ]
    if mode == "phase_b":
        return [
            {"arm_id": label, "layers": layers["L4"], "backward": backward, "source": "T"}
            for label, backward in temporal.items()
            if current - int(backward) > 0
        ]
    if mode == "phase_c":
        rows = [
            {
                "arm_id": label,
                "layers": [int(value) for value in spec["layers"]],
                "backward": int(spec["backward"]),
                "source": "T",
            }
            for label, spec in interactions.items()
            if current - int(spec["backward"]) > 0
        ]
        for source in ("M", "I"):
            for label in ("T0", "T4"):
                backward = int(temporal[label])
                if current - backward > 0:
                    rows.append({
                        "arm_id": f"{source}_{label}",
                        "layers": layers["L4"],
                        "backward": backward,
                        "source": source,
                    })
        return rows
    raise ValueError(mode)


def main() -> None:
    args = parse_args()
    config = read_json(args.config)
    layers = read_json(OUT / "config/layer_scopes.json")["scopes"]
    temporal = read_json(OUT / "config/temporal_windows.json")["backward_offsets"]
    interactions = read_json(OUT / "config/interaction_cells.json")["cells"]
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", str(args.shard_index)))
    if world_size > 1:
        args.shard_index = local_rank
        args.shard_count = world_size
    torch.cuda.set_device(local_rank if world_size > 1 else 0)
    output_dir = args.output_dir.resolve()
    output_dir.relative_to(OUT.resolve())
    if world_size > 1:
        output_dir = output_dir / f"shard_{local_rank}"
    manifest = read_jsonl(args.manifest)[args.shard_index::args.shard_count]
    if args.max_bases:
        manifest = manifest[: args.max_bases]
    events = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")
    }
    rois = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")
    }
    mentions = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3c2/annotations/mention_roi_annotations.jsonl")
    }
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "run_config.json", {
        "mode": args.mode,
        "manifest": str(args.manifest.resolve()),
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "repeat_first": bool(args.repeat_first),
    })
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Stage 3C.4 requires A5000, observed {environment['gpu_name']}")
    observed = {
        "language_layers": int(model.config.text_config.num_hidden_layers),
        "logical_query_heads": int(model.config.text_config.num_attention_heads),
        "kv_heads": int(model.config.text_config.num_key_value_heads),
        "query_heads_per_kv_group": int(
            model.config.text_config.num_attention_heads // model.config.text_config.num_key_value_heads
        ),
        "head_dimension": int(model.config.text_config.head_dim),
    }
    if observed != config["architecture_expected"]:
        raise RuntimeError(f"Architecture mismatch: {observed}")
    write_json(output_dir / "environment.json", {**environment, "architecture_observed": observed})
    torch.cuda.reset_peak_memory_stats()
    run_started = time.perf_counter()
    all_heads = [int(value) for value in config["intervention"]["all_heads"]]

    completed = 0
    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume:
                raise FileExistsError(result_path)
            completed += 1
            print(f"[{completed}/{len(manifest)}] resume skip base {base}", flush=True)
            continue
        started = time.perf_counter()
        event, roi, mention = events[base], rois[base], mentions[base]
        source_row = data[str(item["example_id"])]
        prepared, metadata = prepare_custom_image(
            processor, source_row, condition_original_path(base), device="cuda"
        )
        if metadata["visual_token_indices"] != roi["absolute_source_groups"]["V_all"]:
            raise RuntimeError(f"Visual-token layout mismatch for base {base}")
        groups = source_groups(
            target=roi["absolute_source_groups"]["V_target"],
            mention=mention["mention_absolute_source_positions"],
            irrelevant=roi["absolute_source_groups"]["V_irrelevant"],
        )
        pair_by_target = {row["target_id"]: row for row in item["state_pairs"]}
        target_results: dict[str, Any] = {}
        for target_id in ("target_a", "target_b"):
            current = int(pair_by_target[target_id]["state_R"]["generated_index"])
            baseline = native_score(
                model=model, prepared=prepared, event=event,
                generated_index=current, seed=int(config["seed"]),
            )
            arms: dict[str, Any] = {}
            for arm in arms_for_mode(
                mode=args.mode,
                current=current,
                target_layer=int(config["targets"][target_id]["layer_index"]),
                layers=layers,
                temporal=temporal,
                interactions=interactions,
            ):
                queries = temporal_query_indices(
                    current_generated_index=current, backward=int(arm["backward"])
                )
                score = score_arm(
                    model=model,
                    prepared=prepared,
                    event=event,
                    current_generated_index=current,
                    query_generated_indices=queries,
                    layer_indices=arm["layers"],
                    source_positions=groups[arm["source"]],
                    all_heads=all_heads,
                    seed=int(config["seed"]),
                )
                arms[arm["arm_id"]] = {
                    "source_group": arm["source"],
                    "backward": int(arm["backward"]),
                    "query_generated_indices": queries,
                    "layer_indices": [int(value) for value in arm["layers"]],
                    "score": score,
                }
            identity = None
            repeat = None
            if args.mode == "validation" and item_index == 0:
                queries = [current]
                prefix, bridge, original, counterfactual = evidence_sequences(event, current)
                identity_score = score_window_preference(
                    model=model,
                    prepared=prepared,
                    prefix_token_ids=prefix,
                    bridge_token_ids=bridge,
                    original_suffix_ids=original,
                    counterfactual_suffix_ids=counterfactual,
                    query_generated_indices=queries,
                    layer_indices=layers["L0"],
                    source_positions=groups["T"],
                    selected_heads=all_heads,
                    gain=1.0,
                    seed=int(config["seed"]),
                )
                identity = {
                    "D_exact": float(identity_score["D"]) == float(baseline["D"]),
                    "original_token_log_probabilities_exact": (
                        identity_score["original_candidate"]["token_log_probabilities"]
                        == baseline["original_candidate"]["token_log_probabilities"]
                    ),
                    "counterfactual_token_log_probabilities_exact": (
                        identity_score["counterfactual_candidate"]["token_log_probabilities"]
                        == baseline["counterfactual_candidate"]["token_log_probabilities"]
                    ),
                    "score": identity_score,
                }
                if args.repeat_first:
                    repeated = score_arm(
                        model=model,
                        prepared=prepared,
                        event=event,
                        current_generated_index=current,
                        query_generated_indices=arms["L4_last4"]["query_generated_indices"],
                        layer_indices=arms["L4_last4"]["layer_indices"],
                        source_positions=groups["T"],
                        all_heads=all_heads,
                        seed=int(config["seed"]),
                    )
                    repeat = {
                        "exact": deterministic_view(repeated) == deterministic_view(arms["L4_last4"]["score"]),
                        "D_max_abs_delta": abs(float(repeated["D"]) - float(arms["L4_last4"]["score"]["D"])),
                    }
            target_results[target_id] = {
                "coordinate": config["targets"][target_id]["coordinate"],
                "retrieval_generated_index": current,
                "native": baseline,
                "arms": arms,
                "identity_audit": identity,
                "repeat_audit": repeat,
            }
        write_json(result_path, {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "cohort_role": item["stage3c4_cohort_role"],
            "mode": args.mode,
            "condition": "O",
            "source_groups": groups,
            "condition_layout_exact": True,
            "target_results": target_results,
            "runtime_seconds": time.perf_counter() - started,
            "selection_used_attention": False,
            "target_contribution_only": True,
            "teacher_forced_tokens_frozen": True,
            "downstream_recomputation_allowed": True,
            "sink_directly_intervened": False,
            "donor_state_patched": False,
        })
        completed += 1
        print(f"[{completed}/{len(manifest)}] {args.mode} base {base} seconds={time.perf_counter()-started:.1f}", flush=True)
        del prepared, metadata, target_results
        gc.collect()
        torch.cuda.empty_cache()
    write_json(output_dir / "resource_summary.json", {
        "mode": args.mode,
        "completed": completed,
        "requested": len(manifest),
        "wall_seconds_after_model_load": time.perf_counter() - run_started,
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "gpu_name": str(environment["gpu_name"]),
    })


if __name__ == "__main__":
    main()
