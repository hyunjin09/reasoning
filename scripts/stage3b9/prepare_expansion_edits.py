#!/usr/bin/env python3
"""Build the outcome- and Value-blind Stage 3B.9 expansion edits."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from prepare_edit_repairs_v2 import render, review_sheet, sha256, text_fits, validate
from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
DATASET = Path("/data/dataset/MathVerse")
CONFIG = OUT / "config/expansion_screen.json"


SPECS = {
    "643":([320,203,405,232],18," cm"), "644":([367,120,450,150],18," cm"),
    "729":([226,33,271,62],16," cm"), "731":([148,0,205,26],16,"cm"),
    "732":([220,181,283,213],18,"cm"), "733":([207,53,281,82],18," cm"),
    "735":([0,232,78,264],18," cm"), "736":([187,313,252,344],18," cm"),
    "737":([202,155,257,184],18,"mm"), "738":([146,112,218,144],18," cm"),
    "739":([95,221,169,251],18," cm"), "742":([235,8,320,39],18," cm"),
    "746":([245,47,269,78],15,""), "747":([258,83,304,113],17," cm"),
    "748":([260,181,326,213],18," cm"), "749":([78,104,122,131],16,""),
    "750":([237,210,322,244],19," cm"), "751":([232,8,302,38],18,""),
    "756":([275,125,315,156],18,""), "759":([250,151,330,188],20,"°"),
    "761":([55,170,100,205],20,""), "771":([153,91,205,125],20,""),
    "773":([310,130,405,170],20,"°"), "774":([400,380,545,438],28,"°"),
    "730":([0,181,61,214],18," cm"), "734":([187,50,220,84],18,""),
    "740":([66,9,142,37],18,"mm"), "741":([66,8,143,38],18,"mm"),
    "744":([222,140,330,180],20,"cm"), "745":([61,82,92,118],16,""),
    "753":([310,35,350,70],18,""), "754":([140,100,200,132],18,"°"),
    "758":([175,42,225,76],18,""), "762":([0,169,35,212],18,""),
}


def main() -> None:
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    candidates = [("phase_a", row) for row in payload["phase_a_screen"]] + [("phase_b", row) for row in payload["phase_b_screen"]]
    if len(candidates) != 34 or {str(row["base_problem_id"]) for _, row in candidates} != set(SPECS):
        raise RuntimeError("Expansion specs must exactly cover the frozen 34-problem screen")
    rows = {str(row["sample_index"]): row for row in load_mathverse_rows(DATASET)}
    root = OUT / "fresh_edits/expansion_v1"
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"Expansion edits already exist: {root}")
    built_at = datetime.now(timezone.utc).isoformat()
    manifest = []
    for phase, item in candidates:
        base = str(item["base_problem_id"])
        dataset_row = rows[str(item["example_id"])]
        if str(dataset_row["problem_index"]) != base or str(dataset_row["problem_version"]) != "Vision Dominant":
            raise RuntimeError(f"Expansion dataset identity mismatch for base {base}")
        roi, font, suffix = SPECS[base]
        spec = {"roi": roi, "font": font, "suffix": suffix}
        source = resolve_image_path(DATASET, str(dataset_row["image"]))
        base_dir = root / phase / base
        paths = {"O": base_dir / "O/image.png", "O_sham": base_dir / "O_sham/image.png"}
        ensure_directory(paths["O"].parent)
        shutil.copy2(source, paths["O"])
        values = [str(item["original"])] + ([str(item["counterfactual"])] if phase == "phase_a" else [str(value) for value in item["alternatives"]])
        for value in values:
            if not text_fits(f"{value}{suffix}", spec, [4, 2]):
                raise RuntimeError(f"Expansion text does not fit base {base}: {value}{suffix}")
        render(source, paths["O_sham"], value=values[0], spec=spec, anchor=[4, 2])
        if phase == "phase_a":
            paths["C"] = base_dir / "C/image.png"; paths["C_sham"] = base_dir / "C_sham/image.png"
            render(source, paths["C"], value=values[1], spec=spec, anchor=[4, 2]); render(source, paths["C_sham"], value=values[1], spec=spec, anchor=[5, 2])
        else:
            for index, value in enumerate(values[1:], start=1):
                paths[f"C{index}"] = base_dir / f"C{index}/image.png"; paths[f"C{index}_sham"] = base_dir / f"C{index}_sham/image.png"
                render(source, paths[f"C{index}"], value=value, spec=spec, anchor=[4, 2]); render(source, paths[f"C{index}_sham"], value=value, spec=spec, anchor=[5, 2])
        checks = validate(paths, roi)
        if not checks["passed"]:
            raise RuntimeError(f"Expansion automatic validation failed for base {base}: {checks}")
        sheet = review_sheet(base_dir, paths, roi)
        metadata = {
            **item, "phase": phase, "edit_version": "stage3b9_expansion_v1_edge_preserving", "built_at": built_at,
            "source_image": str(source), "source_image_sha256": sha256(source),
            "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
            "target_evidence_roi_xyxy": roi, "render_suffix": suffix, "font_size": font,
            "construction": {
                "renderer": "visual_reasoning.stage3b9.edits.render_preserving_crossing_strokes",
                "same_original_source_for_every_condition": True, "semantic_anchor": [4,2], "sham_anchor": [5,2],
                "edge_connected_original_strokes_restored": True, "selection_used_attention": False,
                "selection_used_expansion_generation_outcomes": False, "selection_used_stage3b9_value_or_causal_outcomes": False,
            },
            "automatic_validation": checks, "manual_validation": {"status": "pending", "reviewer": None},
            "review_sheet": str(sheet.relative_to(ROOT)),
        }
        write_json(base_dir / "edit_metadata.json", metadata)
        write_text(base_dir / "validation.md", f"# Stage 3B.9 expansion edit — base {base}\n\nAutomatic containment/dimension validation: **PASS**\n\nManual review: **PENDING**\n")
        manifest.append({
            "base_problem_id": base, "example_id": str(item["example_id"]), "phase": phase,
            "edit_version": metadata["edit_version"], "edit_metadata": str((base_dir / "edit_metadata.json").relative_to(ROOT)),
            "automatic_edit_status": "pass", "manual_edit_status": "pending", "generation_outcome_inspected": False,
            "stage3b9_value_or_causal_outcome_inspected": False,
        })
        print(f"built expansion {phase} base {base}", flush=True)
    write_jsonl(root / "construction_manifest.jsonl", manifest)
    print(json.dumps({"built": len(manifest), "phase_a": 24, "phase_b": 10}, indent=2))


if __name__ == "__main__":
    main()
