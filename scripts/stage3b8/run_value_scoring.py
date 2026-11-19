#!/usr/bin/env python3
"""Run frozen Stage 3B.8 ROI-derived Value dose or projector scoring."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3b8.geometry import flatten_head_vectors
from visual_reasoning.stage3b8.metrics import value_restoration_metrics
from visual_reasoning.stage3b8.runtime import (
    CANDIDATES,
    capture_preference_value_states,
    score_preference_with_value_delta,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8"
CONDITIONS = ("O", "O_sham", "C", "C_sham")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--roi-mapping", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cohort-role", choices=("discovery", "primary"), required=True)
    parser.add_argument("--experiment", choices=("capture", "dose", "projected"), required=True)
    parser.add_argument("--projectors", type=Path)
    parser.add_argument("--arms", type=Path)
    parser.add_argument("--stage3b7r-reference-root", type=Path)
    parser.add_argument("--required-gpu-class", default="A5000")
    parser.add_argument("--repeat-first", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def token_hash(token_ids: list[int]) -> str:
    payload = json.dumps([int(value) for value in token_ids], separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def scores_exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["L_o"]) == float(right["L_o"])
        and float(left["L_c"]) == float(right["L_c"])
        and float(left["D"]) == float(right["D"])
        and all(
            left[candidate]["token_log_probabilities"]
            == right[candidate]["token_log_probabilities"]
            for candidate in CANDIDATES
        )
    )


def public_capture(capture: dict[str, Any]) -> dict[str, Any]:
    return {
        "L_o": float(capture["L_o"]),
        "L_c": float(capture["L_c"]),
        "D": float(capture["D"]),
        "current_absolute_position": int(capture["current_absolute_position"]),
        "capture_audits": capture["capture_audits"],
        **{
            candidate: {
                key: value for key, value in capture[candidate].items() if key != "runtime_seconds"
            }
            for candidate in CANDIDATES
        },
    }


def reference_paths(root: Path | None) -> dict[str, Path]:
    if root is None:
        return {}
    found: dict[str, Path] = {}
    for path in sorted(root.glob("primary_phase_b_*/examples/*/result.json")):
        base = path.parent.name
        if base in found:
            raise RuntimeError(f"Duplicate Stage 3B.7-R reference for base {base}")
        found[base] = path
    return found


def reference_v_scores(reference: dict[str, Any], cell_id: str) -> dict[str, dict[str, float]]:
    target = next(row for row in reference["targets"] if row["cell_id"] == cell_id)
    arm = next(row for row in target["arm_results"] if row["kv_mode"] == "V")
    return arm["recipient_scores"]


def paired_metadata(item: dict[str, Any], cohort_role: str) -> dict[str, Any]:
    if cohort_role == "discovery":
        path = ROOT / item["edit_metadata"]
    else:
        path = ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / str(item["base_problem_id"]) / "edit_metadata.json"
    metadata = read_json(path)
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Four-condition edit validation failed for base {item['base_problem_id']}")
    metadata["_metadata_path"] = str(path.relative_to(ROOT))
    return metadata


def finite_preference(row: dict[str, Any]) -> bool:
    return bool(
        math.isfinite(float(row["D"]))
        and all(bool(row[candidate]["finite"]) for candidate in CANDIDATES)
    )


def exact_symmetric_vectors(
    *,
    model: Any,
    prepared: dict[str, dict[str, Any]],
    captures: dict[str, dict[str, Any]],
    context: list[int],
    candidate_original: list[int],
    candidate_counterfactual: list[int],
    intervention_index: int,
    target: dict[str, Any],
    seed: int,
    heads: list[int],
    roi_positions: list[int],
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    def delta(recipient: str, donor: str) -> dict[str, torch.Tensor]:
        scored = score_preference_with_value_delta(
            model=model,
            prepared=prepared[recipient],
            context_token_ids=context,
            candidate_original_ids=candidate_original,
            candidate_counterfactual_ids=candidate_counterfactual,
            intervention_generated_index=intervention_index,
            layer_index=int(target["layer_index"]),
            selected_query_heads=heads,
            recipient_states_by_candidate=captures[recipient]["states"],
            donor_states_by_candidate=captures[donor]["states"],
            roi_positions=roi_positions,
            dose=0.0,
            projector_basis=None,
            seed=seed,
            return_vectors=True,
        )
        return scored["_full_delta_by_candidate"]

    o_to_c = delta("O", "C")
    c_to_o = delta("C", "O")
    o_to_o_sham = delta("O", "O_sham")
    c_to_c_sham = delta("C", "C_sham")
    semantic_by_candidate = {
        candidate: 0.5 * (
            flatten_head_vectors(c_to_o[candidate])
            - flatten_head_vectors(o_to_c[candidate])
        )
        for candidate in CANDIDATES
    }
    sham_by_candidate = {
        candidate: -0.5 * (
            flatten_head_vectors(o_to_o_sham[candidate])
            + flatten_head_vectors(c_to_c_sham[candidate])
        )
        for candidate in CANDIDATES
    }
    semantic_error = float(
        (
            semantic_by_candidate["original_candidate"]
            - semantic_by_candidate["counterfactual_candidate"]
        ).abs().max().item()
    )
    sham_error = float(
        (
            sham_by_candidate["original_candidate"]
            - sham_by_candidate["counterfactual_candidate"]
        ).abs().max().item()
    )
    semantic = semantic_by_candidate["original_candidate"].detach().float().cpu().numpy()[0]
    sham = sham_by_candidate["original_candidate"].detach().float().cpu().numpy()[0]
    return semantic, sham, {
        "candidate_semantic_delta_max_abs_error": semantic_error,
        "candidate_sham_delta_max_abs_error": sham_error,
        "candidate_invariance_exact": semantic_error == 0.0 and sham_error == 0.0,
        "semantic_delta_l2": float(np.linalg.norm(semantic)),
        "sham_delta_l2": float(np.linalg.norm(sham)),
    }


def score_arm(
    *,
    model: Any,
    prepared: dict[str, dict[str, Any]],
    captures: dict[str, dict[str, Any]],
    context: list[int],
    candidate_original: list[int],
    candidate_counterfactual: list[int],
    intervention_index: int,
    target: dict[str, Any],
    roi_positions: list[int],
    dose: float,
    projector_basis: torch.Tensor | None,
    projector_complement: bool,
    seed: int,
    arm_id: str,
    reference_scores: dict[str, dict[str, float]] | None,
) -> dict[str, Any]:
    restored = {
        recipient: {
            donor: score_preference_with_value_delta(
                model=model,
                prepared=prepared[recipient],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                intervention_generated_index=intervention_index,
                layer_index=int(target["layer_index"]),
                selected_query_heads=target["heads"],
                recipient_states_by_candidate=captures[recipient]["states"],
                donor_states_by_candidate=captures[donor]["states"],
                roi_positions=roi_positions,
                dose=dose,
                projector_basis=projector_basis,
                projector_complement=projector_complement,
                seed=seed,
            )
            for donor in CONDITIONS
        }
        for recipient in ("O", "C")
    }
    recipient_scores = {
        recipient: {donor: float(row["D"]) for donor, row in donors.items()}
        for recipient, donors in restored.items()
    }
    metrics = value_restoration_metrics(recipient_scores=recipient_scores)
    self_exact = {
        recipient: scores_exact(restored[recipient][recipient], captures[recipient])
        for recipient in ("O", "C")
    }
    native_endpoint_exact = None
    if float(dose) == 0.0:
        native_endpoint_exact = all(
            scores_exact(restored[recipient][donor], captures[recipient])
            for recipient in ("O", "C")
            for donor in CONDITIONS
        )
    reference_error = None
    reference_within_tolerance = None
    if reference_scores is not None and float(dose) == 1.0 and projector_basis is None:
        reference_error = max(
            abs(float(recipient_scores[recipient][donor]) - float(reference_scores[recipient][donor]))
            for recipient in ("O", "C")
            for donor in CONDITIONS
        )
        reference_within_tolerance = reference_error <= 1e-6
    audits = [
        preference[candidate]["value_patch_audit"]
        for donors in restored.values()
        for preference in donors.values()
        for candidate in CANDIDATES
    ]
    return {
        "arm_id": arm_id,
        "dose": float(dose),
        "projector_rank": int(projector_basis.shape[1]) if projector_basis is not None else None,
        "projector_component": (
            "orthogonal_complement" if projector_complement else "parallel"
        ) if projector_basis is not None else "full",
        **metrics,
        "recipient_scores": recipient_scores,
        "self_restoration_exact": self_exact,
        "all_self_restorations_exact": all(self_exact.values()),
        "native_endpoint_exact": native_endpoint_exact,
        "stage3b7r_v_reference_max_abs_D_error": reference_error,
        "stage3b7r_v_reference_within_tolerance": reference_within_tolerance,
        "all_scores_finite": all(
            finite_preference(preference)
            for donors in restored.values()
            for preference in donors.values()
        ),
        "all_query_head_selectivity_valid": all(
            set(audit["changed_query_heads"]).issubset(set(audit["selected_query_heads"]))
            and audit["nonselected_head_max_abs_delta"] == 0.0
            for audit in audits
        ),
        "all_recipient_tensor_alignment_exact": all(
            audit["recipient_attention_exact"] and audit["recipient_roi_value_exact"]
            for audit in audits
        ),
        "maximum_selected_head_delta": max(float(audit["selected_head_max_abs_delta"]) for audit in audits),
    }


def target_arms(
    *,
    experiment: str,
    target: dict[str, Any],
    config: dict[str, Any],
    projectors: dict[str, np.ndarray] | None,
    arm_config: dict[str, Any] | None,
) -> list[tuple[str, float, torch.Tensor | None, bool]]:
    if experiment == "dose":
        return [(f"lambda_{value:g}", float(value), None, False) for value in config["dose_response"]["lambdas"]]
    if experiment == "capture":
        return []
    if projectors is None or arm_config is None:
        raise ValueError("Projected scoring requires --projectors and --arms")
    rows = []
    for arm in arm_config["arms"]:
        allowed_targets = arm.get("target_ids")
        if allowed_targets is not None and target["target_id"] not in allowed_targets:
            continue
        basis = None
        key_by_target = arm.get("basis_key_by_target")
        key = (
            key_by_target.get(target["target_id"])
            if key_by_target is not None
            else arm.get("basis_key")
        )
        if key is not None:
            key = str(key).format(target_id=target["target_id"])
            if key not in projectors:
                raise KeyError(f"Missing projector basis: {key}")
            basis = torch.from_numpy(np.asarray(projectors[key], dtype=np.float64))
        rows.append((str(arm["arm_id"]), float(arm.get("dose", 1.0)), basis, arm.get("component") == "complement"))
    return rows


def score_one(
    *,
    item: dict[str, Any],
    annotation: dict[str, Any],
    roi: dict[str, Any],
    source_row: dict[str, Any],
    processor: Any,
    model: Any,
    config: dict[str, Any],
    cohort_role: str,
    experiment: str,
    reference: dict[str, Any] | None,
    projectors: dict[str, np.ndarray] | None,
    arm_config: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
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
    attention_groups = {
        key: source_groups[key]
        for key in ("V_all", "V_target", "V_other", "V_irrelevant", "V_target_ring")
    }
    vectors: dict[str, np.ndarray] = {}
    target_rows = []
    mechanical = {
        "all_layout_and_roi_mappings_exact": bool(
            layout_exact
            and roi["target_complement_partition_exact"]
            and roi["target_ring_irrelevant_disjoint"]
            and roi["four_condition_layout_exact"]
        ),
        "all_candidate_representations_invariant": True,
        "all_query_head_selectivity_valid": True,
        "all_recipient_tensor_alignment_exact": True,
        "all_self_restorations_exact": True,
        "all_native_endpoints_exact": True,
        "all_reference_endpoints_within_tolerance": True if reference is not None else None,
        "all_scores_finite": True,
    }
    for target in config["targets"]:
        intervention_index = ed - 1 if target["coordinate"] == "Ed_minus_1" else ed
        captures = {
            condition: capture_preference_value_states(
                model=model,
                prepared=prepared[condition],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                intervention_generated_index=intervention_index,
                layer_index=int(target["layer_index"]),
                selected_query_heads=target["heads"],
                roi_positions=source_groups["V_target"],
                attention_groups=attention_groups,
                seed=int(config["locked_generation_protocol"]["seed"]),
            )
            for condition in CONDITIONS
        }
        semantic, sham, vector_audit = exact_symmetric_vectors(
            model=model,
            prepared=prepared,
            captures=captures,
            context=context,
            candidate_original=candidate_original,
            candidate_counterfactual=candidate_counterfactual,
            intervention_index=intervention_index,
            target=target,
            seed=int(config["locked_generation_protocol"]["seed"]),
            heads=target["heads"],
            roi_positions=source_groups["V_target"],
        )
        vectors[f"{target['target_id']}__semantic_delta"] = semantic
        vectors[f"{target['target_id']}__sham_delta"] = sham
        mechanical["all_candidate_representations_invariant"] &= bool(vector_audit["candidate_invariance_exact"])
        ref_scores = reference_v_scores(reference, target["cell_id"]) if reference is not None else None
        arms = []
        for arm_id, dose, basis, complement in target_arms(
            experiment=experiment,
            target=target,
            config=config,
            projectors=projectors,
            arm_config=arm_config,
        ):
            arm = score_arm(
                model=model,
                prepared=prepared,
                captures=captures,
                context=context,
                candidate_original=candidate_original,
                candidate_counterfactual=candidate_counterfactual,
                intervention_index=intervention_index,
                target=target,
                roi_positions=source_groups["V_target"],
                dose=dose,
                projector_basis=basis,
                projector_complement=complement,
                seed=int(config["locked_generation_protocol"]["seed"]),
                arm_id=arm_id,
                reference_scores=ref_scores,
            )
            arms.append(arm)
            mechanical["all_query_head_selectivity_valid"] &= bool(arm["all_query_head_selectivity_valid"])
            mechanical["all_recipient_tensor_alignment_exact"] &= bool(arm["all_recipient_tensor_alignment_exact"])
            mechanical["all_self_restorations_exact"] &= bool(arm["all_self_restorations_exact"])
            mechanical["all_scores_finite"] &= bool(arm["all_scores_finite"])
            if arm["native_endpoint_exact"] is not None:
                mechanical["all_native_endpoints_exact"] &= bool(arm["native_endpoint_exact"])
            if arm["stage3b7r_v_reference_within_tolerance"] is not None:
                mechanical["all_reference_endpoints_within_tolerance"] &= bool(arm["stage3b7r_v_reference_within_tolerance"])
        target_rows.append({
            **target,
            "intervention_generated_index": intervention_index,
            "representation_vector_audit": vector_audit,
            "no_intervention": {condition: public_capture(capture) for condition, capture in captures.items()},
            "arms": arms,
        })
    return {
        "base_problem_id": base,
        "example_id": str(item["example_id"]),
        "cohort_role": cohort_role,
        "experiment": experiment,
        "edit_metadata": paired["_metadata_path"],
        "prefix_sha256": annotation.get("history_before_ed_sha256") or token_hash(context),
        "ed_generated_index": ed,
        "condition_layout_exact": layout_exact,
        "selection_used_attention": False,
        "selection_used_stage3b8_outcome_or_fit": False,
        "roi_mapping": {
            "target_token_count": roi["target_token_count"],
            "target_positions": source_groups["V_target"],
            "target_complement_partition_exact": roi["target_complement_partition_exact"],
            "target_ring_irrelevant_disjoint": roi["target_ring_irrelevant_disjoint"],
        },
        "targets": target_rows,
        "mechanical_controls": mechanical,
    }, vectors


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to((OUT / "scoring/raw").resolve())
    config = read_json(args.config)
    manifest = read_jsonl(args.manifest)
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(args.annotations)}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(args.roi_mapping)}
    references = reference_paths(args.stage3b7r_reference_root)
    if args.cohort_role == "primary" and len(references) < len(manifest):
        raise RuntimeError("Primary scoring requires immutable Stage 3B.7-R V references")
    if args.experiment == "projected" and (args.projectors is None or args.arms is None):
        raise ValueError("Projected scoring requires --projectors and --arms")
    projector_arrays = dict(np.load(args.projectors)) if args.projectors else None
    arm_config = read_json(args.arms) if args.arms else None
    signature = {
        "manifest": str(args.manifest.resolve()),
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "annotations": str(args.annotations.resolve()),
        "roi_mapping": str(args.roi_mapping.resolve()),
        "config": str(args.config.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "cohort_role": args.cohort_role,
        "experiment": args.experiment,
        "projectors": str(args.projectors.resolve()) if args.projectors else None,
        "arms": str(args.arms.resolve()) if args.arms else None,
        "stage3b7r_reference_root": str(args.stage3b7r_reference_root.resolve()) if args.stage3b7r_reference_root else None,
        "seed": int(config["locked_generation_protocol"]["seed"]),
        "required_gpu_class": args.required_gpu_class,
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
    text_config = model.config.text_config
    observed = {
        "language_layers": int(text_config.num_hidden_layers),
        "logical_query_heads": int(text_config.num_attention_heads),
        "kv_heads": int(text_config.num_key_value_heads),
        "query_heads_per_kv_group": int(text_config.num_attention_heads // text_config.num_key_value_heads),
        "head_dimension": int(text_config.head_dim),
    }
    if observed != config["architecture_expected"]:
        raise RuntimeError(f"GQA architecture mismatch: {observed} != {config['architecture_expected']}")
    environment["stage3b8_gqa_architecture"] = observed
    write_json(output_dir / "environment.json", environment)
    torch.cuda.reset_peak_memory_stats()
    results = []
    repeat_payload = None
    for index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        result_path = output_dir / "examples" / base / "result.json"
        vector_path = output_dir / "examples" / base / "vectors.npz"
        if args.resume and result_path.is_file() and vector_path.is_file():
            results.append(read_json(result_path))
            print(f"[{index + 1}/{len(manifest)}] resumed base {base}", flush=True)
            continue
        if base not in annotations or base not in rois or str(item["example_id"]) not in data:
            raise RuntimeError(f"Missing annotation, ROI, or dataset row for base {base}")
        result, vectors = score_one(
            item=item,
            annotation=annotations[base],
            roi=rois[base],
            source_row=data[str(item["example_id"])],
            processor=processor,
            model=model,
            config=config,
            cohort_role=args.cohort_role,
            experiment=args.experiment,
            reference=read_json(references[base]) if base in references else None,
            projectors=projector_arrays,
            arm_config=arm_config,
        )
        ensure_directory(result_path.parent)
        write_json(result_path, result)
        np.savez_compressed(vector_path, **vectors)
        results.append(result)
        if args.repeat_first and index == 0:
            repeated, repeated_vectors = score_one(
                item=item,
                annotation=annotations[base],
                roi=rois[base],
                source_row=data[str(item["example_id"])],
                processor=processor,
                model=model,
                config=config,
                cohort_role=args.cohort_role,
                experiment=args.experiment,
                reference=read_json(references[base]) if base in references else None,
                projectors=projector_arrays,
                arm_config=arm_config,
            )
            repeat_payload = {
                "base_problem_id": base,
                "exact_public_result_match": repeated == result,
                "exact_vector_match": all(np.array_equal(vectors[key], repeated_vectors[key]) for key in vectors),
            }
            write_json(output_dir / "determinism_repeat.json", repeat_payload)
        print(f"[{index + 1}/{len(manifest)}] completed base {base}", flush=True)
        gc.collect()
        torch.cuda.empty_cache()
    write_jsonl(output_dir / "results.jsonl", results)
    boolean_mechanics = [
        value
        for result in results
        for key, value in result["mechanical_controls"].items()
        if key.startswith("all_")
        and key != "all_candidate_representations_invariant"
        and value is not None
    ]
    write_json(output_dir / "result.json", {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "cohort_role": args.cohort_role,
        "experiment": args.experiment,
        "base_problem_count": len(results),
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "all_mechanical_controls_passed": all(boolean_mechanics),
        "candidate_shape_invariance_is_a_recorded_numerical_audit_not_a_gate": True,
        "determinism_repeat": repeat_payload,
    })


if __name__ == "__main__":
    main()
