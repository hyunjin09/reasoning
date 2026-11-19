#!/usr/bin/env python3
"""Build Stage 3C.9 O/O_sham/C/C_sham edits from frozen manual specs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3c9.edits import construct_quartet, normalize_numeric_surface, sha256


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semantic-manifest", type=Path, required=True)
    parser.add_argument("--specs", type=Path, required=True)
    parser.add_argument("--append", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    semantic = {str(row["base_problem_id"]): row for row in read_jsonl(args.semantic_manifest)}
    specs = read_jsonl(args.specs)
    if not specs:
        raise ValueError("No edit specs supplied")
    dataset_root = Path(read_json(OUT / "config/stage3c9_config.json")["dataset_root"])
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(dataset_root)}
    manifest_path = OUT / "cohort/edit_manifest_pending.jsonl"
    manifest = read_jsonl(manifest_path) if args.append and manifest_path.is_file() else []
    existing = {str(row["base_problem_id"]): row for row in manifest}
    if len(existing) != len(manifest):
        raise RuntimeError("Existing pending edit manifest contains duplicate bases")
    built_at = datetime.now(timezone.utc).isoformat()
    for spec in specs:
        base = str(spec["base_problem_id"])
        if base not in semantic:
            raise RuntimeError(f"Edit spec base {base} is not semantic-audit accepted")
        item = semantic[base]
        if str(spec["example_id"]) != str(item["example_id"]):
            raise RuntimeError(f"Example mismatch for base {base}")
        for key in ("original_value", "counterfactual_value"):
            if normalize_numeric_surface(str(spec[key])) != normalize_numeric_surface(str(item[key])):
                raise RuntimeError(f"{key} mismatch for base {base}")
        if spec.get("attention_used") is not False or spec.get("causal_scores_available") is not False:
            raise RuntimeError(f"Edit spec provenance is not score-blind for base {base}")
        if base in existing:
            metadata = read_json(ROOT / existing[base]["edit_metadata"])
            stable = ("example_id", "original_value", "counterfactual_value", "roi_xyxy", "font_size", "text_anchor", "render_suffix", "renderer", "counterfactual_sham_anchor_delta")
            if any(metadata.get(key) != spec.get(key) for key in stable):
                raise RuntimeError(f"Existing edit specification changed for base {base}")
            continue
        row = dataset[str(item["example_id"])]
        source = resolve_image_path(dataset_root, str(row["image"]))
        base_dir = OUT / "counterfactuals" / base
        built = construct_quartet(source_image=source, target_dir=base_dir, spec=spec)
        metadata = {
            **spec,
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "edit_version": "stage3c9_v1",
            "built_at": built_at,
            "source_image": str(source.resolve()),
            "source_image_sha256": sha256(source),
            "paths": {name: str(path.relative_to(ROOT)) for name, path in built["paths"].items()},
            "target_evidence_roi_xyxy": [int(value) for value in spec["roi_xyxy"]],
            "construction": built["construction"],
            "automatic_validation": built["automatic_validation"],
            "manual_validation": {"status": "pending", "reviewer": None, "causal_scores_available": False},
            "review_sheet": str(built["review_sheet"].relative_to(ROOT)),
        }
        write_json(base_dir / "edit_metadata.json", metadata)
        (base_dir / "validation.md").write_text(
            f"# Stage 3C.9 edit validation — base {base}\n\nAutomatic containment/dimension validation: **PASS**\n\nManual review: **PENDING**\n",
            encoding="utf-8",
        )
        manifest.append({
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "screen_order": int(item["screen_order"]),
            "edit_metadata": str((base_dir / "edit_metadata.json").relative_to(ROOT)),
            "automatic_edit_status": "pass",
            "manual_edit_status": "pending",
            "selection_used_attention": False,
            "causal_scores_available": False,
        })
    manifest.sort(key=lambda row: int(row["screen_order"]))
    write_jsonl(manifest_path, manifest)
    print(json.dumps({"pending_total": len(manifest), "automatic_pass": len(manifest)}, indent=2))


if __name__ == "__main__":
    main()
