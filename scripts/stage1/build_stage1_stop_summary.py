#!/usr/bin/env python3
"""Build the Stage 1 stop-boundary manifests and acceptance reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect(run_dir: Path, pilot: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    manifest = {
        str(row["example_id"]): row
        for row in (
            json.loads(line)
            for line in (run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    for result_path in sorted((run_dir / "examples").glob("*/result.json"), key=lambda path: int(path.parent.name)):
        result = read(result_path)
        generation = read(result_path.parent / "generation.json")
        example_id = str(result["example_id"])
        rows.append(
            {
                "pilot": pilot,
                "example_id": example_id,
                "problem_index": str(result["problem_index"]),
                "mathverse_variant": result["mathverse_variant"],
                "subject": result["subject"],
                "selection_reason": manifest[example_id]["selection_reason"],
                "status": result["status"],
                "complete": bool(result["complete"]),
                "correct": bool(result["correct"]),
                "generated_token_count": int(result["generated_token_count"]),
                "extracted_final_answer": generation["extracted_final_answer"],
                "latency_seconds": float(result["runtime"]["elapsed_seconds"]),
                "peak_gpu_allocated_bytes": int(result["runtime"]["peak_gpu_allocated_bytes"]),
                "artifact_bytes": int(result["output_bytes"]),
                "artifact_dir": str(result_path.parent.resolve()),
                "instrumentation_valid": bool(result["validation"]["passed"]),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-4096-dir", type=Path, required=True)
    parser.add_argument("--pilot-8192-dir", type=Path, required=True)
    parser.add_argument("--protocol-report", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    protocol = read(args.protocol_report)
    if protocol["decision"] != "stop_before_stage1b":
        raise RuntimeError("Stop summary is valid only after the 8,192 stop gate is reached")
    rows_4096 = collect(args.pilot_4096_dir.resolve(), "4096")
    rows_8192 = collect(args.pilot_8192_dir.resolve(), "8192")
    output_root = args.output_root.resolve()
    write_jsonl(output_root / "protocol_pilot" / "raw_outcome_manifest.jsonl", rows_4096 + rows_8192)

    criteria = [
        {"id": 1, "criterion": "A final generation cap is prospectively selected.", "status": "FAIL", "evidence": "Neither 4096 nor 8192 met the truncation gate."},
        {"id": 2, "criterion": "Pilot truncation rate under the selected cap is <=10%.", "status": "FAIL", "evidence": "4096 and 8192 each had 50% truncation."},
        {"id": 3, "criterion": "Selected-cap instrumented/uninstrumented generation matches 3/3.", "status": "FAIL", "evidence": "Not run because no cap was selected; the stop gate precedes faithfulness."},
        {"id": 4, "criterion": "At least 80 completed-correct eligible discovery trajectories are available.", "status": "FAIL", "evidence": "Stage 1B was not authorized."},
        {"id": 5, "criterion": "Wrong, truncated, and invalid outcomes are preserved separately.", "status": "PASS", "evidence": "All 30 pilot-run artifacts and aggregate raw-outcome rows are preserved."},
        {"id": 6, "criterion": "Token and span timelines are reproducible.", "status": "PASS", "evidence": "All pilot bundles passed independent token/span/array validation; derived-span rebuild is recorded for the 4096 run."},
        {"id": 7, "criterion": "Visual/prompt/reasoning mass and source-count-normalized density are available.", "status": "PASS", "evidence": "Available and independently shape/finite-checked for all pilot bundles."},
        {"id": 8, "criterion": "Visual-focus distributions and uncertainty signals are available.", "status": "PASS", "evidence": "Available and independently shape/finite-checked for all pilot bundles."},
        {"id": 9, "criterion": "Dataset-level temporal statistics are computed.", "status": "FAIL", "evidence": "Stage 1B was not authorized, so discovery statistics were not computed."},
        {"id": 10, "criterion": "At least 10 representative trajectories are manually inspected.", "status": "FAIL", "evidence": "Stage 1B was not authorized; Stage 0 inspections do not satisfy this Stage 1 criterion."},
        {"id": 11, "criterion": "MathVerse paired variants are reliably aligned for the next stage.", "status": "FAIL", "evidence": "Stage 1B paired-variant preparation was not performed."},
        {"id": 12, "criterion": "No attention-only result is presented as causal visual usage.", "status": "PASS", "evidence": "No causal interpretation was made."},
        {"id": 13, "criterion": "No Stage 2 causal experiment has started.", "status": "PASS", "evidence": "Stage 2 was not started."},
    ]
    write_json(
        output_root / "summaries" / "stage1_acceptance.json",
        {
            "overall": "FAIL",
            "stop_boundary": "Stage 1A after the 8192 protocol pilot",
            "stage1b_started": False,
            "stage2_started": False,
            "criteria": criteria,
        },
    )
    table = "\n".join(
        f"| {item['id']} | {item['status']} | {item['criterion']} | {item['evidence']} |" for item in criteria
    )
    summary = f"""# Stage 1 Summary — Stopped at the Stage 1A Gate

## Outcome

Stage 1 did not pass. The prospective 4,096-token pilot truncated 10/20 traces (50%). The conditional 8,192-token pilot then truncated 5/10 traces (50%), exceeding the allowed 10%. Per the predefined stop condition, no generation cap was locked, the new-cap faithfulness check was not run, and Stage 1B was not started.

The independently validated 8,192 outcomes were 3 correct, 2 wrong, 5 truncated, and 0 invalid. Completed-trace correctness was 60%. Median/p90/max generation length was 8,150.5/8,192/8,192 tokens. Median/p90 latency was 271.4/273.8 seconds, peak GPU allocation was 14.26 GiB, and the largest bundle was 36.76 MiB.

All raw pilot outcomes are preserved in `outputs/stage1/protocol_pilot/raw_outcome_manifest.jsonl` and their per-example artifact directories. A whitespace-only span-boundary defect found by independent validation in the 4,096 artifacts was repaired by regenerating only derived spans, span summaries, and candidate-peak metadata. Raw token IDs, generation text, logits-derived uncertainty, attention arrays, statuses, and Stage 0 artifacts were unchanged.

## Discovery work not performed

Because Stage 1B was prohibited, there is no discovery cohort, dataset-level dynamics analysis, representative qualitative set, paired-variant report, or ranked candidate-hypothesis report. Creating any of these from the small cap-pilot sample would weaken the predeclared design.

## Scientific boundary

The pilot artifacts contain descriptive attention signals, but this report makes no claim about causal visual usage. Attention is descriptive evidence, not causal evidence. Stage 2 was not started.

## Acceptance criteria

| # | Status | Criterion | Evidence |
|---:|:---:|---|---|
{table}
"""
    write_text(output_root / "summaries" / "stage1_summary.md", summary)
    hypotheses = """# Stage 1 Candidate Hypotheses

No hypotheses are ranked from Stage 1 dynamics because Stage 1B was not authorized. The generation-protocol pilots were designed to select a complete-trajectory horizon, not to support dataset-level temporal claims. Treating their small, truncation-enriched cohort as the discovery set would be post hoc and misleading.

The only supported protocol observation is that 8,192 generated tokens remained insufficient for 5/10 rerun traces. This is not an attention-based or causal finding. See `outputs/stage1/protocol_pilot/protocol_report.md` for prospective protocol-revision options. No Stage 2 experiment was started.
"""
    write_text(output_root / "summaries" / "candidate_hypotheses.md", hypotheses)
    print(json.dumps({"overall": "FAIL", "criteria": criteria}, indent=2))


if __name__ == "__main__":
    main()
