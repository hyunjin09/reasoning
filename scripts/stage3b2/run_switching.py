#!/usr/bin/env python3
"""Run frozen Stage 3B.2 bidirectional visual-source switching scores."""

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
from visual_reasoning.stage3b2.metrics import normalize_by_evidence_gap, switch_metrics
from visual_reasoning.stage3b2.runtime import (
    capture_audit_valid,
    capture_preference_visual_kv,
    score_preference_with_visual_source,
    stage3a_divergent_tail_exact,
)


ROOT = Path(__file__).resolve().parents[2]
SEED = 1_234
CONDITIONS = ("original", "counterfactual", "sham")
CANDIDATES = ("original_candidate", "counterfactual_candidate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--stage3a-facts", type=Path, required=True)
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


def audit_summary(audit: list[dict[str, Any]]) -> dict[str, Any]:
    layers = sorted(int(row["layer_index"]) for row in audit)
    absolute = audit[0]["switched_absolute_query_indices"] if audit else []
    return {
        "layer_count": len(audit),
        "layers": layers,
        "first_switched_absolute_query": audit[0]["first_switched_absolute_query"] if audit else None,
        "minimum_switched_absolute_query": min(absolute) if absolute else None,
        "maximum_switched_absolute_query": max(absolute) if absolute else None,
        "switched_query_count_per_layer": len(absolute),
        "queries_before_switch_modified": sum(int(row["queries_before_switch_modified"]) for row in audit),
        "nonvisual_key_value_entries_replaced": sum(
            int(row["nonvisual_key_value_entries_replaced"]) for row in audit
        ),
        "source_visual_key_exact_recipient_match_all_layers": all(
            bool(row["source_visual_key_exact_recipient_match"]) for row in audit
        ),
        "source_visual_value_exact_recipient_match_all_layers": all(
            bool(row["source_visual_value_exact_recipient_match"]) for row in audit
        ),
        "visual_indices": audit[0]["visual_indices"] if audit else [],
    }


def public_preference(preference: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "L_o": float(preference["L_o"]),
        "L_c": float(preference["L_c"]),
        "D": float(preference["D"]),
    }
    if "all_switch_audits_valid" in preference:
        result["all_switch_audits_valid"] = bool(preference["all_switch_audits_valid"])
    for candidate in CANDIDATES:
        source = preference[candidate]
        clean = {key: value for key, value in source.items() if key != "switch_audit"}
        if "switch_audit" in source:
            clean["switch_audit_summary"] = audit_summary(source["switch_audit"])
        result[candidate] = clean
    return result


def public_capture(capture: dict[str, Any]) -> dict[str, Any]:
    result = public_preference(capture)
    result["capture_audit"] = {
        candidate: {
            "layer_count": len(capture["capture_audits"][candidate]),
            "layers": sorted(int(row["layer_index"]) for row in capture["capture_audits"][candidate]),
            "visual_indices": capture["capture_audits"][candidate][0]["visual_indices"],
            "captured_visual_key_shape": capture["capture_audits"][candidate][0][
                "captured_visual_key_shape"
            ],
        }
        for candidate in CANDIDATES
    }
    return result


