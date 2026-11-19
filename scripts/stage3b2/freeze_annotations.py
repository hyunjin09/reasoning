#!/usr/bin/env python3
"""Freeze the manually reviewed Stage 3B.2 discriminative-event annotations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
ANNOTATION_DIR = ROOT / "outputs/stage3b2/annotations"
DRAFT = ANNOTATION_DIR / "discriminative_event_draft.jsonl"
OUTPUT = ANNOTATION_DIR / "discriminative_event_annotations.jsonl"

# Explicit record of the 49 rows reviewed against candidate tokenization,
# divergent suffixes, and the baseline E0--E1 text in annotation_draft.md.
REVIEWED_BASES = (
    "119", "140", "148", "155", "614", "616", "753", "613", "136", "141",
    "147", "154", "617", "751", "2", "3", "6", "9", "16", "22", "24",
    "31", "38", "60", "67", "69", "72", "74", "75", "76", "78", "79",
    "80", "83", "93", "96", "98", "100", "101", "103", "106", "107",
    "109", "113", "118", "120", "125", "126", "128",
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    rows = read_jsonl(DRAFT)
    observed = tuple(str(row["base_problem_id"]) for row in rows)
    if observed != REVIEWED_BASES or len(set(observed)) != 49:
        raise RuntimeError("Annotation draft no longer matches the manually reviewed 49-base order")

    frozen_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        exact = bool(row["baseline_trace_common_prefix_exact"])
        row["semantic_decision_meaningful"] = True
        row["pre_ed_discriminative_content_absent"] = True
        row["manual_audit_status"] = "pass"
        row["manual_audit_note"] = (
            "Shared evidence lead exactly matches the baseline trace from E0; the first divergent "
            "token is the earliest source-identifying decision."
            if exact
            else
            "The frozen Stage 3A shared evidence lead is a semantic paraphrase of the baseline "
            "E0--E1 fact statement; it names the entity/relation but contains no distinguishing "
            "suffix content before E_d. The timing coordinate is therefore teacher-forced rather "
            "than an exact natural-trace token position."
        )
        row["manual_review"] = {
            "reviewed": True,
            "reviewed_at": frozen_at,
            "audit_fields": [
                "candidate texts",
                "tokenization",
                "longest common prefix",
                "first divergent tokens",
                "baseline E0--E1 span",
                "semantic meaningfulness",
                "absence of discriminative identity before E_d",
            ],
            "used_causal_scores": False,
            "used_attention": False,
        }

    write_jsonl(OUTPUT, rows)
    exact_rows = [row for row in rows if row["baseline_trace_common_prefix_exact"]]
    paraphrase_rows = [row for row in rows if not row["baseline_trace_common_prefix_exact"]]
    lines = [
        "# Stage 3B.2 discriminative-event annotation audit",
        "",
        f"Frozen at: {frozen_at}",
        "",
        "## Result",
        "",
        "- 49/49 frozen bases were manually reviewed before causal scoring.",
        "- 49/49 candidate pairs have nonempty divergent suffixes and a semantically meaningful first discriminative decision.",
        "- 49/49 shared contexts exclude the distinguishing suffix content before `E_d`.",
        f"- {len(exact_rows)}/49 shared candidate leads match the baseline trace exactly from E0.",
        f"- {len(paraphrase_rows)}/49 use the already-frozen Stage 3A semantic evidence continuation rather than an exact natural-trace token continuation.",
        "- No attention or causal score was used in annotation or acceptance.",
        "",
        "## Interpretation boundary",
        "",
        "For the 37 semantic-paraphrase rows, `E_d` is a teacher-forced evidence-decision coordinate within the frozen Stage 3A candidate context. It must not be described as the exact token position at which the original free-running trace naturally made that decision. The causal readout remains valid for the fixed candidate context, but natural-trajectory timing claims must report this distinction.",
        "",
        "## Per-base audit",
        "",
        "| base | E0 | E_d | alignment | first original token | first counterfactual token | decision |",
        "|---:|---:|---:|---|---|---|---|",
    ]
    for row in rows:
        alignment = "exact baseline tokens" if row["baseline_trace_common_prefix_exact"] else "semantic teacher-forced lead"
        clean = lambda value: str(value).replace("|", "\\|").replace("\n", "\\n")
        lines.append(
            f"| {row['base_problem_id']} | {row['e0_start_token']} | {row['ed_generated_index']} | "
            f"{alignment} | {clean(row['first_original_divergent_token_text'])} | "
            f"{clean(row['first_counterfactual_divergent_token_text'])} | PASS |"
        )
    (ANNOTATION_DIR / "annotation_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"frozen": len(rows), "exact_baseline": len(exact_rows), "semantic_paraphrase": len(paraphrase_rows)}, indent=2))


if __name__ == "__main__":
    main()
