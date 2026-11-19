#!/usr/bin/env python3
"""Prepare token-indexed, score-blind E_d audit drafts for discovery candidates."""

from __future__ import annotations

import json
import re
from pathlib import Path

from transformers import AutoTokenizer

from visual_reasoning.stage0.io import ensure_directory, write_jsonl, write_text
from visual_reasoning.stage3b2.annotations import longest_common_prefix


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"
CHECKPOINT = Path("/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e")


SPECS = {
    "302": (" total segment GJ is 8", " total segment GJ is 16", ["GJ", "8", "segment"]),
    "303": (" angle B is 3x + 40 degrees", " angle B is 3x + 36 degrees", ["3x", "40", "angle B"]),
    "309": (" the equilateral side is x + 9", " the equilateral side is x + 6", ["x + 9", "equilateral", "side"]),
    "312": (" the left triangle angle is 36 degrees", " the left triangle angle is 40 degrees", ["36", "angle", "triangle"]),
    "314": (" angle M is 80 degrees", " angle M is 120 degrees", ["80", "angle M", "trapezoid"]),
    "319": (" the blue rhombus area is 36 square yards", " the blue rhombus area is 72 square yards", ["36", "blue", "rhombus"]),
    "322": (" segment MQ is 2x + 2", " segment MQ is 2x + 0", ["2x + 2", "MQ", "distance"]),
    "324": (" the circumradius is 6 cm", " the circumradius is 3 cm", ["6 cm", "radius", "octagon"]),
    "325": (" the included angle is 45 degrees", " the included angle is 30 degrees", ["45", "angle", "parallelogram"]),
    "332": (" the bearing offset is 50 degrees", " the bearing offset is 40 degrees", ["50", "bearing", "south"]),
    "334": (" the bearing offset is 28 degrees", " the bearing offset is 38 degrees", ["28", "bearing", "east"]),
    "361": (" the observer separation is 29 m", " the observer separation is 39 m", ["29", "observer", "separation"]),
    "362": (" the aircraft altitude is 12 m", " the aircraft altitude is 18 m", ["12", "altitude", "aircraft"]),
    "363": (" the left flag pole is 13 m high", " the left flag pole is 10 m high", ["13", "flag", "post"]),
    "364": (" the tower height is 35.5 m", " the tower height is 45.5 m", ["35.5", "height", "tower"]),
    "365": (" the aircraft altitude is 10369 m", " the aircraft altitude is 12000 m", ["10369", "altitude", "aircraft"]),
    "366": (" the longer sight line is 37 m", " the longer sight line is 40 m", ["37", "sight", "lighthouse"]),
    "367": (" the base width is 10.6 m", " the base width is 12 m", ["10.6", "base", "mountain"]),
    "371": (" the short leg is 11", " the short leg is 8", ["11", "leg", "triangle"]),
    "373": (" the side opposite 30 degrees is 8.5", " the side opposite 30 degrees is 6", ["8.5", "opposite", "30"]),
    "377": (" the hypotenuse is 9", " the hypotenuse is 12", ["9", "hypotenuse", "triangle"]),
    "379": (" the slanted side is 8", " the slanted side is 6", ["8", "slanted", "30"]),
    "387": (" the circle radius is 8 cm", " the circle radius is 12 cm", ["8 cm", "radius", "circle"]),
    "389": (" the circle diameter is 13 cm", " the circle diameter is 16 cm", ["13 cm", "diameter", "circle"]),
    "390": (" the circumference is 44 cm", " the circumference is 66 cm", ["44 cm", "circumference", "circle"]),
    "392": (" the sector radius is 10 mm", " the sector radius is 12 mm", ["10 mm", "radius", "sector"]),
    "393": (" the circle radius is 6 cm", " the circle radius is 8 cm", ["6 cm", "radius", "circle"]),
    "394": (" the sector radius is 2 cm", " the sector radius is 4 cm", ["2 cm", "radius", "sector"]),
    "395": (" the circle radius is 3 cm", " the circle radius is 5 cm", ["3 cm", "radius", "circle"]),
    "396": (" the circle radius is 11 cm", " the circle radius is 7 cm", ["11 cm", "radius", "circle"]),
    "397": (" the circle radius is 50 cm", " the circle radius is 25 cm", ["50 cm", "radius", "circle"]),
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
        if start <= character < end or start == end == character:
            return index
    return len(offsets) - 1


def contexts(text: str, offsets: list[tuple[int, int]], terms: list[str]) -> list[dict]:
    found, seen = [], set()
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
                "context": text[max(0, match.start() - 180):min(len(text), match.end() + 260)].replace("\n", "\\n"),
            })
    return sorted(found, key=lambda row: (row["token_index"], row["term"]))


def main() -> None:
    rows = read_jsonl(OUT / "completed_correct_pending_strict_ed.jsonl")
    if len(rows) < 16:
        raise RuntimeError("Fewer than 16 completed-correct discovery candidates")
    target = OUT / "ed_audit_draft"
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
            raise RuntimeError(f"Candidates for base {base} lack a divergent suffix")
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
            "ed_generated_index": None,
            "semantic_decision_meaningful": None,
            "pre_ed_discriminative_content_absent": None,
            "manual_audit_status": "pending",
            "selection_used_attention": False,
            "stage3b8_causal_or_fit_scores_inspected": False,
        }
        drafts.append(draft)
        lines = [
            f"# E_d audit draft — base {base}", "",
            f"- Original candidate: `{candidate_o}`",
            f"- Counterfactual candidate: `{candidate_c}`",
            f"- Shared candidate lead: `{draft['common_prefix_text']}`",
            f"- Original divergence: `{draft['original_divergent_suffix_text']}`",
            f"- Counterfactual divergence: `{draft['counterfactual_divergent_suffix_text']}`",
            "- Manual E_d decision: **PENDING**", "", "## Search contexts", "",
        ]
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
