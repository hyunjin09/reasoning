#!/usr/bin/env python3
"""Aggregate the gated fresh prompt type-group K/V decomposition."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from analyze_phase_c import aggregate_patch
from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    gate = read_json(OUT / "config/phase_c_kv_gate.json")
    rows = []
    if gate["run"]:
        raw = [read_json(path) for path in sorted(args.raw_root.glob("**/examples/*/result.json"))]
        expected = sum(1 for line in (OUT / "cohort/fresh_atlas_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())
        if len(raw) != expected:
            raise RuntimeError(f"Gated Phase-C result count mismatch: {len(raw)}/{expected}")
        for result in raw:
            for token_class, class_row in result["class_results"].items():
                for mode, patches in class_row["modes"].items():
                    gain, reference, ratio, details = aggregate_patch(patches)
                    rows.append({
                        "base_problem_id": str(result["base_problem_id"]),
                        "cohort_role": "fresh",
                        "token_class": token_class,
                        "positions": class_row["positions"],
                        "mode": mode,
                        "gain": gain,
                        "reference_gap": reference,
                        "CRR": ratio if math.isfinite(ratio) else None,
                        "bidirectional_metrics": details,
                        "gate_frozen_before_scores": True,
                    })
    rows.sort(key=lambda row: (int(row["base_problem_id"]), row["token_class"], row["mode"]))
    write_jsonl(OUT / "phase_c_prompt/gated_type_kv_decomposition.jsonl", rows)
    print(json.dumps({"gate_run": bool(gate["run"]), "rows": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
