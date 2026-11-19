"""Dependency-light Stage 0 diagnostic plots using Pillow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .io import ensure_directory


COLORS = {
    "visual": (210, 45, 45),
    "prompt": (45, 95, 205),
    "reasoning": (40, 150, 85),
    "entropy": (140, 70, 180),
    "margin": (230, 140, 20),
}


def _font() -> ImageFont.ImageFont:
    return ImageFont.load_default()


def _x_position(index: int, count: int, left: int, right: int) -> int:
    if count <= 1:
        return left
    return int(round(left + (right - left) * index / (count - 1)))


def _draw_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    series: Sequence[tuple[str, Sequence[float], tuple[int, int, int]]],
    title: str,
    y_min: float,
    y_max: float,
    span_boundaries: Sequence[int] = (),
) -> None:
    left, top, right, bottom = box
    draw.rectangle(box, outline=(70, 70, 70), width=1)
    draw.text((left, top - 18), title, fill=(20, 20, 20), font=_font())
    count = max((len(values) for _, values, _ in series), default=0)
    for boundary in span_boundaries:
        x = _x_position(boundary, max(1, count), left, right)
        draw.line((x, top, x, bottom), fill=(220, 220, 220), width=1)
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = int(round(bottom - fraction * (bottom - top)))
        draw.line((left, y, right, y), fill=(238, 238, 238), width=1)
        value = y_min + fraction * (y_max - y_min)
        draw.text((5, y - 6), f"{value:.2f}", fill=(80, 80, 80), font=_font())
    legend_x = left
    for name, values, color in series:
        points: list[tuple[int, int]] = []
        for index, raw_value in enumerate(values):
            value = min(y_max, max(y_min, float(raw_value)))
            x = _x_position(index, max(1, count), left, right)
            normalized = (value - y_min) / max(1e-12, y_max - y_min)
            y = int(round(bottom - normalized * (bottom - top)))
            points.append((x, y))
        if len(points) == 1:
            draw.ellipse((points[0][0] - 2, points[0][1] - 2, points[0][0] + 2, points[0][1] + 2), fill=color)
        elif points:
            draw.line(points, fill=color, width=2)
        draw.line((legend_x, bottom + 14, legend_x + 18, bottom + 14), fill=color, width=3)
        draw.text((legend_x + 23, bottom + 8), name, fill=(30, 30, 30), font=_font())
        legend_x += 125


def save_timeline_plots(token_rows: list[dict[str, Any]], spans: list[dict[str, Any]], plots_dir: Path) -> list[Path]:
    ensure_directory(plots_dir)
    span_boundaries = [int(span["start_token"]) for span in spans[1:]]
    count = len(token_rows)
    width = 1200

    modality = Image.new("RGB", (width, 430), "white")
    draw = ImageDraw.Draw(modality)
    _draw_panel(
        draw,
        (70, 45, width - 25, 365),
        [
            ("visual", [float(row["visual_attention_mass"]) for row in token_rows], COLORS["visual"]),
            ("prompt", [float(row["prompt_attention_mass"]) for row in token_rows], COLORS["prompt"]),
            ("reasoning", [float(row["reasoning_attention_mass"]) for row in token_rows], COLORS["reasoning"]),
        ],
        "Timeline 1 — modality attention mass (layer/head mean)",
        0.0,
        1.0,
        span_boundaries,
    )
    draw.text((70, 405), f"generated token index 0 … {max(0, count - 1)}", fill=(30, 30, 30), font=_font())
    modality_path = plots_dir / "modality_attention_timeline.png"
    modality.save(modality_path)

    uncertainty = Image.new("RGB", (width, 650), "white")
    draw = ImageDraw.Draw(uncertainty)
    entropy_values = [float(row["next_token_entropy"]) for row in token_rows]
    entropy_max = max(1.0, max(entropy_values, default=1.0))
    _draw_panel(
        draw,
        (70, 45, width - 25, 285),
        [("entropy", entropy_values, COLORS["entropy"])],
        "Timeline 2a — next-token entropy",
        0.0,
        entropy_max,
        span_boundaries,
    )
    _draw_panel(
        draw,
        (70, 365, width - 25, 605),
        [("top-1/top-2 margin", [float(row["top1_top2_margin"]) for row in token_rows], COLORS["margin"])],
        "Timeline 2b — confidence margin",
        0.0,
        1.0,
        span_boundaries,
    )
    uncertainty_path = plots_dir / "uncertainty_timeline.png"
    uncertainty.save(uncertainty_path)

    span_image = Image.new("RGB", (width, 640), "white")
    draw = ImageDraw.Draw(span_image)
    draw.text((20, 15), "Timeline 3 — provisional reasoning spans", fill=(20, 20, 20), font=_font())
    bar_left, bar_right, bar_top, bar_bottom = 70, width - 25, 55, 115
    palette = ((220, 235, 255), (235, 250, 225), (255, 235, 220), (245, 225, 250))
    for span in spans:
        start = int(span["start_token"])
        end = max(start + 1, int(span["end_token"]))
        x0 = _x_position(start, max(1, count), bar_left, bar_right)
        x1 = _x_position(end - 1, max(1, count), bar_left, bar_right)
        if x1 <= x0:
            x1 = x0 + 2
        color = palette[int(span["span_id"]) % len(palette)]
        draw.rectangle((x0, bar_top, x1, bar_bottom), fill=color, outline=(100, 100, 100))
    draw.rectangle((bar_left, bar_top, bar_right, bar_bottom), outline=(50, 50, 50))
    y = 140
    for span in spans[:22]:
        label = str(span["provisional_semantic_label"])
        text = " ".join(str(span["span_text"]).split())
        if len(text) > 120:
            text = text[:117] + "..."
        draw.text(
            (25, y),
            f"{span['span_id']:>2} [{span['start_token']}:{span['end_token']}] {label}: {text}",
            fill=(25, 25, 25),
            font=_font(),
        )
        y += 21
    if len(spans) > 22:
        draw.text((25, y), f"… {len(spans) - 22} additional spans saved in spans.json", fill=(80, 80, 80), font=_font())
    span_path = plots_dir / "reasoning_spans_timeline.png"
    span_image.save(span_path)
    return [modality_path, uncertainty_path, span_path]


def _heatmap_rgb(values: np.ndarray) -> Image.Image:
    normalized = values.astype(np.float32)
    maximum = float(normalized.max()) if normalized.size else 0.0
    if maximum > 0:
        normalized = normalized / maximum
    red = np.full_like(normalized, 255, dtype=np.float32)
    green = 255 * (1.0 - normalized)
    blue = 255 * (1.0 - normalized)
    rgb = np.stack((red, green, blue), axis=-1).clip(0, 255).astype(np.uint8)
    return Image.fromarray(rgb, mode="RGB")


def save_visual_focus_snapshots(
    image_path: Path,
    visual_focus: np.ndarray,
    merged_grid_shape: Sequence[int],
    token_rows: list[dict[str, Any]],
    output_dir: Path,
) -> list[Path]:
    ensure_directory(output_dir)
    if visual_focus.ndim != 2 or visual_focus.shape[0] == 0:
        return []
    temporal, grid_h, grid_w = (int(value) for value in merged_grid_shape)
    if visual_focus.shape[1] != temporal * grid_h * grid_w:
        raise ValueError(
            f"Visual focus width {visual_focus.shape[1]} does not match merged grid {list(merged_grid_shape)}"
        )
    visual_mass = np.asarray([float(row["visual_attention_mass"]) for row in token_rows], dtype=np.float32)
    candidate_positions = [0, int(visual_mass.argmax()), visual_focus.shape[0] - 1]
    positions: list[int] = []
    for position in candidate_positions:
        if position not in positions:
            positions.append(position)

    base = Image.open(image_path).convert("RGB")
    saved: list[Path] = []
    for position in positions:
        grid = visual_focus[position].reshape(temporal, grid_h, grid_w).mean(axis=0)
        heatmap = _heatmap_rgb(grid)
        heatmap_path = output_dir / f"token_{position:04d}_heatmap.png"
        heatmap.resize((grid_w * 24, grid_h * 24), resample=Image.Resampling.NEAREST).save(heatmap_path)

        intensity = grid.astype(np.float32)
        maximum = float(intensity.max()) if intensity.size else 0.0
        if maximum > 0:
            intensity = intensity / maximum
        alpha = Image.fromarray((intensity * 175).clip(0, 175).astype(np.uint8), mode="L")
        alpha = alpha.resize(base.size, resample=Image.Resampling.BILINEAR)
        red_layer = Image.new("RGBA", base.size, (255, 0, 0, 0))
        red_layer.putalpha(alpha)
        overlay = Image.alpha_composite(base.convert("RGBA"), red_layer).convert("RGB")
        overlay_path = output_dir / f"token_{position:04d}_overlay.png"
        overlay.save(overlay_path)
        saved.extend((heatmap_path, overlay_path))
    return saved