def finite_preference(preference: dict[str, Any]) -> bool:
    return bool(
        math.isfinite(float(preference["D"]))
        and all(bool(preference[candidate]["finite"]) for candidate in CANDIDATES)
    )


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to((ROOT / "outputs/stage3b2/raw").resolve())
    manifest = read_jsonl(args.manifest)
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(args.annotations)}
    schedules = {str(row["base_problem_id"]): row for row in read_jsonl(args.schedule)}
    stage3a = {str(row["base_problem_id"]): row for row in read_jsonl(args.stage3a_facts)}
    bases = [str(row["base_problem_id"]) for row in manifest]
    signature = {
        "mode": args.mode,
        "manifest": str(args.manifest.resolve()),
        "annotations": str(args.annotations.resolve()),
        "schedule": str(args.schedule.resolve()),
        "base_problem_ids": bases,
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "seed": SEED,
        "scoring_path": "full-sequence eager attention with matching-shape donor visual K/V",
        "required_gpu_class": args.required_gpu_class,
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
    layer_count = int(model.config.text_config.num_hidden_layers)
    kv_heads = int(model.config.text_config.num_key_value_heads)
    head_dim = int(model.config.text_config.head_dim)
    all_results: list[dict[str, Any]] = []
    smoke_rows: list[dict[str, Any]] = []
    peak_gpu_bytes = 0

    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        example = str(item["example_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if args.resume and result_path.is_file():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            all_results.append(result)
            if result.get("smoke") is not None:
                smoke_rows.append(result["smoke"])
            print(f"[{item_index + 1}/{len(manifest)}] resumed base {base}", flush=True)
            continue
        ensure_directory(result_path.parent)
        if base not in annotations or base not in schedules or base not in stage3a:
            raise RuntimeError(f"Missing frozen reference for base {base}")
        annotation = annotations[base]
        schedule = schedules[base]
        if annotation["manual_audit_status"] != "pass" or schedule["prefix_sha256"] != item["prefix_sha256"]:
            raise RuntimeError(f"Unfrozen annotation or schedule mismatch for base {base}")
        context = [int(value) for value in annotation["history_before_ed_token_ids"]]
        ed = int(annotation["ed_generated_index"])
        if len(context) != ed:
            raise RuntimeError(f"History before E_d has the wrong length for base {base}")
        candidate_original = [int(value) for value in annotation["original_divergent_suffix_ids"]]
        candidate_counterfactual = [int(value) for value in annotation["counterfactual_divergent_suffix_ids"]]

        source_row = by_example[example]
        prepared: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        for condition in CONDITIONS:
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, source_row, ROOT / item["conditions"][condition], device="cuda"
            )
        prompt_ids = [metadata[name]["prompt_token_ids"] for name in CONDITIONS]
        visual_sets = [metadata[name]["visual_token_indices"] for name in CONDITIONS]
        grids = [metadata[name]["image_grid_thw"] for name in CONDITIONS]
        if not all(value == prompt_ids[0] for value in prompt_ids[1:]):
            raise RuntimeError(f"Condition prompt token mismatch for base {base}")
        if not all(value == visual_sets[0] for value in visual_sets[1:]) or not all(
            value == grids[0] for value in grids[1:]
        ):
            raise RuntimeError(f"Condition visual layout mismatch for base {base}")
        visual_indices = [int(value) for value in visual_sets[0]]
        prompt_length = len(prompt_ids[0])

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
            peak_gpu_bytes = max(peak_gpu_bytes, int(torch.cuda.max_memory_allocated()))
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
        common_count = int(annotation["common_prefix_token_count"])
        expected3a = stage3a[base]
        tail_exact = all(
            stage3a_divergent_tail_exact(
                captures[condition][candidate],
                expected3a["condition_scores"][condition][candidate],
                common_prefix_token_count=common_count,
            )
            for condition in CONDITIONS
            for candidate in CANDIDATES
        )
        d_oo = float(captures["original"]["D"])
        d_cc = float(captures["counterfactual"]["D"])
        evidence_gap = d_oo - d_cc
        if not math.isfinite(evidence_gap):
            raise RuntimeError(f"Nonfinite no-switch divergent evidence gap for base {base}: {evidence_gap}")

        timing_rows = []
        for checkpoint in schedule["checkpoints"]:
            switch_index = int(checkpoint["switch_generated_index"])
            self_o = score_preference_with_visual_source(
                model=model,
                prepared=prepared["original"],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                source_layers_by_candidate=captures["original"]["source_layers"],
                visual_indices=visual_indices,
                switch_generated_index=switch_index,
                seed=SEED,
            )
            self_c = score_preference_with_visual_source(
                model=model,
                prepared=prepared["counterfactual"],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                source_layers_by_candidate=captures["counterfactual"]["source_layers"],
                visual_indices=visual_indices,
                switch_generated_index=switch_index,
                seed=SEED,
            )
            o_to_c = score_preference_with_visual_source(
                model=model,
                prepared=prepared["original"],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                source_layers_by_candidate=captures["counterfactual"]["source_layers"],
                visual_indices=visual_indices,
                switch_generated_index=switch_index,
                seed=SEED,
            )
            c_to_o = score_preference_with_visual_source(
                model=model,
                prepared=prepared["counterfactual"],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                source_layers_by_candidate=captures["original"]["source_layers"],
                visual_indices=visual_indices,
                switch_generated_index=switch_index,
                seed=SEED,
            )
            o_to_sham = score_preference_with_visual_source(
                model=model,
                prepared=prepared["original"],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                source_layers_by_candidate=captures["sham"]["source_layers"],
                visual_indices=visual_indices,
                switch_generated_index=switch_index,
                seed=SEED,
            )
            peak_gpu_bytes = max(peak_gpu_bytes, int(torch.cuda.max_memory_allocated()))
            metrics = switch_metrics(
                d_oo=d_oo,
                d_oc=float(o_to_c["D"]),
                d_cc=d_cc,
                d_co=float(c_to_o["D"]),
                d_os=float(o_to_sham["D"]),
            )
            controls = {
                "self_O": self_o,
                "self_C": self_c,
                "O_to_C": o_to_c,
                "C_to_O": c_to_o,
                "O_to_sham": o_to_sham,
            }
            timing_rows.append(
                {
                    **checkpoint,
                    "no_switch": {"D_OO": d_oo, "D_CC": d_cc, "evidence_gap": evidence_gap},
                    "controls": {name: public_preference(value) for name, value in controls.items()},
                    **metrics,
                    "normalized_BRI_raw": normalize_by_evidence_gap(metrics["BRI"], evidence_gap),
                    "normalized_S_O_to_C_raw": normalize_by_evidence_gap(
                        metrics["S_O_to_C"], evidence_gap
                    ),
                    "normalized_S_C_to_O_raw": normalize_by_evidence_gap(
                        metrics["S_C_to_O"], evidence_gap
                    ),
                    "normalized_sham_raw": normalize_by_evidence_gap(
                        metrics["S_O_to_Sham"], evidence_gap
                    ),
                    "normalization_valid": evidence_gap > 0.0,
                    "self_O_exact": scores_exact(self_o, captures["original"]),
                    "self_C_exact": scores_exact(self_c, captures["counterfactual"]),
                    "all_switch_audits_valid": all(
                        bool(value["all_switch_audits_valid"]) for value in controls.values()
                    ),
                    "all_finite": all(finite_preference(value) for value in controls.values()),
                }
            )

        smoke = None
        if args.mode == "smoke":
            ed_row = next(row for row in timing_rows if "Ed" in row["labels"])
            repeated = score_preference_with_visual_source(
                model=model,
                prepared=prepared["original"],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                source_layers_by_candidate=captures["counterfactual"]["source_layers"],
                visual_indices=visual_indices,
                switch_generated_index=ed,
                seed=SEED,
            )
            smoke = {
                "base_problem_id": base,
                "ed_generated_index": ed,
                "capture_all_layers_valid": capture_valid,
                "stage3a_divergent_tail_exact": tail_exact,
                "all_checkpoint_switch_audits_valid": all(
                    row["all_switch_audits_valid"] for row in timing_rows
                ),
                "all_self_switches_exact": all(
                    row["self_O_exact"] and row["self_C_exact"] for row in timing_rows
                ),
                "all_finite": all(row["all_finite"] for row in timing_rows),
                "ed_O_to_C_deterministic_exact": scores_exact(repeated, {
                    "L_o": ed_row["controls"]["O_to_C"]["L_o"],
                    "L_c": ed_row["controls"]["O_to_C"]["L_c"],
                    "D": ed_row["controls"]["O_to_C"]["D"],
                    "original_candidate": ed_row["controls"]["O_to_C"]["original_candidate"],
                    "counterfactual_candidate": ed_row["controls"]["O_to_C"]["counterfactual_candidate"],
                }),
                "ed_target_switch_effect": float(ed_row["S_O_to_C"]),
                "ed_sham_switch_effect": float(ed_row["S_O_to_Sham"]),
                "ed_sham_smaller_than_target": abs(float(ed_row["S_O_to_Sham"]))
                < abs(float(ed_row["S_O_to_C"])),
                "condition_prompt_visual_layout_exact": True,
                "checkpoint_count": len(timing_rows),
            }
            smoke_rows.append(smoke)

        result = {
            "base_problem_id": base,
            "example_id": example,
            "evidence_type": item["edit_tier"],
            "prefix_sha256": item["prefix_sha256"],
            "e0_start_token": int(annotation["e0_start_token"]),
            "ed_generated_index": ed,
            "ed_alignment": "exact_baseline_tokens"
            if annotation["baseline_trace_common_prefix_exact"]
            else "semantic_teacher_forced_lead",
            "prompt_token_count": prompt_length,
            "visual_token_count": len(visual_indices),
            "visual_token_indices": visual_indices,
            "condition_layout_exact": True,
            "selection_used_attention": False,
            "no_switch": {condition: public_capture(capture) for condition, capture in captures.items()},
            "no_switch_evidence_gap": evidence_gap,
            "capture_all_layers_valid": capture_valid,
            "stage3a_divergent_tail_exact": tail_exact,
            "timing": timing_rows,
            "smoke": smoke,
        }
        write_json(result_path, result)
        all_results.append(result)
        print(f"[{item_index + 1}/{len(manifest)}] completed base {base} ({len(timing_rows)} checkpoints)", flush=True)
        del prepared, captures, timing_rows
        gc.collect()
        torch.cuda.empty_cache()

    write_jsonl(output_dir / "switch_results.jsonl", all_results)
    if smoke_rows:
        write_jsonl(output_dir / "smoke_results.jsonl", smoke_rows)
    write_json(
        output_dir / "result.json",
        {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "mode": args.mode,
            "base_problem_count": len(all_results),
            "problem_checkpoint_count": sum(len(row["timing"]) for row in all_results),
            "smoke_row_count": len(smoke_rows),
            "peak_gpu_allocated_bytes": peak_gpu_bytes,
            "all_capture_layers_valid": all(row["capture_all_layers_valid"] for row in all_results),
            "all_stage3a_divergent_tails_exact": all(
                row["stage3a_divergent_tail_exact"] for row in all_results
            ),
            "all_switch_audits_valid": all(
                timing["all_switch_audits_valid"] for row in all_results for timing in row["timing"]
            ),
            "all_self_switches_exact": all(
                timing["self_O_exact"] and timing["self_C_exact"]
                for row in all_results
                for timing in row["timing"]
            ),
            "all_finite": all(
                timing["all_finite"] for row in all_results for timing in row["timing"]
            ),
        },
    )


if __name__ == "__main__":
    main()
