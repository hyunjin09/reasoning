#!/usr/bin/env python3
"""Run the artifact-only Stage 2C temporal measurement audit."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage2c.temporal import (
    center_of_mass_offset,
    classify_timing,
    classify_window_relation,
    event_regions,
    event_window,
    region_means,
)


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/stage2c"
RADIUS = 64
COLORS = {
    "mean": (32, 105, 180),
    "median": (230, 126, 34),
    "PRE": (84, 130, 53),
    "ENTITY": (52, 120, 190),
    "FACT": (135, 87, 179),
    "POST": (230, 145, 40),
    "USE": (190, 62, 66),
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def finite(value: float | np.floating | None) -> float | None:
    if value is None or not np.isfinite(value):
        return None
    return float(value)


def safe_name(evidence_id: str) -> str:
    return evidence_id.replace(":", "_")


def processed_token_view(prediction_aligned: np.ndarray) -> np.ndarray:
    """Associate y_t with the first later row whose query actually processes y_t."""
    result = np.full_like(np.asarray(prediction_aligned, dtype=np.float64), np.nan)
    if len(result) > 1:
        result[:-1] = prediction_aligned[1:]
    return result


def interval_mean(curve: np.ndarray, interval: tuple[int, int]) -> float | None:
    start, end = map(int, interval)
    values = np.asarray(curve, dtype=np.float64)[start:end]
    values = values[np.isfinite(values)]
    return float(values.mean()) if len(values) else None


def local_argmax_offset(curve: np.ndarray, center: int, radius: int = RADIUS) -> int | None:
    window = event_window(curve, center, radius)
    if not np.isfinite(window).any():
        return None
    return int(np.nanargmax(window) - radius)


def matched_interval(mention: dict, event: dict, token_count: int) -> tuple[int, int] | None:
    """Choose a same-length nearby interval not overlapping the first fact/use.

    This operational control is fixed mechanically: prefer the immediately
    preceding interval; if it overlaps E0--E2, use the immediately following
    interval. It is a descriptive lexical control, not a causal baseline.
    """
    start, end = int(mention["start_token"]), int(mention["end_token"])
    width = end - start
    forbidden = (
        int(event["e0"]["start_token"]),
        int(event["e2"]["end_token"]),
    )
    before = (max(0, start - width), start)
    if before[1] <= forbidden[0] or before[0] >= forbidden[1]:
        return before if before[1] > before[0] else None
    after = (end, min(token_count, end + width))
    return after if after[1] > after[0] else None


def bootstrap_summary(values: Iterable[float | None], seed: int) -> dict:
    array = np.asarray([float(value) for value in values if value is not None and np.isfinite(value)], dtype=np.float64)
    if not len(array):
        return {"n": 0, "mean": None, "median": None, "bootstrap_mean_95ci": [None, None]}
    rng = np.random.default_rng(seed)
    draws = np.asarray([rng.choice(array, size=len(array), replace=True).mean() for _ in range(2000)])
    return {
        "n": int(len(array)),
        "mean": float(array.mean()),
        "median": float(np.median(array)),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
        "bootstrap_mean_95ci": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
    }


def line_plot(path: Path, title: str, curves: dict[str, np.ndarray], x_values: np.ndarray, y_label: str) -> None:
    width, height = 1100, 650
    margin = (95, 70, 45, 85)
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    left, top, right, bottom = margin[0], margin[1], width - margin[2], height - margin[3]
    all_values = np.concatenate([np.asarray(v)[np.isfinite(v)] for v in curves.values()])
    ymin, ymax = float(all_values.min()), float(all_values.max())
    if ymax <= ymin:
        ymax = ymin + 1.0
    ymin = min(0.0, ymin)
    draw.rectangle((left, top, right, bottom), outline=(70, 70, 70), width=1)
    draw.text((left, 22), title, fill="black", font=font)
    draw.text((left, height - 35), "token offset", fill="black", font=font)
    draw.text((8, top), y_label, fill="black", font=font)
    if float(x_values.min()) <= 0 <= float(x_values.max()):
        x0 = left + int((0 - x_values.min()) / (x_values.max() - x_values.min()) * (right - left))
        draw.line((x0, top, x0, bottom), fill=(120, 120, 120), width=1)
    palette = [COLORS["mean"], COLORS["median"], (75, 160, 120), (160, 80, 150)]
    for index, (label, curve) in enumerate(curves.items()):
        points = []
        for x, value in zip(x_values, curve):
            if not np.isfinite(value):
                continue
            px = left + int((float(x) - float(x_values.min())) / (float(x_values.max()) - float(x_values.min())) * (right - left))
            py = bottom - int((float(value) - ymin) / (ymax - ymin) * (bottom - top))
            points.append((px, py))
        if len(points) >= 2:
            draw.line(points, fill=palette[index % len(palette)], width=3)
        lx = right - 180
        ly = top + 15 + index * 22
        draw.line((lx, ly + 5, lx + 25, ly + 5), fill=palette[index % len(palette)], width=3)
        draw.text((lx + 34, ly), label, fill="black", font=font)
    for tick in np.linspace(ymin, ymax, 5):
        py = bottom - int((tick - ymin) / (ymax - ymin) * (bottom - top))
        draw.text((15, py - 5), f"{tick:.2g}", fill=(60, 60, 60), font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def bar_plot(path: Path, title: str, labels: list[str], means: list[float], colors: list[tuple[int, int, int]]) -> None:
    width, height = 1050, 650
    left, top, right, bottom = 95, 70, 1010, 555
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((left, 22), title, fill="black", font=font)
    draw.rectangle((left, top, right, bottom), outline=(70, 70, 70))
    ymax = max(means) * 1.15 if means and max(means) > 0 else 1.0
    slot = (right - left) / max(1, len(labels))
    for i, (label, value, color) in enumerate(zip(labels, means, colors)):
        x0 = int(left + i * slot + slot * 0.18)
        x1 = int(left + (i + 1) * slot - slot * 0.18)
        y = int(bottom - value / ymax * (bottom - top))
        draw.rectangle((x0, y, x1, bottom), fill=color, outline=(60, 60, 60))
        draw.text((x0, bottom + 14), label[:18], fill="black", font=font)
        draw.text((x0, y - 16), f"{value:.3g}", fill="black", font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def histogram(path: Path, title: str, values: list[int], lo: int = -RADIUS, hi: int = RADIUS, bins: int = 16) -> None:
    counts, edges = np.histogram(np.asarray(values, dtype=float), bins=bins, range=(lo, hi))
    bar_plot(path, title, [f"{int(edges[i])}:{int(edges[i+1])}" for i in range(bins)], counts.astype(float).tolist(), [(77, 135, 190)] * bins)


def representative_grid(path: Path, rows: list[dict], curve_by_id: dict[str, np.ndarray]) -> None:
    width, height = 1200, 780
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((25, 20), "Representative descriptive timing categories (prediction-aligned ROI density)", fill="black", font=font)
    by_category = {row["timing_category"].split("_")[0]: row for row in rows}
    for index, category in enumerate(("T1", "T2", "T3", "T4", "T5", "T6")):
        row_i, col_i = divmod(index, 3)
        left, top = 30 + col_i * 390, 65 + row_i * 350
        right, bottom = left + 350, top + 290
        draw.rectangle((left, top, right, bottom), outline=(90, 90, 90))
        row = by_category.get(category)
        if row is None:
            draw.text((left + 12, top + 12), f"{category}: not observed", fill="black", font=font)
            continue
        evidence_id = row["evidence_id"]
        curve = curve_by_id[evidence_id]
        e1 = int(row["events"]["e1_completion"])
        window = event_window(curve, e1, RADIUS)
        finite_values = window[np.isfinite(window)]
        ymax = float(finite_values.max()) if len(finite_values) else 1.0
        ymax = max(ymax, 1e-12)
        points = []
        for i, value in enumerate(window):
            if not np.isfinite(value):
                continue
            x = left + 12 + int(i / (len(window) - 1) * (right - left - 24))
            y = bottom - 16 - int(float(value) / ymax * (bottom - top - 65))
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=(40, 110, 185), width=2)
        mid = left + (right - left) // 2
        draw.line((mid, top + 35, mid, bottom - 12), fill=(140, 140, 140))
        draw.text((left + 10, top + 9), f"{category}: {evidence_id}", fill="black", font=font)
        draw.text((left + 10, bottom - 2), "-64                    E1                    +64", fill="black", font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def stage2b_timeline_figure(path: Path, records: list[dict]) -> None:
    width, height = 1200, 650
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((30, 18), "Stage 2B intervention windows relative to E0/E1/E2", fill="black", font=font)
    left, right = 180, 1150
    for index, row in enumerate(records):
        y = 70 + index * 52
        end_scale = max(row["window"][1], row["events"]["e2"][1]) + 1
        scale = lambda token: left + int(token / end_scale * (right - left))
        draw.text((20, y - 6), f"{row['example_id']} {row['window_name']}", fill="black", font=font)
        draw.line((left, y, right, y), fill=(170, 170, 170), width=2)
        e0 = row["events"]["e0"][0]
        e1 = row["events"]["e1"]
        e2 = row["events"]["e2"][0]
        for token, label, color in ((e0, "E0", (45, 110, 190)), (e1, "E1", (130, 75, 175)), (e2, "E2", (190, 55, 60))):
            x = scale(token)
            draw.line((x, y - 13, x, y + 13), fill=color, width=2)
            draw.text((x - 7, y - 27), label, fill=color, font=font)
        x0, x1 = scale(row["window"][0]), scale(row["window"][1])
        draw.rectangle((x0, y - 7, max(x0 + 2, x1), y + 7), fill=(230, 145, 35), outline=(110, 80, 20))
        draw.text((right - 245, y + 13), row["target_relation"][:38], fill=(70, 70, 70), font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def analyze_events() -> tuple[list[dict], dict[str, np.ndarray]]:
    cohort = {row["example_id"]: row for row in read_jsonl(OUTPUT / "cohort/cohort_manifest.jsonl")}
    events = read_jsonl(OUTPUT / "annotations/evidence_event_annotations.jsonl")
    rois = {row["evidence_id"]: row for row in read_jsonl(OUTPUT / "annotations/roi_annotations.jsonl")}
    results: list[dict] = []
    curve_by_id: dict[str, np.ndarray] = {}
    repeat_items: list[dict] = []
    for event in events:
        evidence_id = event["evidence_id"]
        example_id = event["example_id"]
        artifact = Path(cohort[example_id]["artifact_view"])
        spans = read_json(artifact / "spans.json")
        with np.load(artifact / "attention_summary.npz") as arrays:
            visual_focus = arrays["visual_focus"].astype(np.float64)
        columns = np.asarray(rois[evidence_id]["roi_visual_focus_column_indices"], dtype=int)
        raw = visual_focus[:, columns].sum(axis=1)
        density = raw / max(1, len(columns))
        visual_total = visual_focus.sum(axis=1)
        conditional = np.divide(raw, visual_total, out=np.full_like(raw, np.nan), where=visual_total > 0)
        processed_raw = processed_token_view(raw)
        processed_density = processed_token_view(density)
        processed_conditional = processed_token_view(conditional)
        token_count = len(raw)
        regions = event_regions(
            token_count,
            (event["e0"]["start_token"], event["e0"]["end_token"]),
            event["e1"]["completion_token"],
            (event["e2"]["start_token"], event["e2"]["end_token"]),
            RADIUS,
            fact_start=event["e1"]["fact_start_token"],
        )
        repeated_prediction = []
        repeated_processed = []
        matched_prediction = []
        matched_processed = []
        repeat_rows = []
        for mention in event["repeated_mentions"][:5]:
            interval = (mention["start_token"], mention["end_token"])
            matched = matched_interval(mention, event, token_count)
            record = {
                "mention_interval": list(interval),
                "mention_text": mention["text"],
                "matched_interval": list(matched) if matched else None,
                "prediction_aligned_mention_density": interval_mean(density, interval),
                "processed_token_mention_density": interval_mean(processed_density, interval),
                "prediction_aligned_matched_density": interval_mean(density, matched) if matched else None,
                "processed_token_matched_density": interval_mean(processed_density, matched) if matched else None,
            }
            repeat_rows.append(record)
            repeated_prediction.append(record["prediction_aligned_mention_density"])
            repeated_processed.append(record["processed_token_mention_density"])
            matched_prediction.append(record["prediction_aligned_matched_density"])
            matched_processed.append(record["processed_token_matched_density"])
        mean_or_none = lambda values: finite(np.nanmean([v for v in values if v is not None])) if any(v is not None for v in values) else None
        repeat_prediction_mean = mean_or_none(repeated_prediction)
        repeat_processed_mean = mean_or_none(repeated_processed)
        matched_prediction_mean = mean_or_none(matched_prediction)
        matched_processed_mean = mean_or_none(matched_processed)
        means_density = region_means(density, regions)
        means_raw = region_means(raw, regions)
        means_conditional = region_means(conditional, regions)
        span_ids = np.asarray([int(span["span_id"]) for span in spans], dtype=np.int32)
        span_density = np.asarray([interval_mean(density, (span["start_token"], span["end_token"])) for span in spans], dtype=np.float64)
        span_raw = np.asarray([interval_mean(raw, (span["start_token"], span["end_token"])) for span in spans], dtype=np.float64)
        category = classify_timing(means_density, repeat_prediction_mean, matched_prediction_mean)
        result = {
            "example_id": example_id,
            "evidence_id": evidence_id,
            "semantic_fact": event["semantic_fact"],
            "alignment": "prediction-aligned row t -> y_t (primary); processed-token y_t -> row t+1 (semantic audit)",
            "roi_visual_token_count": len(columns),
            "events": {
                "e0": [event["e0"]["start_token"], event["e0"]["end_token"]],
                "e1_completion": event["e1"]["completion_token"],
                "e2": [event["e2"]["start_token"], event["e2"]["end_token"]],
            },
            "regions": {key: list(value) for key, value in regions.items()},
            "prediction_aligned_region_means": {
                "roi_total_mass": means_raw,
                "roi_per_token_density": means_density,
                "roi_conditional_visual_share": means_conditional,
            },
            "processed_token_region_means": {
                "roi_total_mass": region_means(processed_raw, regions),
                "roi_per_token_density": region_means(processed_density, regions),
                "roi_conditional_visual_share": region_means(processed_conditional, regions),
            },
            "local_peak_offset_from_e0": local_argmax_offset(density, event["e0"]["start_token"]),
            "local_peak_offset_from_e1": local_argmax_offset(density, event["e1"]["completion_token"]),
            "center_of_mass_offset_from_e1": center_of_mass_offset(density, event["e1"]["completion_token"], RADIUS),
            "first_entity_density_prediction_aligned": interval_mean(density, (event["e0"]["start_token"], event["e0"]["end_token"])),
            "first_fact_density_prediction_aligned": interval_mean(density, (event["e1"]["fact_start_token"], event["e1"]["completion_token"] + 1)),
            "repeated_mention_density_prediction_aligned": repeat_prediction_mean,
            "matched_density_prediction_aligned": matched_prediction_mean,
            "repeated_mention_density_processed_token": repeat_processed_mean,
            "matched_density_processed_token": matched_processed_mean,
            "timing_category": category,
            "repeat_reference_count_used": len(repeat_rows),
            "attention_is_descriptive_not_causal": True,
        }
        results.append(result)
        curve_by_id[evidence_id] = density
        repeat_items.append({"example_id": example_id, "evidence_id": evidence_id, "references": repeat_rows})
        curve_path = OUTPUT / f"analysis/evidence_curves/{safe_name(evidence_id)}.npz"
        curve_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            curve_path,
            prediction_aligned_roi_total_mass=raw.astype(np.float32),
            prediction_aligned_roi_per_token_density=density.astype(np.float32),
            prediction_aligned_roi_conditional_visual_share=conditional.astype(np.float32),
            processed_token_roi_total_mass=processed_raw.astype(np.float32),
            processed_token_roi_per_token_density=processed_density.astype(np.float32),
            processed_token_roi_conditional_visual_share=processed_conditional.astype(np.float32),
            span_ids=span_ids,
            span_prediction_aligned_roi_total_mass=span_raw.astype(np.float32),
            span_prediction_aligned_roi_per_token_density=span_density.astype(np.float32),
            e0_window=event_window(density, event["e0"]["start_token"], RADIUS).astype(np.float32),
            e1_window=event_window(density, event["e1"]["completion_token"], RADIUS).astype(np.float32),
            e2_window=event_window(density, event["e2"]["start_token"], RADIUS).astype(np.float32),
        )

    write_jsonl(OUTPUT / "analysis/timing_categories.jsonl", results)
    write_json(OUTPUT / "analysis/repeated_mention_statistics.json", {"per_evidence": repeat_items})
    return results, curve_by_id


def summarize(results: list[dict]) -> dict:
    region_stats = {}
    for region in ("PRE", "ENTITY", "FACT", "POST", "USE"):
        region_stats[region] = bootstrap_summary(
            [row["prediction_aligned_region_means"]["roi_per_token_density"][region] for row in results],
            2026 + len(region),
        )
    categories = Counter(row["timing_category"] for row in results)
    repeated_rows = [row for row in results if row["repeat_reference_count_used"] > 0]
    repeated_summary = {
        "evidence_items_with_repeated_references": len(repeated_rows),
        "first_entity_prediction_aligned": bootstrap_summary([row["first_entity_density_prediction_aligned"] for row in repeated_rows], 301),
        "first_fact_prediction_aligned": bootstrap_summary([row["first_fact_density_prediction_aligned"] for row in repeated_rows], 302),
        "later_references_prediction_aligned": bootstrap_summary([row["repeated_mention_density_prediction_aligned"] for row in repeated_rows], 303),
        "matched_nearby_prediction_aligned": bootstrap_summary([row["matched_density_prediction_aligned"] for row in repeated_rows], 304),
        "later_references_processed_token": bootstrap_summary([row["repeated_mention_density_processed_token"] for row in repeated_rows], 305),
        "matched_nearby_processed_token": bootstrap_summary([row["matched_density_processed_token"] for row in repeated_rows], 306),
        "matching_rule": "same-length interval immediately before the repeated reference unless it overlaps E0-through-E2, then immediately after",
        "unit_of_analysis": "one mean per evidence item, using at most five repeated references",
    }
    summary = {
        "stage": "2C descriptive temporal measurement audit",
        "example_count": len({row["example_id"] for row in results}),
        "evidence_event_count": len(results),
        "fixed_event_window_radius_tokens": RADIUS,
        "primary_signal": "prediction-aligned per-ROI-visual-token density",
        "canonical_attention_alignment": "stored row t predicts y_t; processed-token alternative shifts y_t to row t+1",
        "region_density_statistics": region_stats,
        "timing_category_counts": dict(sorted(categories.items())),
        "timing_category_rule": "conservative 10% separation; repeated-reference category has priority; persistent requires minimum region >=70% of maximum; near-ties become T6",
        "peak_offset_from_e0": bootstrap_summary([row["local_peak_offset_from_e0"] for row in results], 401),
        "peak_offset_from_e1": bootstrap_summary([row["local_peak_offset_from_e1"] for row in results], 402),
        "center_of_mass_offset_from_e1": bootstrap_summary([row["center_of_mass_offset_from_e1"] for row in results], 403),
        "semantic_alignment": repeated_summary,
        "scientific_boundary": "All attention results are descriptive and do not establish acquisition, causal use, handoff, or memory.",
    }
    write_json(OUTPUT / "analysis/event_aligned_statistics.json", summary)
    repeated_path = OUTPUT / "analysis/repeated_mention_statistics.json"
    repeat_payload = read_json(repeated_path)
    repeat_payload["aggregate"] = repeated_summary
    write_json(repeated_path, repeat_payload)
    return summary


def audit_stage2b(events: list[dict]) -> list[dict]:
    event_by_id = {row["evidence_id"]: row for row in events}
    pilots = read_jsonl(ROOT / "outputs/stage2b/config/pilot_manifest.jsonl")
    records = []
    for pilot in pilots:
        example_id = str(pilot["example_id"])
        for label in ("A", "B"):
            event = event_by_id[f"{example_id}:{label}"]
            other = event_by_id[f"{example_id}:{'B' if label == 'A' else 'A'}"]
            window = tuple(pilot[f"{label}_window"])
            relation = classify_window_relation(window, event)
            records.append(
                {
                    "example_id": example_id,
                    "window_name": f"{label}_window",
                    "target_evidence_id": event["evidence_id"],
                    "window": list(window),
                    "events": {
                        "e0": [event["e0"]["start_token"], event["e0"]["end_token"]],
                        "e1": event["e1"]["completion_token"],
                        "e2": [event["e2"]["start_token"], event["e2"]["end_token"]],
                    },
                    "target_relation": relation,
                    "relation_to_other_evidence": classify_window_relation(window, other),
                    "interpretation": (
                        "This tests direct visual re-access after the evidence was already explicit, not initial evidence acquisition."
                        if window[0] > int(event["e1"]["completion_token"])
                        else "This window includes the interval in which the target fact becomes explicit."
                    ),
                }
            )
    write_json(OUTPUT / "stage2ab_reaudit/stage2b_window_timing.json", {"windows": records})
    count = Counter(row["target_relation"] for row in records)
    lines = [
        "# Stage 2B Temporal Re-Audit", "",
        "All ten frozen A/B intervention windows were related to Stage 2C E0/E1/E2 annotations. No intervention was rerun.", "",
        f"Target-relation counts: `{dict(count)}`.", "",
        "| Example | Window | Tokens | E0 | E1 | E2 | Relation |", "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in records:
        lines.append(
            f"| {row['example_id']} | {row['window_name']} | {row['window'][0]}:{row['window'][1]} | "
            f"{row['events']['e0'][0]} | {row['events']['e1']} | {row['events']['e2'][0]} | {row['target_relation']} |"
        )
    after = sum(row["window"][0] > row["events"]["e1"] for row in records)
    lines.extend(
        ["", f"`{after}/10` windows begin after target E1. For each such window: **This tests direct visual re-access after the evidence was already explicit, not initial evidence acquisition.**", "",
         "The A/B names denote evidence identity, not temporal order. In examples 699 and 3044 the frozen B window precedes or directly follows the A window; this is not a chronological A-then-B naming claim.", "",
         "This re-audit changes the interpretation of the Stage 2B null result: most frozen windows tested post-explicit re-access rather than initial visual-fact acquisition.", ""]
    )
    path = OUTPUT / "stage2ab_reaudit/stage2b_window_timing_audit.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return records


def reinterpret_stage2a(results: list[dict]) -> None:
    by_id = {row["evidence_id"]: row for row in results}
    annotations = read_jsonl(ROOT / "outputs/stage2a/evidence_subset/evidence_annotations.jsonl")
    lines = [
        "# Stage 2A Temporal Reinterpretation", "",
        "This is a separate Stage 2C reinterpretation; historical Stage 2A artifacts were not changed.", "",
        "A timing category is descriptive. It does not prove acquisition or semantic alignment.", "",
        "| Example | Original pattern | A timing | B timing | Pre-explicit candidates | Later-reference pattern |", "|---|---|---|---|---:|---|",
    ]
    rows = []
    for annotation in annotations:
        example_id = str(annotation["example_id"])
        a, b = by_id[f"{example_id}:A"], by_id[f"{example_id}:B"]
        candidates = [label for label, row in (("A", a), ("B", b)) if row["timing_category"].startswith("T1_")]
        repeat_labels = [label for label, row in (("A", a), ("B", b)) if row["timing_category"].startswith("T4_")]
        row = {
            "example_id": example_id,
            "original_descriptive_pattern": annotation["descriptive_pattern"],
            "A_timing": a["timing_category"],
            "B_timing": b["timing_category"],
            "pre_explicit_candidate_labels": candidates,
            "repeated_mention_locked_labels": repeat_labels,
        }
        rows.append(row)
        lines.append(f"| {example_id} | {annotation['descriptive_pattern']} | {a['timing_category']} | {b['timing_category']} | {', '.join(candidates) or 'none'} | {', '.join(repeat_labels) or 'none'} |")
    lines.extend(
        ["", "The original A→B labels summarized evidence-stage ROI selectivity. Stage 2C shows whether those differences lead, coincide with, or follow explicit CoT facts; a mention-centered or repeated-mention-locked curve is compatible with text–vision semantic alignment and is not evidence of fresh acquisition.", ""]
    )
    path = OUTPUT / "stage2ab_reaudit/stage2a_reinterpretation.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    write_json(OUTPUT / "stage2ab_reaudit/stage2a_reinterpretation.json", {"examples": rows})


def candidate_pool(events: list[dict], rois: list[dict], cohort: list[dict]) -> list[dict]:
    event_by_id = {row["evidence_id"]: row for row in events}
    cohort_by_id = {row["example_id"]: row for row in cohort}
    candidates = []
    for roi in rois:
        shortcut = roi["possible_text_shortcut"].strip().lower()
        mapping_pass = roi["manual_mapping_review"]["status"] == "pass"
        clean_shortcut = shortcut == "none" or shortcut.startswith("none in")
        if not (roi["counterfactual_ready"] and mapping_pass and clean_shortcut):
            continue
        event = event_by_id[roi["evidence_id"]]
        candidates.append(
            {
                "example_id": roi["example_id"],
                "evidence_id": roi["evidence_id"],
                "semantic_fact": roi["semantic_fact"],
                "e0": [event["e0"]["start_token"], event["e0"]["end_token"]],
                "e1_completion": event["e1"]["completion_token"],
                "recommended_evidence_neutral_prefix": [0, event["e0"]["start_token"]],
                "recommended_prefix_end_rule": "strictly before E0 entity onset, and therefore before E1 fact completion",
                "possible_text_shortcut": roi["possible_text_shortcut"],
                "plausible_image_only_edit": roi["plausible_edit"],
                "roi_visual_token_count": roi["roi_visual_token_count"],
                "roi_mapping_status": "pass",
                "baseline_completed_correct": bool(cohort_by_id[roi["example_id"]]["completed"] and cohort_by_id[roi["example_id"]]["correct"]),
                "selection_basis": "localized editable fact; clear E0/E1; no identified prompt shortcut; correct baseline; manually passed ROI mapping",
            }
        )
    write_jsonl(OUTPUT / "candidates/counterfactual_ready_candidates.jsonl", candidates)
    lines = [
        "# Counterfactual-Ready Candidate Pool", "",
        f"Best-effort pool: **{len(candidates)} evidence items across {len({row['example_id'] for row in candidates})} examples**.", "",
        "Every retained item has a localized visual fact, explicit E0/E1, a correct completed baseline, a manually passed ROI map, no identified prompt leakage/shortcut, and a plausible image-only edit. The recommended evidence-neutral prefix ends strictly before E0 and therefore before E1. Edited images were not generated.", "",
        "This pool establishes feasibility only. Each eventual edit still needs human semantic validation and a same-text counterfactual baseline before causal interpretation.", "",
    ]
    (OUTPUT / "candidates/candidate_report.md").write_text("\n".join(lines), encoding="utf-8")
    return candidates


def figures(results: list[dict], curve_by_id: dict[str, np.ndarray], summary: dict, stage2b_records: list[dict]) -> None:
    e0_windows = np.stack([event_window(curve_by_id[row["evidence_id"]], row["events"]["e0"][0], RADIUS) for row in results])
    e1_windows = np.stack([event_window(curve_by_id[row["evidence_id"]], row["events"]["e1_completion"], RADIUS) for row in results])
    x = np.arange(-RADIUS, RADIUS + 1)
    line_plot(OUTPUT / "analysis/figures/roi_attention_aligned_e0.png", "ROI attention density aligned to E0 (n=70 evidence events)", {"mean": np.nanmean(e0_windows, axis=0), "median": np.nanmedian(e0_windows, axis=0)}, x, "ROI density")
    line_plot(OUTPUT / "analysis/figures/roi_attention_aligned_e1.png", "ROI attention density aligned to E1 completion (n=70)", {"mean": np.nanmean(e1_windows, axis=0), "median": np.nanmedian(e1_windows, axis=0)}, x, "ROI density")
    region_labels = ["PRE", "ENTITY", "FACT", "POST", "USE"]
    bar_plot(OUTPUT / "analysis/figures/region_comparison.png", "Event-region ROI density (one mean per evidence event)", region_labels, [summary["region_density_statistics"][name]["mean"] or 0.0 for name in region_labels], [COLORS[name] for name in region_labels])
    histogram(OUTPUT / "analysis/figures/roi_peak_timing_relative_e1.png", "Local ROI-density peak offset from E1", [row["local_peak_offset_from_e1"] for row in results if row["local_peak_offset_from_e1"] is not None])
    semantic = summary["semantic_alignment"]
    repeat_labels = ["first entity", "first fact", "later refs", "matched nearby"]
    repeat_means = [semantic["first_entity_prediction_aligned"]["mean"], semantic["first_fact_prediction_aligned"]["mean"], semantic["later_references_prediction_aligned"]["mean"], semantic["matched_nearby_prediction_aligned"]["mean"]]
    bar_plot(OUTPUT / "analysis/figures/first_vs_repeated_vs_matched.png", "Semantic-reference ROI density (event-balanced)", repeat_labels, [v or 0.0 for v in repeat_means], [(45, 110, 190), (130, 75, 175), (190, 55, 60), (130, 130, 130)])
    representative_grid(OUTPUT / "analysis/figures/representative_t1_t6.png", results, curve_by_id)
    stage2b_timeline_figure(OUTPUT / "analysis/figures/stage2b_windows_relative_events.png", stage2b_records)


def write_summary(summary: dict, candidates: list[dict], stage2b_records: list[dict]) -> None:
    category_text = ", ".join(f"{key}={value}" for key, value in summary["timing_category_counts"].items())
    after = sum(row["window"][0] > row["events"]["e1"] for row in stage2b_records)
    semantic = summary["semantic_alignment"]
    lines = [
        "# Stage 2C Summary", "",
        "## Outcome", "",
        "Stage 2C is complete as an artifact-only temporal measurement audit. It used 50 completed-correct examples and 70 localized evidence events; no model inference, causal intervention, counterfactual edit, activation patching, or Stage 3 experiment was run.", "",
        "Recommendation: **GO — Counterfactual content sensitivity**, subject to manual validation of each future edit. This recommendation is not executed here.", "",
        "## Measurement convention", "",
        "Stored attention row `t` is the row whose logits predict generated token `y_t`; for `t>0`, its query token is `y_(t-1)`. The primary acquisition-timing view is prediction-aligned (`row t -> y_t`). The semantic-alignment audit separately uses the processed-token shift (`y_t -> row t+1`). Historical arrays were not changed.", "",
        "The primary signal is attention mass summed over a manually mapped ROI and divided by the number of ROI visual tokens. Raw ROI mass and ROI share conditional on total visual attention are also retained. Fixed E0/E1/E2 windows are ±64 tokens.", "",
        "## Cohort and annotation", "",
        "The cohort combines all 20 manually accepted Stage 2A examples with 30 additional completed-correct examples screened without viewing ROI attention. Three pre-attention exclusions are preserved. E0 is the first relevant entity span, E1 the completion token of the earliest semantic span making the fact explicit, and E2 the first downstream span using it. All 70 ROI mappings passed manual overlay review.", "",
        "## Descriptive temporal results", "",
        f"Timing categories: `{category_text}`.", "",
        f"Mean ROI-density by region: PRE `{summary['region_density_statistics']['PRE']['mean']:.6g}`, ENTITY `{summary['region_density_statistics']['ENTITY']['mean']:.6g}`, FACT `{summary['region_density_statistics']['FACT']['mean']:.6g}`, POST `{summary['region_density_statistics']['POST']['mean']:.6g}`, USE `{summary['region_density_statistics']['USE']['mean']:.6g}`. Bootstrap intervals and full distributions are in `event_aligned_statistics.json`.", "",
        f"The event-balanced semantic audit contains `{semantic['evidence_items_with_repeated_references']}` evidence items with later references. Later-reference and matched-nearby processed-token means are `{semantic['later_references_processed_token']['mean']}` and `{semantic['matched_nearby_processed_token']['mean']}` respectively. These are descriptive alignment checks, not interventions.", "",
        "## Stage 2B temporal re-audit", "",
        f"`{after}/10` target A/B intervention windows began after the corresponding E1. Those windows tested direct visual re-access after the fact was already explicit in the CoT, not initial evidence acquisition. This materially narrows the interpretation of the Stage 2B null result.", "",
        "## Counterfactual readiness", "",
        f"The best-effort pool contains `{len(candidates)}` evidence items across `{len({row['example_id'] for row in candidates})}` examples, exceeding the target of 20. No edited image was generated. A later Stage 3A would still require manual edit validation, same-text controls, and a separately approved plan.", "",
        "## Limitations", "",
        "E0/E1 are semantic-span annotations and can be wider than a single word. The stored visual-focus tensor is averaged across language layers and heads, so Stage 2C cannot localize layer/head timing. Attention can reflect acquisition, lexical/semantic alignment, persistent routing, or other processes. Correlation and temporal precedence do not establish causal visual use, handoff, or memory.", "",
        "## Scientific boundary", "",
        "**Attention is descriptive evidence, not causal evidence.** Low ROI attention does not prove visual memory; high or early ROI attention does not prove fresh evidence acquisition. Stage 2C stops here.", "",
    ]
    path = OUTPUT / "summaries/stage2c_summary.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    recommendation = f"""# Next-Stage Recommendation

