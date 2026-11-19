#!/usr/bin/env python3
"""Freeze Stage 2B pilot definitions before causal execution."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage2b.config import build_frozen_pilot_specs
from visual_reasoning.stage2b.evaluation import MATERIAL_EFFECT_NATS, SPECIFICITY_MARGIN_NATS


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/stage2b/config"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def annotation_hashes(specs: dict[str, dict[str, Any]]) -> dict[str, str]:
    paths = [ROOT / "outputs/stage2a/evidence_subset/evidence_annotations.jsonl"]
    for example_id in specs:
        example = ROOT / "outputs/stage2a/evidence_subset/examples" / example_id
        paths.extend(example / name for name in ("roi_A.json", "roi_B.json", "candidate_intervention_windows.json"))
    return {str(path.relative_to(ROOT)): sha256(path) for path in paths}


def main() -> None:
    specs = build_frozen_pilot_specs(
        ROOT / "outputs/stage2a/evidence_subset/examples",
        ROOT / "outputs/stage1/discovery/examples",
    )
    protocol = json.loads(
        (ROOT / "outputs/stage1/protocol_pilot/protocol_40960_selection.json").read_text(encoding="utf-8")
    )
    manifest_rows = [specs[example_id] for example_id in specs]
    config = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stage": "2B evidence-specific causal dependence feasibility pilot",
        "pilot_example_ids": list(specs),
        "pilot_size": len(specs),
        "intervention": {
            "type": "additive negative attention-mask entries",
            "edge_scope": "generated query positions in frozen window to selected visual ROI key positions only",
            "language_layers": "all",
            "attention_heads": "all via head-broadcast additive mask",
            "weights_changed": False,
            "vision_embeddings_changed": False,
            "kv_cache_changed": False,
            "official_transformers_source": "https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen3_vl/modeling_qwen3_vl.py",
            "official_pytorch_hook_source": "https://docs.pytorch.org/docs/stable/generated/torch.nn.Module.html#torch.nn.Module.register_forward_pre_hook",
        },
        "local_evaluation": {
            "horizon_tokens": 32,
            "horizon_rule": "32 clean tokens beginning at the frozen acquisition-window start",
            "mask_timing": "mask is active only within the frozen acquisition window; the fixed horizon may extend beyond it",
            "distribution": "raw model next-token distribution before sampling processors",
            "primary_metric": "clean-token NLL increase relative to no-intervention baseline",
            "material_effect_threshold_nats_per_token": MATERIAL_EFFECT_NATS,
            "specificity_margin_nats_per_token": SPECIFICITY_MARGIN_NATS,
        },
        "free_rollout": {
            "prefix": "clean Stage 1 token prefix ending at intervention-window start",
            "generation_protocol": protocol["parameters"],
            "paired_seed": int(protocol["parameters"]["seed"]),
            "normal_stop": "EOS",
            "total_reasoning_safety_ceiling_tokens": int(protocol["parameters"]["max_new_tokens"]),
            "rollouts_per_example": 8,
        },
        "faithfulness_gate": {
            "required": "exact token match between unhooked and hook-attached/no-intervention generation on the mandated A6000",
            "historical_stage1_match": (
                "also measured against the frozen A5000 Stage 1 trace; an isolated cross-hardware mismatch is reported but "
                "does not by itself establish hook invasiveness if the paired A6000 generations match exactly"
            ),
        },
        "window_selection_rule": manifest_rows[0]["selection_rule"],
        "irrelevant_control_rule": "same token count (or within one token), disjoint from both evidence ROIs, frozen before outcomes",
        "known_control_limitation": specs["3764"]["control_notes"],
        "stage2a_annotation_hashes_before": annotation_hashes(specs),
        "scientific_scope": "five-example causal feasibility pilot; no prevalence claim and no WHY, hidden-state, or memory intervention",
        "stop_after": "Stage 2B reports and one next-stage recommendation; do not execute it",
    }

    config_path = OUTPUT / "intervention_config.json"
    manifest_path = OUTPUT / "pilot_manifest.jsonl"
    if config_path.exists() or manifest_path.exists():
        raise FileExistsError("Stage 2B configuration already exists; refusing to overwrite prospectively frozen files")
    write_json(config_path, config)
    write_jsonl(manifest_path, manifest_rows)
    print(json.dumps({"config": str(config_path), "manifest": str(manifest_path), "examples": list(specs)}))


if __name__ == "__main__":
    main()
