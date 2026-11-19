#!/usr/bin/env python3
"""Run Stage 2A evidence-ROI analysis using retained Stage 1 arrays only."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage2a.roi import (
    classify_shift,
    map_boxes_to_visual_tokens,
    roi_curves,
    span_means,
    token_cell_box,
)


COLORS = {"A": (220, 45, 45), "B": (35, 95, 220)}


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def draw_mapping(image_path: str, input_row: dict, specs: dict, mapped: dict, output_path: Path) -> None:
    image = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    grid = input_row["visual_mapping"]["merged_grid_shape"]
    size = input_row["original_image_size"]
    for key in ("A", "B"):
        color = COLORS[key]
        for idx in mapped[key]:
            draw.rectangle(token_cell_box(idx, size, grid), fill=(*color, 38), outline=(*color, 130), width=1)
        for box in specs[f"evidence_{key}"]["boxes"]:
            draw.rectangle(tuple(box), outline=(*color, 255), width=3)
        first = specs[f"evidence_{key}"]["boxes"][0]
        draw.text((first[0] + 3, first[1] + 3), key, fill=(*color, 255), stroke_width=1, stroke_fill=(255, 255, 255, 255))
    Image.alpha_composite(image, overlay).convert("RGB").save(output_path)


def stage_span_ids(spec: dict, requirement: str) -> list[int]:
    return sorted({sid for stage in spec["reasoning_stages"] if stage["required_evidence"] == requirement for sid in stage["span_ids"]})


def valid_span_ids(ids: list[int], span_count: int, example_id: str) -> list[int]:
    invalid = [sid for sid in ids if not 0 <= sid < span_count]
    if invalid:
        raise ValueError(f"example {example_id}: invalid span ids {invalid}")
    return ids


def contiguous_windows(span_ids: list[int], ranges: np.ndarray) -> list[dict]:
    if not span_ids:
        return []
    groups: list[list[int]] = [[span_ids[0]]]
    for sid in span_ids[1:]:
        if sid == groups[-1][-1] + 1:
            groups[-1].append(sid)
        else:
            groups.append([sid])
    return [
        {
            "start_span": group[0], "end_span_exclusive": group[-1] + 1,
            "start_token": int(ranges[group[0], 0]), "end_token": int(ranges[group[-1], 1]),
        }
        for group in groups
    ]


def plot_lines(draw: ImageDraw.ImageDraw, box, series: dict[str, np.ndarray], title: str) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, outline=(90, 90, 90), width=1)
    draw.text((x0 + 5, y0 + 4), title, fill=(0, 0, 0))
    finite = np.concatenate([np.asarray(v, dtype=float)[np.isfinite(v)] for v in series.values()])
    ymax = max(float(finite.max()) if finite.size else 0.0, 1e-12)
    for label, values in series.items():
        values = np.asarray(values, dtype=float)
        if values.size < 2:
            continue
        color = COLORS[label]
        points = []
        for i, value in enumerate(values):
            x = x0 + i * (x1 - x0) / (values.size - 1)
            y = y1 - max(0.0, float(value)) / ymax * (y1 - y0 - 22)
            points.append((x, y))
        draw.line(points, fill=color, width=2)
    draw.text((x1 - 155, y0 + 4), f"max={ymax:.3g}", fill=(80, 80, 80))


def draw_timeline(output_path: Path, example_id: str, token: dict, span: dict, classification: str) -> None:
    canvas = Image.new("RGB", (1100, 720), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 10), f"Example {example_id} | descriptive evidence ROI curves | {classification}", fill="black")
    draw.line((805, 18, 835, 18), fill=COLORS["A"], width=3)
    draw.text((840, 10), "Evidence A", fill="black")
    draw.line((940, 18, 970, 18), fill=COLORS["B"], width=3)
    draw.text((975, 10), "Evidence B", fill="black")
    plot_lines(draw, (50, 55, 1050, 245), {"A": token["A"]["raw_mass"], "B": token["B"]["raw_mass"]}, "Token-level raw ROI attention mass")
    plot_lines(draw, (50, 275, 1050, 465), {"A": token["A"]["density"], "B": token["B"]["density"]}, "Token-level per-ROI-token density")
    plot_lines(draw, (50, 495, 1050, 685), {"A": span["A"]["conditional_share"], "B": span["B"]["conditional_share"]}, "Span-level share of visual attention (conditional on visual source)")
    canvas.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default="scripts/stage2a/evidence_annotations_seed.json")
    parser.add_argument("--cohort", default="outputs/stage1/discovery/cohort_manifest.jsonl")
    parser.add_argument("--output-dir", default="outputs/stage2a/evidence_subset")
    parser.add_argument("--mapping-review", default="outputs/stage2a/evidence_subset/manual_roi_mapping_review.json")
    args = parser.parse_args()

    seed = read_json(Path(args.seed))
    cohort = {json.loads(line)["example_id"]: json.loads(line) for line in Path(args.cohort).read_text().splitlines()}
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    review_path = Path(args.mapping_review)
    review = read_json(review_path) if review_path.exists() else {"examples": {}}

    annotations = []
    stats_rows = []
    classifications = Counter()
    roi_sizes: list[int] = []
    confidence = Counter()
    for spec in seed["examples"]:
        eid = spec["example_id"]
        row = cohort[eid]
        example_dir = Path(row["example_view"])
        input_row = read_json(example_dir / "input.json")
        spans = read_json(example_dir / "spans.json")
        attention = np.load(example_dir / "attention_summary.npz")
        span_data = np.load(example_dir / "span_signals.npz")
        visual_focus = attention["visual_focus"]
        span_ranges = span_data["span_ranges"]
        grid = input_row["visual_mapping"]["merged_grid_shape"]
        size = input_row["original_image_size"]
        if visual_focus.shape[1] != int(np.prod(grid)):
            raise ValueError(f"example {eid}: visual focus/grid mismatch")

        mapped = {
            key: map_boxes_to_visual_tokens(spec[f"evidence_{key}"]["boxes"], size, grid)
            for key in ("A", "B")
        }
        absolute = {
            key: [input_row["visual_token_indices"][idx] for idx in mapped[key]]
            for key in ("A", "B")
        }
        token_curves = {key: roi_curves(visual_focus, mapped[key]) for key in ("A", "B")}
        span_curves = {
            key: {name: span_means(values, span_ranges) for name, values in token_curves[key].items()}
            for key in ("A", "B")
        }
        a_spans = valid_span_ids(stage_span_ids(spec, "A"), len(spans), eid)
        b_spans = valid_span_ids(stage_span_ids(spec, "B"), len(spans), eid)
        ab_spans = valid_span_ids(stage_span_ids(spec, "A+B"), len(spans), eid)
        if not a_spans or not b_spans:
            raise ValueError(f"example {eid}: A-only and B-only demand stages are required")
        cls = classify_shift(
            float(span_curves["A"]["density"][a_spans].mean()),
            float(span_curves["B"]["density"][a_spans].mean()),
            float(span_curves["A"]["density"][b_spans].mean()),
            float(span_curves["B"]["density"][b_spans].mean()),
        )
        classifications[cls] += 1
        roi_sizes.extend([len(mapped["A"]), len(mapped["B"])])
        confidence[spec["confidence"]] += 1

        per_dir = output_dir / "examples" / eid
        per_dir.mkdir(parents=True, exist_ok=True)
        draw_mapping(input_row["resolved_image_path"], input_row, spec, mapped, per_dir / "roi_mapping.png")
        draw_timeline(per_dir / "evidence_timeline.png", eid, token_curves, span_curves, cls)
        np.savez_compressed(
            per_dir / "evidence_curves.npz",
            token_A_raw_mass=token_curves["A"]["raw_mass"].astype(np.float32),
            token_B_raw_mass=token_curves["B"]["raw_mass"].astype(np.float32),
            token_A_density=token_curves["A"]["density"].astype(np.float32),
            token_B_density=token_curves["B"]["density"].astype(np.float32),
            token_A_conditional_share=token_curves["A"]["conditional_share"].astype(np.float32),
            token_B_conditional_share=token_curves["B"]["conditional_share"].astype(np.float32),
            span_A_raw_mass=span_curves["A"]["raw_mass"].astype(np.float32),
            span_B_raw_mass=span_curves["B"]["raw_mass"].astype(np.float32),
            span_A_density=span_curves["A"]["density"].astype(np.float32),
            span_B_density=span_curves["B"]["density"].astype(np.float32),
            span_A_conditional_share=span_curves["A"]["conditional_share"].astype(np.float32),
            span_B_conditional_share=span_curves["B"]["conditional_share"].astype(np.float32),
            span_ranges=span_ranges.astype(np.int32),
        )
        verification = review.get("examples", {}).get(eid, {"status": "pending", "notes": "manual overlay review pending"})
        evidence_out = {}
        for key in ("A", "B"):
            evidence = spec[f"evidence_{key}"]
            evidence_out[key] = {
                "semantic_fact": evidence["semantic_fact"],
                "ROI_image_coordinates": evidence["boxes"],
                "ROI_visual_focus_column_indices": mapped[key],
                "ROI_visual_token_indices": absolute[key],
                "ROI_visual_token_count": len(mapped[key]),
                "expected_reasoning_stage": evidence["expected_reasoning_stage"],
            }
            write_json(per_dir / f"roi_{key}.json", evidence_out[key])
        windows = {
            "A_acquisition_windows": contiguous_windows(a_spans, span_ranges),
            "A_computation_windows": contiguous_windows(ab_spans, span_ranges),
            "B_acquisition_windows": contiguous_windows(b_spans, span_ranges),
            "B_computation_windows": contiguous_windows(ab_spans, span_ranges),
            "status": "candidate_windows_only_no_intervention_performed",
        }
        write_json(per_dir / "candidate_intervention_windows.json", windows)
        annotation = {
            "example_id": eid,
            "base_problem_id": row["base_problem_id"],
            "variant": row["variant"],
            "correct": row["correct"],
            "evidence_A": evidence_out["A"],
            "evidence_B": evidence_out["B"],
            "reasoning_stages": spec["reasoning_stages"],
            "candidate_intervention_windows_file": str(per_dir / "candidate_intervention_windows.json"),
            "descriptive_pattern": cls,
            "notes": spec["notes"],
            "ROI_mapping_validation": verification,
        }
        annotations.append(annotation)
        stats_rows.append({
            "example_id": eid, "classification": cls, "confidence": spec["confidence"],
            "roi_A_tokens": len(mapped["A"]), "roi_B_tokens": len(mapped["B"]),
            "A_demand_A_density": float(span_curves["A"]["density"][a_spans].mean()),
            "A_demand_B_density": float(span_curves["B"]["density"][a_spans].mean()),
            "B_demand_A_density": float(span_curves["A"]["density"][b_spans].mean()),
            "B_demand_B_density": float(span_curves["B"]["density"][b_spans].mean()),
        })

    with (output_dir / "evidence_annotations.jsonl").open("w") as handle:
        for row in annotations:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    stats = {
        "screened_count": seed["screening"]["screened_count"],
        "accepted_count": len(annotations),
        "rejected_count": len(seed["screening"]["rejected"]),
        "selection_was_attention_blind": seed["screening"]["selection_was_attention_blind"],
        "rejected": seed["screening"]["rejected"],
        "classification_method": "density dominance score (A-B)/(A+B), threshold 0.10, evaluated in manually annotated A-only and B-only evidence-demand spans",
        "classification_counts": dict(classifications),
        "annotation_confidence_counts": dict(confidence),
        "roi_token_count": {
            "minimum": int(min(roi_sizes)), "median": float(np.median(roi_sizes)),
            "maximum": int(max(roi_sizes)), "all": roi_sizes,
        },
        "mapping_review_status_counts": dict(Counter(a["ROI_mapping_validation"]["status"] for a in annotations)),
        "examples": stats_rows,
        "scientific_boundary": "ROI attention is descriptive evidence, not causal evidence acquisition or usage.",
    }
    write_json(output_dir / "evidence_subset_statistics.json", stats)
    print(json.dumps({k: stats[k] for k in ("screened_count", "accepted_count", "rejected_count", "classification_counts", "mapping_review_status_counts")}, indent=2))


if __name__ == "__main__":
    main()
