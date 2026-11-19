#!/usr/bin/env python3
"""Create attention-free local M/R text windows for prospective lexical review."""

from __future__ import annotations

import json
from pathlib import Path

from transformers import AutoProcessor


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    config = json.loads((OUT / "config/stage3c3_config.json").read_text(encoding="utf-8"))
    processor = AutoProcessor.from_pretrained(config["model_checkpoint"], local_files_only=True)
    events = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")
    }
    manifests = read_jsonl(OUT / "cohort/validation_manifest.jsonl") + read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    rows = []
    for item in manifests:
        base = str(item["base_problem_id"])
        context = [int(value) for value in events[base]["history_before_ed_token_ids"]]
        for pair in item["state_pairs"]:
            m = int(pair["state_M"]["generated_index"])
            r = int(pair["state_R"]["generated_index"])
            rows.append({
                "base_problem_id": base,
                "target_id": pair["target_id"],
                "cohort_role": item["cohort_role"],
                "mention_entity": item["mention_entity"],
                "state_M_generated_index": m,
                "state_R_generated_index": r,
                "state_M_local_text": processor.tokenizer.decode(context[max(0, m - 16):m], skip_special_tokens=False),
                "state_R_local_text": processor.tokenizer.decode(context[max(0, r - 16):r], skip_special_tokens=False),
                "strong_lexical_match": None,
                "manual_reason": None,
                "review_used_attention": False,
                "review_used_stage3c3_outcomes": False,
            })
    path = OUT / "cohort/lexical_review_draft.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "path": str(path.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
