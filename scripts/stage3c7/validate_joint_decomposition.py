#!/usr/bin/env python3
"""Validate the gated Target-A joint K/V decomposition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c7"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--expected-bases", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [read_json(path) for path in sorted(args.raw_dir.glob("shard_*/examples/*/result.json"))]
    details = []
    for row in rows:
        for condition, source in row["target_results"]["target_a"]["conditions"].items():
            mechanics = []
            for mode, arm in source["arms"].items():
                selected = [audit for audit in arm["cache_patch_audits"]["original_candidate"] if audit.get("layer_selected")]
                mechanics.append(bool(
                    arm["finite"] and arm["residual_patch_audits_valid"]
                    and arm["cache_mode"] == mode
                    and arm["cache_layers"] == [34, 35]
                    and len(selected) == 2
                    and all(a["positions_replaced"] == [arm["tpre_absolute_position"]] for a in selected)
                    and all(a["unselected_component_key_max_abs_delta"] == 0.0 and a["unselected_component_value_max_abs_delta"] == 0.0 for a in selected)
                ))
            details.append({
                "base_problem_id": row["base_problem_id"], "condition": condition,
                "only_target_a": row["active_targets"] == ["target_a"],
                "KV_exact_prior_J4": source["KV_exact_prior_J4"],
                "all_modes_mechanically_valid": all(mechanics),
            })
    checks = {
        "expected_base_count": len(rows) == args.expected_bases,
        "target_a_only": bool(details) and all(r["only_target_a"] for r in details),
        "KV_exact_prior_J4": bool(details) and all(r["KV_exact_prior_J4"] for r in details),
        "K_V_KV_isolated": bool(details) and all(r["all_modes_mechanically_valid"] for r in details),
    }
    output = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "details": details}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))
    if output["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
