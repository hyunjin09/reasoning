#!/usr/bin/env python3
"""Run frozen Stage 3B.3 coarse layer-source and residual interventions."""

from __future__ import annotations

import argparse
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
from visual_reasoning.stage3b2.runtime import (
    capture_audit_valid,
    capture_preference_visual_kv,
)
from visual_reasoning.stage3b3.metrics import (
    activation_patch_metrics,
    necessity_metrics,
    sufficiency_metrics,
)
from visual_reasoning.stage3b3.runtime import (
    capture_preference_current_residuals,
    score_preference_with_current_residual,
    score_preference_with_layer_visual_source,
)


ROOT = Path(__file__).resolve().parents[2]
SEED = 1_234
CONDITIONS = ("original", "counterfactual", "sham")
CANDIDATES = ("original_candidate", "counterfactual_candidate")
ALL_LAYERS = tuple(range(36))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--windows", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--stage3b2-results", type=Path, required=True)
    parser.add_argument("--stage3b2-raw-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("smoke", "cohort"), required=True)
    parser.add_argument("--required-gpu-class", choices=("A5000", "A6000"), default="A5000")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def scores_exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        left["L_o"] == right["L_o"]
        and left["L_c"] == right["L_c"]
        and left["D"] == right["D"]
        and all(
            left[name]["token_log_probabilities"] == right[name]["token_log_probabilities"]
            for name in CANDIDATES
        )
    )


def finite_preference(preference: dict[str, Any]) -> bool:
    return bool(
        math.isfinite(float(preference["D"]))
        and all(bool(preference[candidate]["finite"]) for candidate in CANDIDATES)
    )


def audit_summary(audit: list[dict[str, Any]], *, kind: str) -> dict[str, Any]:
    if kind == "layer":
        selected = [row for row in audit if row["layer_selected"]]
        return {
            "call_count": len(audit),
            "selected_layers": [int(row["layer_index"]) for row in selected],
            "unselected_layers": [int(row["layer_index"]) for row in audit if not row["layer_selected"]],
            "queries_before_switch_modified": sum(int(row["queries_before_switch_modified"]) for row in audit),
            "nonvisual_key_value_entries_replaced": sum(
                int(row["nonvisual_key_value_entries_replaced"]) for row in audit
            ),
            "switched_query_count_per_selected_layer": (
                len(selected[0]["switched_absolute_query_indices"]) if selected else 0
            ),
        }
    return {
        "call_count": len(audit),
        "layers": [int(row["layer_index"]) for row in audit],
        "positions_replaced": [row["positions_replaced"] for row in audit],
        "noncurrent_positions_changed": sum(
            int(row["noncurrent_positions_changed"]) for row in audit
        ),
        "all_current_positions_exact_source_match": all(
            bool(row["current_position_exact_source_match"]) for row in audit
        ),
    }


def public_preference(preference: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "L_o": float(preference["L_o"]),
        "L_c": float(preference["L_c"]),
        "D": float(preference["D"]),
    }
    for valid_key in ("all_layer_switch_audits_valid", "all_residual_patch_audits_valid"):
        if valid_key in preference:
            result[valid_key] = bool(preference[valid_key])
    for candidate in CANDIDATES:
        source = preference[candidate]
        clean = {
            key: value
            for key, value in source.items()
            if key not in {"layer_switch_audit", "residual_patch_audit"}
        }
        if "layer_switch_audit" in source:
            clean["layer_switch_audit_summary"] = audit_summary(
                source["layer_switch_audit"], kind="layer"
            )
        if "residual_patch_audit" in source:
            clean["residual_patch_audit_summary"] = audit_summary(
                source["residual_patch_audit"], kind="residual"
            )
        result[candidate] = clean
    return result


def capture_public(capture: dict[str, Any]) -> dict[str, Any]:
    return {
        "L_o": float(capture["L_o"]),
        "L_c": float(capture["L_c"]),
        "D": float(capture["D"]),
        **{
            candidate: {
                key: value
                for key, value in capture[candidate].items()
                if key not in {"switch_audit", "layer_switch_audit"}
            }
            for candidate in CANDIDATES
        },
    }


