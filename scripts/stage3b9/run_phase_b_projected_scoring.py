#!/usr/bin/env python3
"""Run held-out local/global/random Phase-B Value-subspace interventions."""

from __future__ import annotations

import argparse
import gc
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

from scripts.stage3b8.run_value_scoring import score_arm
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3b8.runtime import capture_preference_value_states
from visual_reasoning.stage3b9.geometry import random_rank_family
from visual_reasoning.stage3b9.local_geometry import phase_b_condition_aliases


ROOT = Path(__file__).resolve().parents[2]
CONDITIONS = ("O", "O_sham", "C", "C_sham")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--roi-mapping", type=Path, required=True)
    parser.add_argument("--applicability", type=Path, required=True)
    parser.add_argument("--projectors", type=Path, required=True)
    parser.add_argument("--random-seeds", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--required-gpu-class", default="A5000")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def score_one(*, item: dict, annotation: dict, roi: dict, source_row: dict, processor, model, config: dict, applicability: dict, projectors: dict[str, np.ndarray], seeds: dict) -> dict:
    base = str(item["base_problem_id"])
    edit = read_json(ROOT / item["edit_metadata"])
    prepared, metadata = {}, {}
    for condition, relative in edit["paths"].items():
        prepared[condition], metadata[condition] = prepare_custom_image(processor, source_row, ROOT / relative, device="cuda")
    prompt_ids = [metadata[name]["prompt_token_ids"] for name in edit["paths"]]
    visual_sets = [metadata[name]["visual_token_indices"] for name in edit["paths"]]
    grids = [metadata[name]["image_grid_thw"] for name in edit["paths"]]
    layout_exact = bool(
        all(value == prompt_ids[0] for value in prompt_ids[1:])
        and all(value == visual_sets[0] for value in visual_sets[1:])
        and all(value == grids[0] for value in grids[1:])
        and visual_sets[0] == roi["visual_absolute_positions"]
        and grids[0] == roi["image_grid_thw"]
    )
    if not layout_exact:
        raise RuntimeError(f"Phase-B projected layout mismatch for base {base}")
    question = str(source_row.get("query_cot") or source_row.get("question") or "")
    base_groups = build_token_groups(prompt_token_ids=prompt_ids[0], visual_token_indices=visual_sets[0], question_token_ids=processor.tokenizer.encode(question, add_special_tokens=False))
    source_groups = {key: [int(value) for value in values] for key, values in roi["absolute_source_groups"].items()}
    if source_groups["V_all"] != base_groups["V"]:
        raise RuntimeError(f"All-visual mapping mismatch for base {base}")
    attention_groups = {key: source_groups[key] for key in ("V_all", "V_target", "V_other", "V_irrelevant", "V_target_ring")}
    pairs = {row["pair_id"]: row for row in annotation["candidate_pairs"]}
    target_rows = []
    mechanics = {
        "all_layout_and_roi_mappings_exact": bool(layout_exact and roi["target_complement_partition_exact"] and roi["target_ring_irrelevant_disjoint"]),
        "all_query_head_selectivity_valid": True,
        "all_recipient_tensor_alignment_exact": True,
        "all_self_restorations_exact": True,
        "all_scores_finite": True,
    }
    for target in config["targets"]:
        target_id = target["target_id"]
        gate = applicability[(base, target_id)]
        if not gate["eligible"]:
            target_rows.append({**target, "applicability_eligible": False, "pairs": []})
            continue
        pair_rows = []
        for value_index in range(1, 5):
            pair_id = f"value_{value_index}"
            pair = pairs[pair_id]
            aliases = phase_b_condition_aliases(value_index)
            pair_prepared = {alias: prepared[condition] for alias, condition in aliases.items()}
            context = [int(value) for value in pair["history_before_ed_token_ids"]]
            ed = int(pair["ed_generated_index"])
            candidate_o = [int(value) for value in pair["original_divergent_suffix_ids"]]
            candidate_c = [int(value) for value in pair["counterfactual_divergent_suffix_ids"]]
            intervention = ed - 1 if target["coordinate"] == "Ed_minus_1" else ed
            captures = {
                condition: capture_preference_value_states(
                    model=model,
                    prepared=pair_prepared[condition],
                    context_token_ids=context,
                    candidate_original_ids=candidate_o,
                    candidate_counterfactual_ids=candidate_c,
                    intervention_generated_index=intervention,
                    layer_index=int(target["layer_index"]),
                    selected_query_heads=target["heads"],
                    roi_positions=source_groups["V_target"],
                    attention_groups=attention_groups,
                    seed=int(config["locked_generation_protocol"]["seed"]),
                )
                for condition in CONDITIONS
            }
            arms = []
            for rank in (1, 2, 3):
                local = torch.from_numpy(np.asarray(projectors[f"{base}__{target_id}__{pair_id}__local_rank_{rank}"], dtype=np.float64))
                global_basis = torch.from_numpy(np.asarray(projectors[f"{target_id}__global_rank_{rank}"], dtype=np.float64))
                for arm_id, basis, complement in (
                    (f"local_rank_{rank}", local, False),
                    (f"local_complement_rank_{rank}", local, True),
                    (f"global_rank_{rank}", global_basis, False),
                ):
                    arm = score_arm(
                        model=model, prepared=pair_prepared, captures=captures, context=context,
                        candidate_original=candidate_o, candidate_counterfactual=candidate_c,
                        intervention_index=intervention, target=target, roi_positions=source_groups["V_target"],
                        dose=1.0, projector_basis=basis, projector_complement=complement,
                        seed=int(config["locked_generation_protocol"]["seed"]), arm_id=arm_id, reference_scores=None,
                    )
                    arms.append(arm)
            for random_index in range(100):
                seed = int(seeds[(base, target_id, pair_id, random_index)])
                family = random_rank_family(dimension=512, ranks=(1, 2, 3), seed=seed)
                for rank in (1, 2, 3):
                    arm = score_arm(
                        model=model, prepared=pair_prepared, captures=captures, context=context,
                        candidate_original=candidate_o, candidate_counterfactual=candidate_c,
                        intervention_index=intervention, target=target, roi_positions=source_groups["V_target"],
                        dose=1.0, projector_basis=torch.from_numpy(family[rank]), projector_complement=False,
                        seed=int(config["locked_generation_protocol"]["seed"]),
                        arm_id=f"random_{random_index:03d}_rank_{rank}", reference_scores=None,
                    )
                    arms.append(arm)
            for arm in arms:
                mechanics["all_query_head_selectivity_valid"] &= bool(arm["all_query_head_selectivity_valid"])
                mechanics["all_recipient_tensor_alignment_exact"] &= bool(arm["all_recipient_tensor_alignment_exact"])
                mechanics["all_self_restorations_exact"] &= bool(arm["all_self_restorations_exact"])
                mechanics["all_scores_finite"] &= bool(arm["all_scores_finite"])
            pair_rows.append({
                "pair_id": pair_id,
                "counterfactual_value": pair["counterfactual_value"],
                "full_v_usable": next(row for row in gate["pairs"] if row["pair_id"] == pair_id)["usable"],
                "prefix_sha256": pair["history_before_ed_sha256"],
                "intervention_generated_index": intervention,
                "arms": arms,
            })
        target_rows.append({**target, "applicability_eligible": True, "pairs": pair_rows})
    return {
        "base_problem_id": base,
        "example_id": str(item["example_id"]),
        "phase": "phase_b",
        "experiment": "leave_one_value_out_projected_scoring",
        "condition_layout_exact": layout_exact,
        "selection_used_attention": False,
        "targets": target_rows,
        "mechanical_controls": mechanics,
    }


def main() -> None:
    args = parse_args()
    manifest = read_jsonl(args.manifest)
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(args.annotations)}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(args.roi_mapping)}
    applicability = {(str(row["base_problem_id"]), row["target_id"]): row for row in read_jsonl(args.applicability)}
    projectors = dict(np.load(args.projectors))
    seed_payload = read_json(args.random_seeds)
    seeds = {(str(row["base_problem_id"]), row["target_id"], row["pair_id"], int(row["random_index"])): int(row["seed"]) for row in seed_payload["rows"]}
    config = read_json(args.config)
    output_dir = args.output_dir.resolve()
    signature = {
        "manifest": str(args.manifest.resolve()), "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "annotations": str(args.annotations.resolve()), "roi_mapping": str(args.roi_mapping.resolve()),
        "applicability": str(args.applicability.resolve()), "projectors": str(args.projectors.resolve()),
        "random_seeds": str(args.random_seeds.resolve()), "config": str(args.config.resolve()),
        "dataset_root": str(args.dataset_root.resolve()), "model_checkpoint": str(args.model_checkpoint.resolve()),
    }
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.resume or read_json(output_dir / "config.json")["run_signature"] != signature:
            raise RuntimeError(f"Cannot resume incompatible output: {output_dir}")
    else:
        ensure_directory(output_dir)
        write_json(output_dir / "config.json", {"created_at": datetime.now(timezone.utc).isoformat(), "run_signature": signature})
        write_jsonl(output_dir / "manifest.jsonl", manifest)
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if args.required_gpu_class not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {args.required_gpu_class}, observed {environment['gpu_name']}")
    write_json(output_dir / "environment.json", environment)
    torch.cuda.reset_peak_memory_stats()
    results = []
    for index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if args.resume and result_path.is_file():
            results.append(read_json(result_path)); print(f"[{index + 1}/{len(manifest)}] resumed base {base}", flush=True); continue
        result = score_one(item=item, annotation=annotations[base], roi=rois[base], source_row=data[str(item["example_id"])], processor=processor, model=model, config=config, applicability=applicability, projectors=projectors, seeds=seeds)
        ensure_directory(result_path.parent)
        write_json(result_path, result)
        results.append(result)
        print(f"[{index + 1}/{len(manifest)}] completed base {base}", flush=True)
        gc.collect(); torch.cuda.empty_cache()
    write_jsonl(output_dir / "results.jsonl", results)
    write_json(output_dir / "result.json", {
        "completed_at": datetime.now(timezone.utc).isoformat(), "base_problem_count": len(results),
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "all_mechanical_controls_passed": all(all(value for key, value in row["mechanical_controls"].items() if key.startswith("all_")) for row in results),
    })


if __name__ == "__main__":
    main()
