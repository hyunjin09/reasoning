#!/usr/bin/env python3
"""Run the frozen eight-base Stage 3B.3-R method validation."""

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
from visual_reasoning.stage3b2.runtime import capture_audit_valid, capture_preference_visual_kv
from visual_reasoning.stage3b3.metrics import activation_patch_metrics, sufficiency_metrics
from visual_reasoning.stage3b3.runtime import (
    capture_preference_current_residuals,
    score_preference_with_current_residual,
    score_preference_with_layer_visual_source,
)
from visual_reasoning.stage3b3_redesign.composition import compose_source_layers
from visual_reasoning.stage3b3_redesign.metrics import semantic_restoration_metrics


ROOT = Path(__file__).resolve().parents[2]
REDESIGN_OUT = ROOT / "outputs/stage3b3_redesign"
SEED = 1_234
PAIRED_CONDITIONS = ("O", "O_sham", "C", "C_sham")
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
    parser.add_argument("--required-gpu-class", choices=("A5000", "A6000"), default="A5000")
    parser.add_argument("--technical-controls-only", action="store_true")
    parser.add_argument("--phase", choices=("validation", "primary"), default="validation")
    parser.add_argument("--run-cumulative", action="store_true")
    parser.add_argument("--fine-only", action="store_true")
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


def public_preference(preference: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "L_o": float(preference["L_o"]),
        "L_c": float(preference["L_c"]),
        "D": float(preference["D"]),
    }
    for key in ("all_layer_switch_audits_valid", "all_residual_patch_audits_valid"):
        if key in preference:
            result[key] = bool(preference[key])
    for candidate in CANDIDATES:
        source = preference[candidate]
        result[candidate] = {
            key: copy.deepcopy(value)
            for key, value in source.items()
            if key not in {"layer_switch_audit", "residual_patch_audit"}
        }
        if "layer_switch_audit" in source:
            audit = source["layer_switch_audit"]
            result[candidate]["layer_switch_audit_summary"] = {
                "call_count": len(audit),
                "selected_layers": [int(row["layer_index"]) for row in audit if row["layer_selected"]],
                "queries_before_switch_modified": sum(int(row["queries_before_switch_modified"]) for row in audit),
                "nonvisual_key_value_entries_replaced": sum(
                    int(row["nonvisual_key_value_entries_replaced"]) for row in audit
                ),
            }
        if "residual_patch_audit" in source:
            audit = source["residual_patch_audit"]
            result[candidate]["residual_patch_audit_summary"] = {
                "call_count": len(audit),
                "positions_replaced": [row["positions_replaced"] for row in audit],
                "noncurrent_positions_changed": sum(int(row["noncurrent_positions_changed"]) for row in audit),
                "all_current_positions_exact_source_match": all(
                    bool(row["current_position_exact_source_match"]) for row in audit
                ),
            }
    return result