def stage3b2_raw_paths(root: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for path in sorted(root.glob("cohort_*/examples/*/result.json")):
        base = path.parent.name
        if base in paths:
            raise RuntimeError(f"Duplicate Stage 3B.2 raw reference for base {base}")
        paths[base] = path
    return paths


def stage3b2_coordinate(row: dict[str, Any], label: str) -> dict[str, Any]:
    return next(point for point in row["timing"] if label in point["labels"])


def raw_reference_preference(row: dict[str, Any], label: str, control: str) -> dict[str, Any]:
    point = next(point for point in row["timing"] if label in point["labels"])
    return point["controls"][control]


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to((ROOT / "outputs/stage3b3/raw").resolve())
    manifest = read_jsonl(args.manifest)
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(args.annotations)}
    stage3b2 = {
        str(row["base_problem_id"]): row for row in read_jsonl(args.stage3b2_results)
    }
    raw_paths = stage3b2_raw_paths(args.stage3b2_raw_root)
    windows = json.loads(args.windows.read_text(encoding="utf-8"))
    coarse_windows = windows["coarse_windows"]
    cumulative_rows = [
        row
        for family in ("lower_prefix", "upper_suffix")
        for row in windows["cumulative_windows"][family]
    ]
    activation_layers = [int(value) for value in windows["activation_patch_boundaries_after_layers"]]
    bases = [str(row["base_problem_id"]) for row in manifest]
    signature = {
        "mode": args.mode,
        "manifest": str(args.manifest.resolve()),
        "base_problem_ids": bases,
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "seed": SEED,
        "required_gpu_class": args.required_gpu_class,
        "coordinates": ["Ed_minus_1", "Ed"],
        "coarse_windows": coarse_windows,
        "cumulative_windows": cumulative_rows,
        "activation_patch_boundaries_after_layers": activation_layers,
        "attention_path": "validated eager local override",
    }
    config_path = output_dir / "config.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.resume or not config_path.is_file():
            raise FileExistsError(f"Non-empty output requires --resume: {output_dir}")
        if json.loads(config_path.read_text(encoding="utf-8"))["run_signature"] != signature:
            raise RuntimeError("Resume signature mismatch")
    else:
        ensure_directory(output_dir)
        write_json(
            config_path,
            {"created_at": datetime.now(timezone.utc).isoformat(), "run_signature": signature},
        )
        write_jsonl(output_dir / "manifest.jsonl", manifest)

    data_rows = load_mathverse_rows(args.dataset_root)
    by_example = {str(row["sample_index"]): row for row in data_rows}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if args.required_gpu_class not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {args.required_gpu_class}, observed {environment['gpu_name']}")
    write_json(output_dir / "environment.json", environment)
    layer_count = int(model.config.text_config.num_hidden_layers)
    if layer_count != 36:
        raise RuntimeError(f"Frozen Stage 3B.3 windows require 36 layers, observed {layer_count}")
    kv_heads = int(model.config.text_config.num_key_value_heads)
    head_dim = int(model.config.text_config.head_dim)
    all_results: list[dict[str, Any]] = []
    peak_gpu_bytes = 0

    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        example = str(item["example_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if args.resume and result_path.is_file():
            all_results.append(json.loads(result_path.read_text(encoding="utf-8")))
            print(f"[{item_index + 1}/{len(manifest)}] resumed base {base}", flush=True)
            continue
        ensure_directory(result_path.parent)
        if base not in annotations or base not in stage3b2 or base not in raw_paths:
            raise RuntimeError(f"Missing frozen Stage 3B.2 reference for base {base}")
        annotation = annotations[base]
        reference = stage3b2[base]
        raw_reference = json.loads(raw_paths[base].read_text(encoding="utf-8"))
        context = [int(value) for value in annotation["history_before_ed_token_ids"]]
        ed = int(annotation["ed_generated_index"])
        if len(context) != ed or item["prefix_sha256"] != reference["prefix_sha256"]:
            raise RuntimeError(f"Frozen coordinate mismatch for base {base}")
        candidate_original = [int(value) for value in annotation["original_divergent_suffix_ids"]]
        candidate_counterfactual = [int(value) for value in annotation["counterfactual_divergent_suffix_ids"]]

        prepared: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        source_row = by_example[example]
        for condition in CONDITIONS:
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, source_row, ROOT / item["conditions"][condition], device="cuda"
            )
        prompt_ids = [metadata[name]["prompt_token_ids"] for name in CONDITIONS]
        visual_sets = [metadata[name]["visual_token_indices"] for name in CONDITIONS]
        grids = [metadata[name]["image_grid_thw"] for name in CONDITIONS]
        layout_exact = bool(
            all(value == prompt_ids[0] for value in prompt_ids[1:])
            and all(value == visual_sets[0] for value in visual_sets[1:])
            and all(value == grids[0] for value in grids[1:])
        )
        if not layout_exact:
            raise RuntimeError(f"Condition prompt/visual layout mismatch for base {base}")
        visual_indices = [int(value) for value in visual_sets[0]]

        captures: dict[str, dict[str, Any]] = {}
        for condition in CONDITIONS:
            captures[condition] = capture_preference_visual_kv(
                model=model,
                prepared=prepared[condition],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                visual_indices=visual_indices,
                seed=SEED,
            )
        capture_valid = all(
            capture_audit_valid(
                captures[condition]["capture_audits"][candidate],
                visual_indices=visual_indices,
                layer_count=layer_count,
                kv_heads=kv_heads,
                head_dim=head_dim,
            )
            for condition in CONDITIONS
            for candidate in CANDIDATES
        )
        d_oo = float(captures["original"]["D"])
        d_cc = float(captures["counterfactual"]["D"])

        coordinate_results: list[dict[str, Any]] = []
        for coordinate, switch_index in (("Ed_minus_1", ed - 1), ("Ed", ed)):
            if switch_index < 0:
                raise RuntimeError(f"E_d-1 is invalid for base {base}")
            reference_point = stage3b2_coordinate(reference, coordinate)
            all_layer_bri = float(reference_point["BRI"])
            cache: dict[tuple[str, tuple[int, ...]], dict[str, Any]] = {}

            def switched(kind: str, selected_layers: list[int] | tuple[int, ...]) -> dict[str, Any]:
                key = (kind, tuple(sorted(int(value) for value in selected_layers)))
                if key in cache:
                    return cache[key]
                recipient, donor = {
                    "O_to_C": ("original", "counterfactual"),
                    "C_to_O": ("counterfactual", "original"),
                    "O_to_sham": ("original", "sham"),
                    "self_O": ("original", "original"),
                }[kind]
                value = score_preference_with_layer_visual_source(
                    model=model,
                    prepared=prepared[recipient],
                    context_token_ids=context,
                    candidate_original_ids=candidate_original,
                    candidate_counterfactual_ids=candidate_counterfactual,
                    source_layers_by_candidate=captures[donor]["source_layers"],
                    visual_indices=visual_indices,
                    switch_generated_index=switch_index,
                    selected_layers=key[1],
                    seed=SEED,
                )
                cache[key] = value
                return value

            full = {name: switched(name, ALL_LAYERS) for name in ("O_to_C", "C_to_O", "O_to_sham", "self_O")}
            raw_o_to_c = raw_reference_preference(raw_reference, coordinate, "O_to_C")
            raw_c_to_o = raw_reference_preference(raw_reference, coordinate, "C_to_O")
            raw_o_to_sham = raw_reference_preference(raw_reference, coordinate, "O_to_sham")
            raw_self_o = raw_reference_preference(raw_reference, coordinate, "self_O")
            positive_control = {
                "O_to_C_exact_stage3b2": scores_exact(full["O_to_C"], raw_o_to_c),
                "C_to_O_exact_stage3b2": scores_exact(full["C_to_O"], raw_c_to_o),
                "O_to_sham_exact_stage3b2": scores_exact(full["O_to_sham"], raw_o_to_sham),
                "self_O_exact_stage3b2": scores_exact(full["self_O"], raw_self_o),
                "no_switch_O_exact_stage3b2": scores_exact(captures["original"], raw_reference["no_switch"]["original"]),
                "no_switch_C_exact_stage3b2": scores_exact(captures["counterfactual"], raw_reference["no_switch"]["counterfactual"]),
            }

            coarse_sufficiency = []
            coarse_necessity = []
            for window in coarse_windows:
                selected = [int(value) for value in window["layers"]]
                selective = {name: switched(name, selected) for name in ("O_to_C", "C_to_O", "O_to_sham", "self_O")}
                restored = [value for value in ALL_LAYERS if value not in set(selected)]
                except_window = {name: switched(name, restored) for name in ("O_to_C", "C_to_O", "O_to_sham", "self_O")}
                coarse_sufficiency.append(
                    {
                        **window,
                        **sufficiency_metrics(
                            d_oo=d_oo,
                            d_cc=d_cc,
                            d_o_to_c=float(selective["O_to_C"]["D"]),
                            d_c_to_o=float(selective["C_to_O"]["D"]),
                            d_o_to_sham=float(selective["O_to_sham"]["D"]),
                            all_layer_bri=all_layer_bri,
                        ),
                        "controls": {name: public_preference(value) for name, value in selective.items()},
                        "self_O_exact": scores_exact(selective["self_O"], captures["original"]),
                        "all_audits_valid": all(value["all_layer_switch_audits_valid"] for value in selective.values()),
                        "all_finite": all(finite_preference(value) for value in selective.values()),
                    }
                )
                coarse_necessity.append(
                    {
                        **window,
                        "donor_layers": restored,
                        **necessity_metrics(
                            d_o_to_c_all=float(full["O_to_C"]["D"]),
                            d_c_to_o_all=float(full["C_to_O"]["D"]),
                            d_o_to_c_except_window=float(except_window["O_to_C"]["D"]),
                            d_c_to_o_except_window=float(except_window["C_to_O"]["D"]),
                            d_o_to_sham_all=float(full["O_to_sham"]["D"]),
                            d_o_to_sham_except_window=float(except_window["O_to_sham"]["D"]),
                            all_layer_bri=all_layer_bri,
                        ),
                        "controls": {name: public_preference(value) for name, value in except_window.items()},
                        "self_O_exact": scores_exact(except_window["self_O"], captures["original"]),
                        "all_audits_valid": all(value["all_layer_switch_audits_valid"] for value in except_window.values()),
                        "all_finite": all(finite_preference(value) for value in except_window.values()),
                    }
                )

            cumulative = []
            for cumulative_window in cumulative_rows:
                selected = [int(value) for value in cumulative_window["layers"]]
                values = {name: switched(name, selected) for name in ("O_to_C", "C_to_O", "O_to_sham", "self_O")}
                cumulative.append(
                    {
                        **cumulative_window,
                        **sufficiency_metrics(
                            d_oo=d_oo,
                            d_cc=d_cc,
                            d_o_to_c=float(values["O_to_C"]["D"]),
                            d_c_to_o=float(values["C_to_O"]["D"]),
                            d_o_to_sham=float(values["O_to_sham"]["D"]),
                            all_layer_bri=all_layer_bri,
                        ),
                        "controls": {name: public_preference(value) for name, value in values.items()},
                        "self_O_exact": scores_exact(values["self_O"], captures["original"]),
                        "all_audits_valid": all(value["all_layer_switch_audits_valid"] for value in values.values()),
                        "all_finite": all(finite_preference(value) for value in values.values()),
                    }
                )

            coordinate_results.append(
                {
                    "coordinate": coordinate,
                    "switch_generated_index": switch_index,
                    "D_OO": d_oo,
                    "D_CC": d_cc,
                    "stage3b2_all_layer_BRI": all_layer_bri,
                    "full_all_layer": {name: public_preference(value) for name, value in full.items()},
                    "positive_control": positive_control,
                    "coarse_sufficiency": coarse_sufficiency,
                    "coarse_necessity": coarse_necessity,
                    "cumulative": cumulative,
                    "all_self_exact": all(scores_exact(value, captures["original"]) for (name, _), value in cache.items() if name == "self_O"),
                    "all_audits_valid": all(value["all_layer_switch_audits_valid"] for value in cache.values()),
                    "all_finite": all(finite_preference(value) for value in cache.values()),
                    "unique_layer_set_condition_count": len(cache),
                }
            )
            del cache

        residual_captures = {
            condition: capture_preference_current_residuals(
                model=model,
                prepared=prepared[condition],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                layer_indices=activation_layers,
                seed=SEED,
            )
            for condition in CONDITIONS
        }
        ed_reference = stage3b2_coordinate(reference, "Ed")
        residual_rows = []
        for boundary in activation_layers:
            patched: dict[str, dict[str, Any]] = {}
            for name, recipient, donor in (
                ("O_receive_C", "original", "counterfactual"),
                ("C_receive_O", "counterfactual", "original"),
                ("O_receive_sham", "original", "sham"),
                ("self_O", "original", "original"),
            ):
                patched[name] = score_preference_with_current_residual(
                    model=model,
                    prepared=prepared[recipient],
                    context_token_ids=context,
                    candidate_original_ids=candidate_original,
                    candidate_counterfactual_ids=candidate_counterfactual,
                    layer_index=boundary,
                    source_states_by_candidate={
                        candidate: residual_captures[donor]["states"][candidate][boundary]
                        for candidate in CANDIDATES
                    },
                    seed=SEED,
                )
            residual_rows.append(
                {
                    "after_layer": boundary,
                    **activation_patch_metrics(
                        d_oo=d_oo,
                        d_cc=d_cc,
                        d_o_receive_c=float(patched["O_receive_C"]["D"]),
                        d_c_receive_o=float(patched["C_receive_O"]["D"]),
                        d_o_receive_sham=float(patched["O_receive_sham"]["D"]),
                        all_layer_bri=float(ed_reference["BRI"]),
                    ),
                    "controls": {name: public_preference(value) for name, value in patched.items()},
                    "self_O_exact": scores_exact(patched["self_O"], residual_captures["original"]),
                    "all_audits_valid": all(value["all_residual_patch_audits_valid"] for value in patched.values()),
                    "all_finite": all(finite_preference(value) for value in patched.values()),
                }
            )

        peak_gpu_bytes = max(peak_gpu_bytes, int(torch.cuda.max_memory_allocated()))
        result = {
            "base_problem_id": base,
            "example_id": example,
            "evidence_type": item["edit_tier"],
            "prefix_sha256": item["prefix_sha256"],
            "ed_generated_index": ed,
            "ed_alignment": reference["ed_alignment"],
            "condition_layout_exact": layout_exact,
            "capture_all_layers_valid": capture_valid,
            "selection_used_attention": False,
            "no_switch": {condition: capture_public(value) for condition, value in captures.items()},
            "coordinates": coordinate_results,
            "activation_patch_coordinate": "Ed",
            "activation_patches": residual_rows,
            "residual_capture_audit": {
                condition: value["capture_audits"] for condition, value in residual_captures.items()
            },
        }
        write_json(result_path, result)
        all_results.append(result)
        print(f"[{item_index + 1}/{len(manifest)}] completed base {base}", flush=True)
        del prepared, captures, residual_captures, coordinate_results, residual_rows
        gc.collect()
        torch.cuda.empty_cache()

    write_jsonl(output_dir / "results.jsonl", all_results)
    write_json(
        output_dir / "result.json",
        {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "mode": args.mode,
            "base_problem_count": len(all_results),
            "peak_gpu_allocated_bytes": peak_gpu_bytes,
            "all_condition_layout_exact": all(row["condition_layout_exact"] for row in all_results),
            "all_capture_layers_valid": all(row["capture_all_layers_valid"] for row in all_results),
            "all_positive_controls_exact": all(
                all(point["positive_control"].values())
                for row in all_results
                for point in row["coordinates"]
            ),
            "all_layer_switch_audits_valid": all(
                point["all_audits_valid"] for row in all_results for point in row["coordinates"]
            ),
            "all_self_switches_exact": all(
                point["all_self_exact"] for row in all_results for point in row["coordinates"]
            ),
            "all_residual_patch_audits_valid": all(
                point["all_audits_valid"] for row in all_results for point in row["activation_patches"]
            ),
            "all_residual_self_patches_exact": all(
                point["self_O_exact"] for row in all_results for point in row["activation_patches"]
            ),
            "all_scores_finite": all(
                point["all_finite"] for row in all_results for point in row["coordinates"]
            ) and all(
                point["all_finite"] for row in all_results for point in row["activation_patches"]
            ),
        },
    )


if __name__ == "__main__":
    main()
