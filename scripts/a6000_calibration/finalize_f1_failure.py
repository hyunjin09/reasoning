#!/usr/bin/env python3
"""Materialize the required calibration reports after the prospective F1 stop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from visual_reasoning.a6000_calibration.reporting import f1_acceptance_review


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/a6000_calibration"
SMOKE = OUT / "layer_a_internal/raw_smoke/examples/74/result.json"
DIAGNOSTIC = OUT / "layer_a_internal/parity_diagnostic.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def not_run(reason: str) -> dict[str, Any]:
    return {"status": "NOT_RUN", "reason": reason, "stage3c9_restart_authorized": False}


def main() -> None:
    smoke = read_json(SMOKE)
    diagnostic = read_json(DIAGNOSTIC)
    tolerance = float(read_json(OUT / "config/tolerances.json")["aggregate_D_max_abs_delta"])
    stop_reason = (
        "Prospective F1 stop: full/cached score-path parity exceeded the frozen 1e-5 "
        "token-log-probability and aggregate-D tolerances on the first A6000 smoke base."
    )

    deterministic = {
        "status": "PARTIAL_PASS",
        "scope": "risk-first base-74 smoke only; the remaining frozen cohort was not run",
        "required_repeats": 3,
        "conditions": {
            condition: rows["deterministic_replay"]
            for condition, rows in smoke["conditions"].items()
        },
        "all_executed_replays_passed": all(
            row["passed"]
            for condition in smoke["conditions"].values()
            for row in condition["deterministic_replay"]
        ),
    }
    write_json(OUT / "layer_a_internal/deterministic_replay.json", deterministic)

    full_bounded = {
        "status": "FAIL",
        "failure_code": "F1",
        "tolerance": tolerance,
        "base_problem_id": smoke["base_problem_id"],
        "prefix_length": smoke["prefix_length"],
        "conditions": {
            condition: rows["full_vs_bounded"]
            for condition, rows in smoke["conditions"].items()
        },
        "interpretation": (
            "The bounded path is deterministic but not numerically equivalent to native full-prefix "
            "BF16 recomputation at the prospectively frozen tolerance."
        ),
        "diagnostic_path": str(DIAGNOSTIC.relative_to(ROOT)),
    }
    write_json(OUT / "layer_a_internal/full_vs_memory_bounded.json", full_bounded)

    cached_full = {
        "status": "FAIL",
        "failure_code": "F1",
        "tolerance": tolerance,
        "base_problem_id": diagnostic["base_problem_id"],
        "conditions": {
            condition: {
                "one_shot_cache_versus_full": rows["one_shot_versus_full"],
                "streaming_full_chunk_versus_one_shot": rows["streaming"][str(diagnostic["context_length"])]["versus_one_shot_cache"],
                "streaming_chunk_size_one_versus_full_chunk": rows["streaming_chunk_comparison"],
            }
            for condition, rows in diagnostic["conditions"].items()
        },
        "diagnosis": (
            "The discrepancy is not specific to the new bounded implementation: the historical "
            "one-shot cache path also differs from full recomputation. Chunk-size dependence shows "
            "additional BF16 matrix-shape sensitivity. No evidence of stochastic A6000 replay was found."
        ),
        "historical_corroboration": "outputs/stage3b0/smoke/cached_full_parity_diagnostic.json",
    }
    write_json(OUT / "layer_a_internal/cached_vs_full.json", cached_full)

    self_patch = {
        "status": "PARTIAL_PASS",
        "scope": "base-74 risk-first smoke",
        "full_path": {
            condition: {
                mode: rows["self_patch_controls"][mode]
                for mode in ("K", "V", "KV", "residual")
            }
            for condition, rows in smoke["conditions"].items()
        },
        "full_path_K_V_KV_residual_all_passed": all(
            rows["self_patch_controls"][mode][direction]["passed"]
            for rows in smoke["conditions"].values()
            for mode in ("K", "V", "KV", "residual")
            for direction in ("native_to_native", "suppressed_to_suppressed")
        ),
        "event_span_status": "NOT_EVALUATED_ON_MATCHED_PATH",
        "event_span_note": (
            "The smoke's event-span comparison used a bounded self patch against a full-path recipient; "
            "it is confounded by the failed full/bounded parity test and is not evidence of self-patch failure."
        ),
    }
    write_json(OUT / "layer_a_internal/self_patch_validation.json", self_patch)

    write_json(OUT / "layer_a_internal/intervention_selectivity.json", {
        "status": "PARTIAL_PASS",
        "scope": "base-74 smoke audits only",
        "raw_evidence": str(SMOKE.relative_to(ROOT)),
        "observed": (
            "Full-path K/V/KV and residual self-patch audits reported exact selected-position replacement "
            "and zero nonselected deltas in the executed smoke. Cohort-wide and Stage-3C.9 event-span "
            "selectivity were not run after F1."
        ),
    })
    write_json(OUT / "layer_a_internal/gqa_rope_layout.json", {
        "status": "PARTIAL_PASS",
        "scope": "base-74 smoke",
        "architecture_observed": smoke["architecture"],
        "expected": {
            "language_layers": 36,
            "logical_query_heads": 32,
            "kv_heads": 8,
            "query_heads_per_kv_group": 4,
            "head_dimension": 128,
        },
        "layout_match": smoke["architecture"] == {
            "language_layers": 36,
            "logical_query_heads": 32,
            "kv_heads": 8,
            "query_heads_per_kv_group": 4,
            "head_dimension": 128,
        },
        "raw_evidence": str(SMOKE.relative_to(ROOT)),
    })

    layer_b_reason = stop_reason + " Layer B was therefore not authorized."
    for filename in ("device_replay_results.jsonl", "device_comparison.json", "anomalous_devices.json"):
        path = OUT / "layer_b_cross_device" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = not_run(layer_b_reason)
        if filename.endswith(".jsonl"):
            path.write_text(json.dumps(payload, allow_nan=False) + "\n", encoding="utf-8")
        else:
            write_json(path, payload)

    layer_c_reason = stop_reason + " New A6000 bridge scores were not collected."
    for filename in ("a6000_bridge_scores.jsonl", "continuity_statistics.json", "strong_effect_agreement.json"):
        path = OUT / "layer_c_bridge" / filename
        payload = not_run(layer_c_reason)
        if filename.endswith(".jsonl"):
            path.write_text(json.dumps(payload, allow_nan=False) + "\n", encoding="utf-8")
        else:
            write_json(path, payload)

    layer_d_reason = stop_reason + " Layer D was therefore not authorized."
    for filename in (
        "long_prefix_stress.jsonl",
        "w8_w16_validation.json",
        "event_span_rescue_validation.json",
        "neighbor_control_validation.json",
        "local_final_readout_validation.json",
        "route_dry_run.json",
    ):
        path = OUT / "layer_d_stage3c9" / filename
        payload = not_run(layer_d_reason)
        if filename.endswith(".jsonl"):
            path.write_text(json.dumps(payload, allow_nan=False) + "\n", encoding="utf-8")
        else:
            write_json(path, payload)

    acceptance = f1_acceptance_review()
    write_json(OUT / "summaries/a6000_calibration_acceptance.json", acceptance)
    write_json(OUT / "analysis/platform_readiness.json", {
        "classification": "FAIL — A6000 PLATFORM NOT READY",
        "failure_code": "F1",
        "stage3c9_restart_authorized": False,
        "device_pool_frozen": False,
        "reason": stop_reason,
        "required_next_decision": (
            "Review whether to amend the calibration to use matched cached execution paths for all "
            "causal contrasts, or adopt another prospectively validated scoring implementation."
        ),
    })
    write_json(OUT / "analysis/cross_hardware_drift.json", not_run(layer_c_reason))

    figure_dir = OUT / "analysis/figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    labels, aggregate, token = [], [], []
    for condition, paths in full_bounded["conditions"].items():
        for path_name, comparison in paths.items():
            labels.append(f"{condition}:{path_name}")
            aggregate.append(float(comparison["aggregate_D_max_abs_delta"]))
            token.append(float(comparison["token_log_probability_max_abs_delta"]))
    figure, axis = plt.subplots(figsize=(9, 4.8))
    x = range(len(labels))
    axis.bar([value - 0.18 for value in x], aggregate, width=0.36, label="|ΔD|")
    axis.bar([value + 0.18 for value in x], token, width=0.36, label="max |Δ token log p|")
    axis.axhline(tolerance, color="black", linestyle="--", linewidth=1, label="frozen tolerance")
    axis.set_yscale("log")
    axis.set_xticks(list(x), labels, rotation=30, ha="right")
    axis.set_ylabel("absolute difference (log scale)")
    axis.set_title("A6000 smoke: full versus memory-bounded scoring")
    axis.legend()
    figure.tight_layout()
    figure.savefig(figure_dir / "full_vs_memory_bounded.png", dpi=180)
    plt.close(figure)

    availability_rows = [
        (1, "A5000 vs A6000 native D scatter", "NOT RUN — Layer C blocked"),
        (2, "A5000 vs A6000 causal-gain scatter", "NOT RUN — Layer C blocked"),
        (3, "absolute cross-hardware drift distribution", "NOT RUN — Layer C blocked"),
        (4, "effect-stratum agreement table", "NOT RUN — Layer C blocked"),
        (5, "full vs memory-bounded parity", "AVAILABLE; demonstrates F1 failure"),
        (6, "cross-A6000 device comparison", "NOT RUN — Layer B blocked"),
        (7, "long-prefix VRAM vs prefix length", "NOT RUN — Layer D blocked"),
        (8, "self-patch/selectivity table", "PARTIAL smoke evidence only"),
        (9, "W8/W16 mechanical table", "NOT RUN — Layer D blocked"),
        (10, "20-point checklist", "AVAILABLE in summaries"),
    ]
    lines = ["# Calibration Figure/Table Availability", "", "| # | Required item | Status |", "|---:|---|---|"]
    lines.extend(f"| {index} | {name} | {status} |" for index, name, status in availability_rows)
    (figure_dir / "availability.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = f"""# A6000 Platform Calibration Summary

