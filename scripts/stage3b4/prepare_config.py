#!/usr/bin/env python3
"""Freeze Stage 3B.4 targets, controls, test family, and audited hook contract."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b4.protocol import COORDINATES, MODULES, WINDOWS, retained_module_targets


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b4"
REDESIGN = ROOT / "outputs/stage3b3_redesign"
MODEL_SNAPSHOT = (
    "/home/hyunjin/.cache/huggingface/hub/"
    "models--Qwen--Qwen3-VL-4B-Thinking/snapshots/"
    "1de27d8c51f12e819435303b9e84c4e25ba8401e"
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fine_rows(fine: dict[str, Any]) -> list[dict[str, Any]]:
    sufficiency = {
        (row["coordinate"], row["parent_window"], row["name"]): row
        for row in fine["sufficiency"]
    }
    restoration = {
        (row["coordinate"], row["parent_window"], row["name"]): row
        for row in fine["semantic_restoration"]
    }
    layers = {row["name"]: row["layers"] for row in fine["fine_windows"]}
    rows = []
    for key, sufficiency_row in sufficiency.items():
        restoration_row = restoration[key]
        rows.append({
            "coordinate": key[0],
            "parent_window": key[1],
            "name": key[2],
            "layers": layers[key[2]],
            "BWS_median": sufficiency_row["statistics"]["BWS_normalized"]["median"],
            "BSRC_median": restoration_row["statistics"]["BSRC_normalized"]["median"],
        })
    return rows


def main() -> None:
    ensure_directory(OUT / "config")
    ensure_directory(OUT / "audit")
    ensure_directory(OUT / "validation")
    ensure_directory(OUT / "scoring")
    ensure_directory(OUT / "analysis/figures")
    ensure_directory(OUT / "summaries")

    fine = read_json(REDESIGN / "analysis/fine_layer_statistics.json")
    decision = read_json(REDESIGN / "analysis/decision_rule_evaluation.json")
    targets = retained_module_targets(decision=decision, fine_rows=fine_rows(fine))
    target_by_window = {}
    for window in WINDOWS:
        values = [row for row in targets if row["window"] == window]
        names = {(row["fine_window"], tuple(row["layers"])) for row in values}
        if len(values) != 2 or len(names) != 1:
            raise RuntimeError(f"Retained target is inconsistent across coordinates for {window}")
        fine_window, layers = next(iter(names))
        target_by_window[window] = {"fine_window": fine_window, "layers": list(layers)}

    validation = read_jsonl(REDESIGN / "config/validation_manifest.jsonl")
    primary = read_jsonl(REDESIGN / "primary/primary_41_manifest.jsonl")
    validation_bases = {str(row["base_problem_id"]) for row in validation}
    primary_bases = {str(row["base_problem_id"]) for row in primary}
    if len(validation_bases) != 8 or len(primary_bases) != 41 or validation_bases & primary_bases:
        raise RuntimeError("Stage 3B.4 requires a disjoint 8/41 validation-primary split")
    numeric_primary = [row for row in primary if "structural" not in str(row["edit_tier"])]
    if len(numeric_primary) != 37:
        raise RuntimeError("Paired module restoration requires 37 numeric primary bases")

    model_source = next(
        ROOT.glob(".venv/lib/python*/site-packages/transformers/models/qwen3_vl/modeling_qwen3_vl.py")
    )
    frozen_at = datetime.now(timezone.utc).isoformat()
    config = {
        "frozen_at": frozen_at,
        "source_plan": "plan/stage3b4_plan.md",
        "source_stage": "outputs/stage3b3_redesign",
        "model_checkpoint": MODEL_SNAPSHOT,
        "model": "Qwen3-VL-4B-Thinking",
        "transformers_version": importlib.metadata.version("transformers"),
        "required_gpu_class": "A5000",
        "attention_implementation": "validated eager local override",
        "seed": 1234,
        "coordinates": list(COORDINATES),
        "targets": targets,
        "target_by_window": target_by_window,
        "modules": {
            "attention": ["attention"],
            "mlp": ["mlp"],
            "joint": ["attention", "mlp"],
            "block": ["block"],
        },
        "conditions": ["O", "O_sham", "C", "C_sham"],
        "intervention_scope": "current evidence-decision position only",
        "primary_metric": "unnormalized paired semantic BMR",
        "normalized_metric": "BMR / abs(matching Stage 3B.2 all-layer BRI); unclipped",
        "optional_necessity_arms": False,
        "combined_W4_W5_arm": False,
        "attention_secondary_selection": False,
        "validation": {
            "base_count": 8,
            "baseline_reproduction": "token-log-probability exact on A5000",
            "capture_and_patch_audits": "all requested hooks exactly once; only current position replaced",
            "self_restoration": "exact for O and C at every coordinate/window/module",
            "finite_outputs": "all candidate scores finite",
            "determinism_anchor_base_problem_id": str(validation[0]["base_problem_id"]),
            "determinism": "repeat full anchor result with exact public score/control equality",
            "full_block_gate": {
                "activity": "abs(BMR) >= 0.10 * abs(all-layer BRI)",
                "required_active_bases": 7,
                "required_bidirectionally_consistent_bases": 7,
                "cohort_median_active_base_BMR": "> 0",
                "median_render_to_semantic_ratio_max": 0.25,
                "median_render_to_all_layer_ratio_max": 0.05,
            },
            "all_module_render_gate": {
                "definition": "median across bases of each base's median A_render / abs(all-layer BRI), pooled over the four fixed cells and four modules",
                "maximum": 0.05,
            },
        },
        "primary_inference": {
            "inferential_base_count": 37,
            "cohort_manifest_base_count": 41,
            "paired_module_scoring_base_count": 37,
            "structural_manifest_only_base_count": 4,
            "structural_handling": "retained in the frozen cohort record but excluded from paired module inference because C_sham is unavailable; no uncontrolled replacement test is substituted",
            "one_sided_test": "Wilcoxon signed-rank BMR > 0",
            "multiple_testing": "Holm across exactly 16 coordinate/window/module tests",
            "alpha": 0.05,
            "robust_cell": {
                "holm_adjusted_p": "< 0.05",
                "median_bootstrap_CI_low": "> 0",
                "bidirectional_fraction": ">= 0.70",
                "median_render_to_semantic_ratio": "< 0.25",
                "all_self_restorations_exact": True,
            },
        },
        "decision_thresholds": {
            "minimum_category_cells": 2,
            "substantial_single_module_to_block_ratio": 0.50,
            "single_module_dominance_margin": 0.20,
            "cascade_single_module_min_ratio": 0.20,
            "cascade_joint_min_ratio": 0.70,
            "cascade_joint_must_equal_or_exceed_each_single": True,
        },
        "selection_used_attention": False,
        "no_new_layer_search": True,
    }
    write_json(OUT / "config/stage3b4_config.json", config)

    family = {
        "frozen_at": frozen_at,
        "family_size": 16,
        "tests": [
            {
                "test_id": f"{coordinate}__{window}__{module}",
                "coordinate": coordinate,
                "window": window,
                "fine_window": target_by_window[window]["fine_window"],
                "layers": target_by_window[window]["layers"],
                "module": module,
                "primary_metric": "BMR",
            }
            for coordinate in COORDINATES
            for window in WINDOWS
            for module in MODULES
        ],
        "correction": "Holm",
        "alpha": 0.05,
    }
    write_json(OUT / "config/primary_family.json", family)
    write_jsonl(OUT / "config/cohort_manifest.jsonl", [
        {**row, "stage3b4_role": "primary"} for row in primary
    ])
    write_jsonl(OUT / "validation/validation_manifest.jsonl", [
        {**row, "stage3b4_role": "validation"} for row in validation
    ])

    hook_locations = {
        "frozen_at": frozen_at,
        "transformers_version": config["transformers_version"],
        "source_file": str(model_source.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(model_source.read_bytes()).hexdigest(),
        "decoder_layer_class": "Qwen3VLTextDecoderLayer",
        "attention": {
            "module_path": "model.language_model.layers[L].self_attn",
            "captured_value": "tuple[0] after o_proj and before residual addition",
            "patch_scope": "output[:, current_absolute_position, :]",
        },
        "mlp": {
            "module_path": "model.language_model.layers[L].mlp",
            "captured_value": "down_proj output before residual addition",
            "patch_scope": "output[:, current_absolute_position, :]",
        },
        "block": {
            "module_path": "model.language_model.layers[L]",
            "captured_value": "final block residual after attention and MLP residual additions",
            "patch_scope": "output[:, current_absolute_position, :]",
        },
        "joint": {
            "module_paths": [
                "model.language_model.layers[L].self_attn",
                "model.language_model.layers[L].mlp",
            ],
            "captured_values": "paired donor attention and MLP contributions from the same semantic condition",
        },
        "targets": target_by_window,
        "hooks_frozen_before_validation_scores": True,
    }
    write_json(OUT / "audit/hook_locations.json", hook_locations)
    decomposition = f"""# Qwen3-VL text block decomposition

