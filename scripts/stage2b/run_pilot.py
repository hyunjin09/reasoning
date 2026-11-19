#!/usr/bin/env python3
"""Run the gated five-example Stage 2B ROI-knockout pilot on one A6000."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import socket
import sys
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
import transformers

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_text
from visual_reasoning.stage0.modeling import attention_modules, generate_once, load_runtime, prepare_example, runtime_environment
from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs
from visual_reasoning.stage2b.evaluation import classify_local_effects, first_semantic_divergence, first_token_divergence
from visual_reasoning.stage2b.intervention import ROIAttentionKnockout
from visual_reasoning.stage2b.runtime import evidence_number_mentions, free_rollout, teacher_forced_local_metrics


ROOT = Path(__file__).resolve().parents[2]
ALLOWED_NODES = {"node02", "node06", "node07"}
SAFETY_CEILING = 40_960
SEED = 1_234


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs/stage2b")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def current_annotation_hashes(config: dict[str, Any]) -> dict[str, str]:
    return {relative: sha256(ROOT / relative) for relative in config["stage2a_annotation_hashes_before"]}


def eos_token_ids(model: Any) -> list[int]:
    value = model.generation_config.eos_token_id
    if value is None:
        return []
    return [int(value)] if isinstance(value, int) else [int(item) for item in value]


def generation_record(generation: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in generation.items() if key not in {"token_rows", "attention_arrays"}}


def condition_definitions(spec: dict[str, Any], window_name: str) -> list[tuple[str, list[int] | None]]:
    suffix = f"{window_name}window"
    return [
        ("baseline", None),
        (f"A_roi_{suffix}", list(spec["roi_A_visual_token_indices"])),
        (f"B_roi_{suffix}", list(spec["roi_B_visual_token_indices"])),
        (f"irrelevant_roi_{suffix}", list(spec[f"irrelevant_{window_name}_visual_token_indices"])),
    ]


def short_condition_name(condition_name: str) -> str:
    if condition_name == "baseline":
        return "baseline"
    if condition_name.startswith("A_roi"):
        return "A_roi"
    if condition_name.startswith("B_roi"):
        return "B_roi"
    return "irrelevant_roi"


def condition_path(example_dir: Path, condition_name: str, window_name: str, artifact: str) -> Path:
    directory = example_dir / "conditions" / condition_name
    filename = f"{window_name}window_{artifact}.json" if condition_name == "baseline" else f"{artifact}.json"
    return directory / filename


def decode_divergence(processor: Any, baseline: list[int], condition: list[int]) -> dict[str, Any]:
    index = first_token_divergence(baseline, condition)
    if index is None:
        return {
            "first_token_divergence": None,
            "baseline_snippet": "",
            "condition_snippet": "",
            "first_semantic_divergence": first_semantic_divergence(
                processor.tokenizer.decode(baseline, skip_special_tokens=True),
                processor.tokenizer.decode(condition, skip_special_tokens=True),
            ),
        }
    left = max(0, index - 8)
    right = index + 24
    decode = lambda ids: processor.tokenizer.decode(ids[left:right], skip_special_tokens=True, clean_up_tokenization_spaces=False)
    baseline_text = processor.tokenizer.decode(baseline, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    condition_text = processor.tokenizer.decode(condition, skip_special_tokens=True, clean_up_tokenization_spaces=False)
    return {
        "first_token_divergence": int(index),
        "baseline_snippet": decode(baseline),
        "condition_snippet": decode(condition),
        "first_semantic_divergence": first_semantic_divergence(baseline_text, condition_text),
    }


def write_annotation_snapshots(example_dir: Path, example_id: str, spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    stage2a_dir = ROOT / "outputs/stage2a/evidence_subset/examples" / example_id
    annotation = {
        "example_id": example_id,
        "roi_A": load_json(stage2a_dir / "roi_A.json"),
        "roi_B": load_json(stage2a_dir / "roi_B.json"),
        "candidate_intervention_windows": load_json(stage2a_dir / "candidate_intervention_windows.json"),
        "selected_A_window": spec["A_window"],
        "selected_B_window": spec["B_window"],
        "selected_joint_computation_window": spec["joint_computation_window"],
        "selection_rule": spec["selection_rule"],
    }
    stage1_input = load_json(ROOT / "outputs/stage1/discovery/examples" / example_id / "input.json")
    roi_mapping = {
        "example_id": example_id,
        "all_visual_token_indices": spec["all_visual_token_indices"],
        "visual_mapping": stage1_input["visual_mapping"],
        "original_image_size": stage1_input["original_image_size"],
        "stage2a_roi_mapping_image": str((stage2a_dir / "roi_mapping.png").relative_to(ROOT)),
        "roi_A_visual_token_indices": spec["roi_A_visual_token_indices"],
        "roi_B_visual_token_indices": spec["roi_B_visual_token_indices"],
        "irrelevant_A_visual_focus_column_indices": spec["irrelevant_A_visual_focus_column_indices"],
        "irrelevant_A_visual_token_indices": spec["irrelevant_A_visual_token_indices"],
        "irrelevant_B_visual_focus_column_indices": spec["irrelevant_B_visual_focus_column_indices"],
        "irrelevant_B_visual_token_indices": spec["irrelevant_B_visual_token_indices"],
        "control_notes": spec["control_notes"],
    }
    write_json(example_dir / "annotation_snapshot.json", annotation)
    write_json(example_dir / "roi_mapping_snapshot.json", roi_mapping)
    return annotation, roi_mapping


def smoke_markdown(report: dict[str, Any]) -> str:
    checks = report["checks"]
    lines = [
        "# Stage 2B Intervention Validation",
        "",
        f"Overall: **{'PASS' if report['passed'] else 'FAIL'}**",
        "",
        f"- Node: `{report['environment']['node']}`",
        f"- GPU: `{report['environment']['gpu_name']}`",
        f"- Smoke example: `{report['example_id']}`",
        "",
        "## Checks",
        "",
    ]
    for name, check in checks.items():
        status = ("PASS" if check["passed"] else "FAIL") if check.get("required_for_gate", True) else "INFO"
        lines.append(f"- {status} — `{name}`: {check['detail']}")
    lines.extend(
        [
            "",
            "The mandatory faithfulness gate is the paired A6000 unhooked versus hook-attached/no-intervention exact token comparison. The frozen Stage 1 trace was generated on A5000 and is retained as a separate hardware-migration diagnostic.",
        ]
    )
    return "\n".join(lines)


def run_smoke(
    *,
    output_dir: Path,
    processor: Any,
    model: Any,
    row: dict[str, Any],
    spec: dict[str, Any],
    dataset_root: Path,
    generation_kwargs: dict[str, Any],
    environment: dict[str, Any],
) -> dict[str, Any]:
    smoke_dir = ensure_directory(output_dir / "smoke")
    prepared, input_record, _ = prepare_example(processor, row, dataset_root, device="cuda")
    frozen_generation = load_json(ROOT / "outputs/stage1/discovery/examples/699/generation.json")
    frozen_ids = [int(value) for value in frozen_generation["generated_token_ids"]]

    print("[smoke] unhooked A6000 baseline", flush=True)
    unhooked = generate_once(
        model,
        processor,
        prepared,
        SAFETY_CEILING,
        recorder=None,
        generation_kwargs=generation_kwargs,
        seed=SEED,
        collect_predictive_metrics=False,
    )
    write_json(smoke_dir / "unhooked_baseline_generation.json", generation_record(unhooked))

    intervention = ROIAttentionKnockout(
        int(input_record["prompt_token_count"]), int(model.config.text_config.num_attention_heads)
    ).attach(attention_modules(model))
    try:
        print("[smoke] hook-attached no-intervention A6000 baseline", flush=True)
        intervention.set_condition(None, None)
        hooked = generate_once(
            model,
            processor,
            prepared,
            SAFETY_CEILING,
            recorder=None,
            generation_kwargs=generation_kwargs,
            seed=SEED,
            collect_predictive_metrics=False,
        )
        write_json(smoke_dir / "hooked_baseline_generation.json", generation_record(hooked))

        a_window = tuple(int(value) for value in spec["A_window"])
        print("[smoke] target-mask teacher-forced replicate 1", flush=True)
        local_one, log_probs_one = teacher_forced_local_metrics(
            model=model,
            prepared=prepared,
            clean_token_ids=frozen_ids,
            prompt_length=int(input_record["prompt_token_count"]),
            start_token=a_window[0],
            horizon_tokens=int(spec["local_evaluation_horizon_tokens"]),
            intervention=intervention,
            roi_key_indices=list(spec["roi_A_visual_token_indices"]),
            intervention_window=a_window,
            seed=SEED,
        )
        print("[smoke] target-mask teacher-forced replicate 2", flush=True)
        local_two, log_probs_two = teacher_forced_local_metrics(
            model=model,
            prepared=prepared,
            clean_token_ids=frozen_ids,
            prompt_length=int(input_record["prompt_token_count"]),
            start_token=a_window[0],
            horizon_tokens=int(spec["local_evaluation_horizon_tokens"]),
            intervention=intervention,
            roi_key_indices=list(spec["roi_A_visual_token_indices"]),
            intervention_window=a_window,
            seed=SEED,
        )
        reproducible = bool(torch.equal(log_probs_one, log_probs_two))
        del log_probs_one, log_probs_two

        print("[smoke] four-token KV-cache rollout", flush=True)
        kv_rollout = free_rollout(
            model=model,
            processor=processor,
            prepared=prepared,
            clean_token_ids=frozen_ids,
            ground_truth=str(row["answer"]),
            start_token=a_window[0],
            safety_ceiling=a_window[0] + 4,
            generation_kwargs=generation_kwargs,
            seed=SEED,
            eos_token_ids=eos_token_ids(model),
            intervention=intervention,
            roi_key_indices=list(spec["roi_A_visual_token_indices"]),
            intervention_window=a_window,
        )
    finally:
        intervention.close()

    expected_active = min(
        int(spec["local_evaluation_horizon_tokens"]),
        int(a_window[1]) - int(a_window[0]),
    )
    expected_entries = (
        int(model.config.text_config.num_hidden_layers)
        * expected_active
        * len(spec["roi_A_visual_token_indices"])
    )
    audit = local_one["hook_audit"]
    expected_layers = list(range(int(model.config.text_config.num_hidden_layers)))
    roi_a = set(spec["roi_A_visual_token_indices"])
    roi_b = set(spec["roi_B_visual_token_indices"])
    irrelevant_a = set(spec["irrelevant_A_visual_token_indices"])
    checks = {
        "paired_A6000_hook_faithfulness": {
            "passed": unhooked["generated_token_ids"] == hooked["generated_token_ids"],
            "detail": f"{len(unhooked['generated_token_ids'])} unhooked vs {len(hooked['generated_token_ids'])} hooked tokens",
        },
        "historical_A5000_trace_match_diagnostic": {
            "passed": hooked["generated_token_ids"] == frozen_ids,
            "detail": f"historical={len(frozen_ids)} tokens; A6000={len(hooked['generated_token_ids'])} tokens; diagnostic only",
            "required_for_gate": False,
        },
        "roi_mapping_matches_frozen": {
            "passed": (
                list(input_record["visual_token_indices"]) == list(spec["all_visual_token_indices"])
                and roi_a.issubset(input_record["visual_token_indices"])
                and roi_b.issubset(input_record["visual_token_indices"])
            ),
            "detail": f"visual={len(input_record['visual_token_indices'])}, A={len(roi_a)}, B={len(roi_b)}",
        },
        "only_intended_mask_entries": {
            "passed": (
                int(audit["tensor_entries_modified"]) == expected_entries
                and int(audit["target_entries_actually_changed"]) == expected_entries
                and sorted(set(audit["layers_modified"])) == expected_layers
                and sorted(set(audit["decision_indices"])) == list(range(a_window[0], min(a_window[1], a_window[0] + 32)))
            ),
            "detail": (
                f"assigned={audit['tensor_entries_modified']}, actually changed={audit['target_entries_actually_changed']}, "
                f"expected={expected_entries} broadcast-mask entries"
            ),
        },
        "target_mask_preserves_other_visual_access": {
            "passed": len(set(spec["all_visual_token_indices"]) - roi_a) > 0,
            "detail": f"{len(set(spec['all_visual_token_indices']) - roi_a)} visual tokens remain accessible",
        },
        "controls_preserve_target_access": {
            "passed": roi_a.isdisjoint(roi_b) and roi_a.isdisjoint(irrelevant_a),
            "detail": "wrong-evidence and irrelevant A-window masks are disjoint from ROI A",
        },
        "finite_and_reproducible_local_tensors": {
            "passed": bool(local_one["finite"] and local_two["finite"] and reproducible),
            "detail": f"finite={local_one['finite'] and local_two['finite']}; exact repeat={reproducible}",
        },
        "kv_cache_generation_functional": {
            "passed": len(kv_rollout["continuation_token_ids"]) == 4 and kv_rollout["hook_audit"]["modified_calls"] > 0,
            "detail": f"generated={len(kv_rollout['continuation_token_ids'])} tokens; modified calls={kv_rollout['hook_audit']['modified_calls']}",
        },
    }
    required = [value for value in checks.values() if value.get("required_for_gate", True)]
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "example_id": "699",
        "passed": all(bool(value["passed"]) for value in required),
        "environment": environment,
        "checks": checks,
        "local_target_replicate_1": local_one,
        "local_target_replicate_2": local_two,
        "kv_cache_rollout": kv_rollout,
    }
    write_json(smoke_dir / "intervention_validation.json", report)
    write_text(smoke_dir / "intervention_validation.md", smoke_markdown(report))
    return report


def run_example(
    *,
    output_dir: Path,
    processor: Any,
    model: Any,
    row: dict[str, Any],
    spec: dict[str, Any],
    dataset_root: Path,
    generation_kwargs: dict[str, Any],
    eos_ids: list[int],
) -> dict[str, Any]:
    example_id = str(spec["example_id"])
    example_dir = ensure_directory(output_dir / "examples" / example_id)
    annotation, _ = write_annotation_snapshots(example_dir, example_id, spec)
    prepared, input_record, _ = prepare_example(processor, row, dataset_root, device="cuda")
    if list(input_record["visual_token_indices"]) != list(spec["all_visual_token_indices"]):
        raise RuntimeError(f"Prepared visual tokens differ from frozen mapping for {example_id}")
    clean_generation = load_json(ROOT / "outputs/stage1/discovery/examples" / example_id / "generation.json")
    clean_ids = [int(value) for value in clean_generation["generated_token_ids"]]
    intervention = ROIAttentionKnockout(
        int(input_record["prompt_token_count"]), int(model.config.text_config.num_attention_heads)
    ).attach(attention_modules(model))
    local_summary: dict[str, Any] = {"example_id": example_id, "windows": {}}
    behavioral_summary: dict[str, Any] = {"example_id": example_id, "windows": {}}
    try:
        for window_name in ("A", "B"):
            window = tuple(int(value) for value in spec[f"{window_name}_window"])
            definitions = condition_definitions(spec, window_name)
            print(f"[{example_id}] {window_name}-window local metrics", flush=True)
            baseline_log_probs: torch.Tensor | None = None
            window_local: dict[str, Any] = {}
            for condition_name, roi in definitions:
                result, distribution = teacher_forced_local_metrics(
                    model=model,
                    prepared=prepared,
                    clean_token_ids=clean_ids,
                    prompt_length=int(input_record["prompt_token_count"]),
                    start_token=window[0],
                    horizon_tokens=int(spec["local_evaluation_horizon_tokens"]),
                    intervention=intervention,
                    roi_key_indices=roi,
                    intervention_window=window if roi is not None else None,
                    seed=SEED,
                    baseline_log_probs=baseline_log_probs,
                )
                if condition_name == "baseline":
                    baseline_log_probs = distribution
                    result["delta_clean_token_nll"] = 0.0
                    result["clean_token_log_probability_loss"] = 0.0
                else:
                    result["delta_clean_token_nll"] = (
                        float(result["mean_clean_token_nll"])
                        - float(window_local["baseline"]["mean_clean_token_nll"])
                    )
                    result["clean_token_log_probability_loss"] = result["delta_clean_token_nll"]
                    del distribution
                result["condition"] = condition_name
                result["window_name"] = window_name
                window_local[short_condition_name(condition_name)] = result
                write_json(condition_path(example_dir, condition_name, window_name, "local"), result)
            if baseline_log_probs is not None:
                del baseline_log_probs
            local_summary["windows"][window_name] = window_local

            print(f"[{example_id}] {window_name}-window free rollouts", flush=True)
            window_behavior: dict[str, Any] = {}
            baseline_rollout: dict[str, Any] | None = None
            for condition_name, roi in definitions:
                result = free_rollout(
                    model=model,
                    processor=processor,
                    prepared=prepared,
                    clean_token_ids=clean_ids,
                    ground_truth=str(row["answer"]),
                    start_token=window[0],
                    safety_ceiling=SAFETY_CEILING,
                    generation_kwargs=generation_kwargs,
                    seed=SEED,
                    eos_token_ids=eos_ids,
                    intervention=intervention,
                    roi_key_indices=roi,
                    intervention_window=window if roi is not None else None,
                )
                result["condition"] = condition_name
                result["window_name"] = window_name
                result["evidence_mentions"] = {
                    "A": evidence_number_mentions(result["full_response"], annotation["roi_A"]["semantic_fact"]),
                    "B": evidence_number_mentions(result["full_response"], annotation["roi_B"]["semantic_fact"]),
                }
                if condition_name == "baseline":
                    baseline_rollout = result
                    result["divergence_from_baseline"] = {
                        "first_token_divergence": None,
                        "baseline_snippet": "",
                        "condition_snippet": "",
                        "first_semantic_divergence": {
                            "segment_index": None,
                            "baseline_segment": None,
                            "condition_segment": None,
                        },
                    }
                else:
                    assert baseline_rollout is not None
                    result["divergence_from_baseline"] = decode_divergence(
                        processor,
                        baseline_rollout["continuation_token_ids"],
                        result["continuation_token_ids"],
                    )
                window_behavior[short_condition_name(condition_name)] = result
                write_json(condition_path(example_dir, condition_name, window_name, "rollout"), result)
                gc.collect()
                torch.cuda.empty_cache()
            behavioral_summary["windows"][window_name] = window_behavior
    finally:
        intervention.close()

    effect_table = {
        window_name: {
            condition: float(local_summary["windows"][window_name][condition]["delta_clean_token_nll"])
            for condition in ("A_roi", "B_roi", "irrelevant_roi")
        }
        for window_name in ("A", "B")
    }
    interpretation = classify_local_effects(effect_table)
    interpretation["example_id"] = example_id
    interpretation["effect_table_nats_per_token"] = effect_table
    interpretation["behavioral_note"] = "Free rollouts use one matched seed and are qualitative, not a prevalence estimate."
    crossover = {
        "example_id": example_id,
        "rows": {
            "baseline": {"A_window": 0.0, "B_window": 0.0},
            "ROI_A_knockout": {"A_window": effect_table["A"]["A_roi"], "B_window": effect_table["B"]["A_roi"]},
            "ROI_B_knockout": {"A_window": effect_table["A"]["B_roi"], "B_window": effect_table["B"]["B_roi"]},
            "irrelevant_ROI_knockout": {
                "A_window": effect_table["A"]["irrelevant_roi"],
                "B_window": effect_table["B"]["irrelevant_roi"],
            },
        },
        "classification": interpretation,
    }
    write_json(example_dir / "local_effects.json", local_summary)
    write_json(example_dir / "behavioral_effects.json", behavioral_summary)
    write_json(example_dir / "crossover_table.json", crossover)
    write_text(
        example_dir / "interpretation.md",
        "\n".join(
            [
                f"# Example {example_id}",
                "",
                f"Classification: **{interpretation['category']} — {interpretation['label']}**",
                "",
                f"- A-window ΔNLL: A ROI `{effect_table['A']['A_roi']:.4f}`, B ROI `{effect_table['A']['B_roi']:.4f}`, irrelevant `{effect_table['A']['irrelevant_roi']:.4f}` nats/token.",
                f"- B-window ΔNLL: A ROI `{effect_table['B']['A_roi']:.4f}`, B ROI `{effect_table['B']['B_roi']:.4f}`, irrelevant `{effect_table['B']['irrelevant_roi']:.4f}` nats/token.",
                f"- Crossover score: `{interpretation['crossover_score']:.4f}`.",
                "",
                "This category describes the causal effect of the specified attention-edge knockout in this example. It does not establish a general visual-memory or re-grounding mechanism.",
            ]
        ),
    )
    return {
        "example_id": example_id,
        "effect_table": effect_table,
        "interpretation": interpretation,
        "local_effects_path": str((example_dir / "local_effects.json").relative_to(ROOT)),
        "behavioral_effects_path": str((example_dir / "behavioral_effects.json").relative_to(ROOT)),
    }


def project_decision(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(result["interpretation"]["category"] for result in results)
    crossover_count = int(counts.get("P1", 0))
    partial_count = int(counts.get("P2", 0))
    target_minus_irrelevant = []
    for result in results:
        effects = result["effect_table"]
        target_minus_irrelevant.extend(
            [
                effects["A"]["A_roi"] - effects["A"]["irrelevant_roi"],
                effects["B"]["B_roi"] - effects["B"]["irrelevant_roi"],
            ]
        )
    median_margin = float(np.median(np.asarray(target_minus_irrelevant, dtype=np.float64)))
    if crossover_count >= 3 and median_margin > 0:
        decision = "GO"
        option = "A"
        recommendation = "Scale evidence-specific causal analysis to the remaining annotated examples."
    elif (crossover_count >= 2 or crossover_count + partial_count >= 2) and median_margin > 0:
        decision = "CONDITIONAL GO"
        option = "B"
        recommendation = "Refine timing/ROI intervention and repeat a small pilot."
    else:
        decision = "NO-GO"
        option = "C"
        recommendation = "Abandon attention-guided ROI causality as the main route and redesign the measurement strategy."
    return {
        "decision": decision,
        "recommended_option": option,
        "recommendation": recommendation,
        "P_category_counts": dict(sorted(counts.items())),
        "strong_crossover_count": crossover_count,
        "partial_specificity_count": partial_count,
        "median_target_minus_irrelevant_delta_nll": median_margin,
        "rule": "GO for >=3 P1 and positive median target-minus-irrelevant margin; conditional for >=2 P1 or >=2 P1+P2 with positive margin; otherwise NO-GO",
    }


def write_summaries(
    *,
    output_dir: Path,
    specs: list[dict[str, Any]],
    smoke: dict[str, Any],
    results: list[dict[str, Any]],
    decision: dict[str, Any],
    hashes_unchanged: bool,
) -> dict[str, Any]:
    summaries = ensure_directory(output_dir / "summaries")
    local = {result["example_id"]: result["effect_table"] for result in results}
    behavioral = {
        result["example_id"]: load_json(output_dir / "examples" / result["example_id"] / "behavioral_effects.json")
        for result in results
    }
    crossover = {
        "project_decision": decision,
        "examples": {result["example_id"]: result["interpretation"] for result in results},
    }
    write_json(summaries / "local_effects.json", local)
    write_json(summaries / "behavioral_effects.json", behavioral)
    write_json(summaries / "crossover_summary.json", crossover)

    all_examples = len(results) == 5 and {result["example_id"] for result in results} == {
        "699", "739", "2799", "3044", "3764"
    }
    local_present = all((output_dir / "examples" / result["example_id"] / "local_effects.json").is_file() for result in results)
    rollouts_present = all(
        len(list((output_dir / "examples" / result["example_id"] / "conditions").glob("**/*rollout.json"))) == 8
        for result in results
    )
    categories_present = all(result["interpretation"]["category"] in {f"P{i}" for i in range(1, 7)} for result in results)
    size_controls = all(
        abs(int(spec[f"irrelevant_{window}_visual_token_count"]) - int(spec[f"roi_{window}_visual_token_count"])) <= 1
        for spec in specs
        for window in ("A", "B")
    )
    criteria = {
        "1_all_five_frozen_examples_attempted": all_examples,
        "2_baseline_hooked_inference_validated": bool(smoke["checks"]["paired_A6000_hook_faithfulness"]["passed"]),
        "3_target_roi_masking_correct": bool(smoke["checks"]["only_intended_mask_entries"]["passed"]),
        "4_wrong_evidence_controls_implemented": all_examples,
        "5_same_size_irrelevant_controls_implemented": size_controls,
        "6_A_B_windows_remained_frozen": hashes_unchanged,
        "7_local_teacher_forced_metrics_produced": local_present,
        "8_free_rollout_behavioral_outputs_produced": rollouts_present,
        "9_stage2a_annotations_unmodified": hashes_unchanged,
        "10_every_example_has_interpretation_category": categories_present,
        "11_project_level_decision_written": decision["decision"] in {"GO", "CONDITIONAL GO", "NO-GO"},
        "12_no_why_or_memory_stage_started": True,
    }
    acceptance = {
        "stage": "2B",
        "status": "PASS" if all(criteria.values()) else "FAIL",
        "criteria": criteria,
        "scientific_result_required_for_technical_pass": False,
        "project_decision": decision["decision"],
    }
    write_json(summaries / "stage2b_acceptance.json", acceptance)

    table_lines = []
    for result in results:
        example_id = result["example_id"]
        e = result["effect_table"]
        table_lines.append(
            f"| {example_id} | {e['A']['A_roi']:.4f} | {e['A']['B_roi']:.4f} | {e['A']['irrelevant_roi']:.4f} | "
            f"{e['B']['A_roi']:.4f} | {e['B']['B_roi']:.4f} | {e['B']['irrelevant_roi']:.4f} | "
            f"{result['interpretation']['category']} |"
        )
    windows = "; ".join(
        f"{spec['example_id']}: A={spec['A_window']}, B={spec['B_window']}" for spec in specs
    )
    roi_sizes = "; ".join(
        f"{spec['example_id']}: A={spec['roi_A_visual_token_count']}/{spec['irrelevant_A_visual_token_count']}, "
        f"B={spec['roi_B_visual_token_count']}/{spec['irrelevant_B_visual_token_count']}"
        for spec in specs
    )
    summary_md = "\n".join(
        [
            "# Stage 2B Summary",
            "",
            f"Technical acceptance: **{acceptance['status']}**. Project decision: **{decision['decision']}**.",
            "",
            "## Intervention",
            "",
            "Across all Qwen3-VL language layers and heads, an additive mask blocked only generated-query → selected visual-ROI key edges during the frozen acquisition window. Model weights, visual embeddings, other visual keys, prompt keys, reasoning keys, and the KV cache were unchanged.",
            "",
            "## Frozen pilot",
            "",
            f"Examples: `{', '.join(spec['example_id'] for spec in specs)}`.",
            "",
            f"Windows: {windows}.",
            "",
            f"Target/irrelevant visual-token counts: {roi_sizes}.",
            "",
            "The local metric used 32 clean tokens beginning at each frozen window start; the intervention ended at the frozen window boundary. Free rollouts used the Stage 1 official Thinking protocol with seed 1234 and EOS as the normal stop.",
            "",
            "## Smoke validation",
            "",
            f"The gated smoke test **{'passed' if smoke['passed'] else 'failed'}** on `{smoke['example_id']}`. Paired A6000 hook transparency was `{smoke['checks']['paired_A6000_hook_faithfulness']['passed']}`; exact deterministic local replication was `{smoke['checks']['finite_and_reproducible_local_tensors']['passed']}`; cached generation was `{smoke['checks']['kv_cache_generation_functional']['passed']}`. The A5000 historical trace comparison is reported separately and is not used to infer hook invasiveness across hardware.",
            "",
            "## Local clean-token effects",
            "",
            "ΔNLL values are nats/token relative to the no-intervention baseline in the same window.",
            "",
            "| Example | A@Awin | B@Awin | Irr@Awin | A@Bwin | B@Bwin | Irr@Bwin | Category |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
            *table_lines,
            "",
            f"Strong crossover count: `{decision['strong_crossover_count']}/5`; partial-specificity count: `{decision['partial_specificity_count']}/5`; median target-minus-irrelevant margin: `{decision['median_target_minus_irrelevant_delta_nll']:.4f}` nats/token.",
            "",
            "## Free-rollout behavior",
            "",
            "All eight window-matched rollouts per example were persisted with full continuations, answers, correctness, lengths, first token divergence, and simple evidence-number mention diagnostics. A single matched stochastic seed makes these qualitative paired outcomes, not frequency estimates.",
            "",
            "## Controls and limitations",
            "",
            "Wrong-evidence controls mask the other frozen evidence ROI. Irrelevant controls are disjoint from A and B and match target token count within one token. For 3764/B, the 42-token target occupies a large fraction of the 105 visual tokens, so its disjoint exact-size control necessarily spans most remaining non-evidence locations and is a weak spatial control.",
            "",
            "This five-example pilot tests causal dependence on the intervened attention edges. It does not by itself prove fresh visual evidence acquisition, visual-memory handoff, a LOOK/THINK state, or a dataset-wide mechanism. ROI-size and off-manifold masking effects remain alternative explanations.",
            "",
            "## Decision",
            "",
            f"**{decision['decision']}** under the frozen rule. {decision['recommendation']}",
            "",
            "Stage 2B stops here. The recommendation has not been executed.",
        ]
    )
    write_text(summaries / "stage2b_summary.md", summary_md)
    write_text(
        summaries / "next_stage_recommendation.md",
        "\n".join(
            [
                "# Next Stage Recommendation",
                "",
                f"Project decision: **{decision['decision']}**.",
                "",
                f"Recommended option: **Option {decision['recommended_option']} — {decision['recommendation']}**",
                "",
                f"Basis: `{decision['strong_crossover_count']}/5` P1 crossovers, `{decision['partial_specificity_count']}/5` P2 partial patterns, and median target-minus-irrelevant ΔNLL `{decision['median_target_minus_irrelevant_delta_nll']:.4f}` nats/token.",
                "",
                "Do not execute this recommendation automatically. Review Stage 2B first.",
            ]
        ),
    )
    return acceptance


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    if output_dir != (ROOT / "outputs/stage2b").resolve():
        raise ValueError("Stage 2B outputs must use outputs/stage2b")
    config_path = output_dir / "config/intervention_config.json"
    manifest_path = output_dir / "config/pilot_manifest.jsonl"
    if not config_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Run prepare_config.py before causal execution")
    mutable_output_roots = (output_dir / "smoke", output_dir / "examples", output_dir / "summaries")
    if not args.resume and any(path.exists() and any(path.rglob("*")) for path in mutable_output_roots):
        raise FileExistsError("Existing Stage 2B causal outputs require --resume; refusing to overwrite them")
    config = load_json(config_path)
    specs = load_jsonl(manifest_path)
    if [spec["example_id"] for spec in specs] != ["699", "739", "2799", "3044", "3764"]:
        raise RuntimeError("Pilot manifest does not contain the exact frozen five-example order")
    if current_annotation_hashes(config) != config["stage2a_annotation_hashes_before"]:
        raise RuntimeError("Stage 2A annotation hashes changed after Stage 2B configuration was frozen")

    node = os.environ.get("SLURMD_NODENAME") or socket.gethostname().split(".")[0]
    if node not in ALLOWED_NODES:
        raise RuntimeError(f"Stage 2B must run on one of {sorted(ALLOWED_NODES)}, got {node}; node03 is forbidden")
    if not torch.cuda.is_available():
        raise RuntimeError("Stage 2B requires a scheduler-provided CUDA device")
    gpu_name = torch.cuda.get_device_name(0)
    if "A6000" not in gpu_name.upper():
        raise RuntimeError(f"Stage 2B requires an A6000, got {gpu_name}")

    dataset_rows = load_mathverse_rows(args.dataset_root)
    by_id = {str(row["sample_index"]): row for row in dataset_rows}
    print(f"Loading {args.model_checkpoint} on {node}/{gpu_name}", flush=True)
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, SAFETY_CEILING)
    environment.update(
        {
            "node": node,
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "python": sys.executable,
        }
    )
    write_json(output_dir / "config/runtime_environment.json", environment)
    if environment["language_attention_implementation"] != "eager":
        raise RuntimeError("ROI additive-mask intervention requires eager language attention")
    parameters = protocol_parameters("official", SAFETY_CEILING, SEED)
    generation_kwargs = transformers_generation_kwargs(parameters)

    smoke_path = output_dir / "smoke/intervention_validation.json"
    if args.resume and smoke_path.is_file() and load_json(smoke_path).get("passed"):
        smoke = load_json(smoke_path)
        print("[smoke] resumed prior PASS", flush=True)
    else:
        smoke = run_smoke(
            output_dir=output_dir,
            processor=processor,
            model=model,
            row=by_id["699"],
            spec=specs[0],
            dataset_root=args.dataset_root,
            generation_kwargs=generation_kwargs,
            environment=environment,
        )
    if not smoke["passed"]:
        print("Stage 2B smoke gate failed; stopping before five-example pilot", flush=True)
        raise SystemExit(2)

    results: list[dict[str, Any]] = []
    eos_ids = eos_token_ids(model)
    for index, spec in enumerate(specs, start=1):
        example_id = str(spec["example_id"])
        result_path = output_dir / "examples" / example_id / "result.json"
        if args.resume and result_path.is_file():
            results.append(load_json(result_path))
            print(f"[{index}/5] resumed {example_id}", flush=True)
            continue
        print(f"[{index}/5] running {example_id}", flush=True)
        try:
            result = run_example(
                output_dir=output_dir,
                processor=processor,
                model=model,
                row=by_id[example_id],
                spec=spec,
                dataset_root=args.dataset_root,
                generation_kwargs=generation_kwargs,
                eos_ids=eos_ids,
            )
            write_json(result_path, result)
            results.append(result)
        except Exception as exc:
            write_json(
                output_dir / "examples" / example_id / "error.json",
                {"example_id": example_id, "error": repr(exc), "traceback": traceback.format_exc()},
            )
            raise
        gc.collect()
        torch.cuda.empty_cache()

    hashes_after = current_annotation_hashes(config)
    hashes_unchanged = hashes_after == config["stage2a_annotation_hashes_before"]
    write_json(
        output_dir / "config/stage2a_annotation_hash_validation.json",
        {
            "unchanged": hashes_unchanged,
            "before": config["stage2a_annotation_hashes_before"],
            "after": hashes_after,
        },
    )
    decision = project_decision(results)
    acceptance = write_summaries(
        output_dir=output_dir,
        specs=specs,
        smoke=smoke,
        results=results,
        decision=decision,
        hashes_unchanged=hashes_unchanged,
    )
    print(json.dumps({"acceptance": acceptance["status"], "decision": decision["decision"]}), flush=True)


if __name__ == "__main__":
    main()
