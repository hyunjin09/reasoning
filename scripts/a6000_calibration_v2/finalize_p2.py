#!/usr/bin/env python3
"""Freeze the memory-selected canonical P2 path without reading causal effects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.a6000_calibration_v2.protocol import select_streaming_chunk


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/a6000_calibration_v2"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main() -> None:
    chunking_path = OUT / "config/canonical_chunking.json"
    chunking = read_json(chunking_path)
    stress_manifest = read_jsonl(OUT / "phase1_path_feasibility/stress_manifest.jsonl")
    expected = {str(row["base_problem_id"]) for row in stress_manifest}
    paths = sorted((OUT / "phase1_path_feasibility").glob("p2r_chunk*_base*.json"))
    rows = [read_json(path) for path in paths]
    decision = select_streaming_chunk(
        rows,
        candidates_descending=chunking["candidate_chunk_sizes_descending"],
        expected_bases=expected,
        memory_fraction_max=0.90,
    )
    if decision["status"] != "SELECTED" or int(decision["selected_chunk_size"]) != 2048:
        raise RuntimeError(f"Repaired P2 path did not select the expected memory-safe chunk: {decision}")
    selected_rows = sorted(
        (row for row in rows if int(row["chunk_size"]) == int(decision["selected_chunk_size"])),
        key=lambda row: int(row["stress_order"]),
    )
    if len(selected_rows) != 6 or any(not row["environment"]["release_allocator_cache_between_chunks"] for row in selected_rows):
        raise RuntimeError("Selected P2 evidence does not contain six allocator-release stress cases")
    manifest_path = OUT / "phase1_path_feasibility/fixed_streaming_memory_stress.jsonl"
    manifest_path.write_text(
        "".join(json.dumps(row, allow_nan=False) + "\n" for row in selected_rows),
        encoding="utf-8",
    )
    write_json(OUT / "phase1_path_feasibility/p2_path_decision.json", {
        **decision,
        "selected_path": "P2_fixed_streaming_cached",
        "release_allocator_cache_between_chunks": True,
        "path_selection_basis": "memory feasibility only",
        "scientific_effects_inspected_for_selection": False,
        "largest_rejected_repaired_chunk": 4096,
        "largest_rejected_repaired_chunk_reason": "OOM on frozen longest stress case base 351",
        "selected_stress_manifest": str(manifest_path.relative_to(ROOT)),
        "stage3c9_restart_authorized": False,
    })
    write_json(chunking_path, {
        **chunking,
        "status": "SELECTED",
        "selected_chunk_size": 2048,
        "release_allocator_cache_between_chunks": True,
        "selected_after_streaming_allocator_repair": True,
        "selection_evidence": str(manifest_path.relative_to(ROOT)),
        "largest_rejected_chunk_size": 4096,
        "stage3c9_restart_authorized": False,
    })
    canonical = read_json(OUT / "config/canonical_path_decision.json")
    write_json(OUT / "config/canonical_path_decision.json", {
        **canonical,
        "selected_branch": "P2_fixed_streaming_cached",
        "canonical_streaming_path_frozen": True,
        "canonical_chunk_size": 2048,
        "release_allocator_cache_between_chunks": True,
        "memory_stress_case_count": 6,
        "maximum_peak_reserved_vram_fraction": max(
            float(row["peak_reserved_vram_fraction"]) for row in selected_rows
        ),
        "selection_uses_scientific_effects": False,
        "stage3c9_restart_authorized": False,
    })


if __name__ == "__main__":
    main()
