#!/usr/bin/env python3
"""Run Stage 3C.3-R validation, selected-path gain, or nested redundancy scoring."""

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
from visual_reasoning.stage3c3r.runtime import score_gain_preference


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3r"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("validation", "phase_a", "phase_b"), required=True)
    parser.add_argument("--config", type=Path, default=OUT / "config/stage3c3r_config.json")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-bases", type=int, default=0)
    parser.add_argument("--baseline-audit", action="store_true")
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
        return {
            key: deterministic_view(item)
            for key, item in value.items()
            if key != "runtime_seconds"
        }
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
    if any(sets[i] & sets[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError("T/M/I groups must be disjoint")
    return groups


def public_score(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "L_o": float(row["L_o"]),
        "L_c": float(row["L_c"]),
        "D": float(row["D"]),
        "finite": bool(row["finite"]),
        "original_candidate": row["original_candidate"],
        "counterfactual_candidate": row["counterfactual_candidate"],
        "candidate_audits": row["candidate_audits"],
        "generated_index": int(row["generated_index"]),
        "absolute_position": int(row["absolute_position"]),
        "gain": float(row["gain"]),
        "layer_specs": row["layer_specs"],
    }


def score_arm(
    *,
    model: Any,
    prepared: dict[str, Any],
    event: dict[str, Any],
    generated_index: int,
    layer_specs: list[dict[str, Any]],
    gain: float,
    groups: dict[str, list[int]],
    seed: int,
) -> dict[str, Any]:
    prefix, bridge, original, counterfactual = evidence_sequences(event, generated_index)
    return public_score(score_gain_preference(
        model=model,
        prepared=prepared,
        prefix_token_ids=prefix,
        bridge_token_ids=bridge,
        original_suffix_ids=original,
        counterfactual_suffix_ids=counterfactual,
        generated_index=generated_index,
        layer_specs=layer_specs,
        gain=gain,
        audit_groups=groups,
        seed=seed,
    ))


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
    return {"L_o": lo, "L_c": lc, "D": lo - lc, **candidates}


def phase_a_families(
    target: dict[str, Any], groups: dict[str, list[int]], grids: dict[str, Any]
) -> list[dict[str, Any]]:
    layer = int(target["layer_index"])
    causal = [int(value) for value in target["causal_heads"]]
    noncausal = [int(value) for value in target["noncausal_heads"]]
    target_grid = [float(value) for value in grids["phase_a_target"]]
    control_grid = [float(value) for value in grids["phase_a_controls"]]
    return [
        {
            "arm_id": "target_causal",
            "source_group": "T",
            "head_role": "causal",
            "lambdas": target_grid,
            "layer_specs": [{"layer_index": layer, "heads": causal, "source_positions": groups["T"]}],
        },
        {
            "arm_id": "mention_causal",
            "source_group": "M",
            "head_role": "causal",
            "lambdas": control_grid,
            "layer_specs": [{"layer_index": layer, "heads": causal, "source_positions": groups["M"]}],
        },
        {
            "arm_id": "irrelevant_causal",
            "source_group": "I",
            "head_role": "causal",
            "lambdas": control_grid,
            "layer_specs": [{"layer_index": layer, "heads": causal, "source_positions": groups["I"]}],
        },
        {
            "arm_id": "target_noncausal",
            "source_group": "T",
            "head_role": "noncausal",
            "lambdas": control_grid,
            "layer_specs": [{"layer_index": layer, "heads": noncausal, "source_positions": groups["T"]}],
        },
    ]


def phase_b_families(
    *, target_id: str, groups: dict[str, list[int]], grids: dict[str, Any], nested: dict[str, Any]
) -> list[dict[str, Any]]:
    result = []
    for scope_id in ("R1", "R2", "R3"):
        specs = [
            {
                "layer_index": int(spec["layer_index"]),
                "heads": [int(value) for value in spec["heads"]],
                "source_positions": groups["T"],
            }
            for spec in nested["scopes"][scope_id][target_id]
        ]
        result.append({
            "arm_id": scope_id,
            "source_group": "T",
            "head_role": "nested",
            "lambdas": [float(value) for value in grids["phase_b_nested_scopes"]],
            "layer_specs": specs,
        })
    return result


def main() -> None:
    args = parse_args()
    config = read_json(args.config)
    grids = read_json(OUT / "config/lambda_grid.json")
    nested = read_json(OUT / "config/nested_scope_family.json")
    if args.mode == "phase_b":
        gate = read_json(OUT / "phase_b_redundancy/redundancy_gate.json")
        if not gate.get("phase_b_authorized"):
            raise RuntimeError("Phase B is prohibited because the frozen redundancy gate did not pass")
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
        "baseline_audit": bool(args.baseline_audit),
        "repeat_first": bool(args.repeat_first),
    })
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Stage 3C.3-R requires A5000, observed {environment['gpu_name']}")
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
            target = config["targets"][target_id]
            generated_index = int(pair_by_target[target_id]["state_R"]["generated_index"])
            families = (
                phase_a_families(target, groups, grids)
                if args.mode != "phase_b"
                else phase_b_families(target_id=target_id, groups=groups, grids=grids, nested=nested)
            )
            target_rows: dict[str, Any] = {}
            baseline = None
            if args.baseline_audit and item_index == 0:
                baseline = native_score(
                    model=model, prepared=prepared, event=event,
                    generated_index=generated_index, seed=int(config["seed"]),
                )
            for family in families:
                lambda_rows = {}
                for gain in family["lambdas"]:
                    lambda_rows[str(gain)] = score_arm(
                        model=model,
                        prepared=prepared,
                        event=event,
                        generated_index=generated_index,
                        layer_specs=family["layer_specs"],
                        gain=float(gain),
                        groups=groups,
                        seed=int(config["seed"]),
                    )
                repeat_audit = None
                if args.repeat_first and item_index == 0 and family["arm_id"] == "target_causal":
                    repeated = score_arm(
                        model=model,
                        prepared=prepared,
                        event=event,
                        generated_index=generated_index,
                        layer_specs=family["layer_specs"],
                        gain=0.0,
                        groups=groups,
                        seed=int(config["seed"]),
                    )
                    repeat_audit = {
                        "gain": 0.0,
                        "exact": deterministic_view(lambda_rows["0.0"]) == deterministic_view(repeated),
                        "D_max_abs_delta": abs(float(lambda_rows["0.0"]["D"]) - float(repeated["D"])),
                    }
                baseline_audit = None
                if baseline is not None and "1.0" in lambda_rows:
                    intercepted = lambda_rows["1.0"]
                    baseline_audit = {
                        "D_exact": float(baseline["D"]) == float(intercepted["D"]),
                        "original_token_log_probabilities_exact": (
                            baseline["original_candidate"]["token_log_probabilities"]
                            == intercepted["original_candidate"]["token_log_probabilities"]
                        ),
                        "counterfactual_token_log_probabilities_exact": (
                            baseline["counterfactual_candidate"]["token_log_probabilities"]
                            == intercepted["counterfactual_candidate"]["token_log_probabilities"]
                        ),
                    }
                target_rows[family["arm_id"]] = {
                    "source_group": family["source_group"],
                    "head_role": family["head_role"],
                    "layer_specs": family["layer_specs"],
                    "lambda_results": lambda_rows,
                    "baseline_audit": baseline_audit,
                    "repeat_audit": repeat_audit,
                }
            target_results[target_id] = {
                "coordinate": target["coordinate"],
                "retrieval_generated_index": generated_index,
                "arms": target_rows,
            }
        write_json(result_path, {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "cohort_role": item["stage3c3r_cohort_role"],
            "mode": args.mode,
            "condition": "O",
            "source_groups": groups,
            "condition_layout_exact": True,
            "target_results": target_results,
            "runtime_seconds": time.perf_counter() - started,
            "selection_used_attention": False,
            "contribution_gain_only": True,
            "sink_directly_intervened": False,
            "query_or_hpre_directly_intervened": False,
        })
        completed += 1
        print(
            f"[{completed}/{len(manifest)}] {args.mode} base {base} seconds={time.perf_counter()-started:.1f}",
            flush=True,
        )
        del prepared, metadata, target_results
        gc.collect()
        torch.cuda.empty_cache()
    resource_summary = {
        "mode": args.mode,
        "completed": completed,
        "requested": len(manifest),
        "wall_seconds_after_model_load": time.perf_counter() - run_started,
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "gpu_name": str(environment["gpu_name"]),
    }
    write_json(output_dir / "resource_summary.json", resource_summary)
    print(json.dumps(resource_summary, indent=2))


if __name__ == "__main__":
    main()
