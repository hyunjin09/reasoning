#!/usr/bin/env python3
"""Prepare score-blind strict-E_d drafts for the applicability repair expansion."""

from __future__ import annotations

import json
from pathlib import Path

from transformers import AutoTokenizer

from scripts.stage3b9.prepare_ed_audit_draft import candidate_rows, token_at, token_offsets
from visual_reasoning.stage0.io import ensure_directory, write_jsonl, write_text
from visual_reasoning.stage3b9.evidence import find_evidence_mentions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
CHECKPOINT = Path("/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    target = OUT / "evidence_audit/applicability_expansion_draft"
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"Expansion E_d draft already exists: {target}")
    rows = read_jsonl(OUT / "prospective_generation/applicability_expansion_completed_correct.jsonl")
    if not rows:
        raise RuntimeError("No completed-correct applicability expansion examples")
    ensure_directory(target)
    tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT, local_files_only=True)
    drafts = []
    for row in rows:
        base = str(row["base_problem_id"])
        metadata = read_json(ROOT / row["edit_metadata"])
        example_dir = ROOT / row["artifact_dir"]
        tokens = read_jsonl(example_dir / "tokens.jsonl")
        generation = read_json(example_dir / "generation.json")
        if [int(item["token_id"]) for item in tokens] != [int(value) for value in generation["generated_token_ids"]]:
            raise RuntimeError(f"Token/generation mismatch for base {base}")
        text, offsets = token_offsets(tokens)
        mentions = find_evidence_mentions(text, target=metadata["target"], original_value=metadata["original"])
        for mention in mentions:
            mention["token_index"] = token_at(offsets, mention["character_start"])
            mention["context"] = text[max(0, mention["character_start"] - 220):min(len(text), mention["character_end"] + 320)].replace("\n", "\\n")
        candidates = candidate_rows(tokenizer, metadata)
        draft = {
            "base_problem_id": base, "example_id": str(row["example_id"]), "phase": "phase_a",
            "target": metadata["target"], "original_value": metadata["original"],
            "counterfactual_values": [candidate["counterfactual_value"] for candidate in candidates],
            "edit_version": row["edit_version"], "edit_metadata": row["edit_metadata"],
            "candidate_pairs": candidates, "search_mentions": mentions,
            "score_blind_proposed_e0": min((int(mention["token_index"]) for mention in mentions), default=None),
            "generated_token_count": len(tokens), "generation_path": str((example_dir / "generation.json").relative_to(ROOT)),
            "e0_start_token": None, "e1_completion_token": None, "manual_audit_status": "pending",
            "selection_used_attention": False, "stage3b9_value_or_causal_scores_inspected": False,
            "stage3b9_subspace_fit_inspected": False,
        }
        drafts.append(draft)
        lines = [f"# Strict E_d audit — expansion base {base}", "", f"- Target/value: `{metadata['target']}` / `{metadata['original']}`",
                 f"- Search-only first match: `{draft['score_blind_proposed_e0']}`", "- Manual decision: **PENDING**", "", "## Candidate", "",
                 f"- Original: `{candidates[0]['candidate_original']}`", f"- Counterfactual: `{candidates[0]['candidate_counterfactual']}`", "", "## Search contexts", ""]
        for mention in mentions:
            lines.extend([f"### token {mention['token_index']} — `{mention['matched_text']}`", "", f"```text\n{mention['context']}\n```", ""])
        lines.extend(["## Complete trace", "", f"See `{draft['generation_path']}`.", ""])
        write_text(target / f"base_{base}.md", "\n".join(lines))
    drafts.sort(key=lambda row: int(row["base_problem_id"]))
    write_jsonl(target / "ed_audit_draft.jsonl", drafts)
    print(json.dumps({"drafts": len(drafts), "bases": [row["base_problem_id"] for row in drafts]}, indent=2))


if __name__ == "__main__":
    main()
