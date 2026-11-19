#!/usr/bin/env python3
"""Run Stage 3B.9 Phase-A scoring through the frozen Stage 3B.8 v3 endpoint."""

from __future__ import annotations

import json
from pathlib import Path

import scripts.stage3b8.run_value_scoring as v3_runner


ROOT = Path(__file__).resolve().parents[2]


def paired_metadata(item: dict, _cohort_role: str) -> dict:
    path = ROOT / item["edit_metadata"]
    metadata = json.loads(path.read_text(encoding="utf-8"))
    if metadata["phase"] != "phase_a" or metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Invalid Phase-A edit metadata for base {item['base_problem_id']}")
    if list(metadata["paths"]) != ["O", "O_sham", "C", "C_sham"]:
        raise RuntimeError(f"Unexpected Phase-A condition family for base {item['base_problem_id']}")
    metadata["_metadata_path"] = str(path.relative_to(ROOT))
    return metadata


def main() -> None:
    # Reuse, rather than approximate, the already reconstructed and validated v3
    # selected-head pre-W_O Value endpoint.
    v3_runner.OUT = ROOT / "outputs/stage3b9"
    v3_runner.paired_metadata = paired_metadata
    v3_runner.main()


if __name__ == "__main__":
    main()
