#!/usr/bin/env python3
"""Run Stage 3B.6 discovery, confirmation, upstream, or source-path scoring."""

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
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3b6.metrics import head_restoration_metrics
from visual_reasoning.stage3b6.paths import build_source_token_groups
from visual_reasoning.stage3b6.runtime import (
    CANDIDATES,
    capture_preference_head_states,
    score_preference_with_hybrid_heads,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b6"
CONDITIONS = ("O", "O_sham", "C", "C_sham")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--stage3b5-raw-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--phase", choices=("discovery", "primary", "upstream", "source"), required=True
    )
    parser.add_argument("--candidate-freeze", type=Path)
    parser.add_argument("--source-targets", type=Path)
    parser.add_argument("--required-gpu-class", default="A5000")
    parser.add_argument("--repeat-first", action="store_true")
    parser.add_argument("--discovery-head-count", type=int, default=32)
    parser.add_argument("--max-bases", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def reference_paths(root: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for path in sorted(root.glob("**/examples/*/result.json")):
        base = path.parent.name
        if base in paths:
            raise RuntimeError(f"Duplicate Stage 3B.5 reference for base {base}")
        paths[base] = path
    return paths


def stage3b5_point(row: dict[str, Any], coordinate: str) -> dict[str, Any]:
    return next(point for point in row["coordinates"] if point["coordinate"] == coordinate)


def stage3b5_boundary(
    point: dict[str, Any], *, window: str, layer_role: str, boundary: str
) -> dict[str, Any]:
    return next(
        row
        for row in point["boundary_restoration"]
        if row["window"] == window
        and row["layer_role"] == layer_role
        and row["boundary"] == boundary
    )


def stage3b5_attention_gain(point: dict[str, Any], cell: dict[str, Any]) -> float:
    before = stage3b5_boundary(
        point,
        window=cell["window"],
        layer_role=cell["layer_role"],
        boundary="h_pre",
    )
    after = stage3b5_boundary(
        point,
        window=cell["window"],
        layer_role=cell["layer_role"],
        boundary="h_post_attn",
    )
    return float(after["BMR"]) - float(before["BMR"])


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


def finite_preference(preference: dict[str, Any]) -> bool:
    return bool(
        math.isfinite(float(preference["D"]))
        and all(bool(preference[candidate]["finite"]) for candidate in CANDIDATES)
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
                key: value
                for key, value in capture[candidate].items()
                if key != "runtime_seconds"
            }
            for candidate in CANDIDATES
        },
    }


