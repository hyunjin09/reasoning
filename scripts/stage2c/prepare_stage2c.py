#!/usr/bin/env python3
"""Prepare the attention-blind Stage 2C cohort and event/ROI annotations."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from visual_reasoning.stage2a.roi import map_boxes_to_visual_tokens, token_cell_box
from visual_reasoning.stage2c.temporal import attention_row_convention
from visual_reasoning.stage2c.validation import validate_event_annotation


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/stage2c"
STOPWORDS = {
    "the", "and", "with", "from", "into", "that", "this", "near", "approximately", "visible",
    "plotted", "graph", "figure", "line", "full", "relevant", "has", "have", "are", "its", "all",
}
EXISTING_READY = {
    "594", "699", "739", "764", "774", "2719", "2749", "2799", "2824", "2834", "2869",
    "3044", "3069", "3074", "3079", "3764",
}
EXISTING_EVENT_OVERRIDES = {
    ("2749", "A"): {"use_span_ids": [25]},
    ("2749", "B"): {"fact_span_ids": [45], "use_span_ids": [47]},
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def span_union(spans: list[dict], span_ids: list[int]) -> tuple[int, int, str]:
    ids = sorted({int(value) for value in span_ids})
    if not ids or ids[-1] >= len(spans):
        raise ValueError(f"invalid span ids {ids} for {len(spans)} spans")
    selected = [spans[index] for index in ids]
    return int(selected[0]["start_token"]), int(selected[-1]["end_token"]), " ".join(row["span_text"] for row in selected)


def contiguous_groups(span_ids: list[int]) -> list[list[int]]:
    ids = sorted({int(value) for value in span_ids})
    if not ids:
        return []
    groups = [[ids[0]]]
    for span_id in ids[1:]:
        if span_id == groups[-1][-1] + 1:
            groups[-1].append(span_id)
        else:
            groups.append([span_id])
    return groups


def evidence_stage_ids(annotation: dict, evidence: str) -> list[int]:
    return sorted(
        {
            int(span_id)
            for stage in annotation["reasoning_stages"]
            if stage["required_evidence"] == evidence
            for span_id in stage["span_ids"]
        }
    )


def first_use_group(spans: list[dict], groups: list[list[int]], e1: int) -> list[int]:
    for group in groups:
        if int(spans[group[0]]["start_token"]) > e1:
            return group
    raise ValueError("no downstream A+B use occurs after E1")


def content_terms(text: str) -> set[str]:
    terms = {term.lower() for term in re.findall(r"[A-Za-z][A-Za-z0-9()]*|\d+(?:\.\d+)?", text)}
    return {term for term in terms if (len(term) >= 3 or any(char.isdigit() for char in term)) and term not in STOPWORDS}


def automatic_repeated_groups(spans: list[dict], semantic_fact: str, e1: int, use_ids: set[int]) -> list[list[int]]:
    terms = content_terms(semantic_fact)
    numeric = {term for term in terms if any(char.isdigit() for char in term)}
    candidates: list[list[int]] = []
    for span in spans:
        span_id = int(span["span_id"])
        if span_id in use_ids or int(span["start_token"]) <= e1:
            continue
        text = span["span_text"].lower()
        hits = {term for term in terms if term in text}
        if len(hits) >= min(2, max(1, len(terms))) and (not numeric or numeric & hits):
            candidates.append([span_id])
        if len(candidates) >= 5:
            break
    return candidates


def event_record(
    example_id: str,
    evidence_id: str,
    semantic_fact: str,
    spans: list[dict],
    e0_ids: list[int],
    fact_ids: list[int],
    use_ids: list[int],
    repeated_groups: list[list[int]],
    annotation_source: str,
    confidence: str,
    notes: str,
) -> dict:
    e0_start, e0_end, e0_text = span_union(spans, e0_ids)
    fact_start, fact_end, fact_text = span_union(spans, fact_ids)
    use_start, use_end, use_text = span_union(spans, use_ids)
    repeated = []
    for group in repeated_groups:
        start, end, text = span_union(spans, group)
        if start > fact_end - 1:
            repeated.append({"span_ids": group, "start_token": start, "end_token": end, "text": text})
    row = {
        "example_id": example_id,
        "evidence_id": evidence_id,
        "semantic_fact": semantic_fact,
        "annotation_source": annotation_source,
        "annotation_confidence": confidence,
        "e0": {"span_ids": e0_ids, "start_token": e0_start, "end_token": e0_end, "text": e0_text},
        "e1": {
            "span_ids": fact_ids,
            "fact_start_token": fact_start,
            "completion_token": fact_end - 1,
            "end_token_exclusive": fact_end,
            "text": fact_text,
        },
        "e2": {"span_ids": use_ids, "start_token": use_start, "end_token": use_end, "text": use_text},
        "repeated_mentions": repeated,
        "scratchpad_boundary": {
            "pre_e1": [0, fact_end - 1],
            "post_e1_explicit_scratchpad": [fact_end, int(spans[-1]["end_token"])],
        },
        "notes": notes,
    }
    failures = validate_event_annotation(row, token_count=int(spans[-1]["end_token"]))
    if failures:
        raise ValueError(f"{evidence_id}: {'; '.join(failures)}")
    return row


def draw_roi_overlay(input_row: dict, boxes: list[list[int]], mapped: list[int], output: Path) -> None:
    image = Image.open(input_row["resolved_image_path"]).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    for index in mapped:
        draw.rectangle(
            token_cell_box(index, input_row["original_image_size"], input_row["visual_mapping"]["merged_grid_shape"]),
            fill=(0, 160, 90, 45), outline=(0, 120, 65, 150), width=1,
        )
    for box in boxes:
        draw.rectangle(tuple(box), outline=(230, 45, 45, 255), width=3)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(image, overlay).convert("RGB").save(output)


def draw_overlay_contacts(example_ids: list[str]) -> None:
    columns, cell_width, cell_height, per_page = 5, 300, 250, 10
    for page_start in range(0, len(example_ids), per_page):
        page = example_ids[page_start : page_start + per_page]
        canvas = Image.new("RGB", (columns * cell_width, 2 * cell_height), "white")
        draw = ImageDraw.Draw(canvas)
        for local, example_id in enumerate(page):
            row, column = divmod(local, columns)
            left, top = column * cell_width, row * cell_height
            image = Image.open(OUTPUT / f"annotations/roi_overlays/{example_id}.png").convert("RGB")
            image.thumbnail((cell_width - 16, cell_height - 38), Image.Resampling.LANCZOS)
            canvas.paste(image, (left + (cell_width - image.width) // 2, top + 28))
            draw.rectangle((left, top, left + cell_width - 1, top + cell_height - 1), outline=(130, 130, 130))
            draw.text((left + 8, top + 7), f"example {example_id}", fill="black")
        canvas.save(OUTPUT / f"annotations/roi_overlay_contact_{page_start // per_page:02d}.png")


def prepare_convention_audit(cohort: dict[str, dict]) -> None:
    example_id = "699"
    example = Path(cohort[example_id]["example_view"])
    input_row = read_json(example / "input.json")
    generation = read_json(example / "generation.json")
    tokens = read_jsonl(example / "tokens.jsonl")
    with np.load(example / "attention_summary.npz") as arrays:
        rows = attention_row_convention(
            arrays["query_lengths"], arrays["key_lengths"], int(input_row["prompt_token_count"]),
            generation["generated_token_ids"],
        )
        checked_index = 2
        checked = {
            **rows[checked_index],
            "example_id": example_id,
            "prompt_token_count": int(input_row["prompt_token_count"]),
            "context_generated_tokens_before_query": [tokens[0]["decoded_token"]],
            "query_token": tokens[1]["decoded_token"],
            "query_token_id": int(tokens[1]["token_id"]),
            "logits_next_token": tokens[2]["decoded_token"],
            "logits_next_token_id": int(tokens[2]["token_id"]),
            "recorded_top1_probability_for_generated_token": float(tokens[2]["top1_probability"]),
            "stored_visual_focus_shape": list(arrays["visual_focus"][checked_index].shape),
            "stored_modality_by_layer_shape": list(arrays["modality_by_layer"][checked_index].shape),
            "historical_row_label": "generated token y_t predicted by this forward",
            "actual_query": "generated token y_(t-1), except row 0 queries the final prompt token",
        }
        validation = {
            "all_rows_checked": len(rows),
            "expected_key_progression": [int(input_row["prompt_token_count"]), int(input_row["prompt_token_count"]) + len(rows) - 1],
            "observed_key_progression": [int(arrays["key_lengths"][0]), int(arrays["key_lengths"][-1])],
            "query_lengths_unique": sorted({int(value) for value in arrays["query_lengths"]}),
            "exact_convention": "row t is the final query row used to produce logits for y_t; row 0 queries the final prompt token and row t>0 queries y_(t-1)",
            "stage2c_primary_alignment": "prediction-aligned: retain historical row t at event coordinate y_t",
            "semantic_alignment_view": "processed-token: associate y_t with row t+1, because that is the first row whose query is y_t",
            "historical_arrays_modified": False,
        }
    write_json(OUTPUT / "convention_audit/attention_indexing_example.json", {"hand_checked_row": checked, "validation": validation})
    md = f"""# Attention Indexing Audit

