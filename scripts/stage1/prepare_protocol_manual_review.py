#!/usr/bin/env python3
"""Prepare compact excerpts for manual review of the longest protocol traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_text


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def excerpt(text: str, start: int, width: int = 1_200) -> str:
    return text[start : start + width].replace("\x00", "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition-root", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()
    root = args.condition_root.resolve()
    summary = read_json(root / "run_summary.json")
    outcomes = read_jsonl(root / "raw_outcome_manifest.jsonl")
    selected = sorted(outcomes, key=lambda row: (-int(row["generated_token_count"]), int(row["example_id"])))[: args.count]
    records = []
    markdown_parts = [
        f"# Manual Review Packet — {summary['condition']}",
        "",
        "Review scope: longest trajectories by generated-token count. Excerpts are diagnostic aids; assessments must be added after human/agent inspection.",
    ]
    for row in selected:
        example_dir = Path(row["artifact_dir"])
        generation = read_json(example_dir / "generation.json")
        repetition = read_json(example_dir / "repetition_diagnostics.json")
        text = str(generation["full_generated_response"])
        center_start = max(0, len(text) // 2 - 600)
        end_start = max(0, len(text) - 1_200)
        record = {
            "example_id": str(row["example_id"]),
            "generated_token_count": int(row["generated_token_count"]),
            "status": row["status"],
            "termination_reason": row["termination_reason"],
            "repetition": repetition,
            "excerpts": {
                "start": excerpt(text, 0),
                "middle": excerpt(text, center_start),
                "end": excerpt(text, end_start),
            },
            "manual_assessment": None,
        }
        records.append(record)
        markdown_parts.extend(
            [
                "",
                f"## Example {record['example_id']}",
                "",
                f"- Tokens: {record['generated_token_count']}",
                f"- Status / termination: {record['status']} / {record['termination_reason']}",
                f"- Automated pathology flag: {repetition['any_pathology_flag']}",
                f"- Repeated n-grams (3/4/8): {repetition['repeated_ngram_fraction']['n3']:.3f} / {repetition['repeated_ngram_fraction']['n4']:.3f} / {repetition['repeated_ngram_fraction']['n8']:.3f}",
                f"- Repeated-sentence fraction: {repetition['repeated_sentence_fraction']:.3f}",
                f"- Self-correction cues: {sum(repetition['self_correction_cue_counts'].values())}",
                "- Manual assessment: PENDING",
                "",
                "### Start excerpt",
                "",
                "```text",
                record["excerpts"]["start"],
                "```",
                "",
                "### Middle excerpt",
                "",
                "```text",
                record["excerpts"]["middle"],
                "```",
                "",
                "### End excerpt",
                "",
                "```text",
                record["excerpts"]["end"],
                "```",
            ]
        )
    write_json(args.output_prefix.with_suffix(".json"), {"condition": summary["condition"], "records": records})
    write_text(args.output_prefix.with_suffix(".md"), "\n".join(markdown_parts) + "\n")
    print(f"Prepared {len(records)} longest-trace review records for {summary['condition']}")


if __name__ == "__main__":
    main()
