#!/usr/bin/env python3
"""Materialize explicit Stage 3C.9 gated/omitted analyses without running them."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    gate = read_json(OUT / "phase_d_routes/gate.json")
    if not gate["run_phase_d"]:
        for name in ("direct_route", "prior_checkpoint_route", "short_history_route", "joint_route"):
            write_jsonl(OUT / f"phase_d_routes/{name}.jsonl", [])
        payload = {
            "status": "NOT_RUN_FEASIBILITY_GATE",
            "gate": gate,
            "interpretation": "Fewer than 16 bases had two confirmed separated checkpoints; no route absence is inferred.",
            "causal_route_intervention_started": False,
        }
        write_json(OUT / "phase_d_routes/route_classification.json", payload)
        write_json(OUT / "analysis/route_analysis.json", payload)
    write_json(OUT / "secondary/attention_qk_overlap.json", {
        "status": "OMITTED_OPTIONAL",
        "reason": "The attention/QK overlay is optional and descriptive only; Stage 3C.9 decisions use the frozen causal checkpoint assays without this overlay.",
        "attention_used_for_selection": False,
    })
    write_json(OUT / "secondary/sink_overlap.json", {
        "status": "OMITTED_OPTIONAL",
        "reason": "No sink manipulation is permitted in Stage 3C.9 and the optional descriptive overlay was not required.",
        "sink_manipulation_started": False,
    })
    print(json.dumps({"phase_d_run": gate["run_phase_d"], "optional_secondary_omitted": True}, indent=2))


if __name__ == "__main__":
    main()