def capture_public(capture: dict[str, Any]) -> dict[str, Any]:
    return {
        "L_o": float(capture["L_o"]),
        "L_c": float(capture["L_c"]),
        "D": float(capture["D"]),
        **{
            candidate: {
                key: copy.deepcopy(value)
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
    allowed_output_root = (
        REDESIGN_OUT / "validation/raw"
        if args.phase == "validation"
        else REDESIGN_OUT / "primary/raw"
    )
    output_dir.relative_to(allowed_output_root.resolve())
    manifest = read_jsonl(args.manifest)
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(args.annotations)}
    stage3b2 = {str(row["base_problem_id"]): row for row in read_jsonl(args.stage3b2_results)}
    raw_paths = stage3b2_raw_paths(args.stage3b2_raw_root)
    windows = json.loads(args.windows.read_text(encoding="utf-8"))
    coarse_windows = windows["fine_windows"] if args.fine_only else windows["coarse_windows"]
    cumulative_rows = (
        [
            row
            for family in ("lower_prefix", "upper_suffix")
            for row in windows["cumulative_windows"][family]
        ]
        if not args.fine_only else []
    )
    activation_layers = (
        [int(value) for value in windows["activation_patch_boundaries_after_layers"]]
        if not args.fine_only else []
    )
    bases = [str(row["base_problem_id"]) for row in manifest]
    signature = {
        "manifest": str(args.manifest.resolve()),
        "base_problem_ids": bases,
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "seed": SEED,
        "required_gpu_class": args.required_gpu_class,
        "coordinates": ["Ed_minus_1", "Ed"],
        "coarse_windows": coarse_windows,
        "activation_patch_boundaries_after_layers": activation_layers,
        "attention_path": "validated eager local override",
        "paired_conditions": list(PAIRED_CONDITIONS),
        "fine_localization": False,
        "technical_controls_only": bool(args.technical_controls_only),
        "phase": args.phase,
        "run_cumulative": bool(args.run_cumulative),
        "fine_only": bool(args.fine_only),
    }
    config_path = output_dir / "config.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.resume or not config_path.is_file():
            raise FileExistsError(f"Non-empty output requires --resume: {output_dir}")
        if json.loads(config_path.read_text(encoding="utf-8"))["run_signature"] != signature:
            raise RuntimeError("Resume signature mismatch")
    else:
        ensure_directory(output_dir)
        write_json(config_path, {"created_at": datetime.now(timezone.utc).isoformat(), "run_signature": signature})
        write_jsonl(output_dir / "manifest.jsonl", manifest)

    data_rows = load_mathverse_rows(args.dataset_root)
    by_example = {str(row["sample_index"]): row for row in data_rows}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if args.required_gpu_class not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {args.required_gpu_class}, observed {environment['gpu_name']}")
    write_json(output_dir / "environment.json", environment)
    torch.cuda.reset_peak_memory_stats()
    layer_count = int(model.config.text_config.num_hidden_layers)
    if layer_count != 36:
        raise RuntimeError(f"Frozen windows require 36 language layers, observed {layer_count}")
    kv_heads = int(model.config.text_config.num_key_value_heads)
    head_dim = int(model.config.text_config.head_dim)
    all_results: list[dict[str, Any]] = []

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
        paired_metadata_path = REDESIGN_OUT / "counterfactual_shams" / base / "edit_metadata.json"
        paired_controls = paired_metadata_path.is_file()
        paired_metadata = (
            json.loads(paired_metadata_path.read_text(encoding="utf-8"))
            if paired_controls else None
        )
        if paired_controls and paired_metadata["manual_validation"]["status"] != "pass":
            raise RuntimeError(f"Paired image controls are not manually valid for base {base}")
        if not paired_controls and args.phase != "primary":
            raise RuntimeError(f"Validation base lacks paired image controls: {base}")
        conditions = PAIRED_CONDITIONS if paired_controls else ("O", "O_sham", "C")
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
        for condition in conditions:
            if paired_controls:
                image_path = ROOT / paired_metadata["paths"][condition]
            else:
                condition_key = {"O": "original", "O_sham": "sham", "C": "counterfactual"}[condition]
                image_path = ROOT / item["conditions"][condition_key]
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, source_row, image_path, device="cuda"
            )
        prompt_ids = [metadata[name]["prompt_token_ids"] for name in conditions]
        visual_sets = [metadata[name]["visual_token_indices"] for name in conditions]
        grids = [metadata[name]["image_grid_thw"] for name in conditions]
        layout_exact = bool(
            all(value == prompt_ids[0] for value in prompt_ids[1:])
            and all(value == visual_sets[0] for value in visual_sets[1:])
            and all(value == grids[0] for value in grids[1:])
        )
        if not layout_exact:
            raise RuntimeError(f"Condition prompt/visual layout mismatch for base {base}")
        visual_indices = [int(value) for value in visual_sets[0]]

        captures = {
            condition: capture_preference_visual_kv(
                model=model,
                prepared=prepared[condition],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                visual_indices=visual_indices,
                seed=SEED,
            )
            for condition in conditions
        }
        capture_valid = all(
            capture_audit_valid(
                captures[condition]["capture_audits"][candidate],
                visual_indices=visual_indices,
                layer_count=layer_count,
                kv_heads=kv_heads,
                head_dim=head_dim,
            )
            for condition in conditions for candidate in CANDIDATES
        )
        d_oo = float(captures["O"]["D"])
        d_cc = float(captures["C"]["D"])

        if args.technical_controls_only:
            technical_coordinates = []
            for coordinate, switch_index in (("Ed_minus_1", ed - 1), ("Ed", ed)):
                technical = {}
                for name, recipient, donor in (
                    ("O_to_C", "O", "C"),
                    ("C_to_O", "C", "O"),
                    ("O_to_O_sham", "O", "O_sham"),
                    ("self_O", "O", "O"),
                ):
                    technical[name] = score_preference_with_layer_visual_source(
                        model=model,
                        prepared=prepared[recipient],
                        context_token_ids=context,
                        candidate_original_ids=candidate_original,
                        candidate_counterfactual_ids=candidate_counterfactual,
                        source_layers_by_candidate=captures[donor]["source_layers"],
                        visual_indices=visual_indices,
                        switch_generated_index=switch_index,
                        selected_layers=ALL_LAYERS,
                        seed=SEED,
                    )
                raw_controls = {
                    "O_to_C": raw_reference_preference(raw_reference, coordinate, "O_to_C"),
                    "C_to_O": raw_reference_preference(raw_reference, coordinate, "C_to_O"),
                    "O_to_O_sham": raw_reference_preference(raw_reference, coordinate, "O_to_sham"),
                    "self_O": raw_reference_preference(raw_reference, coordinate, "self_O"),
                }
                technical_coordinates.append({
                    "coordinate": coordinate,
                    "controls": {name: public_preference(value) for name, value in technical.items()},
                    "exact_stage3b2": {
                        name: scores_exact(technical[name], raw_controls[name]) for name in technical
                    },
                    "all_audits_valid": all(
                        value["all_layer_switch_audits_valid"] for value in technical.values()
                    ),
                    "all_scores_finite": all(finite_preference(value) for value in technical.values()),
                })
            technical_result = {
                "base_problem_id": base,
                "example_id": example,
                "technical_controls_only": True,
                "condition_layout_exact": layout_exact,
                "capture_all_layers_valid": capture_valid,
                "no_switch_exact_stage3b2": {
                    "O": scores_exact(captures["O"], raw_reference["no_switch"]["original"]),
                    "C": scores_exact(captures["C"], raw_reference["no_switch"]["counterfactual"]),
                },
                "coordinates": technical_coordinates,
            }
            write_json(result_path, technical_result)
            all_results.append(technical_result)
            print(f"[{item_index + 1}/{len(manifest)}] technical controls completed base {base}", flush=True)
            del prepared, captures, technical_coordinates
            gc.collect()
            torch.cuda.empty_cache()
            continue

        coordinate_results = []

        for coordinate, switch_index in (("Ed_minus_1", ed - 1), ("Ed", ed)):
            reference_point = stage3b2_coordinate(reference, coordinate)
            all_layer_bri = float(reference_point["BRI"])
            simple_cache: dict[tuple[str, str, tuple[int, ...]], dict[str, Any]] = {}
            composed_cache: dict[tuple[str, str, str, tuple[int, ...]], dict[str, Any]] = {}

            def simple(recipient: str, donor: str, selected_layers: tuple[int, ...] | list[int]) -> dict[str, Any]:
                layers = tuple(sorted(int(value) for value in selected_layers))
                key = (recipient, donor, layers)
                if key not in simple_cache:
                    simple_cache[key] = score_preference_with_layer_visual_source(
                        model=model,
                        prepared=prepared[recipient],
                        context_token_ids=context,
                        candidate_original_ids=candidate_original,
                        candidate_counterfactual_ids=candidate_counterfactual,
                        source_layers_by_candidate=captures[donor]["source_layers"],
                        visual_indices=visual_indices,
                        switch_generated_index=switch_index,
                        selected_layers=layers,
                        seed=SEED,
                    )
                return simple_cache[key]

            def composed(recipient: str, default: str, window_source: str, selected_layers: list[int]) -> dict[str, Any]:
                layers = tuple(sorted(int(value) for value in selected_layers))
                key = (recipient, default, window_source, layers)
                if key not in composed_cache:
                    source_by_candidate = {
                        candidate: compose_source_layers(
                            captures[default]["source_layers"][candidate],
                            captures[window_source]["source_layers"][candidate],
                            selected_layers=layers,
                        )
                        for candidate in CANDIDATES
                    }
                    composed_cache[key] = score_preference_with_layer_visual_source(
                        model=model,
                        prepared=prepared[recipient],
                        context_token_ids=context,
                        candidate_original_ids=candidate_original,
                        candidate_counterfactual_ids=candidate_counterfactual,
                        source_layers_by_candidate=source_by_candidate,
                        visual_indices=visual_indices,
                        switch_generated_index=switch_index,
                        selected_layers=ALL_LAYERS,
                        seed=SEED,
                    )
                return composed_cache[key]

            full = {
                recipient: {source: simple(recipient, source, ALL_LAYERS) for source in conditions}
                for recipient in ("O", "C")
            }
            raw_o_to_c = raw_reference_preference(raw_reference, coordinate, "O_to_C")
            raw_c_to_o = raw_reference_preference(raw_reference, coordinate, "C_to_O")
            raw_o_to_sham = raw_reference_preference(raw_reference, coordinate, "O_to_sham")
            raw_self_o = raw_reference_preference(raw_reference, coordinate, "self_O")
            positive_control = {
                "O_to_C_exact_stage3b2": scores_exact(full["O"]["C"], raw_o_to_c),
                "C_to_O_exact_stage3b2": scores_exact(full["C"]["O"], raw_c_to_o),
                "O_to_O_sham_exact_stage3b2": scores_exact(full["O"]["O_sham"], raw_o_to_sham),
                "self_O_exact_stage3b2": scores_exact(full["O"]["O"], raw_self_o),
                "no_switch_O_exact_stage3b2": scores_exact(captures["O"], raw_reference["no_switch"]["original"]),
                "no_switch_C_exact_stage3b2": scores_exact(captures["C"], raw_reference["no_switch"]["counterfactual"]),
            }
            full_paired_metrics = (
                semantic_restoration_metrics(
                    original_history={source: float(full["O"][source]["D"]) for source in conditions},
                    counterfactual_history={source: float(full["C"][source]["D"]) for source in conditions},
                    all_layer_bri=all_layer_bri,
                ) if paired_controls else None
            )

            selective_rows = []
            restoration_rows = []
            for window in coarse_windows:
                layers = [int(value) for value in window["layers"]]
                selective = {
                    recipient: {source: simple(recipient, source, layers) for source in conditions}
                    for recipient in ("O", "C")
                }
                bws = sufficiency_metrics(
                    d_oo=d_oo,
                    d_cc=d_cc,
                    d_o_to_c=float(selective["O"]["C"]["D"]),
                    d_c_to_o=float(selective["C"]["O"]["D"]),
                    d_o_to_sham=float(selective["O"]["O_sham"]["D"]),
                    all_layer_bri=all_layer_bri,
                )
                paired_selective = (
                    semantic_restoration_metrics(
                        original_history={source: float(selective["O"][source]["D"]) for source in conditions},
                        counterfactual_history={source: float(selective["C"][source]["D"]) for source in conditions},
                        all_layer_bri=all_layer_bri,
                    ) if paired_controls else None
                )
                selective_rows.append({
                    **window,
                    **bws,
                    "paired_semantic_controls": paired_selective,
                    "controls": {
                        recipient: {source: public_preference(value) for source, value in sources.items()}
                        for recipient, sources in selective.items()
                    },
                    "self_O_exact": scores_exact(selective["O"]["O"], captures["O"]),
                    "self_C_exact": scores_exact(selective["C"]["C"], captures["C"]),
                    "all_audits_valid": all(
                        value["all_layer_switch_audits_valid"]
                        for sources in selective.values() for value in sources.values()
                    ),
                    "all_finite": all(
                        finite_preference(value) for sources in selective.values() for value in sources.values()
                    ),
                })

                if paired_controls:
                    restoration = {
                        "original_history": {
                            source: composed("O", "C", source, layers) for source in conditions
                        },
                        "counterfactual_history": {
                            source: composed("C", "O", source, layers) for source in conditions
                        },
                    }
                    restoration_metric = semantic_restoration_metrics(
                        original_history={
                            source: float(restoration["original_history"][source]["D"])
                            for source in conditions
                        },
                        counterfactual_history={
                            source: float(restoration["counterfactual_history"][source]["D"])
                            for source in conditions
                        },
                        all_layer_bri=all_layer_bri,
                    )
                    restoration_rows.append({
                        **window,
                        **restoration_metric,
                        "composition": {
                            "original_history_default_source": "C",
                            "counterfactual_history_default_source": "O",
                            "window_sources": list(conditions),
                            "all_layers_replaced_with_composed_per_layer_sources": True,
                        },
                        "controls": {
                            history: {source: public_preference(value) for source, value in sources.items()}
                            for history, sources in restoration.items()
                        },
                        "all_audits_valid": all(
                            value["all_layer_switch_audits_valid"]
                            for sources in restoration.values() for value in sources.values()
                        ),
                        "all_finite": all(
                            finite_preference(value) for sources in restoration.values() for value in sources.values()
                        ),
                    })

            cumulative = []
            if args.run_cumulative:
                for cumulative_window in cumulative_rows:
                    layers = [int(value) for value in cumulative_window["layers"]]
                    values = {
                        "O_to_C": simple("O", "C", layers),
                        "C_to_O": simple("C", "O", layers),
                        "O_to_O_sham": simple("O", "O_sham", layers),
                        "self_O": simple("O", "O", layers),
                    }
                    cumulative.append({
                        **cumulative_window,
                        **sufficiency_metrics(
                            d_oo=d_oo,
                            d_cc=d_cc,
                            d_o_to_c=float(values["O_to_C"]["D"]),
                            d_c_to_o=float(values["C_to_O"]["D"]),
                            d_o_to_sham=float(values["O_to_O_sham"]["D"]),
                            all_layer_bri=all_layer_bri,
                        ),
                        "controls": {name: public_preference(value) for name, value in values.items()},
                        "self_O_exact": scores_exact(values["self_O"], captures["O"]),
                        "all_audits_valid": all(value["all_layer_switch_audits_valid"] for value in values.values()),
                        "all_finite": all(finite_preference(value) for value in values.values()),
                    })

            coordinate_results.append({
                "coordinate": coordinate,
                "switch_generated_index": switch_index,
                "D_OO": d_oo,
                "D_CC": d_cc,
                "stage3b2_all_layer_BRI": all_layer_bri,
                "positive_control": positive_control,
                "full_all_layer": {
                    recipient: {source: public_preference(value) for source, value in sources.items()}
                    for recipient, sources in full.items()
                },
                "full_paired_semantic_controls": full_paired_metrics,
                "selective": selective_rows,
                "semantic_restoration": restoration_rows,
                "cumulative": cumulative,
                "all_switch_audits_valid": all(
                    value["all_layer_switch_audits_valid"]
                    for value in list(simple_cache.values()) + list(composed_cache.values())
                ),
                "all_scores_finite": all(
                    finite_preference(value)
                    for value in list(simple_cache.values()) + list(composed_cache.values())
                ),
            })
            del simple_cache, composed_cache

        residual_captures = (
            {
                condition: capture_preference_current_residuals(
                    model=model,
                    prepared=prepared[condition],
                    context_token_ids=context,
                    candidate_original_ids=candidate_original,
                    candidate_counterfactual_ids=candidate_counterfactual,
                    layer_indices=activation_layers,
                    seed=SEED,
                )
                for condition in conditions
            }
            if not args.fine_only else {}
        )
        ed_reference = stage3b2_coordinate(reference, "Ed")
        residual_rows = []
        for boundary in ([] if args.fine_only else activation_layers):
            patched = {}
            patch_specs = [
                ("O_receive_C", "O", "C"),
                ("C_receive_O", "C", "O"),
                ("O_receive_O_sham", "O", "O_sham"),
                ("self_O", "O", "O"),
                ("self_C", "C", "C"),
            ]
            if paired_controls:
                patch_specs.append(("C_receive_C_sham", "C", "C_sham"))
            for name, recipient, donor in patch_specs:
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
            residual_rows.append({
                "after_layer": boundary,
                **activation_patch_metrics(
                    d_oo=d_oo,
                    d_cc=d_cc,
                    d_o_receive_c=float(patched["O_receive_C"]["D"]),
                    d_c_receive_o=float(patched["C_receive_O"]["D"]),
                    d_o_receive_sham=float(patched["O_receive_O_sham"]["D"]),
                    all_layer_bri=float(ed_reference["BRI"]),
                ),
                "counterfactual_render_activation_shift": (
                    float(patched["C_receive_C_sham"]["D"]) - d_cc
                    if paired_controls else None
                ),
                "controls": {name: public_preference(value) for name, value in patched.items()},
                "self_O_exact": scores_exact(patched["self_O"], residual_captures["O"]),
                "self_C_exact": scores_exact(patched["self_C"], residual_captures["C"]),
                "all_audits_valid": all(value["all_residual_patch_audits_valid"] for value in patched.values()),
                "all_finite": all(finite_preference(value) for value in patched.values()),
            })

        result = {
            "base_problem_id": base,
            "example_id": example,
            "evidence_type": item["edit_tier"],
            "prefix_sha256": item["prefix_sha256"],
            "ed_generated_index": ed,
            "ed_alignment": reference["ed_alignment"],
            "condition_layout_exact": layout_exact,
            "capture_all_layers_valid": capture_valid,
            "paired_semantic_restoration_included": paired_controls,
            "manual_four_image_validation_passed": bool(paired_controls),
            "selection_used_attention": False,
            "fine_only": bool(args.fine_only),
            "no_switch": {condition: capture_public(value) for condition, value in captures.items()},
            "coordinates": coordinate_results,
            "activation_patch_coordinate": "Ed",
            "activation_patches": residual_rows,
        }
        write_json(result_path, result)
        all_results.append(result)
        print(f"[{item_index + 1}/{len(manifest)}] completed base {base}", flush=True)
        del prepared, captures, residual_captures, coordinate_results, residual_rows
        gc.collect()
        torch.cuda.empty_cache()

    write_jsonl(output_dir / "results.jsonl", all_results)
    if args.technical_controls_only:
        technical_summary = {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "technical_controls_only": True,
            "base_problem_count": len(all_results),
            "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
            "all_condition_layout_exact": all(row["condition_layout_exact"] for row in all_results),
            "all_capture_layers_valid": all(row["capture_all_layers_valid"] for row in all_results),
            "all_no_switch_exact": all(
                all(row["no_switch_exact_stage3b2"].values()) for row in all_results
            ),
            "all_layer_switch_controls_exact": all(
                all(point["exact_stage3b2"].values())
                for row in all_results for point in row["coordinates"]
            ),
            "all_layer_switch_audits_valid": all(
                point["all_audits_valid"] for row in all_results for point in row["coordinates"]
            ),
            "all_scores_finite": all(
                point["all_scores_finite"] for row in all_results for point in row["coordinates"]
            ),
        }
        technical_summary["passed"] = all(
            bool(value) for key, value in technical_summary.items() if key.startswith("all_")
        )
        write_json(output_dir / "result.json", technical_summary)
        return
    summary = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "base_problem_count": len(all_results),
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "all_condition_layout_exact": all(row["condition_layout_exact"] for row in all_results),
        "all_capture_layers_valid": all(row["capture_all_layers_valid"] for row in all_results),
        "all_positive_controls_exact": all(
            all(point["positive_control"].values())
            for row in all_results for point in row["coordinates"]
        ),
        "all_layer_switch_audits_valid": all(
            point["all_switch_audits_valid"] for row in all_results for point in row["coordinates"]
        ),
        "all_residual_patch_audits_valid": all(
            point["all_audits_valid"] for row in all_results for point in row["activation_patches"]
        ),
        "all_self_controls_exact": all(
            point["self_O_exact"] and point["self_C_exact"]
            for row in all_results for point in row["activation_patches"]
        ) and all(
            window["self_O_exact"] and window["self_C_exact"]
            for row in all_results for point in row["coordinates"] for window in point["selective"]
        ),
        "all_scores_finite": all(
            point["all_scores_finite"] for row in all_results for point in row["coordinates"]
        ) and all(
            point["all_finite"] for row in all_results for point in row["activation_patches"]
        ),
    }
    summary["all_mechanical_controls_passed"] = all(
        bool(value) for key, value in summary.items() if key.startswith("all_")
    )
    write_json(output_dir / "result.json", summary)


if __name__ == "__main__":
    main()
