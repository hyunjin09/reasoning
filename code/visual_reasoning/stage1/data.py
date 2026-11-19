"""Deterministic Stage 1 pilot and discovery selection."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


PILOT_COMPLETED_IDS = ("3", "4", "29", "69")
PILOT_TRUNCATED_IDS = (
    "8",
    "9",
    "13",
    "14",
    "18",
    "19",
    "23",
    "24",
    "28",
    "33",
    "34",
    "38",
    "39",
    "43",
    "44",
    "48",
)
VISUAL_VARIANTS = ("Vision Intensive", "Vision Dominant")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_pilot_manifest(rows: list[dict[str, Any]], stage0_dir: Path) -> list[dict[str, Any]]:
    by_id = {str(row["sample_index"]): row for row in rows}
    selected_ids = [*PILOT_TRUNCATED_IDS, *PILOT_COMPLETED_IDS]
    manifest: list[dict[str, Any]] = []
    for sample_id in selected_ids:
        if sample_id not in by_id:
            raise KeyError(f"MathVerse sample {sample_id} is absent")
        result_path = stage0_dir / "examples" / sample_id / "result.json"
        if not result_path.is_file():
            raise FileNotFoundError(result_path)
        stage0_result = read_json(result_path)
        expected = "correct" if sample_id in PILOT_COMPLETED_IDS else "truncated"
        if str(stage0_result["status"]) != expected:
            raise ValueError(f"Stage 0 sample {sample_id} is {stage0_result['status']}, expected {expected}")
        row = by_id[sample_id]
        manifest.append(
            {
                "order": len(manifest),
                "example_id": sample_id,
                "problem_index": str(row["problem_index"]),
                "variant": str(row["problem_version"]),
                "subject": str(row.get("metadata", {}).get("subject", "unknown")),
                "stage0_status": expected,
                "stage0_generated_tokens": int(stage0_result["generated_token_count"]),
                "selection_reason": "completed control" if expected == "correct" else "previously truncated",
            }
        )
    return manifest


def select_8192_manifest(
    pilot_4096_results: Iterable[dict[str, Any]],
    rows: list[dict[str, Any]],
    stage0_dir: Path,
    minimum_examples: int = 10,
) -> list[dict[str, Any]]:
    truncated = [str(result["example_id"]) for result in pilot_4096_results if result["status"] == "truncated"]
    if not truncated:
        return []
    selected = list(truncated)
    for sample_id in PILOT_TRUNCATED_IDS:
        if len(selected) >= minimum_examples:
            break
        if sample_id not in selected:
            selected.append(sample_id)
    if len(selected) < minimum_examples:
        stage0_truncated = []
        for result_path in sorted(
            (stage0_dir / "examples").glob("*/result.json"),
            key=lambda path: int(path.parent.name),
        ):
            result = read_json(result_path)
            if result["status"] == "truncated" and str(result["example_id"]) not in selected:
                stage0_truncated.append(str(result["example_id"]))
        selected.extend(stage0_truncated[: max(0, minimum_examples - len(selected))])
    by_id = {str(row["sample_index"]): row for row in rows}
    return [
        {
            "order": index,
            "example_id": sample_id,
            "problem_index": str(by_id[sample_id]["problem_index"]),
            "variant": str(by_id[sample_id]["problem_version"]),
            "subject": str(by_id[sample_id].get("metadata", {}).get("subject", "unknown")),
            "selection_reason": "truncated at 4096" if sample_id in truncated else "added Stage 0-truncated sample",
        }
        for index, sample_id in enumerate(selected)
    ]


def select_discovery_rows(rows: list[dict[str, Any]], max_attempts: int = 200) -> list[dict[str, Any]]:
    """Select paired visually intensive rows without using model outcomes or attention."""

    if max_attempts <= 0 or max_attempts % 2:
        raise ValueError("max_attempts must be a positive even number for paired selection")
    by_problem: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        variant = str(row["problem_version"])
        if variant in VISUAL_VARIANTS:
            by_problem[str(row["problem_index"])][variant] = row
    groups: list[tuple[str, str, int, dict[str, dict[str, Any]]]] = []
    for problem_id, variants in by_problem.items():
        if not all(variant in variants for variant in VISUAL_VARIANTS):
            continue
        subject = str(variants[VISUAL_VARIANTS[0]].get("metadata", {}).get("subject", "unknown"))
        question_length = max(len(str(row.get("question", "")).split()) for row in variants.values())
        groups.append((subject, problem_id, question_length, variants))
    buckets: dict[str, deque[tuple[str, str, int, dict[str, dict[str, Any]]]]] = {}
    for subject in sorted({group[0] for group in groups}):
        subject_groups = [group for group in groups if group[0] == subject]
        subject_groups.sort(key=lambda group: (-group[2], int(group[1])))
        buckets[subject] = deque(subject_groups)
    selected_groups: list[tuple[str, str, int, dict[str, dict[str, Any]]]] = []
    target_groups = max_attempts // 2
    while len(selected_groups) < target_groups and any(buckets.values()):
        for subject in sorted(buckets):
            if buckets[subject] and len(selected_groups) < target_groups:
                selected_groups.append(buckets[subject].popleft())
    selected: list[dict[str, Any]] = []
    for _subject, _problem_id, _question_length, variants in selected_groups:
        selected.extend(variants[variant] for variant in VISUAL_VARIANTS)
    if len(selected) != max_attempts:
        raise ValueError(f"Could select only {len(selected)} of {max_attempts} requested rows")
    return selected