Result: **verified from code and retained artifacts; no new inference was needed**.

`OnlineAttentionRecorder` stores the final query row of every generation forward. Stored row `t` produces the logits that select generated token `y_t`. At row 0 the query is the final prompt token. With cache enabled, row `t>0` has query token `y_(t-1)` and predicts `y_t`.

The historical Stage 1 token label therefore names the **next token predicted by that row**, not the token supplying its query. Stage 2C keeps row `t` prediction-aligned to `y_t` for the main acquisition-timing audit. A separate processed-token view shifts by one row (`y_t` uses row `t+1`) when testing mention/semantic alignment. Historical arrays were not changed.

Hand check: example `{example_id}`, stored row `{checked_index}`, prompt length `{checked['prompt_token_count']}`, key length `{checked['key_length']}`, query length `{checked['query_length']}`. The query is generated token index `{checked['query_generated_token_index']}` (`{checked['query_token']}`, id `{checked['query_token_id']}`), and its logits predict token index `{checked['predicted_generated_token_index']}` (`{checked['logits_next_token']}`, id `{checked['logits_next_token_id']}`). The stored row contains visual focus shape `{checked['stored_visual_focus_shape']}` and modality-by-layer shape `{checked['stored_modality_by_layer_shape']}`.

This convention resolves indexing only. It does not make attention causal evidence.
"""
    (OUTPUT / "convention_audit/attention_indexing_audit.md").write_text(md, encoding="utf-8")


def main() -> None:
    cohort_rows = read_jsonl(ROOT / "outputs/stage1/discovery/cohort_manifest.jsonl")
    cohort = {str(row["example_id"]): row for row in cohort_rows}
    seed = read_json(ROOT / "scripts/stage2c/annotation_seed.json")
    stage2a = read_jsonl(ROOT / "outputs/stage2a/evidence_subset/evidence_annotations.jsonl")
    stage2a_by_id = {str(row["example_id"]): row for row in stage2a}
    new_by_id = {str(row["example_id"]): row for row in seed["new_examples"]}
    manual_review_path = OUTPUT / "annotations/manual_roi_mapping_review.json"
    manual_reviews = read_json(manual_review_path)["examples"] if manual_review_path.exists() else {}
    target_ids = list(stage2a_by_id) + list(new_by_id)
    if len(target_ids) != 50 or len(set(target_ids)) != 50:
        raise ValueError("Stage 2C must freeze exactly 50 unique examples")

    event_rows: list[dict] = []
    roi_rows: list[dict] = []
    manifest_rows: list[dict] = []
    for example_id in target_ids:
        source_row = cohort[example_id]
        example = Path(source_row["example_view"])
        input_row = read_json(example / "input.json")
        spans = read_json(example / "spans.json")
        with np.load(example / "attention_summary.npz") as arrays:
            visual_count = int(arrays["visual_focus"].shape[1])
        evidence_count = 0
        if example_id in stage2a_by_id:
            annotation = stage2a_by_id[example_id]
            for label in ("A", "B"):
                fact = annotation[f"evidence_{label}"]
                specific = evidence_stage_ids(annotation, label)
                first_group = contiguous_groups(specific)[0]
                override = EXISTING_EVENT_OVERRIDES.get((example_id, label), {})
                first_group = override.get("fact_span_ids", first_group)
                _, fact_end, _ = span_union(spans, first_group)
                uses = override.get("use_span_ids")
                if uses is None:
                    uses = first_use_group(spans, contiguous_groups(evidence_stage_ids(annotation, "A+B")), fact_end - 1)
                later_groups = contiguous_groups([span_id for span_id in specific if span_id > first_group[-1]])
                event_rows.append(
                    event_record(
                        example_id, f"{example_id}:{label}", fact["semantic_fact"], spans,
                        [first_group[0]], first_group, uses, later_groups,
                        "reused Stage 2A manually curated reasoning-stage annotation",
                        annotation["notes"]["annotation_confidence"], annotation["notes"].get("ambiguity", ""),
                    )
                )
                roi_rows.append(
                    {
                        "example_id": example_id,
                        "evidence_id": f"{example_id}:{label}",
                        "semantic_fact": fact["semantic_fact"],
                        "roi_image_coordinates": fact["ROI_image_coordinates"],
                        "roi_visual_focus_column_indices": fact["ROI_visual_focus_column_indices"],
                        "roi_visual_token_indices": fact["ROI_visual_token_indices"],
                        "roi_visual_token_count": fact["ROI_visual_token_count"],
                        "mapping_source": "frozen Stage 2A mapping reused unchanged",
                        "manual_mapping_review": annotation["ROI_mapping_validation"],
                        "possible_text_shortcut": annotation["notes"].get("possible_text_shortcut", "unknown"),
                        "counterfactual_ready": example_id in EXISTING_READY,
                        "plausible_edit": "localized numeric/shape edit" if example_id in EXISTING_READY else "not retained after editability/leakage screen",
                    }
                )
                evidence_count += 1
        else:
            spec = new_by_id[example_id]
            mapped = map_boxes_to_visual_tokens(
                spec["roi_boxes"], input_row["original_image_size"], input_row["visual_mapping"]["merged_grid_shape"]
            )
            absolute = [int(input_row["visual_token_indices"][index]) for index in mapped]
            _, fact_end, _ = span_union(spans, spec["fact_span_ids"])
            repeated = automatic_repeated_groups(spans, spec["semantic_fact"], fact_end - 1, set(spec["use_span_ids"]))
            event_rows.append(
                event_record(
                    example_id, f"{example_id}:A", spec["semantic_fact"], spans,
                    spec["e0_span_ids"], spec["fact_span_ids"], spec["use_span_ids"], repeated,
                    "Stage 2C manual text/image annotation completed before ROI-attention inspection",
                    spec["confidence"], spec["notes"],
                )
            )
            roi_rows.append(
                {
                    "example_id": example_id,
                    "evidence_id": f"{example_id}:A",
                    "semantic_fact": spec["semantic_fact"],
                    "roi_image_coordinates": spec["roi_boxes"],
                    "roi_visual_focus_column_indices": mapped,
                    "roi_visual_token_indices": absolute,
                    "roi_visual_token_count": len(mapped),
                    "mapping_source": "Stage 2C original-image boxes mapped by token-cell centers",
                    "manual_mapping_review": manual_reviews.get(
                        example_id, {"status": "pending", "notes": "generated overlay awaiting manual inspection"}
                    ),
                    "possible_text_shortcut": spec["possible_text_shortcut"],
                    "counterfactual_ready": bool(spec["counterfactual_ready"]),
                    "plausible_edit": spec["plausible_edit"],
                }
            )
            draw_roi_overlay(
                input_row, spec["roi_boxes"], mapped,
                OUTPUT / f"annotations/roi_overlays/{example_id}.png",
            )
            evidence_count = 1
        manifest_rows.append(
            {
                "example_id": example_id,
                "base_problem_id": str(source_row["base_problem_id"]),
                "variant": source_row["variant"],
                "subject": source_row["subject"],
                "completed": bool(source_row["completed"]),
                "correct": bool(source_row["correct"]),
                "reasoning_length": int(source_row["reasoning_length"]),
                "evidence_item_count": evidence_count,
                "selection_source": "Stage 2A reuse" if example_id in stage2a_by_id else "Stage 2C attention-blind screen",
                "selection_was_attention_blind": True,
                "artifact_view": source_row["example_view"],
                "visual_token_count": visual_count,
            }
        )

    write_jsonl(OUTPUT / "cohort/cohort_manifest.jsonl", manifest_rows)
    write_jsonl(
        OUTPUT / "cohort/exclusion_log.jsonl",
        [
            {
                **row,
                "selection_stage": "Stage 2C pre-attention screen",
                "attention_inspected_before_exclusion": False,
            }
            for row in seed["screened_exclusions"]
        ],
    )
    write_jsonl(OUTPUT / "annotations/evidence_event_annotations.jsonl", event_rows)
    write_jsonl(OUTPUT / "annotations/roi_annotations.jsonl", roi_rows)
    repeated_rows = [
        {
            "example_id": row["example_id"], "evidence_id": row["evidence_id"],
            "mention_index": index, **mention,
        }
        for row in event_rows
        for index, mention in enumerate(row["repeated_mentions"])
    ]
    write_jsonl(OUTPUT / "annotations/repeated_mentions.jsonl", repeated_rows)
    draw_overlay_contacts(list(new_by_id))

    review_lines = [
        "# Evidence Event Annotation Review", "",
        "All E0/E1/E2 rows below were produced from manually selected semantic spans before ROI-attention curves were inspected.", "",
    ]
    for row in event_rows:
        review_lines.extend(
            [
                f"## {row['evidence_id']} — {row['semantic_fact']}", "",
                f"- E0 `{row['e0']['start_token']}:{row['e0']['end_token']}`: {row['e0']['text']}",
                f"- E1 completion `{row['e1']['completion_token']}`: {row['e1']['text']}",
                f"- E2 `{row['e2']['start_token']}:{row['e2']['end_token']}`: {row['e2']['text']}",
                f"- Repeated references retained: {len(row['repeated_mentions'])}", "",
            ]
        )
    (OUTPUT / "annotations/manual_event_annotation_review.md").write_text("\n".join(review_lines) + "\n", encoding="utf-8")
    prepare_convention_audit(cohort)
    print(json.dumps({"examples": len(manifest_rows), "evidence_items": len(event_rows), "repeated_mentions": len(repeated_rows)}, indent=2))


if __name__ == "__main__":
    main()
