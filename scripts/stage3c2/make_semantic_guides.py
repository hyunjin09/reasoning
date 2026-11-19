#!/usr/bin/env python3
"""Render attention-blind semantic checkpoint guides for Stage 3C.2."""

from __future__ import annotations

import json
from pathlib import Path

from transformers import AutoTokenizer


ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = Path(
    "/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/"
    "snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e"
)
A_OFFSETS = (-16, -8, -4, -2, -1, 0)
B_OFFSETS = (-16, -8, -4, -2, -1, 0)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    candidates = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3c2/cohort/candidate_manifest.jsonl")
    }
    events = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(
            ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl"
        )
    }
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, local_files_only=True)
    rows: list[dict] = []
    for base, candidate in candidates.items():
        event = events[base]
        token_ids = [int(value) for value in event["history_before_ed_token_ids"]]
        ed = int(event["ed_generated_index"])
        for target_id, center, offsets in (
            ("target_a", ed, A_OFFSETS),
            ("target_b", ed - 1, B_OFFSETS),
        ):
            for offset in offsets:
                generated_index = center + offset
                if generated_index < 1:
                    continue
                prefix_ids = token_ids[:generated_index]
                rows.append(
                    {
                        "base_problem_id": base,
                        "example_id": candidate["example_id"],
                        "target_id": target_id,
                        "offset_from_target": offset,
                        "generated_index": generated_index,
                        "active_token_id": prefix_ids[-1],
                        "active_token": tokenizer.convert_ids_to_tokens(prefix_ids[-1]),
                        "text_tail": tokenizer.decode(prefix_ids, skip_special_tokens=False)[-360:],
                        "semantic_state": "pending",
                        "annotation_used_attention": False,
                    }
                )
    out = ROOT / "outputs/stage3c2/annotations/semantic_checkpoint_review.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    print(json.dumps({"rows": len(rows), "bases": len(candidates), "output": str(out)}))


if __name__ == "__main__":
    main()