## Decision

**FAIL — A6000 PLATFORM NOT READY (F1 scoring-path parity failure).** Stage 3C.9 restart is not authorized.

This is an implementation/methods result, not a scientific finding about the model or hardware.

## What was frozen before scoring

The hardware migration amendment, 12-base historical cohort, four-device pool, software/model configuration, and `1e-5` token/aggregate parity tolerances were persisted before any A6000 calibration score. The partial A5000 Stage 3C.9 screen remains provenance-only and was not mixed into this calibration.

## Risk-first Layer A result

Base 74 was run first on A6000 GPU UUID `GPU-d2516130-3b52-5a2b-afd5-77efd3c612c1` with three deterministic repeats in original and counterfactual image conditions.

- Deterministic full-path replay: passed for native, source-suppressed, and K+V rescue scores and captured states.
- Full-path K-only, V-only, K+V, and residual self patches: passed in native→native and suppressed→suppressed controls.
- Architecture: 36 language layers, 32 logical query heads, 8 KV heads, 4 query heads per KV group, head dimension 128.
- All executed scores: finite.
- Peak allocated GPU memory: 9,150,241,792 bytes.

The mandatory parity gate failed. Across original/counterfactual conditions and native/suppressed/KV-rescue paths, full-versus-bounded differences ranged from `0.0203` to `2.9393` in aggregate D and from `0.1481` to `8.8680` in token log probability, far above `1e-5`.

