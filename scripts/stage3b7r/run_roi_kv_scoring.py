#!/usr/bin/env python3
"""Score frozen Stage 3B.7-R spatial or K/V interventions.

Fresh validation captures its own baselines. Primary scoring can additionally
check those baselines against the immutable Stage 3B.5 reference artifacts.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3b6.runtime import CANDIDATES, capture_preference_head_states


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/stage3b7"))
from run_roi_kv_scoring import (  # noqa: E402
    legacy_all_v_score,
    public_capture,
    score_unit,
    scores_exact,
)


OUT = ROOT / "outputs/stage3b7r"
CONDITIONS = ("O", "O_sham", "C", "C_sham")
PHASE_A_GROUPS = {
    "all_visual": "V_all",
    "target_roi": "V_target",
    "visual_complement": "V_other",
    "irrelevant_roi": "V_irrelevant",
    "target_ring": "V_target_ring",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--roi-mapping", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--targets", type=Path)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cohort-role", choices=("fresh_validation", "primary"), required=True)
    parser.add_argument("--phase", choices=("phase_a", "phase_b"), required=True)
    parser.add_argument("--stage3b5-raw-root", type=Path)
    parser.add_argument("--required-gpu-class", default="A5000")
    parser.add_argument("--repeat-first", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def add_layer_role(target: dict[str, Any]) -> dict[str, Any]:
    result = dict(target)
    expected = "second" if result["coordinate"] == "Ed" else "first"
    if result.get("layer_role", expected) != expected:
        raise RuntimeError(f"Unexpected layer role for {result['target_id']}")
    result["layer_role"] = expected
    return result


def target_rows(config: dict[str, Any], target_path: Path | None) -> list[dict[str, Any]]:
    if target_path is None:
        rows = config["targets"]
    else:
        payload = read_json(target_path)
        rows = payload.get("targets", payload.get("eligible_targets", []))
    if not rows:
        raise RuntimeError("No frozen eligible targets were supplied")
    return [add_layer_role(row) for row in rows]


def reference_paths(root: Path | None) -> dict[str, Path]:
    if root is None:
        return {}
    found: dict[str, Path] = {}
    for path in sorted(root.glob("**/examples/*/result.json")):
        base = path.parent.name
        if base in found:
            raise RuntimeError(f"Duplicate Stage 3B.5 reference for base {base}")
        found[base] = path
    return found


def reference_point(row: dict[str, Any], coordinate: str) -> dict[str, Any]:
    return next(point for point in row["coordinates"] if point["coordinate"] == coordinate)


def paired_metadata(item: dict[str, Any], cohort_role: str) -> dict[str, Any]:
    path = (
        ROOT / item["edit_metadata"]
        if cohort_role == "fresh_validation"
        else ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / str(item["base_problem_id"]) / "edit_metadata.json"
    )
    paired = read_json(path)
    if paired["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Four-condition edit validation failed for base {item['base_problem_id']}")
    paired["_metadata_path"] = str(path.relative_to(ROOT))
    return paired


def finite_capture(capture: dict[str, Any]) -> bool:
    return bool(
        math.isfinite(float(capture["D"]))
        and all(bool(capture[candidate]["finite"]) for candidate in CANDIDATES)
    )


def token_hash(token_ids: list[int]) -> str:
    payload = json.dumps([int(value) for value in token_ids], separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def score_one(
    *,
    item: dict[str, Any],
    annotation: dict[str, Any],
    roi: dict[str, Any],
    source_row: dict[str, Any],
    processor: Any,
    model: Any,
    targets: list[dict[str, Any]],
    seed: int,
    cohort_role: str,
    phase: str,
    stage3b5: dict[str, Any] | None,
) -> dict[str, Any]:
    base = str(item["base_problem_id"])
    paired = paired_metadata(item, cohort_role)
    if roi["manual_overlay_validation"]["status"] != "pass":
        raise RuntimeError(f"ROI overlay validation failed for base {base}")

    prepared: dict[str, dict[str, Any]] = {}
    metadata: dict[str, dict[str, Any]] = {}
    for condition in CONDITIONS:
        prepared[condition], metadata[condition] = prepare_custom_image(
            processor, source_row, ROOT / paired["paths"][condition], device="cuda"
        )
    prompt_ids = [metadata[condition]["prompt_token_ids"] for condition in CONDITIONS]
    visual_sets = [metadata[condition]["visual_token_indices"] for condition in CONDITIONS]
    grids = [metadata[condition]["image_grid_thw"] for condition in CONDITIONS]
    layout_exact = bool(
        all(value == prompt_ids[0] for value in prompt_ids[1:])
        and all(value == visual_sets[0] for value in visual_sets[1:])
        and all(value == grids[0] for value in grids[1:])
        and visual_sets[0] == roi["visual_absolute_positions"]
        and grids[0] == roi["image_grid_thw"]
    )
    if not layout_exact:
        raise RuntimeError(f"Condition/ROI token layout mismatch for base {base}")

    context = [int(value) for value in annotation["history_before_ed_token_ids"]]
    ed = int(annotation["ed_generated_index"])
    if len(context) != ed:
        raise RuntimeError(f"Frozen E_d history mismatch for base {base}")
    candidate_original = [int(value) for value in annotation["original_divergent_suffix_ids"]]
    candidate_counterfactual = [int(value) for value in annotation["counterfactual_divergent_suffix_ids"]]
    question = str(source_row.get("query_cot") or source_row.get("question") or "")
    base_groups = build_token_groups(
        prompt_token_ids=prompt_ids[0],
        visual_token_indices=visual_sets[0],
        question_token_ids=processor.tokenizer.encode(question, add_special_tokens=False),
    )
    source_groups = {key: [int(value) for value in values] for key, values in roi["absolute_source_groups"].items()}
    if source_groups["V_all"] != base_groups["V"]:
        raise RuntimeError(f"Frozen all-visual group changed for base {base}")
    attention_groups = {key: source_groups[key] for key in ("V_all", "V_target", "V_other", "V_irrelevant", "V_target_ring")}

    mechanical = {
        "all_reference_baselines_exact": True if stage3b5 is not None else None,
        "all_query_head_selectivity_valid": True,
        "all_source_group_isolation_valid": True,
        "all_self_restorations_exact": True,
        "all_scores_finite": True,
        "all_roi_mappings_exact": bool(
            roi["target_complement_partition_exact"]
            and roi["target_ring_irrelevant_disjoint"]
            and roi["four_condition_layout_exact"]
            and roi["manual_overlay_validation"]["status"] == "pass"
        ),
    }
    output_targets = []
    for target in targets:
        intervention_index = ed - 1 if target["coordinate"] == "Ed_minus_1" else ed
        captures = {
            condition: capture_preference_head_states(
                model=model,
                prepared=prepared[condition],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                intervention_generated_index=intervention_index,
                layer_index=int(target["layer_index"]),
                attention_groups=attention_groups,
                seed=seed,
            )
            for condition in CONDITIONS
        }
        baseline_exact = None
        if stage3b5 is not None:
            point = reference_point(stage3b5, target["coordinate"])
            baseline_exact = {
                condition: scores_exact(captures[condition], point["no_switch"][condition])
                for condition in CONDITIONS
            }
            mechanical["all_reference_baselines_exact"] = bool(
                mechanical["all_reference_baselines_exact"] and all(baseline_exact.values())
            )
        mechanical["all_scores_finite"] &= all(finite_capture(capture) for capture in captures.values())

        if phase == "phase_a":
            arms = [(arm, group, "KV") for arm, group in PHASE_A_GROUPS.items()]
        else:
            source_group = str(target["phase_b_source_group"])
            if source_group not in ("V_target", "V_target_ring"):
                raise RuntimeError(f"Invalid frozen Phase-B source group: {source_group}")
            arms = [(mode, source_group, mode) for mode in ("K", "V", "KV")]
        arm_results = []
        for arm, source_group, mode in arms:
            scored = score_unit(
                model=model,
                prepared=prepared,
                captures=captures,
                context=context,
                candidate_original=candidate_original,
                candidate_counterfactual=candidate_counterfactual,
                intervention_index=intervention_index,
                target=target,
                source_positions=source_groups[source_group],
                attention_groups=attention_groups,
                attention_gain=0.0,
                seed=seed,
                spatial_arm=arm,
                source_group=source_group,
                mode=mode,
            )
            if phase == "phase_a" and arm == "all_visual":
                legacy = legacy_all_v_score(
                    model=model,
                    prepared=prepared,
                    captures=captures,
                    context=context,
                    candidate_original=candidate_original,
                    candidate_counterfactual=candidate_counterfactual,
                    intervention_index=intervention_index,
                    target=target,
                    source_positions=source_groups[source_group],
                    attention_groups=attention_groups,
                    seed=seed,
                )
                scored["legacy_all_v_reference"] = legacy
                scored["legacy_all_v_recipient_scores_exact"] = bool(legacy["recipient_scores"] == scored["recipient_scores"])
            arm_results.append(scored)
            mechanical["all_query_head_selectivity_valid"] &= bool(scored["mechanical_audit"]["all_query_head_selectivity_valid"])
            mechanical["all_source_group_isolation_valid"] &= bool(scored["mechanical_audit"]["all_source_group_isolation_valid"])
            mechanical["all_self_restorations_exact"] &= bool(scored["all_self_restorations_exact"])
            mechanical["all_scores_finite"] &= bool(scored["all_scores_finite"])
        output_targets.append({
            **target,
            "intervention_generated_index": intervention_index,
            "baseline_exact_reference": baseline_exact,
            "no_intervention": {condition: public_capture(capture) for condition, capture in captures.items()},
            "arm_results": arm_results,
        })

    return {
        "base_problem_id": base,
        "example_id": str(item["example_id"]),
        "cohort_role": cohort_role,
        "phase": phase,
        "edit_metadata": paired["_metadata_path"],
        "prefix_sha256": annotation.get("history_before_ed_sha256") or token_hash(context),
        "ed_generated_index": ed,
        "condition_layout_exact": layout_exact,
        "selection_used_attention": False,
        "roi_mapping": {
            "target_token_count": roi["target_token_count"],
            "ring_token_count": roi["ring_token_count"],
            "irrelevant_token_count": roi["irrelevant_token_count"],
            "target_complement_partition_exact": roi["target_complement_partition_exact"],
            "target_ring_irrelevant_disjoint": roi["target_ring_irrelevant_disjoint"],
        },
        "targets": output_targets,
        "mechanical_controls": mechanical,
    }


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to((OUT / "scoring/raw").resolve())
    config = read_json(args.config)
    targets = target_rows(config, args.targets)
    manifest = read_jsonl(args.manifest)
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(args.annotations)}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(args.roi_mapping)}
    references = reference_paths(args.stage3b5_raw_root)
    if args.cohort_role == "primary" and len(references) < len(manifest):
        raise RuntimeError("Primary scoring requires immutable Stage 3B.5 references")
    seed = int(config["locked_generation_protocol"]["seed"])
    signature = {
        "manifest": str(args.manifest.resolve()),
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "annotations": str(args.annotations.resolve()),
        "roi_mapping": str(args.roi_mapping.resolve()),
        "config": str(args.config.resolve()),
        "targets": str(args.targets.resolve()) if args.targets else None,
        "dataset_root": str(args.dataset_root.resolve()),
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "cohort_role": args.cohort_role,
        "phase": args.phase,
        "stage3b5_raw_root": str(args.stage3b5_raw_root.resolve()) if args.stage3b5_raw_root else None,
        "seed": seed,
    }
    config_path = output_dir / "config.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.resume or not config_path.is_file() or read_json(config_path)["run_signature"] != signature:
            raise RuntimeError(f"Non-empty output cannot be resumed with this signature: {output_dir}")
    else:
        ensure_directory(output_dir)
        write_json(config_path, {"created_at": datetime.now(timezone.utc).isoformat(), "run_signature": signature})
        write_jsonl(output_dir / "manifest.jsonl", manifest)

    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if args.required_gpu_class not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {args.required_gpu_class}, observed {environment['gpu_name']}")
    expected_architecture = read_json(ROOT / "outputs/stage3b6/config/stage3b6_config.json")["architecture_expected"]
    text_config = model.config.text_config
    observed_architecture = {
        "language_layers": int(text_config.num_hidden_layers),
        "logical_query_heads": int(text_config.num_attention_heads),
        "kv_heads": int(text_config.num_key_value_heads),
        "query_heads_per_kv_group": int(text_config.num_attention_heads // text_config.num_key_value_heads),
        "head_dimension": int(text_config.head_dim),
    }
    if observed_architecture != expected_architecture:
        raise RuntimeError(f"GQA architecture mismatch: {observed_architecture} != {expected_architecture}")
    environment["stage3b7r_gqa_architecture"] = observed_architecture
    write_json(output_dir / "environment.json", environment)
    torch.cuda.reset_peak_memory_stats()

    results = []
    repeat_payload = None
    for index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if args.resume and result_path.is_file():
            results.append(read_json(result_path))
            print(f"[{index + 1}/{len(manifest)}] resumed base {base}", flush=True)
            continue
        if base not in annotations or base not in rois or str(item["example_id"]) not in data:
            raise RuntimeError(f"Missing annotation, ROI, or dataset row for base {base}")
        result = score_one(
            item=item,
            annotation=annotations[base],
            roi=rois[base],
            source_row=data[str(item["example_id"])],
            processor=processor,
            model=model,
            targets=targets,
            seed=seed,
            cohort_role=args.cohort_role,
            phase=args.phase,
            stage3b5=read_json(references[base]) if base in references else None,
        )
        ensure_directory(result_path.parent)
        write_json(result_path, result)
        results.append(result)
        if args.repeat_first and index == 0:
            repeated = score_one(
                item=item,
                annotation=annotations[base],
                roi=rois[base],
                source_row=data[str(item["example_id"])],
                processor=processor,
                model=model,
                targets=targets,
                seed=seed,
                cohort_role=args.cohort_role,
                phase=args.phase,
                stage3b5=read_json(references[base]) if base in references else None,
            )
            repeat_payload = {"base_problem_id": base, "exact_public_result_match": repeated == result}
            write_json(output_dir / "determinism_repeat.json", repeat_payload)
        print(f"[{index + 1}/{len(manifest)}] completed base {base}", flush=True)
        gc.collect()
        torch.cuda.empty_cache()

    write_jsonl(output_dir / "results.jsonl", results)
    boolean_mechanics = [
        value
        for result in results
        for key, value in result["mechanical_controls"].items()
        if key.startswith("all_") and value is not None
    ]
    all_legacy_exact = all(
        bool(arm["legacy_all_v_recipient_scores_exact"])
        for result in results
        for target in result["targets"]
        for arm in target["arm_results"]
        if args.phase == "phase_a" and arm["spatial_arm"] == "all_visual"
    ) if args.phase == "phase_a" else None
    summary = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "cohort_role": args.cohort_role,
        "phase": args.phase,
        "base_problem_count": len(results),
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "all_condition_layout_exact": all(result["condition_layout_exact"] for result in results),
        "all_mechanical_controls_passed": all(boolean_mechanics),
        "all_legacy_all_v_recipient_scores_exact": all_legacy_exact,
        "determinism_repeat": repeat_payload,
    }
    write_json(output_dir / "result.json", summary)


if __name__ == "__main__":
    main()
