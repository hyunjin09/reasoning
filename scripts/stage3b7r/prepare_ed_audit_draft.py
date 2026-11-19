#!/usr/bin/env python3
"""Prepare score-blind token-indexed E_d audit drafts for fresh validation."""

from __future__ import annotations

import json
import re
from pathlib import Path

from transformers import AutoTokenizer

from visual_reasoning.stage0.io import ensure_directory, write_jsonl, write_text
from visual_reasoning.stage3b2.annotations import longest_common_prefix


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r"
CHECKPOINT = Path("/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e")


SPECS = {
    "183": (" the circle radius is 2", " the circle radius is 4", ["radius", "circle", "tangent"]),
    "184": (" the circle radius is 2", " the circle radius is 1", ["radius", "circle", "tangent"]),
    "199": (" chord CD is 24", " chord CD is 10", ["chord", "CD", "24"]),
    "208": (" angle JMK is 55 degrees", " angle JMK is 20 degrees", ["JMK", "55", "angle"]),
    "214": (" angle FAB is 32 degrees", " angle FAB is 72 degrees", ["FAB", "32", "angle"]),
    "235": (" angle 3 is 110 degrees", " angle 3 is 55 degrees", ["angle 3", "110", "3"]),
    "257": (" segment ED is 5", " segment ED is 4", ["ED", "segment", "5"]),
    "265": (" angle 4 is 2x + 23", " angle 4 is 2x + 5", ["angle 4", "2x", "23"]),
    "267": (" arc AC is 122 degrees", " arc AC is 58 degrees", ["arc", "122", "AC"]),
    "268": (" segment NL is 5", " segment NL is 6", ["NL", "segment", "5"]),
    "278": (" segment W'W is 8", " segment W'W is 4", ["W'", "scale", "8"]),
    "282": (" the congruent chord expression is 2x + 14", " the congruent chord expression is 2x + 7", ["2x", "14", "chord"]),
    "283": (" half-chord FL is 24", " half-chord FL is 16", ["FL", "24", "chord"]),
    "296": (" the equilateral side is 2x + 11", " the equilateral side is 2x + 15", ["2x", "11", "equilateral"]),
    "297": (" angle 1 is 123 degrees", " angle 1 is 113 degrees", ["123", "angle 1", "14"]),
    "299": (" the hypotenuse is 20", " the hypotenuse is 10", ["hypotenuse", "20", "isosceles"]),
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def token_offsets(tokens: list[dict]) -> tuple[str, list[tuple[int, int]]]:
    pieces = [str(row["decoded_token"]) for row in tokens]
    text = "".join(pieces)
    offsets, cursor = [], 0
    for piece in pieces:
        offsets.append((cursor, cursor + len(piece)))
        cursor += len(piece)
    return text, offsets


def token_at_character(offsets: list[tuple[int, int]], character: int) -> int:
    for index, (start, end) in enumerate(offsets):
        if start <= character < end or (start == end == character):
            return index
    return len(offsets) - 1


def contexts(text: str, offsets: list[tuple[int, int]], terms: list[str]) -> list[dict]:
    found = []
    seen = set()
    for term in terms:
        for match in re.finditer(re.escape(term), text, flags=re.IGNORECASE):
            token = token_at_character(offsets, match.start())
            key = (token, match.group(0).lower())
            if key in seen:
                continue
            seen.add(key)
            found.append({
                "term": term,
                "matched_text": match.group(0),
                "token_index": token,
                "context": text[max(0, match.start() - 180) : min(len(text), match.end() + 260)].replace("\n", "\\n"),
            })
    return sorted(found, key=lambda row: (row["token_index"], row["term"]))


def main() -> None:
    source = OUT / "validation_cohort/completed_correct_pending_strict_ed.jsonl"
    rows = read_jsonl(source)
    if len(rows) < 12:
        raise RuntimeError("Fewer than 12 completed-correct rows; do not prepare a passing validation cohort")
    target = OUT / "validation_cohort/ed_audit_draft"
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"E_d audit draft already exists: {target}")
    ensure_directory(target)
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, local_files_only=True)
    drafts = []
    for row in rows:
        base = str(row["base_problem_id"])
        candidate_o, candidate_c, terms = SPECS[base]
        original_ids = tokenizer.encode(candidate_o, add_special_tokens=False)
        counter_ids = tokenizer.encode(candidate_c, add_special_tokens=False)
        common = longest_common_prefix(original_ids, counter_ids)
        if not common or len(common) == min(len(original_ids), len(counter_ids)):
            raise RuntimeError(f"Candidates for base {base} lack a meaningful divergent suffix")
        example_dir = ROOT / row["artifact_dir"]
        tokens = read_jsonl(example_dir / "tokens.jsonl")
        generation = json.loads((example_dir / "generation.json").read_text(encoding="utf-8"))
        ids = [int(item["token_id"]) for item in tokens]
        if ids != [int(value) for value in generation["generated_token_ids"]]:
            raise RuntimeError(f"Token artifact mismatch for base {base}")
        text, offsets = token_offsets(tokens)
        matches = contexts(text, offsets, terms)
        draft = {
            "base_problem_id": base,
            "example_id": str(row["example_id"]),
            "edit_version": row["edit_version"],
            "edit_metadata": row["edit_metadata"],
            "candidate_original": candidate_o,
            "candidate_counterfactual": candidate_c,
            "original_candidate_token_ids": original_ids,
            "counterfactual_candidate_token_ids": counter_ids,
            "common_prefix_token_ids": common,
            "common_prefix_text": tokenizer.decode(common, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "original_divergent_suffix_ids": original_ids[len(common):],
            "counterfactual_divergent_suffix_ids": counter_ids[len(common):],
            "original_divergent_suffix_text": tokenizer.decode(original_ids[len(common):], skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "counterfactual_divergent_suffix_text": tokenizer.decode(counter_ids[len(common):], skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "search_terms": terms,
            "search_matches": matches,
            "generated_token_count": len(tokens),
            "e0_start_token": None,
            "e1_completion_token": None,
            "semantic_decision_meaningful": None,
            "pre_ed_discriminative_content_absent": None,
            "manual_audit_status": "pending",
            "selection_used_attention": False,
            "causal_scores_inspected": False,
        }
        drafts.append(draft)
        lines = [
            f"# E_d audit draft — base {base}", "",
            f"- Original candidate: `{candidate_o}`",
            f"- Counterfactual candidate: `{candidate_c}`",
            f"- Shared candidate lead: `{draft['common_prefix_text']}`",
            f"- Original divergence: `{draft['original_divergent_suffix_text']}`",
            f"- Counterfactual divergence: `{draft['counterfactual_divergent_suffix_text']}`",
            "- Manual E0/E1 decision: **PENDING**", "", "## Search contexts", "",
        ]
        if not matches:
            lines.append("No configured keyword match; inspect the complete trace.")
        for match in matches:
            lines.extend([
                f"### token {match['token_index']} — `{match['matched_text']}` (term `{match['term']}`)", "",
                f"```text\n{match['context']}\n```", "",
            ])
        lines.extend(["## Complete trace", "", f"See `{example_dir.relative_to(ROOT) / 'generation.json'}`.", ""])
        write_text(target / f"base_{base}.md", "\n".join(lines))
    write_jsonl(target / "discriminative_event_draft.jsonl", drafts)
    print(json.dumps({"rows": len(drafts), "search_matches": sum(len(row["search_matches"]) for row in drafts)}, indent=2))


if __name__ == "__main__":
    main()
