#!/usr/bin/env python3
"""Run the prospectively gated Stage 3B.3 two-layer refinement scan."""

from __future__ import annotations

import argparse
import gc
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from scripts.stage3b3.run_coarse import (
    ALL_LAYERS,
    CANDIDATES,
    CONDITIONS,
    ROOT,
    SEED,
    finite_preference,
    public_preference,
    scores_exact,
    stage3b2_coordinate,
)
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b2.runtime import capture_audit_valid, capture_preference_visual_kv
from visual_reasoning.stage3b3.metrics import necessity_metrics, sufficiency_metrics
from visual_reasoning.stage3b3.runtime import score_preference_with_layer_visual_source


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--fine-windows", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--stage3b2-results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--required-gpu-class", choices=("A5000", "A6000"), default="A5000")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to((ROOT / "outputs/stage3b3/raw/fine").resolve())
    manifest = read_jsonl(args.manifest)
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(args.annotations)}
    references = {str(row["base_problem_id"]): row for row in read_jsonl(args.stage3b2_results)}
    fine_payload = json.loads(args.fine_windows.read_text(encoding="utf-8"))
    windows = fine_payload["fine_windows"]
    if not windows:
        raise RuntimeError("Fine runner must not be launched when the frozen gate selects no windows")
    signature = {
        "manifest": str(args.manifest.resolve()),
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "fine_windows": windows,
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "seed": SEED,
        "required_gpu_class": args.required_gpu_class,
    }
    config_path = output_dir / "config.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.resume or not config_path.is_file():
            raise FileExistsError(f"Non-empty output requires --resume: {output_dir}")
        if json.loads(config_path.read_text(encoding="utf-8"))["run_signature"] != signature:
            raise RuntimeError("Resume signature mismatch")
    else:
        ensure_directory(output_dir)
        write_json(config_path, {"created_at": datetime.now(timezone.utc).isoformat(), "run_signature": signature})
        write_jsonl(output_dir / "manifest.jsonl", manifest)

    data_rows = load_mathverse_rows(args.dataset_root)
    by_example = {str(row["sample_index"]): row for row in data_rows}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if args.required_gpu_class not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {args.required_gpu_class}, observed {environment['gpu_name']}")
    write_json(output_dir / "environment.json", environment)
    layer_count = int(model.config.text_config.num_hidden_layers)
    kv_heads = int(model.config.text_config.num_key_value_heads)
    head_dim = int(model.config.text_config.head_dim)
    results: list[dict[str, Any]] = []
    peak_gpu_bytes = 0

    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        example = str(item["example_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if args.resume and result_path.is_file():
            results.append(json.loads(result_path.read_text(encoding="utf-8")))
            print(f"[{item_index + 1}/{len(manifest)}] resumed base {base}", flush=True)
            continue
        ensure_directory(result_path.parent)
        annotation = annotations[base]
        reference = references[base]
        context = [int(value) for value in annotation["history_before_ed_token_ids"]]
        ed = int(annotation["ed_generated_index"])
        candidate_original = [int(value) for value in annotation["original_divergent_suffix_ids"]]
        candidate_counterfactual = [int(value) for value in annotation["counterfactual_divergent_suffix_ids"]]
        prepared: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        for condition in CONDITIONS:
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, by_example[example], ROOT / item["conditions"][condition], device="cuda"
            )
        prompt_ids = [metadata[name]["prompt_token_ids"] for name in CONDITIONS]
        visual_sets = [metadata[name]["visual_token_indices"] for name in CONDITIONS]
        grids = [metadata[name]["image_grid_thw"] for name in CONDITIONS]
        layout_exact = bool(
            all(value == prompt_ids[0] for value in prompt_ids[1:])
            and all(value == visual_sets[0] for value in visual_sets[1:])
            and all(value == grids[0] for value in grids[1:])
        )
        if not layout_exact:
            raise RuntimeError(f"Condition layout mismatch for base {base}")
        visual_indices = [int(value) for value in visual_sets[0]]
        captures = {
            condition: capture_preference_visual_kv(
                model=model,
                prepared=prepared[condition],
                context_token_ids=context,
                candidate_original_ids=candidate_original,
                candidate_counterfactual_ids=candidate_counterfactual,
                visual_indices=visual_indices,
                seed=SEED,
            )
            for condition in CONDITIONS
        }
        capture_valid = all(
            capture_audit_valid(
                captures[condition]["capture_audits"][candidate],
                visual_indices=visual_indices,
                layer_count=layer_count,
                kv_heads=kv_heads,
                head_dim=head_dim,
            )
            for condition in CONDITIONS
            for candidate in CANDIDATES
        )
        d_oo = float(captures["original"]["D"])
        d_cc = float(captures["counterfactual"]["D"])
        rows = []
        for coordinate, switch_index in (("Ed_minus_1", ed - 1), ("Ed", ed)):
            ref = stage3b2_coordinate(reference, coordinate)
            all_bri = float(ref["BRI"])
            cache: dict[tuple[str, tuple[int, ...]], dict[str, Any]] = {}

            def switched(kind: str, layers: list[int]) -> dict[str, Any]:
                key = (kind, tuple(sorted(layers)))
                if key not in cache:
                    recipient, donor = {
                        "O_to_C": ("original", "counterfactual"),
                        "C_to_O": ("counterfactual", "original"),
                        "O_to_sham": ("original", "sham"),
                        "self_O": ("original", "original"),
                    }[kind]
                    cache[key] = score_preference_with_layer_visual_source(
                        model=model,
                        prepared=prepared[recipient],
                        context_token_ids=context,
                        candidate_original_ids=candidate_original,
                        candidate_counterfactual_ids=candidate_counterfactual,
                        source_layers_by_candidate=captures[donor]["source_layers"],
                        visual_indices=visual_indices,
                        switch_generated_index=switch_index,
                        selected_layers=key[1],
                        seed=SEED,
                    )
                return cache[key]

            for window in windows:
                selected = [int(value) for value in window["layers"]]
                complement = [value for value in ALL_LAYERS if value not in set(selected)]
                selective = {name: switched(name, selected) for name in ("O_to_C", "C_to_O", "O_to_sham", "self_O")}
                restored = {name: switched(name, complement) for name in ("O_to_C", "C_to_O", "O_to_sham", "self_O")}
                sufficiency = sufficiency_metrics(
                    d_oo=d_oo,
                    d_cc=d_cc,
                    d_o_to_c=float(selective["O_to_C"]["D"]),
                    d_c_to_o=float(selective["C_to_O"]["D"]),
                    d_o_to_sham=float(selective["O_to_sham"]["D"]),
                    all_layer_bri=all_bri,
                )
                necessity = necessity_metrics(
                    d_o_to_c_all=float(ref["D_OC"]),
                    d_c_to_o_all=float(ref["D_CO"]),
                    d_o_to_c_except_window=float(restored["O_to_C"]["D"]),
                    d_c_to_o_except_window=float(restored["C_to_O"]["D"]),
                    d_o_to_sham_all=float(ref["D_OS"]),
                    d_o_to_sham_except_window=float(restored["O_to_sham"]["D"]),
                    all_layer_bri=all_bri,
                )
                rows.append(
                    {
                        "coordinate": coordinate,
                        "switch_generated_index": switch_index,
                        **window,
                        **sufficiency,
                        **necessity,
                        "sufficiency_bidirectionally_source_consistent": sufficiency[
                            "bidirectionally_source_consistent"
                        ],
                        "necessity_bidirectionally_source_consistent": necessity[
                            "bidirectionally_source_consistent"
                        ],
                        "selective_controls": {name: public_preference(value) for name, value in selective.items()},
                        "restoration_controls": {name: public_preference(value) for name, value in restored.items()},
                        "selective_self_exact": scores_exact(selective["self_O"], captures["original"]),
                        "restoration_self_exact": scores_exact(restored["self_O"], captures["original"]),
                        "all_audits_valid": all(value["all_layer_switch_audits_valid"] for value in (*selective.values(), *restored.values())),
                        "all_finite": all(finite_preference(value) for value in (*selective.values(), *restored.values())),
                    }
                )
        peak_gpu_bytes = max(peak_gpu_bytes, int(torch.cuda.max_memory_allocated()))
        result = {
            "base_problem_id": base,
            "example_id": example,
            "evidence_type": item["edit_tier"],
            "ed_alignment": reference["ed_alignment"],
            "condition_layout_exact": layout_exact,
            "capture_all_layers_valid": capture_valid,
            "selection_used_attention": False,
            "fine_rows": rows,
        }
        write_json(result_path, result)
        results.append(result)
        print(f"[{item_index + 1}/{len(manifest)}] completed base {base}", flush=True)
        del prepared, captures, rows
        gc.collect()
        torch.cuda.empty_cache()

    write_jsonl(output_dir / "results.jsonl", results)
    write_json(
        output_dir / "result.json",
        {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "base_problem_count": len(results),
            "fine_window_count": len(windows),
            "peak_gpu_allocated_bytes": peak_gpu_bytes,
            "all_controls_valid": all(
                row["condition_layout_exact"]
                and row["capture_all_layers_valid"]
                and all(
                    point["selective_self_exact"]
                    and point["restoration_self_exact"]
                    and point["all_audits_valid"]
                    and point["all_finite"]
                    for point in row["fine_rows"]
                )
                for row in results
            ),
        },
    )


if __name__ == "__main__":
    main()
