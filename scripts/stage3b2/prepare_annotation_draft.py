#!/usr/bin/env python3
"""Create the pre-score Stage 3B.2 E_d annotation draft for manual audit."""

from __future__ import annotations

import json
from pathlib import Path

from transformers import AutoTokenizer

from visual_reasoning.stage0.io import ensure_directory, write_jsonl
from visual_reasoning.stage3b2.annotations import discriminative_event, longest_common_prefix


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/stage3a/cohort/primary_manifest.jsonl"
STAGE0_CONFIG = ROOT / "outputs/stage0/config.json"
OUTPUT = ROOT / "outputs/stage3b2/annotations"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def decode(tokenizer, values: list[int]) -> str:
    return tokenizer.decode(values, skip_special_tokens=False, clean_up_tokenization_spaces=False)


def main() -> None:
    manifest = read_jsonl(SOURCE)
    bases = [str(row["base_problem_id"]) for row in manifest]
    if len(manifest) != 49 or len(set(bases)) != 49:
        raise RuntimeError("Stage 3B.2 annotation requires the frozen 49-base Stage 3A cohort")
    config = json.loads(STAGE0_CONFIG.read_text(encoding="utf-8"))
    checkpoint = Path(config["run_signature"]["model_checkpoint"])
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)

    rows = []
    for item in manifest:
        original_ids = tokenizer.encode(str(item["candidate_original"]), add_special_tokens=False)
        counterfactual_ids = tokenizer.encode(str(item["candidate_counterfactual"]), add_special_tokens=False)
        event = discriminative_event(
            e0_start_token=int(item["event"]["e0_start_token"]),
            original_candidate_ids=original_ids,
            counterfactual_candidate_ids=counterfactual_ids,
        )
        e0 = int(event["e0_start_token"])
        ed = int(event["ed_generated_index"])
        generated = [int(value) for value in item["full_generated_token_ids"]]
        baseline_after_e0 = generated[e0:]
        baseline_common = longest_common_prefix(
            baseline_after_e0,
            event["common_prefix_token_ids"],
        )
        history_ids = [*item["prefix_token_ids"], *event["common_prefix_token_ids"]]
        rows.append(
            {
                "base_problem_id": str(item["base_problem_id"]),
                "example_id": str(item["example_id"]),
                "evidence_type": item["edit_tier"],
                "original_fact": item["original_fact"],
                "counterfactual_fact": item["counterfactual_fact"],
                "candidate_original": item["candidate_original"],
                "candidate_counterfactual": item["candidate_counterfactual"],
                "original_candidate_token_ids": original_ids,
                "counterfactual_candidate_token_ids": counterfactual_ids,
                "original_candidate_tokens": tokenizer.convert_ids_to_tokens(original_ids),
                "counterfactual_candidate_tokens": tokenizer.convert_ids_to_tokens(counterfactual_ids),
                **event,
                "common_prefix_text": decode(tokenizer, event["common_prefix_token_ids"]),
                "original_divergent_suffix_text": decode(
                    tokenizer, event["original_divergent_suffix_ids"]
                ),
                "counterfactual_divergent_suffix_text": decode(
                    tokenizer, event["counterfactual_divergent_suffix_ids"]
                ),
                "first_original_divergent_token_text": decode(
                    tokenizer, [event["first_original_divergent_token_id"]]
                ),
                "first_counterfactual_divergent_token_text": decode(
                    tokenizer, [event["first_counterfactual_divergent_token_id"]]
                ),
                "history_before_ed_token_ids": history_ids,
                "history_before_ed_text": decode(tokenizer, history_ids),
                "history_before_ed_sha256_source": "prefix_token_ids + common_prefix_token_ids",
                "baseline_trace_common_prefix_match_count": len(baseline_common),
                "baseline_trace_common_prefix_exact": len(baseline_common)
                == len(event["common_prefix_token_ids"]),
                "baseline_e0_to_e1_text": decode(
                    tokenizer,
                    generated[
                        e0 : min(len(generated), int(item["event"]["e1_completion_token"]) + 1)
                    ],
                ),
                "mapping_rule": "E_d is E0 plus the token LCP of the two frozen evidence continuations; switching scores the complete divergent suffix under their shared context.",
                "semantic_decision_meaningful": None,
                "pre_ed_discriminative_content_absent": None,
                "manual_audit_status": "pending",
                "manual_audit_note": None,
            }
        )

    ensure_directory(OUTPUT)
    write_jsonl(OUTPUT / "discriminative_event_draft.jsonl", rows)
    lines = [
        "# Stage 3B.2 discriminative-event annotation draft",
        "",
        "This is a pre-score audit sheet. `E_d` is frozen only after every row is manually reviewed.",
        "",
        "| base | E0 | E_d | shared candidate text | original divergence | counterfactual divergence | baseline shared-prefix exact |",
        "|---:|---:|---:|---|---|---|:---:|",
    ]
    for row in rows:
        clean = lambda value: str(value).replace("|", "\\|").replace("\n", "\\n")
        lines.append(
            f"| {row['base_problem_id']} | {row['e0_start_token']} | {row['ed_generated_index']} | "
            f"{clean(row['common_prefix_text'])} | {clean(row['original_divergent_suffix_text'])} | "
            f"{clean(row['counterfactual_divergent_suffix_text'])} | "
            f"{row['baseline_trace_common_prefix_exact']} |"
        )
    (OUTPUT / "annotation_draft.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "rows": len(rows),
                "baseline_shared_prefix_exact": sum(
                    bool(row["baseline_trace_common_prefix_exact"]) for row in rows
                ),
                "min_ed": min(int(row["ed_generated_index"]) for row in rows),
                "max_ed": max(int(row["ed_generated_index"]) for row in rows),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
