#!/usr/bin/env python3
"""Run frozen Stage 3B.5 current-position boundary restoration scoring."""

from __future__ import annotations

import argparse
import copy
import gc
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b5.boundaries import BOUNDARIES
from visual_reasoning.stage3b5.metrics import boundary_restoration_metrics
from visual_reasoning.stage3b5.runtime import (
    CANDIDATES,
    capture_preference_boundaries,
    score_preference_with_boundary,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b5"
CONDITIONS = ("O", "O_sham", "C", "C_sham")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--stage3b2-results", type=Path, required=True)
    parser.add_argument("--stage3b4-raw-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--phase", choices=("validation", "primary"), required=True)
    parser.add_argument("--required-gpu-class", default="A5000")
    parser.add_argument("--repeat-first", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def reference_paths(root: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for path in sorted(root.glob("**/examples/*/result.json")):
        base = path.parent.name
        if base in paths:
            raise RuntimeError(f"Duplicate Stage 3B.4 reference for base {base}")
        paths[base] = path
    return paths


def stage3b2_coordinate(row: dict[str, Any], label: str) -> dict[str, Any]:
    return next(point for point in row["timing"] if label in point["labels"])


def stage3b4_coordinate(row: dict[str, Any], label: str) -> dict[str, Any]:
    return next(point for point in row["coordinates"] if point["coordinate"] == label)


def stage3b4_module(point: dict[str, Any], window: str, module: str) -> dict[str, Any]:
    return next(
        row for row in point["module_restoration"]
        if row["window"] == window and row["module"] == module
    )


def scores_exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        left["L_o"] == right["L_o"]
        and left["L_c"] == right["L_c"]
        and left["D"] == right["D"]
        and all(
            left[candidate]["token_log_probabilities"]
            == right[candidate]["token_log_probabilities"]
            for candidate in CANDIDATES
        )
    )


def finite_preference(preference: dict[str, Any]) -> bool:
    return bool(
        math.isfinite(float(preference["D"]))
        and all(bool(preference[candidate]["finite"]) for candidate in CANDIDATES)
    )


def public_preference(preference: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "L_o": float(preference["L_o"]),
        "L_c": float(preference["L_c"]),
        "D": float(preference["D"]),
    }
    if "all_boundary_patch_audits_valid" in preference:
        result["all_boundary_patch_audits_valid"] = bool(
            preference["all_boundary_patch_audits_valid"]
        )
    for candidate in CANDIDATES:
        source = preference[candidate]
        result[candidate] = {
            key: copy.deepcopy(value)
            for key, value in source.items()
            if key not in {"boundary_patch_audit", "runtime_seconds"}
        }
        if "boundary_patch_audit" in source:
            audit = source["boundary_patch_audit"]
            result[candidate]["boundary_patch_audit_summary"] = copy.deepcopy(audit[0])
    return result


def capture_public(capture: dict[str, Any]) -> dict[str, Any]:
    return {
        "L_o": float(capture["L_o"]),
        "L_c": float(capture["L_c"]),
        "D": float(capture["D"]),
        "all_boundary_capture_audits_valid": bool(
            capture["all_boundary_capture_audits_valid"]
        ),
        "current_absolute_position": int(capture["current_absolute_position"]),
        "capture_audit_summaries": {
            candidate: copy.deepcopy(capture["capture_audits"][candidate])
            for candidate in CANDIDATES
        },
        "residual_addition_audits": copy.deepcopy(capture["residual_addition_audits"]),
        **{
            candidate: {
                key: copy.deepcopy(value)
                for key, value in capture[candidate].items()
                if key != "runtime_seconds"
            }
            for candidate in CANDIDATES
        },
    }


def all_control_scores_exact(
    left: dict[str, dict[str, dict[str, Any]]],
    right: dict[str, dict[str, dict[str, Any]]],
) -> bool:
    return all(
        scores_exact(left[recipient][donor], right[recipient][donor])
        for recipient in ("O", "C")
        for donor in CONDITIONS
    )


def capture_interface_exact(
    captures: dict[str, dict[str, Any]], first: int, second: int
) -> bool:
    return all(
        torch.equal(
            captures[condition]["states"][candidate]["h_post_block"][first],
            captures[condition]["states"][candidate]["h_pre"][second],
        )
        for condition in CONDITIONS
        for candidate in CANDIDATES
    )


def score_one(
    *,
    item: dict[str, Any],
    annotation: dict[str, Any],
    stage3b2: dict[str, Any],
    stage3b4: dict[str, Any],
    source_row: dict[str, Any],
    processor: Any,
    model: Any,
    config: dict[str, Any],
) -> dict[str, Any]:
    base = str(item["base_problem_id"])
    metadata_path = ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json"
    if not metadata_path.is_file():
        raise RuntimeError(f"Paired boundary restoration requires C_sham; missing for base {base}")
    paired = read_json(metadata_path)
    if paired["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Four-image validation did not pass for base {base}")

    prepared: dict[str, dict[str, Any]] = {}
    image_metadata: dict[str, dict[str, Any]] = {}
    for condition in CONDITIONS:
        image_path = ROOT / paired["paths"][condition]
        prepared[condition], image_metadata[condition] = prepare_custom_image(
            processor, source_row, image_path, device="cuda"
        )
    prompt_ids = [image_metadata[name]["prompt_token_ids"] for name in CONDITIONS]
    visual_sets = [image_metadata[name]["visual_token_indices"] for name in CONDITIONS]
    grids = [image_metadata[name]["image_grid_thw"] for name in CONDITIONS]
    layout_exact = bool(
        all(value == prompt_ids[0] for value in prompt_ids[1:])
        and all(value == visual_sets[0] for value in visual_sets[1:])
        and all(value == grids[0] for value in grids[1:])
    )
    if not layout_exact:
        raise RuntimeError(f"Condition prompt/visual layout mismatch for base {base}")

    context = [int(value) for value in annotation["history_before_ed_token_ids"]]
    ed = int(annotation["ed_generated_index"])
    if len(context) != ed or item["prefix_sha256"] != stage3b2["prefix_sha256"]:
        raise RuntimeError(f"Frozen E_d coordinate mismatch for base {base}")
    candidate_original = [int(value) for value in annotation["original_divergent_suffix_ids"]]
    candidate_counterfactual = [int(value) for value in annotation["counterfactual_divergent_suffix_ids"]]
    target_by_window = config["target_by_window"]
    all_target_layers = sorted({
        int(layer)
        for target in target_by_window.values()
        for layer in target["layers"]
    })

    coordinate_rows = []
    all_capture_valid = True
    all_baseline_exact = True
    all_patch_valid = True
    all_self_exact = True
    all_finite = True
    all_interfaces_exact = True
    all_capture_interfaces_exact = True
    for coordinate, intervention_index in (("Ed_minus_1", ed - 1), ("Ed", ed)):
        if intervention_index <= 0:
            raise RuntimeError(f"E_d-1 is not defined for base {base}")
        all_layer_bri = float(stage3b2_coordinate(stage3b2, coordinate)["BRI"])
        frozen_point = stage3b4_coordinate(stage3b4, coordinate)
        captures = {
            condition: capture_preference_boundaries(
                model=model,
                prepared=prepared[condition],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                intervention_generated_index=intervention_index,
                layer_indices=all_target_layers,
                seed=int(config["seed"]),
            )
            for condition in CONDITIONS
        }
        capture_valid = all(
            bool(capture["all_boundary_capture_audits_valid"])
            for capture in captures.values()
        )
        baseline_exact = {
            condition: scores_exact(captures[condition], frozen_point["no_switch"][condition])
            for condition in CONDITIONS
        }

        rows = []
        control_objects: dict[tuple[str, str, str], dict[str, dict[str, dict[str, Any]]]] = {}
        captured_interfaces: dict[str, bool] = {}
        for window in ("W4", "W5"):
            layers = [int(value) for value in target_by_window[window]["layers"]]
            captured_interfaces[window] = capture_interface_exact(captures, layers[0], layers[1])
            frozen_modules = {
                module: stage3b4_module(frozen_point, window, module)
                for module in ("attention", "mlp", "joint", "block")
            }
            for layer_role, layer_index in zip(("first", "second"), layers):
                for boundary in BOUNDARIES:
                    restored = {
                        recipient: {
                            donor: score_preference_with_boundary(
                                model=model,
                                prepared=prepared[recipient],
                                context_token_ids=context,
                                candidate_original_ids=candidate_original,
                                candidate_counterfactual_ids=candidate_counterfactual,
                                intervention_generated_index=intervention_index,
                                layer_index=layer_index,
                                boundary=boundary,
                                source_states_by_candidate=captures[donor]["states"],
                                seed=int(config["seed"]),
                            )
                            for donor in CONDITIONS
                        }
                        for recipient in ("O", "C")
                    }
                    metrics = boundary_restoration_metrics(
                        recipient_scores={
                            recipient: {
                                donor: float(preference["D"])
                                for donor, preference in donor_rows.items()
                            }
                            for recipient, donor_rows in restored.items()
                        },
                        all_layer_bri=all_layer_bri,
                    )
                    patch_valid = all(
                        bool(preference["all_boundary_patch_audits_valid"])
                        for donor_rows in restored.values()
                        for preference in donor_rows.values()
                    )
                    self_exact = {
                        "O": scores_exact(restored["O"]["O"], captures["O"]),
                        "C": scores_exact(restored["C"]["C"], captures["C"]),
                    }
                    self_error = {
                        recipient: abs(
                            float(restored[recipient][recipient]["D"])
                            - float(captures[recipient]["D"])
                        )
                        for recipient in ("O", "C")
                    }
                    finite = all(
                        finite_preference(preference)
                        for donor_rows in restored.values()
                        for preference in donor_rows.values()
                    )
                    control_objects[(window, layer_role, boundary)] = restored
                    rows.append({
                        "test_id": f"{coordinate}__{window}__{layer_role}__{boundary}",
                        "window": window,
                        "fine_window": target_by_window[window]["fine_window"],
                        "layers": layers,
                        "layer_role": layer_role,
                        "layer_index": layer_index,
                        "boundary": boundary,
                        "two_layer_entry_alias": bool(layer_role == "first" and boundary == "h_pre"),
                        **metrics,
                        "controls": {
                            recipient: {
                                donor: public_preference(preference)
                                for donor, preference in donor_rows.items()
                            }
                            for recipient, donor_rows in restored.items()
                        },
                        "self_restoration_exact": self_exact,
                        "self_restoration_absolute_error": self_error,
                        "maximum_self_restoration_absolute_error": max(self_error.values()),
                        "all_self_restorations_exact": all(self_exact.values()),
                        "all_patch_audits_valid": patch_valid,
                        "all_expected_downstream_recompute_verified": patch_valid,
                        "all_scores_finite": finite,
                        "stage3b4_precomputed_references": {
                            module: {
                                "BMR": float(reference["BMR"]),
                                "BMR_normalized": reference["BMR_normalized"],
                            }
                            for module, reference in frozen_modules.items()
                        },
                    })
                    all_patch_valid = all_patch_valid and patch_valid
                    all_self_exact = all_self_exact and all(self_exact.values())
                    all_finite = all_finite and finite

        interface_rows = []
        for window in ("W4", "W5"):
            score_equivalent = all_control_scores_exact(
                control_objects[(window, "first", "h_post_block")],
                control_objects[(window, "second", "h_pre")],
            )
            interface_rows.append({
                "window": window,
                "captured_first_h_post_block_equals_second_h_pre": captured_interfaces[window],
                "patched_scores_exact_all_recipients_donors_candidates": score_equivalent,
            })
            all_interfaces_exact = all_interfaces_exact and score_equivalent
            all_capture_interfaces_exact = all_capture_interfaces_exact and captured_interfaces[window]

        coordinate_rows.append({
            "coordinate": coordinate,
            "intervention_generated_index": intervention_index,
            "current_absolute_position": next(iter(captures.values()))["current_absolute_position"],
            "stage3b2_all_layer_BRI": all_layer_bri,
            "no_switch": {
                condition: capture_public(capture) for condition, capture in captures.items()
            },
            "baseline_exact_stage3b4": baseline_exact,
            "all_capture_audits_valid": capture_valid,
            "boundary_restoration": rows,
            "adjacent_interface_equivalence": interface_rows,
        })
        all_capture_valid = all_capture_valid and capture_valid
        all_baseline_exact = all_baseline_exact and all(baseline_exact.values())

    return {
        "base_problem_id": base,
        "example_id": str(item["example_id"]),
        "evidence_type": item["edit_tier"],
        "prefix_sha256": item["prefix_sha256"],
        "ed_generated_index": ed,
        "condition_layout_exact": layout_exact,
        "paired_boundary_restoration_included": True,
        "selection_used_attention": False,
        "coordinates": coordinate_rows,
        "mechanical_controls": {
            "all_capture_audits_valid": all_capture_valid,
            "all_baselines_exact_stage3b4": all_baseline_exact,
            "all_patch_audits_valid": all_patch_valid,
            "all_downstream_recompute_verified": all_patch_valid,
            "all_self_restorations_exact": all_self_exact,
            "all_scores_finite": all_finite,
            "all_adjacent_interface_scores_exact": all_interfaces_exact,
            "all_adjacent_interface_captured_states_exact": all_capture_interfaces_exact,
        },
    }


def main() -> None:
    args = parse_args()
    config = read_json(args.config)
    output_dir = args.output_dir.resolve()
    allowed = OUT / ("validation/raw" if args.phase == "validation" else "scoring/raw")
    output_dir.relative_to(allowed.resolve())
    manifest = read_jsonl(args.manifest)
    if any("structural" in str(row["edit_tier"]) for row in manifest):
        raise RuntimeError("Runner accepts only paired numeric bases")
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(args.annotations)}
    stage3b2 = {str(row["base_problem_id"]): row for row in read_jsonl(args.stage3b2_results)}
    raw_paths = reference_paths(args.stage3b4_raw_root)
    bases = [str(row["base_problem_id"]) for row in manifest]
    signature = {
        "manifest": str(args.manifest.resolve()),
        "base_problem_ids": bases,
        "config": str(args.config.resolve()),
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "seed": int(config["seed"]),
        "required_gpu_class": args.required_gpu_class,
        "phase": args.phase,
        "repeat_first": bool(args.repeat_first),
    }
    config_path = output_dir / "config.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.resume or not config_path.is_file():
            raise FileExistsError(f"Non-empty output requires --resume: {output_dir}")
        if read_json(config_path)["run_signature"] != signature:
            raise RuntimeError("Resume signature mismatch")
    else:
        ensure_directory(output_dir)
        write_json(config_path, {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "run_signature": signature,
        })
        write_jsonl(output_dir / "manifest.jsonl", manifest)

    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if args.required_gpu_class not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {args.required_gpu_class}, observed {environment['gpu_name']}")
    write_json(output_dir / "environment.json", environment)
    torch.cuda.reset_peak_memory_stats()
    if int(model.config.text_config.num_hidden_layers) != 36:
        raise RuntimeError("Frozen boundary targets require 36 language layers")

    results = []
    repeat_payload = None
    for index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if args.resume and result_path.is_file():
            result = read_json(result_path)
            results.append(result)
            print(f"[{index + 1}/{len(manifest)}] resumed base {base}", flush=True)
            continue
        if base not in annotations or base not in stage3b2 or base not in raw_paths:
            raise RuntimeError(f"Missing frozen reference for base {base}")
        if str(item["example_id"]) not in data:
            raise RuntimeError(f"Missing MathVerse example {item['example_id']}")
        result = score_one(
            item=item,
            annotation=annotations[base],
            stage3b2=stage3b2[base],
            stage3b4=read_json(raw_paths[base]),
            source_row=data[str(item["example_id"])],
            processor=processor,
            model=model,
            config=config,
        )
        ensure_directory(result_path.parent)
        write_json(result_path, result)
        results.append(result)
        if args.repeat_first and index == 0:
            repeated = score_one(
                item=item,
                annotation=annotations[base],
                stage3b2=stage3b2[base],
                stage3b4=read_json(raw_paths[base]),
                source_row=data[str(item["example_id"])],
                processor=processor,
                model=model,
                config=config,
            )
            repeat_payload = {
                "base_problem_id": base,
                "exact_public_result_match": repeated == result,
            }
            write_json(output_dir / "determinism_repeat.json", repeat_payload)
        print(f"[{index + 1}/{len(manifest)}] completed base {base}", flush=True)
        gc.collect()
        torch.cuda.empty_cache()

    write_jsonl(output_dir / "results.jsonl", results)
    summary = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "phase": args.phase,
        "base_problem_count": len(results),
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "all_condition_layout_exact": all(row["condition_layout_exact"] for row in results),
        **{
            key: all(bool(row["mechanical_controls"][key]) for row in results)
            for key in (
                "all_capture_audits_valid", "all_baselines_exact_stage3b4",
                "all_patch_audits_valid", "all_downstream_recompute_verified",
                "all_self_restorations_exact", "all_scores_finite",
                "all_adjacent_interface_scores_exact",
                "all_adjacent_interface_captured_states_exact",
            )
        },
        "determinism_repeat": repeat_payload,
    }
    summary["all_mechanical_controls_passed"] = all(
        bool(value) for key, value in summary.items() if key.startswith("all_")
    )
    write_json(output_dir / "result.json", summary)


if __name__ == "__main__":
    main()
