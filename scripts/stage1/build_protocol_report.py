#!/usr/bin/env python3
"""Build the gated Stage 1A generation-protocol report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_text


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def metric_section(name: str, metrics: dict[str, Any] | None) -> str:
    if metrics is None:
        return f"## {name}\n\nNot run."
    return f"""## {name}

- Examples: {metrics['total']}
- Completed: {metrics['completed']} ({metrics['completion_rate']:.1%})
- Truncated: {metrics['truncated']} ({metrics['truncation_rate']:.1%})
- Correct / wrong / invalid: {metrics['correct']} / {metrics['wrong']} / {metrics['invalid']}
- Correctness among completed: {metrics['correctness_among_completed']:.1%}
- Generation length median / p90 / max: {metrics['median_generation_length']:.1f} / {metrics['p90_generation_length']:.1f} / {metrics['maximum_generation_length']}
- Latency median / p90: {metrics['median_latency_seconds']:.1f}s / {metrics['p90_latency_seconds']:.1f}s
- Peak GPU allocation: {metrics['peak_gpu_allocated_bytes'] / (1024 ** 3):.2f} GiB
- Largest artifact bundle: {metrics['maximum_artifact_bytes'] / (1024 ** 2):.2f} MiB
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-4096-dir", type=Path, required=True)
    parser.add_argument("--pilot-8192-dir", type=Path)
    parser.add_argument("--faithfulness-dir", type=Path)
    parser.add_argument("--validation-4096", type=Path)
    parser.add_argument("--validation-8192", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    metrics_4096 = read(args.pilot_4096_dir / "run_summary.json")
    metrics_8192 = read(args.pilot_8192_dir / "run_summary.json") if args.pilot_8192_dir else None
    faithfulness = read(args.faithfulness_dir / "run_summary.json") if args.faithfulness_dir else None
    validation_4096 = read(args.validation_4096) if args.validation_4096 else None
    validation_8192 = read(args.validation_8192) if args.validation_8192 else None
    if metrics_4096["truncation_rate"] <= 0.10:
        selected_cap = 4096
        decision = "selected_4096"
        stop_reason = None
    elif metrics_8192 is None:
        selected_cap = None
        decision = "requires_8192"
        stop_reason = None
    elif metrics_8192["truncation_rate"] <= 0.10:
        selected_cap = 8192
        decision = "selected_8192"
        stop_reason = None
    else:
        selected_cap = None
        decision = "stop_before_stage1b"
        stop_reason = "The 8,192-token pilot truncation rate remains above 10%."
    faithfulness_passed = bool(
        faithfulness
        and selected_cap is not None
        and int(faithfulness["max_new_tokens"]) == selected_cap
        and int(faithfulness["total"]) >= 3
        and bool(faithfulness["faithfulness_passed"])
    )
    stage1a_pass = selected_cap is not None and faithfulness_passed
    report = {
        "pilot_4096": metrics_4096,
        "pilot_8192": metrics_8192,
        "selected_max_new_tokens": selected_cap,
        "decision": decision,
        "stop_reason": stop_reason,
        "faithfulness": faithfulness,
        "faithfulness_passed": faithfulness_passed,
        "independent_validation_4096_passed": bool(validation_4096 and validation_4096["passed"]),
        "independent_validation_8192_passed": bool(validation_8192 and validation_8192["passed"]),
        "stage1a_pass": stage1a_pass,
        "stage1b_authorized": stage1a_pass,
        "stage2_started": False,
    }
    output_dir = args.output_dir.resolve()
    write_json(output_dir / "protocol_report.json", report)
    if faithfulness:
        write_json(output_dir / "faithfulness_check.json", faithfulness)
    selected_text = str(selected_cap) if selected_cap is not None else "none"
    if decision == "stop_before_stage1b":
        revision = """## Protocol-revision options (not executed)

Recommended next action, subject to explicit approval, is a separate prospective 16,384-token pilot on the five 8,192-truncated examples plus additional previously truncated examples to reach about ten when feasible. It should retain the same deterministic decoding and instrumentation, set a new truncation gate before inference, and repeat 3/3 faithfulness only if a cap is selected. The present pilot suggests an A6000 is likely practical, but that extrapolation must be checked prospectively: 8,192 used 14.26 GiB peak allocation, 271.4 seconds median latency, and 36.76 MiB maximum artifact storage.

Other options requiring explicit protocol/scope approval are to change the discovery benchmark slice to one with reliably complete trajectories under 8,192, or to revise the model/decoding protocol. Analyzing only the five completed 8,192 traces would not satisfy the discovery-cohort design and is not recommended.

No option above was executed in this task.
"""
    else:
        revision = ""
    faithfulness_text = "passed" if faithfulness_passed else ("failed" if faithfulness else "not run (no cap selected)")
    markdown = f"""# Stage 1A Generation Protocol Report

{metric_section('4,096-token pilot', metrics_4096)}

{metric_section('8,192-token pilot', metrics_8192)}

## Protocol decision

- Decision: `{decision}`
- Selected final `max_new_tokens`: `{selected_text}`
- Selected-cap truncation requirement: at most 10%
- Faithfulness: `{faithfulness_text}`
- Stage 1A pass: `{str(stage1a_pass).lower()}`
- Stage 1B authorized: `{str(stage1a_pass).lower()}`
- Stage 2 started: `false`
- Independent 4,096 artifact validation: `{str(bool(validation_4096 and validation_4096['passed'])).lower()}`
- Independent 8,192 artifact validation: `{str(bool(validation_8192 and validation_8192['passed'])).lower()}`

{f'- Stop reason: {stop_reason}' if stop_reason else ''}

## Implications

- Latency and storage statistics above are measured from the fixed pilot artifacts.
- Instrumentation, prompt, preprocessing, evaluator, visual mapping, and greedy decoding remain unchanged from Stage 0.
- Attention remains descriptive evidence and is not interpreted as causal visual usage.

{revision}
"""
    write_text(output_dir / "protocol_report.md", markdown)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
