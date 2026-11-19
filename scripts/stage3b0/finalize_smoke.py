#!/usr/bin/env python3
"""Validate the Stage 3B.0 smoke gate and write its required audit artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from transformers import AutoProcessor

from visual_reasoning.stage0.io import write_json


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "outputs/stage3b0/raw/smoke/validated"
OUT = ROOT / "outputs/stage3b0"
MODEL = Path("/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e")


def compact_audit(audit: dict) -> dict:
    return {
        "enabled": audit["enabled"],
        "modified_calls": audit["modified_calls"],
        "layers_modified_unique": sorted(set(audit["layers_modified"])),
        "minimum_modified_query_index": min(audit["absolute_query_indices"]),
        "maximum_modified_query_index": max(audit["absolute_query_indices"]),
        "prefill_modified": audit["prefill_modified"],
        "logical_head_edges_modified": audit["logical_head_edges_modified"],
    }


def main() -> None:
    paths = sorted((RAW / "examples").glob("*/result.json"), key=lambda path: int(path.parent.name))
    if len(paths) != 3:
        raise RuntimeError(f"Expected three smoke bundles, found {len(paths)}")
    rows = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    criteria = {
        "stage3a_no_hook_exact_3_of_3": all(row["smoke"]["stage3a_no_hook_exact"] for row in rows),
        "hooked_noop_exact_3_of_3": all(row["smoke"]["hooked_noop_exact"] for row in rows),
        "cutoff_all_layers_and_generated_start_only_3_of_3": all(
            row["smoke"]["cutoff_all_layers_and_generated_start_only"] for row in rows
        ),
        "prefix_and_groups_aligned_3_of_3": all(row["smoke"]["prefix_and_groups_aligned"] for row in rows),
        "cache_layout_valid_3_of_3": all(
            row["cache_diagnostic"]["tensor_shape"][1:]
            == [8, len(row["layout"]["prompt_token_ids"]), 128]
            and row["cache_diagnostic"]["layer_count"] == 36
            for row in rows
        ),
        "self_patch_exact_3_of_3": all(row["smoke"]["self_patch_max_abs_D_shift"] == 0.0 for row in rows),
        "cached_scoring_deterministic_3_of_3": all(row["smoke"]["cached_deterministic_exact"] for row in rows),
        "finite_3_of_3": all(row["smoke"]["all_finite"] for row in rows),
    }
    if not all(criteria.values()):
        raise RuntimeError(f"Stage 3B.0 smoke gate failed: {criteria}")

    transparency = {
        "gate": "PASS",
        "criteria": criteria,
        "per_base": [
            {
                key: row["smoke"][key]
                for key in (
                    "base_problem_id",
                    "stage3a_no_hook_exact",
                    "hooked_noop_exact",
                    "cutoff_all_layers_and_generated_start_only",
                    "cached_vs_full_cutoff_max_abs_D_or_L",
                    "self_patch_max_abs_D_shift",
                    "cached_deterministic_exact",
                    "all_finite",
                    "prefix_and_groups_aligned",
                )
            }
            for row in rows
        ],
        "cached_full_diagnostic": "outputs/stage3b0/smoke/cached_full_parity_diagnostic.json",
        "scoring_resolution": "RQ1 uses full-sequence Stage 3A-compatible scoring; cache-patch recovery uses matched cached recipient/source baselines.",
    }
    write_json(OUT / "smoke/hook_transparency.json", transparency)
    write_json(
        OUT / "layout_audit/cache_shape_diagnostics.json",
        {
            "status": "PASS",
            "architecture": {
                "query_heads": 32,
                "kv_heads": 8,
                "head_dimension": 128,
                "language_layers": 36,
                "gqa_query_heads_per_kv_head": 4,
            },
            "cache_layout": {
                "axis_order": ["batch", "kv_head", "sequence", "head_dimension"],
                "sequence_axis": 2,
                "patched_components": ["post-RoPE key", "value"],
                "all_language_layers": True,
            },
            "per_base": [
                {"base_problem_id": row["base_problem_id"], **row["cache_diagnostic"]} for row in rows
            ],
        },
    )

    processor = AutoProcessor.from_pretrained(MODEL, local_files_only=True)
    layout_lines = [
        "# Stage 3B.0 token-layout audit",
        "",
        "Status: **PASS**. The groups below were defined and frozen before cohort-scale scoring. No attention value was used.",
        "",
        "The causal order in all three prompts is: pre-image user/control prefix → visual placeholders `V` → vision-end bridge → exact question content `Q` → trailing user/assistant control positions `T`. `P_post-image` contains every nonvisual position after the last member of `V`.",
        "",
        "| Base | Prompt | V range/count | Bridge range/count | Q range/count | T range/count | P count | Q+T count |",
        "|---:|---:|---|---|---|---|---:|---:|",
    ]
    decoded = []
    for row in rows:
        groups = row["layout"]["groups"]
        prompt_ids = row["layout"]["prompt_token_ids"]
        bridge = [index for index in groups["P_post_image"] if index < groups["Q"][0]]
        layout_lines.append(
            f"| {row['base_problem_id']} | {len(prompt_ids)} | {groups['V'][0]}–{groups['V'][-1]} / {len(groups['V'])} | "
            f"{bridge[0]}–{bridge[-1]} / {len(bridge)} | {groups['Q'][0]}–{groups['Q'][-1]} / {len(groups['Q'])} | "
            f"{groups['T'][0]}–{groups['T'][-1]} / {len(groups['T'])} | {len(groups['P_post_image'])} | {len(groups['Q_plus_T'])} |"
        )
        decoded.append(
            {
                "base_problem_id": row["base_problem_id"],
                "pre_image_prefix": processor.tokenizer.decode(prompt_ids[: groups["V"][0]], skip_special_tokens=False),
                "bridge": processor.tokenizer.decode([prompt_ids[index] for index in bridge], skip_special_tokens=False),
                "question": processor.tokenizer.decode([prompt_ids[index] for index in groups["Q"]], skip_special_tokens=False),
                "trailing": processor.tokenizer.decode([prompt_ids[index] for index in groups["T"]], skip_special_tokens=False),
            }
        )
    layout_lines.extend(
        [
            "",
            "Across original, counterfactual, and sham conditions, prompt token IDs, image-grid shape, visual-token count, text-token positions, and every source/recipient patch index were exactly aligned for all 3/3 examples. All frozen groups were nonempty, so the prospectively defined optional `T` and `Q+T` groups remain in the cohort protocol.",
            "",
            "Decoded group audit:",
            "",
            "```json",
            json.dumps(decoded, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    (OUT / "layout_audit/token_layout_audit.md").write_text("\n".join(layout_lines) + "\n", encoding="utf-8")

    first = rows[0]["smoke"]["full_sequence_cutoff"]["original"]["hook_audits"]["original_candidate"]
    (OUT / "smoke/visual_cutoff_validation.md").write_text(
        "# Generation-start visual-cutoff validation\n\n"
        "Status: **PASS (3/3)**. The additive mask changed all and only generated-token-query → visual-key entries across all 36 language layers. The minimum modified absolute query index equaled the prompt length in every example, so prefill was untouched and the first generated token was the first masked query. All 32 logical query heads were affected through the shared additive mask.\n\n"
        f"Representative compact audit (base {rows[0]['base_problem_id']}):\n\n```json\n{json.dumps(compact_audit(first), indent=2)}\n```\n",
        encoding="utf-8",
    )
    (OUT / "smoke/kv_patch_validation.md").write_text(
        "# KV-patch validation\n\n"
        "Status: **PASS (3/3)**. Qwen3-VL exposes 36 dynamic-cache layers with tensors `[batch, kv_head, sequence, head_dim]`; the audited shapes were `[1, 8, prompt_length, 128]`. Both post-RoPE K and V were replaced at exactly the frozen sequence positions in every layer. Self-patching produced exactly zero change in evidence preference for every group and example. Repeated cached scoring was bit-exact and all values were finite.\n\n"
        "A focused diagnostic found small deterministic full-sequence/cached BF16 differences even without intervention. Accordingly, full-sequence scoring is used for the primary generation-start cutoff CE, while every patch recovery is computed against its matched cached no-patch recipient/source baselines. This keeps kernel path fixed within each causal patch contrast.\n",
        encoding="utf-8",
    )
    print(json.dumps(transparency, indent=2))


if __name__ == "__main__":
    main()
