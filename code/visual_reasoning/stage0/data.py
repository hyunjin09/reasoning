"""MathVerse loading, path resolution, and deterministic Stage 0 selection."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


VISUAL_VARIANTS = ("Vision Intensive", "Vision Dominant")


def load_mathverse_rows(dataset_root: Path) -> list[dict[str, Any]]:
    source = dataset_root / "testmini.json"
    if not source.is_file():
        raise FileNotFoundError(f"MathVerse metadata not found: {source}")
    rows = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"Expected a non-empty JSON array in {source}")
    return rows


def image_path_candidates(dataset_root: Path, image_reference: str) -> list[Path]:
    reference = Path(image_reference)
    if reference.is_absolute():
        return [reference]
    return [dataset_root / reference, dataset_root / "images" / reference]


def resolve_image_path(dataset_root: Path, image_reference: str) -> Path:
    candidates = image_path_candidates(dataset_root, image_reference)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    rendered = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"MathVerse image not found; checked: {rendered}")


def _problem_sort_key(problem_index: str) -> tuple[int, str]:
    try:
        return int(problem_index), problem_index
    except ValueError:
        return 10**12, problem_index


def select_stage0_subset(rows: list[dict[str, Any]], count: int, mode: str) -> list[dict[str, Any]]:
    """Select deterministic paired visually demanding examples.

    Problems are ordered by numeric ``problem_index``. Within each problem,
    Vision Intensive precedes Vision Dominant. This gives the full run paired
    examples while allowing a 2–5 row smoke prefix.
    """

    if mode not in {"smoke", "full"}:
        raise ValueError(f"Unsupported Stage 0 mode: {mode}")
    if count <= 0:
        raise ValueError("count must be positive")
    if mode == "smoke" and not 2 <= count <= 5:
        raise ValueError("smoke count must be between 2 and 5")
    if mode == "full" and not 30 <= count <= 50:
        raise ValueError("full count must be between 30 and 50")

    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        variant = str(row.get("problem_version", ""))
        if variant in VISUAL_VARIANTS:
            grouped[str(row.get("problem_index", ""))][variant] = row

    ordered: list[dict[str, Any]] = []
    for problem_index in sorted(grouped, key=_problem_sort_key):
        variants = grouped[problem_index]
        if not all(variant in variants for variant in VISUAL_VARIANTS):
            continue
        ordered.extend(variants[variant] for variant in VISUAL_VARIANTS)
        if len(ordered) >= count:
            break

    if len(ordered) < count:
        raise ValueError(f"Only {len(ordered)} paired visually demanding examples available; requested {count}")
    return ordered[:count]


def dataset_inventory(rows: list[dict[str, Any]], selected: list[dict[str, Any]]) -> dict[str, Any]:
    variant_counts = Counter(str(row.get("problem_version", "unknown")) for row in rows)
    subject_counts = Counter(str((row.get("metadata") or {}).get("subject", "unknown")) for row in selected)
    problem_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        problem_groups[str(row.get("problem_index", ""))].append(row)

    complete_groups = 0
    for group in problem_groups.values():
        present = {str(row.get("problem_version", "")) for row in group}
        if set(variant_counts).issubset(present):
            complete_groups += 1

    selected_pairing: dict[str, list[str]] = defaultdict(list)
    for row in selected:
        selected_pairing[str(row["problem_index"])].append(str(row["problem_version"]))

    return {
        "total_rows": len(rows),
        "unique_problem_count": len(problem_groups),
        "variant_counts": dict(sorted(variant_counts.items())),
        "pairing_key": "problem_index",
        "complete_variant_group_count": complete_groups,
        "selected_count": len(selected),
        "selected_sample_indices": [str(row["sample_index"]) for row in selected],
        "selected_problem_count": len(selected_pairing),
        "selected_problem_variants": dict(selected_pairing),
        "selected_subject_counts": dict(sorted(subject_counts.items())),
    }

