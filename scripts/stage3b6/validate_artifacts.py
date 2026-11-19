#!/usr/bin/env python3
"""Independently validate persisted Stage 3B.6 metrics, cohorts, and gates."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage3b6.metrics import head_restoration_metrics


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b6"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def close(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-12)


def raw_bases(prefix: str) -> list[dict[str, Any]]:
    return [
        row
        for directory in sorted((OUT / "scoring/raw").glob(f"{prefix}_*"))
        for row in read_jsonl(directory / "results.jsonl")
    ]


def flattened(bases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"base_problem_id": str(base["base_problem_id"]), **unit}
        for base in bases
        for cell in base["cells"]
        for unit in cell["unit_results"]
    ]


def main() -> None:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    config = read_json(OUT / "config/stage3b6_config.json")
    split = read_json(OUT / "config/discovery_primary_split.json")
    freeze = read_json(OUT / "config/frozen_head_candidates.json")
    head_stats = read_json(OUT / "analysis/head_restoration_statistics.json")
    targets = read_json(OUT / "analysis/source_path_targets.json")
    acceptance = read_json(OUT / "summaries/stage3b6_acceptance.json")

    expected_cells = [
        ("Ed_minus_1__W4", 28, "qualifying_attention"),
        ("Ed_minus_1__W5", 32, "qualifying_attention"),
        ("Ed__W4", 29, "qualifying_attention"),
        ("Ed__W5", 32, "upstream_control"),
    ]
    observed_cells = [
        (row["cell_id"], int(row["layer_index"]), row["role"])
        for row in config["frozen_cells"]
    ]
    check("exact frozen cells and layers", observed_cells == expected_cells, observed_cells)
    discovery = read_jsonl(OUT / "discovery/per_head_discovery_results.jsonl")
    check("discovery row count", len(discovery) == 768, len(discovery))
    check(
        "discovery 8-base split",
        {row["base_problem_id"] for row in discovery}
        == set(split["discovery_base_problem_ids"]),
    )
    discovery_counts = Counter((row["cell_id"], tuple(row["heads"])) for row in discovery)
    check(
        "every discovery cell/head has eight bases",
        len(discovery_counts) == 96 and set(discovery_counts.values()) == {8},
        {"groups": len(discovery_counts), "counts": sorted(set(discovery_counts.values()))},
    )
    check(
        "candidate rankings are complete permutations",
        all(sorted(payload["ranking"]) == list(range(32)) for payload in freeze["cells"].values()),
    )
    check("candidate selection did not use attention", freeze["selection_used_attention"] is False)

    primary_bases = raw_bases("primary")
    upstream_bases = raw_bases("upstream")
    check("primary base set exact", {row["base_problem_id"] for row in primary_bases} == set(split["primary_base_problem_ids"]), len(primary_bases))
    check("upstream base set exact", {row["base_problem_id"] for row in upstream_bases} == set(split["primary_base_problem_ids"]), len(upstream_bases))
    check(
        "all primary mechanics pass",
        all(all(bool(value) for value in row["mechanical_controls"].values()) for row in primary_bases),
    )
    check(
        "all upstream mechanics pass",
        all(all(bool(value) for value in row["mechanical_controls"].values()) for row in upstream_bases),
    )

    metric_failures = []
    for row in [*flattened(primary_bases), *flattened(upstream_bases)]:
        recomputed = head_restoration_metrics(
            recipient_scores=row["recipient_scores"],
            stage3b5_attention_gain=float(row["stage3b5_attention_gain"]),
        )
        for key in ("BHR_O", "BHR_C", "BHR", "HRR", "sham_effect", "sham_to_semantic_ratio"):
            if not close(row[key], recomputed[key]):
                metric_failures.append({
                    "base_problem_id": row["base_problem_id"],
                    "cell_id": row["cell_id"],
                    "unit_id": row["unit_id"],
                    "key": key,
                    "saved": row[key],
                    "recomputed": recomputed[key],
                })
    check("all persisted head metrics independently recompute", not metric_failures, metric_failures[:10])
    check(
        "Holm family size matches frozen tests",
        int(head_stats["frozen_family_size"]) == len(head_stats["unit_statistics"])
        == len(head_stats["holm_family"]),
    )

    source = read_jsonl(OUT / "scoring/source_path_results.jsonl")
    if targets["gate_passed"]:
        expected_source_rows = 37 * len(targets["targets"]) * 4
        check("source row count", len(source) == expected_source_rows, len(source))
        check("all V/P/R/all groups present", {row["source_group"] for row in source} == {"all", "V", "P", "R"})
        source_lookup = {
            (row["base_problem_id"], row["cell_id"], row["unit_id"], row["source_group"]): row
            for row in source
        }
        path_failures = []
        for row in source:
            all_row = source_lookup[(row["base_problem_id"], row["cell_id"], row["unit_id"], "all")]
            expected_prr = None if float(all_row["BPR"]) == 0.0 else float(row["BPR"]) / float(all_row["BPR"])
            if not close(row["BPR"], row["BHR"]) or not close(row["PRR"], expected_prr):
                path_failures.append({
                    "base_problem_id": row["base_problem_id"],
                    "cell_id": row["cell_id"],
                    "unit_id": row["unit_id"],
                    "source_group": row["source_group"],
                })
        check("source BPR/PRR independently recompute", not path_failures, path_failures[:10])
    else:
        check("source scoring skipped after failed gate", len(source) == 0, len(source))

    required = [
        "config/stage3b6_config.json",
        "config/qualifying_cells.json",
        "config/discovery_primary_split.json",
        "config/frozen_head_candidates.json",
        "audit/gqa_head_map.md",
        "audit/head_tensor_layout.json",
        "audit/output_projection_slices.json",
        "audit/source_token_groups.json",
        "audit/hook_validation.md",
        "discovery/per_head_discovery_results.jsonl",
        "discovery/head_rankings.json",
        "discovery/candidate_freeze_report.md",
        "validation/head_intervention_validation.json",
        "validation/source_path_validation.json",
        "validation/validation_report.md",
        "scoring/primary_head_results.jsonl",
        "scoring/cumulative_headset_results.jsonl",
        "scoring/upstream_control_results.jsonl",
        "scoring/source_path_results.jsonl",
        "analysis/head_restoration_statistics.json",
        "analysis/sparse_vs_distributed_heads.json",
        "analysis/source_path_statistics.json",
        "analysis/cutoff_triangulation.json",
        "analysis/attention_secondary_analysis.json",
        "summaries/stage3b6_summary.md",
        "summaries/stage3b6_acceptance.json",
        "summaries/next_stage_recommendation.md",
    ]
    missing = [path for path in required if not (OUT / path).is_file()]
    check("all required artifacts exist", not missing, missing)
    figures = sorted((OUT / "analysis/figures").glob("*.png"))
    check("all ten required figures exist", len(figures) >= 10, [path.name for path in figures])
    prohibited_names = [
        path.relative_to(OUT).as_posix()
        for path in OUT.rglob("*")
        if path.is_file()
        and any(term in path.name.lower() for term in ("roi_specific", "k_vs_v", "pattern_value", "neuron"))
    ]
    check("no prohibited follow-on artifact exists", not prohibited_names, prohibited_names)
    check("acceptance reports 17 criteria", acceptance["total_count"] == 17, acceptance)
    check("later stage not started", acceptance["stage3b7_started"] is False and acceptance["prohibited_analyses_started"] is False)

    payload = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "validator": "independent persisted-artifact recomputation",
        "status": "PASS" if all(row["passed"] for row in checks) else "FAIL",
        "passed_count": sum(bool(row["passed"]) for row in checks),
        "total_count": len(checks),
        "checks": checks,
    }
    write_json(OUT / "analysis/artifact_validation.json", payload)
    if payload["status"] != "PASS":
        raise RuntimeError("Stage 3B.6 artifact validation failed")


if __name__ == "__main__":
    main()
