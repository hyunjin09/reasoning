#!/usr/bin/env python3
"""Prepare score-, fit-, and attention-blind strict E_d audit drafts."""

from __future__ import annotations

import json
from pathlib import Path

from transformers import AutoTokenizer

from visual_reasoning.stage0.io import ensure_directory, write_jsonl, write_text
from visual_reasoning.stage3b2.annotations import longest_common_prefix
from visual_reasoning.stage3b9.evidence import build_candidate_text, find_evidence_mentions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
CHECKPOINT = Path("/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def token_at(offsets: list[tuple[int, int]], character: int) -> int:
    for index, (start, end) in enumerate(offsets):
        if start <= character < end or start == end == character:
            return index
    return len(offsets) - 1


def candidate_rows(tokenizer, metadata: dict) -> list[dict]:
    original = str(metadata["original"])
    values = [str(metadata["counterfactual"])] if metadata["phase"] == "phase_a" else [str(value) for value in metadata["alternatives"]]
    rows = []
    for index, value in enumerate(values, start=1):
        original_text = build_candidate_text(metadata["target"], original, metadata["render_suffix"])
        counterfactual_text = build_candidate_text(metadata["target"], value, metadata["render_suffix"])
        original_ids = tokenizer.encode(original_text, add_special_tokens=False)
        counterfactual_ids = tokenizer.encode(counterfactual_text, add_special_tokens=False)
        common = longest_common_prefix(original_ids, counterfactual_ids)
        if not common or len(common) == min(len(original_ids), len(counterfactual_ids)):
            raise RuntimeError(f"Candidates do not define a divergent suffix for base {metadata['base_problem_id']}")
        rows.append({
            "pair_id": "semantic" if metadata["phase"] == "phase_a" else f"value_{index}",
            "counterfactual_condition": "C" if metadata["phase"] == "phase_a" else f"C{index}",
            "counterfactual_value": value,
            "candidate_original": original_text,
            "candidate_counterfactual": counterfactual_text,
            "original_candidate_token_ids": original_ids,
            "counterfactual_candidate_token_ids": counterfactual_ids,
            "common_prefix_token_ids": common,
            "common_prefix_text": tokenizer.decode(common, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "original_divergent_suffix_ids": original_ids[len(common):],
            "counterfactual_divergent_suffix_ids": counterfactual_ids[len(common):],
            "original_divergent_suffix_text": tokenizer.decode(original_ids[len(common):], skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "counterfactual_divergent_suffix_text": tokenizer.decode(counterfactual_ids[len(common):], skip_special_tokens=False, clean_up_tokenization_spaces=False),
        })
    return rows


def main() -> None:
    target = OUT / "evidence_audit/draft_v2"
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"E_d draft already exists: {target}")
    ensure_directory(target)
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, local_files_only=True)
    drafts = []
    for phase in ("phase_a", "phase_b"):
        rows = read_jsonl(OUT / f"prospective_generation/{phase}_completed_correct_pool.jsonl")
        for row in rows:
            base = str(row["base_problem_id"])
            metadata = read_json(ROOT / row["edit_metadata"])
            example_dir = ROOT / row["artifact_dir"]
            tokens = read_jsonl(example_dir / "tokens.jsonl")
            generation = read_json(example_dir / "generation.json")
            generated_ids = [int(value) for value in generation["generated_token_ids"]]
            if generated_ids != [int(item["token_id"]) for item in tokens]:
                raise RuntimeError(f"Token/generation mismatch for base {base}")
            text, offsets = token_offsets(tokens)
            mentions = find_evidence_mentions(text, target=metadata["target"], original_value=metadata["original"])
            for mention in mentions:
                mention["token_index"] = token_at(offsets, mention["character_start"])
                mention["context"] = text[max(0, mention["character_start"] - 180):min(len(text), mention["character_end"] + 260)].replace("\n", "\\n")
            candidates = candidate_rows(tokenizer, metadata)
            proposed_e0 = min((int(mention["token_index"]) for mention in mentions), default=None)
            draft = {
                "base_problem_id": base,
                "example_id": str(row["example_id"]),
                "phase": phase,
                "target": metadata["target"],
                "original_value": metadata["original"],
                "counterfactual_values": [candidate["counterfactual_value"] for candidate in candidates],
                "edit_version": row["edit_version"],
                "edit_metadata": row["edit_metadata"],
                "candidate_pairs": candidates,
                "search_mentions": mentions,
                "score_blind_proposed_e0": proposed_e0,
                "generated_token_count": len(tokens),
                "generation_path": str((example_dir / "generation.json").relative_to(ROOT)),
                "e0_start_token": None,
                "e1_completion_token": None,
                "manual_audit_status": "pending",
                "selection_used_attention": False,
                "stage3b9_value_or_causal_scores_inspected": False,
                "stage3b9_subspace_fit_inspected": False,
            }
            drafts.append(draft)
            lines = [
                f"# Strict E_d audit — base {base}", "",
                f"- Phase: `{phase}`",
                f"- Target: `{metadata['target']}`",
                f"- Original value: `{metadata['original']}`",
                f"- Proposed E0 (search only): `{proposed_e0}`",
                "- Manual decision: **PENDING**", "", "## Frozen candidate pairs", "",
            ]
            for candidate in candidates:
                lines.extend([
                    f"### {candidate['pair_id']}", "",
                    f"- Original: `{candidate['candidate_original']}`",
                    f"- Counterfactual: `{candidate['candidate_counterfactual']}`",
                    f"- Shared lead: `{candidate['common_prefix_text']}`",
                    f"- Divergence: `{candidate['original_divergent_suffix_text']}` vs `{candidate['counterfactual_divergent_suffix_text']}`", "",
                ])
            lines.extend(["## Search contexts", ""])
            for mention in mentions:
                lines.extend([
                    f"### token {mention['token_index']} — `{mention['matched_text']}` (term `{mention['term']}`)", "",
                    f"```text\n{mention['context']}\n```", "",
                ])
            lines.extend(["## Complete trace", "", f"See `{draft['generation_path']}`.", ""])
            write_text(target / f"base_{base}.md", "\n".join(lines))
    drafts.sort(key=lambda row: (row["phase"], int(row["base_problem_id"])))
    write_jsonl(target / "ed_audit_draft.jsonl", drafts)
    print(json.dumps({"drafts": len(drafts), "phase_a": sum(row['phase'] == 'phase_a' for row in drafts), "phase_b": sum(row['phase'] == 'phase_b' for row in drafts)}, indent=2))


if __name__ == "__main__":
    main()
