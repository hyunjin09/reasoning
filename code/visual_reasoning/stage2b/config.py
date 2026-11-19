"""Prospectively frozen Stage 2B pilot configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PILOT_EXAMPLE_IDS = ("699", "739", "2799", "3044", "3764")
LOCAL_HORIZON_TOKENS = 32

# These image-grid positions were chosen before any Stage 2B causal outputs were
# inspected. They avoid both frozen evidence ROIs and do not contain the labeled
# numerical evidence items. Values are zero-based visual-focus columns, not
# language-prompt positions.
IRRELEVANT_FOCUS_COLUMNS: dict[str, dict[str, list[int]]] = {
    "699": {
        "A": [9, 10, 20, 21],
        "B": [7, 8, 9, 10, 18, 19, 20, 21, 29, 30, 31, 32, 40, 41, 42, 43],
    },
    "739": {
        "A": [0, 1, 2, 12, 13, 14],
        "B": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
    },
    "2799": {
        "A": [7, 8, 9, 17, 18, 19],
        "B": [3, 4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 17, 18, 19, 29],
    },
    "3044": {
        "A": [247, 248, 249, 250, 268, 269, 270, 271, 289, 290, 291, 292],
        "B": [17, 18, 19, 38, 39, 40],
    },
    "3764": {
        "A": [6, 7, 8, 9, 10, 11, 12, 13, 21, 22, 36, 37, 51, 52, 66, 67, 81, 82, 96, 97],
        # ROI B covers 42/105 tokens. The only exact-count control disjoint from
        # both evidence ROIs is necessarily broad; this predeclared complement
        # control is a known interpretation limitation, not an outcome-driven
        # adjustment. Focus column 0 remains unmasked.
        "B": [],
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _window_tuple(row: dict[str, Any]) -> tuple[int, int]:
    return int(row["start_token"]), int(row["end_token"])


def _select_linked_windows(candidate: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    a_computation = {_window_tuple(row): row for row in candidate["A_computation_windows"]}
    b_computation = {_window_tuple(row): row for row in candidate["B_computation_windows"]}
    for key in sorted(set(a_computation) & set(b_computation)):
        joint = a_computation[key]
        joint_start = int(joint["start_token"])
        prior_a = [row for row in candidate["A_acquisition_windows"] if int(row["end_token"]) <= joint_start]
        prior_b = [row for row in candidate["B_acquisition_windows"] if int(row["end_token"]) <= joint_start]
        if prior_a and prior_b:
            selected_a = max(prior_a, key=lambda row: int(row["end_token"]))
            selected_b = max(prior_b, key=lambda row: int(row["end_token"]))
            return selected_a, selected_b, joint
    raise ValueError("No joint computation window has preceding A and B acquisition windows")


def build_frozen_pilot_specs(stage2a_examples_root: Path, stage1_examples_root: Path) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for example_id in PILOT_EXAMPLE_IDS:
        stage2a = stage2a_examples_root / example_id
        stage1 = stage1_examples_root / example_id
        roi_a = _load_json(stage2a / "roi_A.json")
        roi_b = _load_json(stage2a / "roi_B.json")
        candidate = _load_json(stage2a / "candidate_intervention_windows.json")
        input_record = _load_json(stage1 / "input.json")
        selected_a, selected_b, joint = _select_linked_windows(candidate)

        visual_indices = [int(value) for value in input_record["visual_token_indices"]]
        roi_a_indices = [int(value) for value in roi_a["ROI_visual_token_indices"]]
        roi_b_indices = [int(value) for value in roi_b["ROI_visual_token_indices"]]
        focus_controls = {key: list(values) for key, values in IRRELEVANT_FOCUS_COLUMNS[example_id].items()}
        if example_id == "3764":
            evidence_prompt = set(roi_a_indices) | set(roi_b_indices)
            focus_controls["B"] = [
                focus_index
                for focus_index, prompt_index in enumerate(visual_indices)
                if prompt_index not in evidence_prompt and focus_index != 0
            ]

        controls: dict[str, list[int]] = {}
        for window_name in ("A", "B"):
            focus_columns = focus_controls[window_name]
            if len(set(focus_columns)) != len(focus_columns):
                raise ValueError(f"Duplicate irrelevant focus columns for {example_id}/{window_name}")
            if not focus_columns or min(focus_columns) < 0 or max(focus_columns) >= len(visual_indices):
                raise ValueError(f"Invalid irrelevant focus columns for {example_id}/{window_name}")
            controls[window_name] = [visual_indices[index] for index in focus_columns]

        evidence_set = set(roi_a_indices) | set(roi_b_indices)
        if not set(roi_a_indices).isdisjoint(roi_b_indices):
            raise ValueError(f"Frozen A/B ROIs overlap for {example_id}")
        if not evidence_set.issubset(visual_indices):
            raise ValueError(f"Frozen ROI is outside visual tokens for {example_id}")
        for window_name, irrelevant in controls.items():
            if not set(irrelevant).isdisjoint(evidence_set):
                raise ValueError(f"Irrelevant control overlaps evidence for {example_id}/{window_name}")
            target_count = len(roi_a_indices if window_name == "A" else roi_b_indices)
            if abs(len(irrelevant) - target_count) > 1:
                raise ValueError(f"Irrelevant control is not size matched for {example_id}/{window_name}")

        specs[example_id] = {
            "example_id": example_id,
            "selection_rule": (
                "earliest frozen computation window shared by A and B with preceding acquisition windows; "
                "latest preceding A and B acquisition windows"
            ),
            "local_evaluation_horizon_tokens": LOCAL_HORIZON_TOKENS,
            "A_window": list(_window_tuple(selected_a)),
            "B_window": list(_window_tuple(selected_b)),
            "joint_computation_window": list(_window_tuple(joint)),
            "A_window_source": selected_a,
            "B_window_source": selected_b,
            "joint_computation_window_source": joint,
            "roi_A_visual_token_indices": roi_a_indices,
            "roi_B_visual_token_indices": roi_b_indices,
            "roi_A_visual_token_count": len(roi_a_indices),
            "roi_B_visual_token_count": len(roi_b_indices),
            "irrelevant_A_visual_focus_column_indices": focus_controls["A"],
            "irrelevant_A_visual_token_indices": controls["A"],
            "irrelevant_A_visual_token_count": len(controls["A"]),
            "irrelevant_B_visual_focus_column_indices": focus_controls["B"],
            "irrelevant_B_visual_token_indices": controls["B"],
            "irrelevant_B_visual_token_count": len(controls["B"]),
            "all_visual_token_indices": visual_indices,
            "prompt_token_count": int(input_record["prompt_token_count"]),
            "stage1_generated_token_count": int(_load_json(stage1 / "generation.json")["generated_token_count"]),
            "control_notes": (
                "For 3764/B the exact-count disjoint control spans nearly all remaining non-evidence tokens because "
                "the target ROI occupies 42/105 visual tokens; treat that comparison as a weak spatial control."
                if example_id == "3764"
                else "Manually selected same-count grid cells outside both frozen evidence ROIs and labeled evidence facts."
            ),
        }
    return specs

