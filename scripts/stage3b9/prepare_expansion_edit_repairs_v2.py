#!/usr/bin/env python3
"""Repair only expansion-v1 edits rejected by the blinded manual audit."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from prepare_edit_repairs_v2 import review_sheet, sha256, validate
from prepare_expansion_edits import CONFIG, DATASET, OUT
from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b9.edits import render_preserving_crossing_strokes


ROOT = Path(__file__).resolve().parents[2]
V1 = OUT / "fresh_edits/expansion_v1"
V2 = OUT / "fresh_edits/expansion_v2"


# Coordinates enclose the complete original label.  The v1 audit showed that
# its erase boxes were generally shifted right of the label.  Base 753 is a
# semantic correction: v1 targeted the box label rather than the frozen sphere
# radius label.  Base 744 recreates the complete white h'=... label.
REPAIRS: dict[str, dict] = {
    "644":{"roi":[325,110,450,156]},
    "731":{"roi":[105,0,205,32]},
    "732":{"roi":[172,174,283,214]},
    "733":{"roi":[165,45,281,90]},
    "736":{"roi":[140,304,252,352]},
    "737":{"roi":[160,146,257,192]},
    "738":{"roi":[105,103,218,152]},
    "739":{"roi":[50,208,169,251]},
    "742":{"roi":[185,0,320,46]},
    "749":{"roi":[34,91,122,131]},
    "750":{"roi":[185,200,322,252]},
    "751":{"roi":[182,0,302,46]},
    "756":{"roi":[228,115,315,165]},
    "759":{"roi":[222,140,330,197]},
    "761":{"roi":[8,158,100,215]},
    "771":{"roi":[108,80,205,136]},
    "774":{"roi":[338,360,545,452]},
    "734":{"roi":[142,40,225,93]},
    "740":{"roi":[20,0,142,46]},
    "741":{"roi":[20,0,143,46]},
    "744":{"roi":[165,115,345,194],"template":"h'={value}cm","text_color":[255,255,255],"font":20},
    "753":{"roi":[53,0,118,40]},
    "754":{"roi":[88,88,200,142]},
    "758":{"roi":[120,28,225,86]},
}


def _font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _text(item: dict, value: str, repair: dict) -> str:
    if "template" in repair:
        return str(repair["template"]).format(value=value)
    metadata = json.loads((V1 / item["phase"] / str(item["base_problem_id"]) / "edit_metadata.json").read_text(encoding="utf-8"))
    return f"{value}{metadata['render_suffix']}"


def _render(source: Path, destination: Path, *, text: str, repair: dict, font_size: int, anchor: list[int]) -> None:
    ensure_directory(destination.parent)
    with Image.open(source) as opened:
        rendered = render_preserving_crossing_strokes(
            opened.convert("RGB"),
            text,
            roi_xyxy=repair["roi"],
            text_anchor=anchor,
            font_size=font_size,
            text_color=repair.get("text_color", [0, 0, 0]),
        )
        rendered.save(destination)


def main() -> None:
    if V2.exists() and any(V2.iterdir()):
        raise FileExistsError(f"Expansion-v2 edits already exist: {V2}")
    audit = [json.loads(line) for line in (V1 / "manual_audit.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rejected = {str(row["base_problem_id"]): row for row in audit if row["status"] == "fail"}
    if set(rejected) != set(REPAIRS):
        raise RuntimeError("Repair definitions must exactly cover the 24 v1 manual failures")
    screen = json.loads(CONFIG.read_text(encoding="utf-8"))
    items = [
        {**row, "phase": phase}
        for phase, rows in (("phase_a", screen["phase_a_screen"]), ("phase_b", screen["phase_b_screen"]))
        for row in rows
        if str(row["base_problem_id"]) in rejected
    ]
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(DATASET)}
    built_at = datetime.now(timezone.utc).isoformat()
    manifest = []
    for item in items:
        base = str(item["base_problem_id"])
        phase = item["phase"]
        repair = REPAIRS[base]
        font_size = int(repair.get("font", json.loads((V1 / phase / base / "edit_metadata.json").read_text(encoding="utf-8"))["font_size"]))
        source = resolve_image_path(DATASET, str(dataset[str(item["example_id"])]["image"]))
        base_dir = V2 / phase / base
        paths = {"O": base_dir / "O/image.png", "O_sham": base_dir / "O_sham/image.png"}
        ensure_directory(paths["O"].parent)
        shutil.copy2(source, paths["O"])
        values = [str(item["original"])] + ([str(item["counterfactual"])] if phase == "phase_a" else [str(value) for value in item["alternatives"]])
        for value in values:
            text = _text(item, value, repair)
            box = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=_font(font_size))
            width, height = box[2] - box[0], box[3] - box[1]
            roi = repair["roi"]
            if 4 + width > roi[2] - roi[0] or 2 + height > roi[3] - roi[1]:
                raise RuntimeError(f"Repair text does not fit base {base}: {text!r}")
        _render(source, paths["O_sham"], text=_text(item, values[0], repair), repair=repair, font_size=font_size, anchor=[4, 2])
        if phase == "phase_a":
            for name, anchor in (("C", [4, 2]), ("C_sham", [5, 2])):
                paths[name] = base_dir / f"{name}/image.png"
                _render(source, paths[name], text=_text(item, values[1], repair), repair=repair, font_size=font_size, anchor=anchor)
        else:
            for index, value in enumerate(values[1:], start=1):
                for name, anchor in ((f"C{index}", [4, 2]), (f"C{index}_sham", [5, 2])):
                    paths[name] = base_dir / f"{name}/image.png"
                    _render(source, paths[name], text=_text(item, value, repair), repair=repair, font_size=font_size, anchor=anchor)
        checks = validate(paths, repair["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic expansion-v2 validation failed for base {base}: {checks}")
        sheet = review_sheet(base_dir, paths, repair["roi"])
        metadata = {
            **item,
            "edit_version": "stage3b9_expansion_v2_label_repair",
            "supersedes": str((V1 / phase / base / "edit_metadata.json").relative_to(ROOT)),
            "repair_reason": rejected[base]["reason"],
            "built_at": built_at,
            "source_image": str(source),
            "source_image_sha256": sha256(source),
            "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
            "target_evidence_roi_xyxy": repair["roi"],
            "render_suffix": json.loads((V1 / phase / base / "edit_metadata.json").read_text(encoding="utf-8"))["render_suffix"],
            "font_size": font_size,
            "text_template": repair.get("template", "{value}<v1 suffix>"),
            "construction": {
                "renderer": "visual_reasoning.stage3b9.edits.render_preserving_crossing_strokes",
                "same_original_source_for_every_condition": True,
                "semantic_anchor": [4, 2],
                "sham_anchor": [5, 2],
                "selection_used_attention": False,
                "selection_used_expansion_generation_outcomes": False,
                "selection_used_stage3b9_value_or_causal_outcomes": False,
            },
            "automatic_validation": checks,
            "manual_validation": {"status": "pending", "reviewer": None},
            "review_sheet": str(sheet.relative_to(ROOT)),
        }
        write_json(base_dir / "edit_metadata.json", metadata)
        write_text(base_dir / "validation.md", f"# Stage 3B.9 expansion-v2 edit — base {base}\n\nAutomatic validation: **PASS**\n\nManual review: **PENDING**\n")
        manifest.append({
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "phase": phase,
            "edit_version": metadata["edit_version"],
            "edit_metadata": str((base_dir / "edit_metadata.json").relative_to(ROOT)),
            "automatic_edit_status": "pass",
            "manual_edit_status": "pending",
            "generation_outcome_inspected": False,
            "stage3b9_value_or_causal_outcome_inspected": False,
        })
        print(f"built expansion-v2 {phase} base {base}", flush=True)
    write_jsonl(V2 / "construction_manifest.jsonl", manifest)
    print(json.dumps({"built": len(manifest), "phase_a": sum(row["phase"] == "phase_a" for row in manifest), "phase_b": sum(row["phase"] == "phase_b" for row in manifest)}, indent=2))


if __name__ == "__main__":
    main()
