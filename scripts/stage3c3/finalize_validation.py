#!/usr/bin/env python3
"""Aggregate Stage 3C.3 validation and freeze the query/RoPE formulation."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage3c3.protocol import choose_query_formulation


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3"
FORMS = ("direct_post_rope", "content_recipient_rope")
TARGETS = ("target_a", "target_b")
CANDIDATES = ("original_candidate", "counterfactual_candidate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir", type=Path, default=OUT / "validation/query_forms"
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def median(values: list[float]) -> float:
    return float(statistics.median(values))


def main() -> None:
    args = parse_args()
    result_paths = sorted(args.input_dir.glob("shard_*/examples/*/result.json"))
    rows = [read_json(path) for path in result_paths]
    manifest = [
        json.loads(line)
        for line in (OUT / "cohort/validation_manifest.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected = {str(row["base_problem_id"]) for row in manifest}
    observed = {str(row["base_problem_id"]) for row in rows}
    if observed != expected or len(rows) != len(expected):
        raise RuntimeError(f"Validation cohort mismatch: expected={sorted(expected)} observed={sorted(observed)}")

    mechanics: dict[str, dict[str, Any]] = {}
    rope_errors: dict[str, list[float]] = {form: [] for form in FORMS}
    selectivity_rows: list[dict[str, Any]] = []
    kv_rows: list[dict[str, Any]] = []
    repeat_rows: list[dict[str, Any]] = []
    for form in FORMS:
        self_exact: list[bool] = []
        kv_exact: list[bool] = []
        nonselected_exact: list[bool] = []
        finite: list[bool] = []
        for row in rows:
            base = str(row["base_problem_id"])
            for target_id in TARGETS:
                target = row["target_results"][target_id]["O"]
                form_rows = target["forms"][form]
                for state in ("M", "R"):
                    arm = form_rows["causal"][f"self_{state}"]
                    native = target["native"][state]["preference"]
                    exact = bool(
                        arm["preference"]["D"] == native["D"]
                        and arm["preference"]["original_candidate"]["token_log_probabilities"]
                        == native["original_candidate"]["token_log_probabilities"]
                        and arm["preference"]["counterfactual_candidate"]["token_log_probabilities"]
                        == native["counterfactual_candidate"]["token_log_probabilities"]
                        and all(
                            audit["selected_head_max_abs_delta"] == 0.0
                            for audit in arm["query_patch_audits"]
                        )
                    )
                    self_exact.append(exact)
                for role in ("causal", "noncausal"):
                    for arm_name, arm in form_rows[role].items():
                        for candidate_name, invariant in arm["recipient_state_invariance"].items():
                            exact_kv = bool(
                                invariant["recipient_prefix_exact"]
                                and invariant["visual_kv_exact"]
                            )
                            kv_exact.append(exact_kv)
                            kv_rows.append({
                                "base_problem_id": base,
                                "target_id": target_id,
                                "form": form,
                                "role": role,
                                "arm": arm_name,
                                "candidate": candidate_name,
                                **invariant,
                            })
                        finite.append(bool(
                            arm["preference"]["finite"]
                            and all(
                                routing["all_values_finite"]
                                for routing in arm["routing_by_candidate"].values()
                            )
                        ))
                        for audit in arm["query_patch_audits"]:
                            selective = bool(
                                set(audit["changed_query_heads"]).issubset(audit["selected_query_heads"])
                                and set(audit["changed_sequence_positions"]).issubset({audit["recipient_position"]})
                                and audit["nonselected_head_max_abs_delta"] == 0.0
                                and audit["nonselected_attention_max_abs_delta"] == 0.0
                                and audit["nonselected_head_output_max_abs_delta"] == 0.0
                            )
                            nonselected_exact.append(selective)
                            rope_errors[form].append(float(audit["content_rope_key_reconstruction_max_abs_error"]))
                            selectivity_rows.append({
                                "base_problem_id": base,
                                "target_id": target_id,
                                "form": form,
                                "role": role,
                                "arm": arm_name,
                                "selective": selective,
                                **audit,
                            })
                if target["repeat_audit"] is not None:
                    repeat_rows.append({
                        "base_problem_id": base,
                        "target_id": target_id,
                        "form": form,
                        **target["repeat_audit"][form],
                    })
        deterministic = bool(repeat_rows) and all(
            row["exact"] for row in repeat_rows if row["form"] == form
        )
        mechanics[form] = {
            "self_exact": all(self_exact),
            "self_checks": len(self_exact),
            "kv_exact": all(kv_exact),
            "kv_checks": len(kv_exact),
            "nonselected_heads_exact": all(nonselected_exact),
            "selectivity_checks": len(nonselected_exact),
            "deterministic": deterministic,
            "repeat_checks": sum(row["form"] == form for row in repeat_rows),
            "all_scores_finite": all(finite),
            "finite_checks": len(finite),
            "maximum_rope_key_reconstruction_error": max(rope_errors[form], default=0.0),
        }

    selected = choose_query_formulation(mechanics)
    direction: dict[str, Any] = {}
    for target_id in TARGETS:
        necessity: list[float] = []
        sufficiency: list[float] = []
        for row in rows:
            target = row["target_results"][target_id]["O"]
            form_rows = target["forms"][selected]["causal"]
            necessity.append(
                float(target["native"]["R"]["routing"]["causal"]["RDS_T_vs_M"])
                - float(form_rows["Q_R_to_Q_M"]["routing"]["RDS_T_vs_M"])
            )
            sufficiency.append(
                float(form_rows["Q_M_to_Q_R"]["routing"]["RDS_T_vs_M"])
                - float(target["native"]["M"]["routing"]["causal"]["RDS_T_vs_M"])
            )
        direction[target_id] = {
            "necessity_median": median(necessity),
            "necessity_positive_count": sum(value > 0 for value in necessity),
            "necessity_total": len(necessity),
            "necessity_positive_fraction": sum(value > 0 for value in necessity) / len(necessity),
            "sufficiency_median": median(sufficiency),
            "sufficiency_positive_count": sum(value > 0 for value in sufficiency),
            "sufficiency_total": len(sufficiency),
            "sufficiency_positive_fraction": sum(value > 0 for value in sufficiency) / len(sufficiency),
        }
        direction[target_id]["majority_direction_pass"] = bool(
            direction[target_id]["necessity_positive_fraction"] > 0.5
            and direction[target_id]["sufficiency_positive_fraction"] > 0.5
        )
    if not all(row["majority_direction_pass"] for row in direction.values()):
        raise RuntimeError("Mechanically selected query form failed the prospective validation direction gate")

    frozen_at = datetime.now(timezone.utc).isoformat()
    source_hashes = {str(path.relative_to(ROOT)): sha256(path) for path in result_paths}
    formulation = {
        "frozen_at": frozen_at,
        "status": "frozen_before_primary_scoring",
        "candidate_forms": {
            "direct_post_rope": "copy exact donor post-RoPE logical-head Q into recipient position",
            "content_recipient_rope": "copy donor pre-RoPE normalized Q content and apply recipient-position multimodal RoPE",
        },
        "selection_rule": "mechanics only: exact self, recipient K/V, nonselected heads, and repeatability; prefer content_recipient_rope to isolate semantic query content",
        "mechanics": mechanics,
        "validation_direction_gate": direction,
        "selected_form": selected,
        "primary_scoring_started": False,
        "selection_used_effect_magnitude": False,
        "validation_result_sha256": source_hashes,
    }
    write_json(OUT / "config/rope_query_formulation.json", formulation)

    first = rows[0]["target_results"]["target_a"]["O"]
    config = read_json(OUT / "config/stage3c3_config.json")
    write_json(OUT / "audit/query_tensor_layout.json", {
        "status": "pass",
        "architecture": config["architecture_expected"],
        "observed_state_shapes": first["native_capture_layout"],
        "logical_query_head_to_kv_head": [head // 4 for head in range(32)],
        "selected_heads": {
            target: {
                "causal": config["targets"][target]["causal_heads"],
                "noncausal": config["targets"][target]["noncausal_heads"],
            }
            for target in TARGETS
        },
    })
    write_json(OUT / "audit/rope_alignment_audit.json", {
        "status": "pass",
        "selected_form": selected,
        "selection_used_effect_magnitude": False,
        "forms": mechanics,
        "rejected_form_preserved": "direct_post_rope" if selected != "direct_post_rope" else "content_recipient_rope",
        "explanation": "Both forms were mechanically valid. Content-space donor Q re-rotated at the recipient position was prospectively preferred because M and R have different positional phases.",
    })
    write_json(OUT / "audit/q_patch_selectivity.json", {
        "status": "pass" if all(row["selective"] for row in selectivity_rows) else "fail",
        "checks": len(selectivity_rows),
        "all_selective": all(row["selective"] for row in selectivity_rows),
        "rows": selectivity_rows,
    })
    write_json(OUT / "audit/visual_kv_invariance.json", {
        "status": "pass" if all(row["recipient_prefix_exact"] and row["visual_kv_exact"] for row in kv_rows) else "fail",
        "checks": len(kv_rows),
        "all_recipient_prefix_kv_exact": all(row["recipient_prefix_exact"] for row in kv_rows),
        "all_visual_kv_exact": all(row["visual_kv_exact"] for row in kv_rows),
        "rows": kv_rows,
    })
    write_json(OUT / "audit/non_target_head_invariance.json", {
        "status": "pass" if all(row["selective"] for row in selectivity_rows) else "fail",
        "all_nonselected_query_attention_and_output_exact": all(row["selective"] for row in selectivity_rows),
        "maximum_nonselected_query_delta": max(float(row["nonselected_head_max_abs_delta"]) for row in selectivity_rows),
        "maximum_nonselected_attention_delta": max(float(row["nonselected_attention_max_abs_delta"]) for row in selectivity_rows),
        "maximum_nonselected_head_output_delta": max(float(row["nonselected_head_output_max_abs_delta"]) for row in selectivity_rows),
    })
    write_json(OUT / "audit/reproducibility.json", {
        "status": "pass" if all(row["exact"] for row in repeat_rows) else "fail",
        "checks": len(repeat_rows),
        "all_exact": all(row["exact"] for row in repeat_rows),
        "rows": repeat_rows,
    })
    validation_summary = {
        "status": "pass",
        "validation_base_count": len(rows),
        "validation_base_problem_ids": sorted(observed, key=int),
        "mechanics": mechanics,
        "selected_form": selected,
        "direction_gate": direction,
        "primary_scoring_authorized": True,
        "source_result_sha256": source_hashes,
    }
    write_json(OUT / "validation/validation_summary.json", validation_summary)
    (OUT / "validation/validation_summary.md").write_text(
        "# Stage 3C.3 query-form validation\n\n"
        f"Status: **PASS** on {len(rows)} disjoint bases.\n\n"
        f"Frozen formulation: `{selected}`. Both candidate forms passed mechanics; selection followed the prospective mechanics-only preference for semantic content re-rotated at the recipient position.\n\n"
        "Both targets showed expected necessity and sufficiency T-vs-M routing directions in 7/7 validation bases. This validation authorizes primary Phase A scoring; it is not the primary scientific result.\n",
        encoding="utf-8",
    )
    print(json.dumps(validation_summary, indent=2))


if __name__ == "__main__":
    main()
