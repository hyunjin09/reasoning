#!/usr/bin/env python3
"""Aggregate three single-example Stage 1A.2 faithfulness shards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for shard_dir in sorted((root / "shards").glob("example_*")):
        example_dirs = [path for path in (shard_dir / "examples").iterdir() if path.is_dir()]
        if len(example_dirs) != 1:
            failures.append(f"{shard_dir.name}: expected one example directory")
            continue
        example_dir = example_dirs[0]
        required = ("baseline_generation.json", "generation.json", "faithfulness.json", "result.json")
        missing = [name for name in required if not (example_dir / name).is_file()]
        if missing:
            failures.append(f"{example_dir.name}: missing {missing}")
            continue
        baseline = read_json(example_dir / "baseline_generation.json")
        instrumented = read_json(example_dir / "generation.json")
        faithfulness = read_json(example_dir / "faithfulness.json")
        result = read_json(example_dir / "result.json")
        ids_match = baseline["generated_token_ids"] == instrumented["generated_token_ids"]
        passed = bool(faithfulness["passed"]) and ids_match and bool(result["validation"]["passed"])
        if not passed:
            failures.append(f"{example_dir.name}: paired faithfulness failed")
        rows.append(
            {
                "example_id": str(example_dir.name),
                "generated_token_count": int(result["generated_token_count"]),
                "status": result["status"],
                "generated_token_ids_match": ids_match,
                "final_answers_match": bool(faithfulness["final_answers_match"]),
                "instrumentation_validation_passed": bool(result["validation"]["passed"]),
                "passed": passed,
                "artifact_dir": str(example_dir.resolve()),
            }
        )
    report = {
        "selected_protocol": "qwen_official_style_thinking",
        "max_new_tokens": 40_960,
        "seed": 1_234,
        "gpu_scope": "NVIDIA RTX A5000",
        "example_count": len(rows),
        "exact_match_count": sum(bool(row["generated_token_ids_match"]) for row in rows),
        "passed": len(rows) == 3 and not failures and all(bool(row["passed"]) for row in rows),
        "examples": rows,
        "failures": failures,
    }
    write_json(args.output.resolve(), report)
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