def cross_patch_audit(restored: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    rows = []
    for recipient in ("O", "C"):
        for donor in CONDITIONS:
            for candidate in CANDIDATES:
                audit = restored[recipient][donor][candidate]["head_patch_audit"]
                rows.append({
                    "recipient": recipient,
                    "donor": donor,
                    "candidate": candidate,
                    "selected_query_heads": audit["selected_query_heads"],
                    "selected_kv_groups": audit["selected_kv_groups"],
                    "changed_query_heads": audit["changed_query_heads"],
                    "changed_sequence_positions": audit["changed_sequence_positions"],
                    "query_head_selectivity_valid": audit[
                        "query_head_selectivity_valid"
                    ],
                    "source_group_isolation_valid": audit[
                        "source_group_isolation_valid"
                    ],
                    "assigned_position_count": audit["kv_swap"][
                        "assigned_position_count"
                    ],
                    "recipient_attention_summary": audit[
                        "recipient_attention_summary"
                    ],
                })
    return {
        "all_query_head_selectivity_valid": all(
            bool(row["query_head_selectivity_valid"]) for row in rows
        ),
        "all_source_group_isolation_valid": all(
            bool(row["source_group_isolation_valid"]) for row in rows
        ),
        "calls": rows,
    }


def score_unit(
    *,
    model: Any,
    prepared: dict[str, dict[str, Any]],
    captures: dict[str, dict[str, Any]],
    context: list[int],
    candidate_original: list[int],
    candidate_counterfactual: list[int],
    intervention_index: int,
    cell: dict[str, Any],
    unit: dict[str, Any],
    source_positions: list[int],
    attention_groups: dict[str, list[int]],
    attention_gain: float,
    seed: int,
    source_group: str,
) -> dict[str, Any]:
    restored = {
        recipient: {
            donor: score_preference_with_hybrid_heads(
                model=model,
                prepared=prepared[recipient],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                intervention_generated_index=intervention_index,
                layer_index=int(cell["layer_index"]),
                selected_heads=unit["heads"],
                source_states_by_candidate=captures[donor]["states"],
                source_positions=source_positions,
                attention_groups=attention_groups,
                seed=seed,
            )
            for donor in CONDITIONS
        }
        for recipient in ("O", "C")
    }
    recipient_scores = {
        recipient: {
            donor: float(preference["D"])
            for donor, preference in donor_rows.items()
        }
        for recipient, donor_rows in restored.items()
    }
    metrics = head_restoration_metrics(
        recipient_scores=recipient_scores,
        stage3b5_attention_gain=attention_gain,
    )
    self_exact = {
        recipient: scores_exact(restored[recipient][recipient], captures[recipient])
        for recipient in ("O", "C")
    }
    self_error = {
        recipient: abs(
            float(restored[recipient][recipient]["D"])
            - float(captures[recipient]["D"])
        )
        for recipient in ("O", "C")
    }
    mechanical = cross_patch_audit(restored)
    all_finite = all(
        finite_preference(preference)
        for donor_rows in restored.values()
        for preference in donor_rows.values()
    )
    return {
        "cell_id": cell["cell_id"],
        "coordinate": cell["coordinate"],
        "window": cell["window"],
        "layer_role": cell["layer_role"],
        "layer_index": int(cell["layer_index"]),
        "cell_role": cell["role"],
        "unit_id": unit["unit_id"],
        "unit_kind": unit["kind"],
        "heads": [int(head) for head in unit["heads"]],
        "origin_cell_id": unit.get("origin_cell_id"),
        "source_group": source_group,
        "source_position_count": len(source_positions),
        "stage3b5_attention_gain": float(attention_gain),
        **metrics,
        "recipient_scores": recipient_scores,
        "self_restoration_exact": self_exact,
        "self_restoration_absolute_error": self_error,
        "maximum_self_restoration_absolute_error": max(self_error.values()),
        "all_self_restorations_exact": all(self_exact.values()),
        "all_scores_finite": all_finite,
        "mechanical_audit": mechanical,
    }


def units_for_cell(
    *,
    phase: str,
    cell: dict[str, Any],
    freeze: dict[str, Any] | None,
    discovery_head_count: int,
) -> list[dict[str, Any]]:
    if phase == "discovery":
        if discovery_head_count < 1 or discovery_head_count > 32:
            raise ValueError("Discovery head count must be in [1, 32]")
        return [
            {"unit_id": f"head_{head:02d}", "kind": "single", "heads": [head]}
            for head in range(discovery_head_count)
        ]
    if freeze is None:
        raise ValueError(f"{phase} requires a candidate freeze")
    if phase in {"primary", "source"}:
        return list(freeze["cells"][cell["cell_id"]]["units"])
    if phase == "upstream":
        return list(freeze["upstream_units"])
    raise ValueError(phase)


def score_one(
    *,
    item: dict[str, Any],
    annotation: dict[str, Any],
    stage3b5: dict[str, Any],
    source_row: dict[str, Any],
    processor: Any,
    model: Any,
    config: dict[str, Any],
    phase: str,
    freeze: dict[str, Any] | None,
    source_targets: dict[str, Any] | None,
    discovery_head_count: int,
) -> dict[str, Any]:
    base = str(item["base_problem_id"])
    paired_path = (
        ROOT
        / "outputs/stage3b3_redesign/counterfactual_shams"
        / base
        / "edit_metadata.json"
    )
    paired = read_json(paired_path)
    if paired["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Four-condition image validation failed for base {base}")
    prepared: dict[str, dict[str, Any]] = {}
    metadata: dict[str, dict[str, Any]] = {}
    for condition in CONDITIONS:
        prepared[condition], metadata[condition] = prepare_custom_image(
            processor,
            source_row,
            ROOT / paired["paths"][condition],
            device="cuda",
        )
    prompt_ids = [metadata[condition]["prompt_token_ids"] for condition in CONDITIONS]
    visual_sets = [metadata[condition]["visual_token_indices"] for condition in CONDITIONS]
    grids = [metadata[condition]["image_grid_thw"] for condition in CONDITIONS]
    layout_exact = bool(
        all(value == prompt_ids[0] for value in prompt_ids[1:])
        and all(value == visual_sets[0] for value in visual_sets[1:])
        and all(value == grids[0] for value in grids[1:])
    )
    if not layout_exact:
        raise RuntimeError(f"Condition token layout mismatch for base {base}")

    context = [int(value) for value in annotation["history_before_ed_token_ids"]]
    ed = int(annotation["ed_generated_index"])
    if len(context) != ed:
        raise RuntimeError(f"Frozen E_d history mismatch for base {base}")
    candidate_original = [int(value) for value in annotation["original_divergent_suffix_ids"]]
    candidate_counterfactual = [
        int(value) for value in annotation["counterfactual_divergent_suffix_ids"]
    ]
    question = str(source_row.get("query_cot") or source_row.get("question") or "")
    base_groups = build_token_groups(
        prompt_token_ids=prompt_ids[0],
        visual_token_indices=visual_sets[0],
        question_token_ids=processor.tokenizer.encode(question, add_special_tokens=False),
    )
    cells = [
        cell
        for cell in config["frozen_cells"]
        if (phase == "upstream") == (cell["role"] == "upstream_control")
    ]
    if phase == "source":
        if source_targets is None:
            raise ValueError("Source phase requires frozen source targets")
        target_ids = set(source_targets["target_cell_ids"])
        cells = [cell for cell in cells if cell["cell_id"] in target_ids]
    cell_rows = []
    mechanical = {
        "all_baselines_exact_stage3b5": True,
        "all_query_head_selectivity_valid": True,
        "all_source_group_isolation_valid": True,
        "all_self_restorations_exact": True,
        "all_scores_finite": True,
    }
    for cell in cells:
        intervention_index = ed - 1 if cell["coordinate"] == "Ed_minus_1" else ed
        point = stage3b5_point(stage3b5, cell["coordinate"])
        prompt_length = len(prompt_ids[0])
        current_position = prompt_length + intervention_index - 1
        source_groups = build_source_token_groups(
            prompt_length=prompt_length,
            current_absolute_position=current_position,
            visual_positions=base_groups["V"],
            eligible_prefix_positions=base_groups["P_post_image"],
        )
        attention_groups = {
            "V": source_groups["V"],
            "P": source_groups["P"],
            "R": source_groups["R"],
        }
        captures = {
            condition: capture_preference_head_states(
                model=model,
                prepared=prepared[condition],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                intervention_generated_index=intervention_index,
                layer_index=int(cell["layer_index"]),
                attention_groups=attention_groups,
                seed=int(config["seed"]),
            )
            for condition in CONDITIONS
        }
        baseline_exact = {
            condition: scores_exact(captures[condition], point["no_switch"][condition])
            for condition in CONDITIONS
        }
        mechanical["all_baselines_exact_stage3b5"] &= all(baseline_exact.values())
        gain = stage3b5_attention_gain(point, cell)
        units = units_for_cell(
            phase=phase,
            cell=cell,
            freeze=freeze,
            discovery_head_count=discovery_head_count,
        )
        if phase == "source":
            allowed = {
                (row["cell_id"], row["unit_id"])
                for row in source_targets["targets"]
            }
            units = [unit for unit in units if (cell["cell_id"], unit["unit_id"]) in allowed]
        rows = []
        physical_cache: dict[tuple[tuple[int, ...], str], dict[str, Any]] = {}
        for unit in units:
            groups = config["source_path_gate"]["groups"] if phase == "source" else ["all"]
            for group in groups:
                cache_key = (tuple(int(head) for head in unit["heads"]), group)
                if cache_key not in physical_cache:
                    physical_cache[cache_key] = score_unit(
                        model=model,
                        prepared=prepared,
                        captures=captures,
                        context=context,
                        candidate_original=candidate_original,
                        candidate_counterfactual=candidate_counterfactual,
                        intervention_index=intervention_index,
                        cell=cell,
                        unit=unit,
                        source_positions=source_groups[group],
                        attention_groups=attention_groups,
                        attention_gain=gain,
                        seed=int(config["seed"]),
                        source_group=group,
                    )
                row = copy.deepcopy(physical_cache[cache_key])
                row["unit_id"] = unit["unit_id"]
                row["unit_kind"] = unit["kind"]
                row["origin_cell_id"] = unit.get("origin_cell_id")
                row["physical_score_reused"] = cache_key in physical_cache and bool(
                    rows and any(
                        previous["heads"] == row["heads"]
                        and previous["source_group"] == group
                        for previous in rows
                    )
                )
                rows.append(row)
                mechanical["all_query_head_selectivity_valid"] &= bool(
                    row["mechanical_audit"]["all_query_head_selectivity_valid"]
                )
                mechanical["all_source_group_isolation_valid"] &= bool(
                    row["mechanical_audit"]["all_source_group_isolation_valid"]
                )
                mechanical["all_self_restorations_exact"] &= bool(
                    row["all_self_restorations_exact"]
                )
                mechanical["all_scores_finite"] &= bool(row["all_scores_finite"])
        cell_rows.append({
            **cell,
            "intervention_generated_index": intervention_index,
            "current_absolute_position": current_position,
            "stage3b5_attention_gain": gain,
            "source_groups": source_groups,
            "baseline_exact_stage3b5": baseline_exact,
            "no_intervention": {
                condition: public_capture(capture)
                for condition, capture in captures.items()
            },
            "unit_results": rows,
        })

    return {
        "base_problem_id": base,
        "example_id": str(item["example_id"]),
        "evidence_type": item["edit_tier"],
        "prefix_sha256": item["prefix_sha256"],
        "ed_generated_index": ed,
        "phase": phase,
        "condition_layout_exact": layout_exact,
        "selection_used_attention": False,
        "cells": cell_rows,
        "mechanical_controls": mechanical,
    }


def main() -> None:
    args = parse_args()
    config = read_json(args.config)
    freeze = read_json(args.candidate_freeze) if args.candidate_freeze else None
    source_targets = read_json(args.source_targets) if args.source_targets else None
    output_dir = args.output_dir.resolve()
    output_dir.relative_to((OUT / ("discovery/raw" if args.phase == "discovery" else "scoring/raw")).resolve())
    manifest = read_jsonl(args.manifest)
    if args.max_bases < 0:
        raise ValueError("--max-bases must be nonnegative")
    if args.max_bases:
        manifest = manifest[: int(args.max_bases)]
    annotations = {
        str(row["base_problem_id"]): row for row in read_jsonl(args.annotations)
    }
    stage3b5_paths = reference_paths(args.stage3b5_raw_root)
    bases = [str(row["base_problem_id"]) for row in manifest]
    signature = {
        "manifest": str(args.manifest.resolve()),
        "base_problem_ids": bases,
        "config": str(args.config.resolve()),
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "stage3b5_raw_root": str(args.stage3b5_raw_root.resolve()),
        "phase": args.phase,
        "candidate_freeze": str(args.candidate_freeze.resolve()) if args.candidate_freeze else None,
        "source_targets": str(args.source_targets.resolve()) if args.source_targets else None,
        "seed": int(config["seed"]),
        "required_gpu_class": args.required_gpu_class,
        "repeat_first": bool(args.repeat_first),
        "discovery_head_count": int(args.discovery_head_count),
        "max_bases": int(args.max_bases),
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
        raise RuntimeError(
            f"Expected {args.required_gpu_class}, observed {environment['gpu_name']}"
        )
    architecture = config["architecture_expected"]
    text_config = model.config.text_config
    observed = {
        "language_layers": int(text_config.num_hidden_layers),
        "logical_query_heads": int(text_config.num_attention_heads),
        "kv_heads": int(text_config.num_key_value_heads),
        "query_heads_per_kv_group": int(
            text_config.num_attention_heads // text_config.num_key_value_heads
        ),
        "head_dimension": int(text_config.head_dim),
    }
    if observed != architecture:
        raise RuntimeError(f"GQA architecture mismatch: {observed} != {architecture}")
    environment["stage3b6_gqa_architecture"] = observed
    write_json(output_dir / "environment.json", environment)
    torch.cuda.reset_peak_memory_stats()

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
        if base not in annotations or base not in stage3b5_paths:
            raise RuntimeError(f"Missing frozen annotation/reference for base {base}")
        example_id = str(item["example_id"])
        if example_id not in data:
            raise RuntimeError(f"Missing MathVerse example {example_id}")
        result = score_one(
            item=item,
            annotation=annotations[base],
            stage3b5=read_json(stage3b5_paths[base]),
            source_row=data[example_id],
            processor=processor,
            model=model,
            config=config,
            phase=args.phase,
            freeze=freeze,
            source_targets=source_targets,
            discovery_head_count=int(args.discovery_head_count),
        )
        ensure_directory(result_path.parent)
        write_json(result_path, result)
        results.append(result)
        if args.repeat_first and index == 0:
            repeated = score_one(
                item=item,
                annotation=annotations[base],
                stage3b5=read_json(stage3b5_paths[base]),
                source_row=data[example_id],
                processor=processor,
                model=model,
                config=config,
                phase=args.phase,
                freeze=freeze,
                source_targets=source_targets,
                discovery_head_count=int(args.discovery_head_count),
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
                "all_baselines_exact_stage3b5",
                "all_query_head_selectivity_valid",
                "all_source_group_isolation_valid",
                "all_self_restorations_exact",
                "all_scores_finite",
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
