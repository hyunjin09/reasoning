#!/usr/bin/env python3
"""Construct prospective Phase-A and Phase-B Stage 3B.9 numeric edits."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3a.edits import _render


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
DATASET = Path("/data/dataset/MathVerse")
SCREEN = OUT / "config/prospective_cohort_screen.json"


SPECS: dict[str, dict[str, Any]] = {
    "646":{"roi":[215,215,310,244],"font":18,"suffix":" cm"},
    "647":{"roi":[248,195,273,222],"font":17,"suffix":""},
    "650":{"roi":[212,26,286,58],"font":20,"suffix":" cm"},
    "656":{"roi":[555,140,610,176],"font":22,"suffix":""},
    "659":{"roi":[200,43,275,72],"font":18,"suffix":"mm"},
    "661":{"roi":[180,84,247,113],"font":20,"suffix":" cm"},
    "673":{"roi":[245,438,385,475],"font":24,"suffix":" mm"},
    "676":{"roi":[292,94,410,134],"font":28,"suffix":"cm"},
    "679":{"roi":[332,40,423,80],"font":28,"suffix":"cm"},
    "680":{"roi":[258,52,276,88],"font":14,"suffix":""},
    "682":{"roi":[207,50,242,78],"font":14,"suffix":""},
    "684":{"roi":[132,170,198,200],"font":15,"suffix":" cm"},
    "685":{"roi":[76,93,101,122],"font":11,"suffix":""},
    "688":{"roi":[265,165,334,195],"font":20,"suffix":" cm"},
    "689":{"roi":[265,285,340,316],"font":20,"suffix":" cm"},
    "692":{"roi":[225,322,294,354],"font":20,"suffix":" cm"},
    "695":{"roi":[184,229,235,260],"font":20,"suffix":"°"},
    "696":{"roi":[299,26,370,57],"font":20,"suffix":" cm"},
    "698":{"roi":[213,174,290,206],"font":20,"suffix":" cm"},
    "699":{"roi":[125,248,190,279],"font":20,"suffix":" cm"},
    "700":{"roi":[27,130,67,158],"font":16,"suffix":"m"},
    "701":{"roi":[252,96,309,123],"font":16,"suffix":" cm"},
    "702":{"roi":[104,141,169,168],"font":16,"suffix":" cm"},
    "703":{"roi":[244,103,292,133],"font":16,"suffix":" cm"},
    "704":{"roi":[41,182,87,210],"font":16,"suffix":"cm"},
    "706":{"roi":[254,121,318,149],"font":16,"suffix":" cm"},
    "707":{"roi":[392,184,434,214],"font":16,"suffix":" cm"},
    "708":{"roi":[141,176,191,205],"font":16,"suffix":" cm"},
    "710":{"roi":[220,248,289,280],"font":20,"suffix":" cm"},
    "712":{"roi":[204,148,258,179],"font":18,"suffix":"mm"},
    "713":{"roi":[368,126,441,159],"font":20,"suffix":" cm"},
    "714":{"roi":[284,253,345,282],"font":16,"suffix":" m"},
    "715":{"roi":[299,222,366,251],"font":16,"suffix":" cm"},
    "716":{"roi":[218,70,250,101],"font":16,"suffix":""},
    "717":{"roi":[164,88,207,115],"font":15,"suffix":" cm"},
    "718":{"roi":[79,123,114,152],"font":16,"suffix":""},
    "725":{"roi":[413,163,472,194],"font":18,"suffix":" cm"},
    "726":{"roi":[70,135,122,168],"font":18,"suffix":"cm"},
    "727":{"roi":[334,103,390,135],"font":18,"suffix":" cm"},
    "728":{"roi":[109,324,174,353],"font":18,"suffix":" cm"},
    "648":{"roi":[244,122,316,153],"font":20,"suffix":" cm"},
    "649":{"roi":[294,174,382,206],"font":20,"suffix":" cm"},
    "651":{"roi":[257,122,346,154],"font":20,"suffix":" cm"},
    "652":{"roi":[258,128,382,161],"font":20,"suffix":" mm"},
    "653":{"roi":[224,96,258,129],"font":20,"suffix":""},
    "654":{"roi":[181,82,292,115],"font":20,"suffix":" cm"},
    "664":{"roi":[294,140,383,174],"font":22,"suffix":" cm"},
    "665":{"roi":[365,199,442,232],"font":20,"suffix":" cm"},
    "666":{"roi":[340,183,474,216],"font":20,"suffix":" mm"},
    "667":{"roi":[282,135,316,167],"font":20,"suffix":""},
    "668":{"roi":[270,111,304,144],"font":20,"suffix":""},
    "669":{"roi":[262,104,382,139],"font":20,"suffix":" m"},
    "686":{"roi":[197,58,263,92],"font":20,"suffix":" cm"},
    "687":{"roi":[137,62,204,94],"font":20,"suffix":" cm"},
    "690":{"roi":[138,212,208,246],"font":20,"suffix":" cm"},
    "691":{"roi":[155,274,225,307],"font":20,"suffix":" cm"}
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(source: Path, destination: Path, *, value: str, spec: dict[str, Any], anchor: list[int]) -> None:
    ensure_directory(destination.parent)
    with Image.open(source) as opened:
        _render(opened.convert("RGB"), f"{value}{spec['suffix']}", {
            "roi_xyxy": spec["roi"],
            "background_mode": "roi_bright_median",
            "text_color": [0, 0, 0],
            "font_size": spec["font"],
            "text_anchor": anchor,
        }).save(destination)


def validate(paths: dict[str, Path], roi: list[int]) -> dict[str, Any]:
    arrays = {name: np.asarray(Image.open(path).convert("RGB")) for name, path in paths.items()}
    if len({array.shape for array in arrays.values()}) != 1:
        return {"passed": False, "reason": "dimension mismatch"}
    height, width = arrays["O"].shape[:2]
    x0, y0, x1, y1 = roi
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        return {"passed": False, "reason": "ROI outside image", "shape": [height, width]}
    outside = np.ones((height, width), dtype=bool)
    outside[y0:y1, x0:x1] = False
    original = arrays["O"]
    outside_exact = {name: bool(np.array_equal(original[outside], array[outside])) for name, array in arrays.items() if name != "O"}
    inside_diffs = {
        name: int(np.count_nonzero(np.any(original[y0:y1, x0:x1] != array[y0:y1, x0:x1], axis=-1)))
        for name, array in arrays.items() if name != "O"
    }
    return {
        "passed": bool(all(outside_exact.values()) and all(value > 0 for value in inside_diffs.values())),
        "shape": [height, width, 3],
        "outside_roi_exact_to_original": outside_exact,
        "inside_roi_diff_pixels": inside_diffs,
        "sha256": {name: sha256(path) for name, path in paths.items()},
    }


def review_sheet(base_dir: Path, paths: dict[str, Path], roi: list[int]) -> Path:
    labels = list(paths)
    originals = [Image.open(paths[label]).convert("RGB") for label in labels]
    scale = min(1.0, 420 / max(image.width for image in originals), 320 / max(image.height for image in originals))
    full = [image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale)))) for image in originals]
    crop_scale = min(8, max(2, 360 // max(roi[2]-roi[0], roi[3]-roi[1])))
    crops = [image.crop(tuple(roi)).resize(((roi[2]-roi[0])*crop_scale, (roi[3]-roi[1])*crop_scale), Image.Resampling.NEAREST) for image in originals]
    columns = min(5, len(labels))
    rows = (len(labels) + columns - 1) // columns
    cell_w = max(max(image.width for image in full), max(image.width for image in crops)) + 10
    cell_h = 28 + max(image.height for image in full) + 28 + max(image.height for image in crops)
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=15)
    for index, (label, image, crop) in enumerate(zip(labels, full, crops)):
        col, row = index % columns, index // columns
        x, y = col * cell_w, row * cell_h
        draw.text((x + 2, y + 3), label, fill="black", font=font)
        sheet.paste(image, (x, y + 28))
        cy = y + 28 + max(item.height for item in full)
        draw.text((x + 2, cy + 3), f"ROI x{crop_scale}", fill="black", font=font)
        sheet.paste(crop, (x, cy + 28))
    target = base_dir / "review_sheet.png"
    sheet.save(target)
    for image in originals + full + crops:
        image.close()
    return target


def main() -> None:
    screen = json.loads(SCREEN.read_text(encoding="utf-8"))
    all_rows = [*screen["phase_a_screen"], *screen["phase_b_screen"]]
    if len(all_rows) != 56 or {str(row["base_problem_id"]) for row in all_rows} != set(SPECS):
        raise RuntimeError("Render specs must exactly cover the prospectively frozen 56-base screen")
    rows = {str(row["sample_index"]): row for row in load_mathverse_rows(DATASET)}
    root = OUT / "fresh_edits/v1"
    ensure_directory(root)
    built_at = datetime.now(timezone.utc).isoformat()
    phase_a_manifest = []
    phase_b_manifest = []
    for phase_name, candidates in (("phase_a", screen["phase_a_screen"]), ("phase_b", screen["phase_b_screen"])):
        for item in candidates:
            base = str(item["base_problem_id"])
            spec = SPECS[base]
            dataset_row = rows[str(item["example_id"])]
            if str(dataset_row["problem_index"]) != base or str(dataset_row["problem_version"]) != "Vision Dominant":
                raise RuntimeError(f"Dataset identity mismatch for base {base}")
            source = resolve_image_path(DATASET, str(dataset_row["image"]))
            base_dir = root / phase_name / base
            metadata_path = base_dir / "edit_metadata.json"
            if metadata_path.is_file():
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                if metadata["phase"] != phase_name or str(metadata["example_id"]) != str(item["example_id"]):
                    raise RuntimeError(f"Existing edit signature mismatch for base {base}")
                record = {
                    "base_problem_id": base,
                    "example_id": str(item["example_id"]),
                    "phase": phase_name,
                    "variant": "Vision Dominant",
                    "target": item["target"],
                    "edit_metadata": str(metadata_path.relative_to(ROOT)),
                    "automatic_edit_status": "pass",
                    "manual_edit_status": metadata["manual_validation"]["status"],
                    "selection_used_attention": False,
                    "generation_outcome_inspected": False,
                    "stage3b9_value_or_causal_outcome_inspected": False
                }
                (phase_a_manifest if phase_name == "phase_a" else phase_b_manifest).append(record)
                print(f"resumed {phase_name} base {base}", flush=True)
                continue
            paths: dict[str, Path] = {"O": base_dir / "O/image.png", "O_sham": base_dir / "O_sham/image.png"}
            ensure_directory(paths["O"].parent)
            shutil.copy2(source, paths["O"])
            render(source, paths["O_sham"], value=str(item["original"]), spec=spec, anchor=[2, 1])
            if phase_name == "phase_a":
                paths["C"] = base_dir / "C/image.png"
                paths["C_sham"] = base_dir / "C_sham/image.png"
                render(source, paths["C"], value=str(item["counterfactual"]), spec=spec, anchor=[2, 1])
                render(source, paths["C_sham"], value=str(item["counterfactual"]), spec=spec, anchor=[3, 1])
            else:
                for index, value in enumerate(item["alternatives"], start=1):
                    paths[f"C{index}"] = base_dir / f"C{index}/image.png"
                    paths[f"C{index}_sham"] = base_dir / f"C{index}_sham/image.png"
                    render(source, paths[f"C{index}"], value=str(value), spec=spec, anchor=[2, 1])
                    render(source, paths[f"C{index}_sham"], value=str(value), spec=spec, anchor=[3, 1])
            checks = validate(paths, spec["roi"])
            if not checks["passed"]:
                raise RuntimeError(f"Automatic edit validation failed for base {base}: {checks}")
            sheet = review_sheet(base_dir, paths, spec["roi"])
            metadata = {
                **item,
                "phase": phase_name,
                "edit_version": "stage3b9_v1",
                "built_at": built_at,
                "source_image": str(source),
                "source_image_sha256": sha256(source),
                "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
                "target_evidence_roi_xyxy": spec["roi"],
                "render_suffix": spec["suffix"],
                "font_size": spec["font"],
                "construction": {
                    "renderer": "visual_reasoning.stage3a.edits._render",
                    "same_original_source_for_every_condition": True,
                    "same_roi_and_font": True,
                    "semantic_anchor": [2,1],
                    "sham_anchor": [3,1],
                    "selection_used_attention": False,
                    "selection_used_stage3b9_value_or_causal_outcomes": False
                },
                "automatic_validation": checks,
                "manual_validation": {"status":"pending","reviewer":None},
                "review_sheet": str(sheet.relative_to(ROOT))
            }
            write_json(base_dir / "edit_metadata.json", metadata)
            write_text(base_dir / "validation.md", f"# Stage 3B.9 edit validation — base {base}\n\nAutomatic pixel validation: **PASS**\n\nManual review: **PENDING**\n")
            record = {
                "base_problem_id": base,
                "example_id": str(item["example_id"]),
                "phase": phase_name,
                "variant": "Vision Dominant",
                "target": item["target"],
                "edit_metadata": str((base_dir / "edit_metadata.json").relative_to(ROOT)),
                "automatic_edit_status": "pass",
                "manual_edit_status": "pending",
                "selection_used_attention": False,
                "generation_outcome_inspected": False,
                "stage3b9_value_or_causal_outcome_inspected": False
            }
            (phase_a_manifest if phase_name == "phase_a" else phase_b_manifest).append(record)
            print(f"built {phase_name} base {base}", flush=True)
    write_jsonl(OUT / "phase_a_shared/candidate_screening.jsonl", phase_a_manifest)
    write_jsonl(OUT / "phase_b_local/candidate_screening.jsonl", phase_b_manifest)
    write_jsonl(root / "construction_manifest.jsonl", [*phase_a_manifest, *phase_b_manifest])
    print(json.dumps({"phase_a":len(phase_a_manifest),"phase_b":len(phase_b_manifest),"automatic_pass":56}, indent=2))


if __name__ == "__main__":
    main()