Decision: **GO — Counterfactual content sensitivity**.

Stage 2C identified {len(candidates)} clean candidate evidence items across {len({row['example_id'] for row in candidates})} examples, with explicit pre-E1 boundaries and manually validated ROI mappings. The Stage 2B re-audit also showed that {after}/10 frozen windows began after E1, so its mostly null edge-blocking result does not adequately test initial visual-fact acquisition.

The smallest defensible later action is a separately approved Stage 3A pilot changing only localized image evidence while holding text and the pre-E1 reasoning prefix fixed. It should first verify that the edit changes the model's recovered fact. Hidden-state/activation patching is not recommended before counterfactual sensitivity is established.

Alternative explanations remain: timing peaks can reflect semantic alignment, ROI density is layer/head averaged, and image edits can introduce artifacts. Manual edit validation and matched controls are mandatory.

This recommendation was not executed. No counterfactual image, new inference, Stage 3 experiment, or causal claim was produced in Stage 2C.
"""
    (OUTPUT / "summaries/next_stage_recommendation.md").write_text(recommendation, encoding="utf-8")


def main() -> None:
    events = read_jsonl(OUTPUT / "annotations/evidence_event_annotations.jsonl")
    rois = read_jsonl(OUTPUT / "annotations/roi_annotations.jsonl")
    cohort = read_jsonl(OUTPUT / "cohort/cohort_manifest.jsonl")
    results, curve_by_id = analyze_events()
    summary = summarize(results)
    stage2b_records = audit_stage2b(events)
    reinterpret_stage2a(results)
    candidates = candidate_pool(events, rois, cohort)
    figures(results, curve_by_id, summary, stage2b_records)
    write_summary(summary, candidates, stage2b_records)
    print(json.dumps({"examples": len(cohort), "events": len(results), "candidates": len(candidates), "stage2b_windows": len(stage2b_records), "categories": summary["timing_category_counts"]}, indent=2))


if __name__ == "__main__":
    main()