## Focused diagnosis

A single predeclared follow-up compared full recomputation, the historical one-shot cache path, and streaming cache paths on the same frozen base.

- One-shot cache versus full also failed: aggregate |ΔD| was `0.0998` (O) and `0.0342` (C).
- Streaming chunk-size sensitivity was nonzero: aggregate |ΔD| was `0.1018` (O) and `0.000042` (C) between full-prefix and one-token chunks.
- This reproduces the already documented Stage 3B.0 observation that BF16 full and cached execution use different matrix shapes and are deterministic but not numerically identical.

Thus the result does not support a simple stochastic-device or token-coordinate failure. It does show that the current frozen `1e-5` full/cache equivalence criterion is not met by the existing BF16 implementation.

## Stop handling

The plan's F1 rule says to stop before Stage 3C.9 and fix scoring implementation. Therefore Layers B, C, and D were not run; their required paths contain explicit `NOT_RUN` records. No device pool was accepted, no cross-hardware scientific continuity claim was made, and Stage 3C.9 was not restarted.

## Required next decision

The next action needs review because it would amend the calibration design. The cleanest candidate is to define all Stage 3C.9 causal contrasts against matched recipient/source baselines within one fixed cached/chunked execution path, then prospectively validate deterministic replay, self-patch exactness, selectivity, and chunking sensitivity. Another option is a different scoring implementation that genuinely matches full recomputation under the frozen dtype. Neither change was made here.
"""
    summary_path = OUT / "summaries/a6000_calibration_summary.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")

    authorization = """# Stage 3C.9 Restart Authorization

## NOT AUTHORIZED

The A6000 calibration encountered the plan-defined F1 full/cached parity failure on the first risk-first Layer A smoke. The prospectively frozen `1e-5` token-log-probability and aggregate-D tolerances were exceeded by both the historical one-shot cache path and the current streaming path.

Do not restart Stage 3C.9, do not mix the partial A5000 screen with future A6000 outputs, and do not treat A6000 as the frozen primary platform yet. A reviewed calibration amendment and a new passing mechanical validation are required first.
"""
    (OUT / "summaries/stage3c9_restart_authorization.md").write_text(authorization, encoding="utf-8")


if __name__ == "__main__":
    main()