Frozen before Stage 3B.4 module scoring: `{frozen_at}`.

Audited source: `{hook_locations['source_file']}` (`transformers=={config['transformers_version']}`, SHA-256 `{hook_locations['source_sha256']}`).

`Qwen3VLTextDecoderLayer` uses the following actual pre-norm order:

1. Save the input residual `r0`.
2. Apply `input_layernorm` (RMSNorm).
3. Run `self_attn`; its returned tensor has already passed `o_proj`.
4. Add the attention contribution to `r0`, producing the post-attention residual `r1`.
5. Apply `post_attention_layernorm` (RMSNorm) to `r1`.
6. Run the gated MLP and `down_proj`.
7. Add the MLP contribution to `r1`, producing the final block residual `r2`.

Stage 3B.4 hooks therefore capture/restore only the current decision position at:

- **Attention:** `self_attn` output tuple element 0, after `o_proj`, before step 4.
- **MLP:** `mlp` tensor output, after `down_proj`, before step 7.
- **Attention+MLP:** both contribution surfaces from the same donor condition.
- **Block:** decoder-layer tensor output `r2` after step 7.

Frozen targets are W4/F28_29 (layers 28--29) and W5/F32_33 (layers 32--33), at `E_d-1` and `E_d`. No other layer or sequence position is patched.
"""
    write_text(OUT / "audit/block_decomposition.md", decomposition)
    print(json.dumps({
        "validation_bases": len(validation),
        "primary_bases": len(primary),
        "numeric_primary_bases": len(numeric_primary),
        "targets": target_by_window,
        "primary_tests": len(family["tests"]),
    }, indent=2))


if __name__ == "__main__":
    main()
