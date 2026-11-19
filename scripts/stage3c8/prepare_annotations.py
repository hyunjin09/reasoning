#!/usr/bin/env python3
"""Freeze token/span annotations before any Stage 3C8 carrier score exists."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from transformers import AutoProcessor

from run_phase_a import ROOT, assets, coordinates, read_json, read_jsonl
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3c8.annotations import annotate_token_sequence


OUT = ROOT / "outputs/stage3c8"
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifests", type=Path, nargs="+", required=True)
    parser.add_argument("--visual-entity-lexicon", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    return parser.parse_args()


def consecutive_runs(positions: list[int]) -> list[list[int]]:
    result: list[list[int]] = []
    for position in sorted(positions):
        if not result or position != result[-1][-1] + 1:
            result.append([position])
        else:
            result[-1].append(position)
    return result


def attach_span_fields(
    spans: list[dict[str, Any]], *, base: str, coordinate: str, stream: str,
    absolute_positions: list[int], generated: bool,
) -> list[dict[str, Any]]:
    result = []
    for span in spans:
        members = [int(value) for value in span["constituent_positions"]]
        row = {
            **span,
            "span_id": f"{stream}:{coordinate}:{span['span_id']}:{absolute_positions[members[0]]}",
            "base_problem_id": base,
            "coordinate": coordinate,
            "stream": stream,
            "absolute_positions": [absolute_positions[index] for index in members],
            "annotation_used_attention": False,
            "causal_scores_available_at_freeze": False,
        }
        if generated:
            row["generated_indices"] = [index + 1 for index in members]
        result.append(row)
    return result


def main() -> None:
    args = parse_args()
    targets = [
        OUT / "annotations/per_token_annotations.jsonl",
        OUT / "annotations/lexical_spans.jsonl",
        OUT / "annotations/visual_alignment_annotations.jsonl",
        OUT / "annotations/reasoning_role_annotations.jsonl",
        OUT / "audit/tokenizer_span_audit.json",
    ]
    if any(path.exists() for path in targets):
        raise FileExistsError("Frozen Stage 3C8 annotations already exist")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for manifest_path in args.manifests:
        for item in read_jsonl(manifest_path):
            base = str(item["base_problem_id"])
            if base in seen:
                raise RuntimeError(f"Duplicate annotated base {base}")
            seen.add(base)
            item = {**item, "annotation_cohort_role": str(item.get("cohort_role") or manifest_path.stem)}
            items.append(item)
    lexicon = {str(row["base_problem_id"]): row for row in read_jsonl(args.visual_entity_lexicon)}
    if set(lexicon) != seen:
        raise RuntimeError("Manual visual-entity lexicon must exactly cover annotated bases")
    for base, row in lexicon.items():
        if row.get("manual_review_status") != "pass" or row.get("attention_used") is not False:
            raise RuntimeError(f"Manual visual-entity lexicon is not frozen for base {base}")
    old_events = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")}
    old_rois = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")}
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    processor = AutoProcessor.from_pretrained(args.model_checkpoint, local_files_only=True)
    tokenizer = processor.tokenizer
    token_rows: list[dict[str, Any]] = []
    span_rows: list[dict[str, Any]] = []
    entity_audit: list[dict[str, Any]] = []
    prompt_coverage, reasoning_coverage = [], []
    frozen_at = datetime.now(timezone.utc).isoformat()
    for item in items:
        base = str(item["base_problem_id"])
        mode = "fresh" if item.get("edit_metadata") else ("historical" if item["annotation_cohort_role"].startswith("historical") else "validation")
        edit, event, _ = assets(item, old_events, old_rois)
        row = dataset[str(item["example_id"])]
        prepared, metadata = prepare_custom_image(
            processor, row, ROOT / edit["paths"]["O"], device="cpu"
        )
        del prepared
        prompt_ids = [int(value) for value in metadata["prompt_token_ids"]]
        question_ids = tokenizer.encode(str(row.get("query_cot") or row.get("question") or ""), add_special_tokens=False)
        groups = build_token_groups(
            prompt_token_ids=prompt_ids,
            visual_token_indices=metadata["visual_token_indices"],
            question_token_ids=question_ids,
        )
        lexical = lexicon[base]
        visual_entities = {str(value).lower() for value in lexical["visual_entities"]}
        target_terms = {str(value).lower() for value in lexical["target_aligned_terms"]}
        mention_terms = {str(value).lower() for value in lexical["mention_aligned_terms"]}
        entity_audit.append({
            "base_problem_id": base,
            "cohort_role": mode,
            "manual_entity_source": str(args.visual_entity_lexicon.resolve()),
            "visual_entity_terms": sorted(visual_entities),
            "target_alignment_terms": sorted(target_terms),
            "mention_alignment_terms": sorted(mention_terms),
            "source_is_attention": False,
            "manual_review_status": "pass",
            "causal_scores_available_at_freeze": False,
        })

        q_positions = [int(value) for value in groups["Q"]]
        q_ids = [prompt_ids[position] for position in q_positions]
        q_texts = [tokenizer.decode([token_id], skip_special_tokens=False, clean_up_tokenization_spaces=False) for token_id in q_ids]
        q_tokens, q_spans = annotate_token_sequence(
            token_ids=q_ids,
            token_texts=q_texts,
            stream="PROMPT_QUESTION",
            visual_entities=visual_entities,
            target_entities=target_terms,
            mention_entities=mention_terms,
            absolute_offset=q_positions[0],
        )
        if q_positions != list(range(q_positions[0], q_positions[-1] + 1)):
            raise RuntimeError(f"Question positions are not contiguous for base {base}")
        for token, absolute in zip(q_tokens, q_positions):
            token_rows.append({
                **token,
                "base_problem_id": base,
                "coordinate": "prefill",
                "absolute_sequence_position": absolute,
                "cohort_role": mode,
                "frozen_at": frozen_at,
                "causal_scores_available_at_freeze": False,
            })
        span_rows.extend(attach_span_fields(
            q_spans,
            base=base,
            coordinate="prefill",
            stream="PROMPT_QUESTION",
            absolute_positions=q_positions,
            generated=False,
        ))
        special_positions = sorted(set(groups["P_post_image"]) - set(q_positions))
        for run_number, run in enumerate(consecutive_runs(special_positions)):
            ids = [prompt_ids[position] for position in run]
            texts = [tokenizer.decode([token_id], skip_special_tokens=False, clean_up_tokenization_spaces=False) for token_id in ids]
            special_tokens, special_spans = annotate_token_sequence(
                token_ids=ids,
                token_texts=texts,
                stream="SPECIAL_CONTROL",
                absolute_offset=run[0],
            )
            for token, absolute in zip(special_tokens, run):
                token_rows.append({
                    **token,
                    "base_problem_id": base,
                    "coordinate": "prefill",
                    "absolute_sequence_position": absolute,
                    "cohort_role": mode,
                    "frozen_at": frozen_at,
                    "causal_scores_available_at_freeze": False,
                })
            span_rows.extend(attach_span_fields(
                special_spans,
                base=base,
                coordinate=f"prefill_control_{run_number}",
                stream="SPECIAL_CONTROL",
                absolute_positions=run,
                generated=False,
            ))
        prompt_coverage.append({
            "base_problem_id": base,
            "eligible_count": len(groups["P_post_image"]),
            "question_count": len(q_positions),
            "special_control_count": len(special_positions),
            "exact": len(groups["P_post_image"]) == len(q_positions) + len(special_positions),
        })

        history = [int(value) for value in event["history_before_ed_token_ids"]]
        for coordinate, current in coordinates(item, event, mode):
            ids = history[:current]
            texts = [tokenizer.decode([token_id], skip_special_tokens=False, clean_up_tokenization_spaces=False) for token_id in ids]
            absolute_offset = len(prompt_ids)
            current_absolute = len(prompt_ids) + current - 1
            reasoning_tokens, reasoning_spans = annotate_token_sequence(
                token_ids=ids,
                token_texts=texts,
                stream="PREVIOUS_REASONING",
                visual_entities=visual_entities,
                target_entities=target_terms,
                mention_entities=mention_terms,
                absolute_offset=absolute_offset,
                target_position=current_absolute,
            )
            for generated_index, token in enumerate(reasoning_tokens, start=1):
                token_rows.append({
                    **token,
                    "base_problem_id": base,
                    "coordinate": coordinate,
                    "generated_index": generated_index,
                    "cohort_role": mode,
                    "frozen_at": frozen_at,
                    "causal_scores_available_at_freeze": False,
                })
            span_rows.extend(attach_span_fields(
                reasoning_spans,
                base=base,
                coordinate=coordinate,
                stream="PREVIOUS_REASONING",
                absolute_positions=list(range(absolute_offset, absolute_offset + len(ids))),
                generated=True,
            ))
            reasoning_coverage.append({
                "base_problem_id": base,
                "coordinate": coordinate,
                "expected_tokens": current,
                "annotated_tokens": len(reasoning_tokens),
                "exact": current == len(reasoning_tokens),
            })
    token_rows.sort(key=lambda row: (int(row["base_problem_id"]), row["coordinate"], int(row["absolute_sequence_position"]), row["stream"]))
    span_rows.sort(key=lambda row: (int(row["base_problem_id"]), row["coordinate"], int(row["absolute_positions"][0]), row["stream"]))
    write_jsonl(targets[0], token_rows)
    write_jsonl(targets[1], span_rows)
    write_jsonl(targets[2], entity_audit)
    write_jsonl(targets[3], [row for row in token_rows if row["stream"] == "PREVIOUS_REASONING"])
    write_json(targets[4], {
        "status": "PASS" if all(row["exact"] for row in prompt_coverage + reasoning_coverage) else "FAIL",
        "frozen_at": frozen_at,
        "base_count": len(items),
        "token_count": len(token_rows),
        "span_count": len(span_rows),
        "prompt_coverage": prompt_coverage,
        "reasoning_coverage": reasoning_coverage,
        "annotation_used_attention": False,
        "causal_scores_available_at_freeze": False,
    })
    print(json.dumps({"bases": len(items), "tokens": len(token_rows), "spans": len(span_rows)}, indent=2))


if __name__ == "__main__":
    main()
