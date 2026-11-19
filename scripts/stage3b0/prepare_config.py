#!/usr/bin/env python3
"""Freeze the Stage 3B.0 cohort, token groups, and intervention protocol."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/stage3a/cohort/primary_manifest.jsonl"
OUTPUT = ROOT / "outputs/stage3b0"
SMOKE_BASES = {"119", "140", "148"}


def main() -> None:
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    bases = [str(row["base_problem_id"]) for row in rows]
    if len(rows) != 49 or len(set(bases)) != 49:
        raise RuntimeError("Stage 3B.0 requires the frozen 49-unique-base Stage 3A manifest")
    smoke = [row for row in rows if str(row["base_problem_id"]) in SMOKE_BASES]
    if len(smoke) != 3 or any(row["edit_tier"] != "tier1_local_numeric_label" for row in smoke):
        raise RuntimeError("Smoke cohort must contain the three prospectively selected numeric examples")

    for directory in (
        "config",
        "layout_audit",
        "smoke",
        "cutoff",
        "patching",
        "analysis/figures",
        "summaries",
        "raw/smoke",
        "raw/shards",
    ):
        ensure_directory(OUTPUT / directory)
    write_jsonl(OUTPUT / "config/cohort_manifest.jsonl", rows)
    write_jsonl(OUTPUT / "config/smoke_manifest.jsonl", smoke)
    write_json(
        OUTPUT / "config/stage3b0_config.json",
        {
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "source_manifest": str(SOURCE.relative_to(ROOT)),
            "primary_unit": "base_problem_id",
            "base_problem_count": 49,
            "evidence_strata": {"tier1_local_numeric_label": 45, "tier3_structural_visual_edit": 4},
            "selection_used_attention": False,
            "seed": 1234,
            "model_protocol": "Qwen3-VL-4B-Thinking locked Stage 1 official-style protocol",
            "strict_prefix": "exact Stage 3A y_<E0 token IDs, identical across all conditions",
            "cutoff": {
                "prefill": "unmodified",
                "active_queries": "all generated-token query positions, beginning with y_0",
                "blocked_keys": "all image-token placeholder positions V",
                "layers": "all language layers",
                "heads": "all query heads through the additive attention mask",
            },
            "frozen_token_groups": ["P_post_image", "Q", "T", "Q_plus_T"],
            "primary_patch_groups": ["P_post_image", "Q"],
            "optional_prospectively_frozen_groups": ["T", "Q_plus_T"],
            "patch_components": ["post-RoPE K", "V"],
            "patch_layers": "all language layers",
            "patch_directions": ["counterfactual<-original", "original<-counterfactual"],
            "controls": ["no_patch", "self_patch", "original<-sham", "sham<-original"],
            "smoke_base_problem_ids": sorted(SMOKE_BASES, key=int),
            "stage3b1_started": False,
        },
    )
    write_json(
        OUTPUT / "layout_audit/token_group_definition.json",
        {
            "frozen_before_cohort_scoring": True,
            "selection_used_attention": False,
            "V": "all prompt positions equal to the processor image-token ID",
            "Q": "the unique exact tokenization of the MathVerse generation question within the prompt",
            "T": "all prompt positions strictly after the end of Q",
            "Q_plus_T": "Q union T",
            "P_post_image": "all nonvisual prompt positions strictly after the final visual placeholder, including the vision-end bridge, Q, and T",
            "eligibility": "positions must exist at identical indices in original/counterfactual/sham prompts",
            "causal_order": "only positions after the final visual placeholder are eligible as nonvisual prefill carriers",
            "groups_frozen": ["P_post_image", "Q", "T", "Q_plus_T"],
            "attention_used": False,
        },
    )
    print(json.dumps({"cohort": len(rows), "smoke": len(smoke), "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
