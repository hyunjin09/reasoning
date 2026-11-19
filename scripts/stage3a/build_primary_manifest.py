#!/usr/bin/env python3
"""Build a validated Stage 3A scoring manifest from manually accepted edits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def generation_path(example_id: str) -> Path:
    stage1 = ROOT / f"outputs/stage1/discovery/examples/{example_id}/generation.json"
    if stage1.is_file():
        return stage1
    matches = list((OUT / "cohort_expansion").glob(f"**/examples/{example_id}/generation.json"))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one generation artifact for example {example_id}, found {matches}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum", type=int, default=30)
    parser.add_argument("--base", action="append", default=[])
    args = parser.parse_args()
    screen = read_jsonl(OUT / "cohort/candidate_screening.jsonl")
    order = {str(row["base_problem_id"]): index for index, row in enumerate(screen)}
    timing_rows = read_jsonl(ROOT / "outputs/stage2c/analysis/timing_categories.jsonl")
    timing = {(str(row["example_id"]), int(row["events"]["e0"][0])): row["timing_category"] for row in timing_rows}
    requested = {str(value) for value in args.base}
    items = []
    for path in (OUT / "counterfactuals").glob("*/edit_metadata.json"):
        item = json.loads(path.read_text(encoding="utf-8"))
        base = str(item["base_problem_id"])
        if requested and base not in requested:
            continue
        if item["manual_validation"]["status"] != "pass" or item.get("event") is None:
            continue
        if item.get("prefix_token_ids") is None:
            continue
        gen_path = generation_path(str(item["example_id"]))
        generation = json.loads(gen_path.read_text(encoding="utf-8"))
        if generation["status"] != "correct" or not generation["complete"]:
            raise RuntimeError(f"Primary item is not completed-correct: {base}")
        full_ids = [int(value) for value in generation["generated_token_ids"]]
        e0 = int(item["event"]["e0_start_token"])
        prefix = [int(value) for value in item["prefix_token_ids"]]
        if len(prefix) != e0 or prefix != full_ids[:e0]:
            raise RuntimeError(f"Prefix is not exact y_<E0 for base {base}")
        for condition_path in item["conditions"].values():
            if not (ROOT / condition_path).is_file():
                raise FileNotFoundError(condition_path)
        item["full_generated_token_ids"] = full_ids
        item["generation_source"] = str(gen_path.relative_to(ROOT))
        item["stage2c_attention_category"] = timing.get((str(item["example_id"]), e0))
        item["primary_independent_unit"] = "base_problem_id"
        items.append(item)
    if requested and requested != {str(item["base_problem_id"]) for item in items}:
        missing = sorted(requested - {str(item["base_problem_id"]) for item in items}, key=int)
        raise RuntimeError(f"Requested bases were not eligible: {missing}")
    items.sort(key=lambda item: (order.get(str(item["base_problem_id"]), 10**9), int(item["base_problem_id"])))
    if len(items) < args.minimum:
        raise RuntimeError(f"Only {len(items)} eligible unique bases; minimum is {args.minimum}")
    if len({str(item["base_problem_id"]) for item in items}) != len(items):
        raise RuntimeError("Primary manifest contains duplicate base_problem_id")
    write_jsonl(args.output, items)
    print(json.dumps({"written": len(items), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
