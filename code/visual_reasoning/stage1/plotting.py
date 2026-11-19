"""Compact descriptive Stage 1 span timelines."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.io import ensure_directory


LABEL_COLORS = {
    "VISUAL_READ": (208, 74, 67),
    "COMPUTE": (61, 121, 184),
    "RELATION_INFERENCE": (74, 151, 92),
    "VERIFY": (149, 91, 177),
    "PLAN": (218, 143, 48),
    "ANSWER_SELECTION": (68, 68, 68),
    "OTHER": (175, 175, 175),
}


def _font() -> ImageFont.ImageFont:
    return ImageFont.load_default()


def _line_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    values: Sequence[float],
    color: tuple[int, int, int],
    title: str,
    peak_positions: set[int],
    normalized_positions: Sequence[float],
    fixed_range: tuple[float, float] | None = None,
) -> None:
    left, top, right, bottom = box
    draw.rectangle(box, outline=(85, 85, 85))
    draw.text((left, top - 16), title, fill=(25, 25, 25), font=_font())
    if not values:
        return
    minimum, maximum = fixed_range or (min(values), max(values))
    if maximum <= minimum:
        maximum = minimum + 1e-9
    points = []
    for index, raw in enumerate(values):
        x = int(round(left + (right - left) * float(normalized_positions[index])))
        y = int(round(bottom - (float(raw) - minimum) / (maximum - minimum) * (bottom - top)))
        points.append((x, y))
        if index in peak_positions:
            draw.line((x, top, x, bottom), fill=(225, 205, 205), width=1)
    if len(points) > 1:
        draw.line(points, fill=color, width=2)
    else:
        draw.ellipse((points[0][0] - 2, points[0][1] - 2, points[0][0] + 2, points[0][1] + 2), fill=color)
    draw.text((5, top - 2), f"{maximum:.3g}", fill=(80, 80, 80), font=_font())
    draw.text((5, bottom - 10), f"{minimum:.3g}", fill=(80, 80, 80), font=_font())


def save_span_timeline(
    spans: list[dict[str, Any]],
    peaks: dict[str, Any],
    output_path: Path,
    title: str,
) -> Path:
    """Render semantic, attention, and uncertainty signals at span resolution."""

    ensure_directory(output_path.parent)
    width, height = 1400, 590
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 12), title, fill=(15, 15, 15), font=_font())
    left, right = 90, width - 25
    count = len(spans)
    total_tokens = int(spans[-1]["end_token"]) if spans else 0
    normalized_positions = [
        ((int(span["start_token"]) + int(span["end_token"])) / 2.0) / max(1, total_tokens)
        for span in spans
    ]
    peak_positions = {int(row["span_id"]) for row in peaks.get("peaks", [])}

    draw.text((left, 39), "semantic spans", fill=(25, 25, 25), font=_font())
    for index, span in enumerate(spans):
        x0 = int(round(left + (right - left) * int(span["start_token"]) / max(1, total_tokens)))
        x1 = int(round(left + (right - left) * int(span["end_token"]) / max(1, total_tokens)))
        color = LABEL_COLORS.get(str(span["semantic_label"]), LABEL_COLORS["OTHER"])
        draw.rectangle((x0, 56, max(x0 + 1, x1), 86), fill=color)
        if index in peak_positions:
            draw.rectangle((x0, 54, max(x0 + 2, x1), 88), outline=(0, 0, 0), width=1)

    visual = [float(span["attention"]["visual_mass"]["mean"]) for span in spans]
    reasoning = [float(span["attention"]["reasoning_mass"]["mean"]) for span in spans]
    entropy = [float(span["uncertainty"]["entropy"]["mean"]) for span in spans]
    turnover = [float(span["visual_focus_metrics"].get("turnover_from_previous_span") or 0.0) for span in spans]
    _line_panel(draw, (left, 125, right, 235), visual, (205, 55, 48), "visual attention mass (descriptive)", peak_positions, normalized_positions, (0.0, 1.0))
    _line_panel(draw, (left, 275, right, 385), reasoning, (47, 137, 82), "previous-reasoning attention mass", peak_positions, normalized_positions, (0.0, 1.0))
    _line_panel(draw, (left, 425, right, 515), entropy, (132, 74, 168), "predictive entropy", peak_positions, normalized_positions)
    draw.text((left, 535), "focus turnover: " + " ".join(f"{value:.2f}" for value in turnover[:18]) + (" …" if count > 18 else ""), fill=(55, 55, 55), font=_font())
    draw.text((left, 560), f"x-axis: normalized generated-token time ({count} spans); outlined blocks / pale lines mark candidate attention peaks", fill=(55, 55, 55), font=_font())
    image.save(output_path)
    return output_path
