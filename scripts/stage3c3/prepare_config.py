#!/usr/bin/env python3
"""Freeze the prospective Stage 3C.3 cohort, states, controls, and gates."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage3c3.protocol import split_validation_primary


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3"
SEED = 20260903
VALIDATION_COUNT = 7


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def token_hash(values: list[int]) -> str:
    payload = json.dumps([int(value) for value in values], separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def main() -> None:
    created = datetime.now(timezone.utc).isoformat()
    plan = ROOT / "plan/stage3c3_plan.md"
    source_manifest_path = ROOT / "outputs/stage3c2/cohort/primary_dissociation_manifest.jsonl"
    source_pairs_path = ROOT / "outputs/stage3c2/annotations/state_pair_annotations.jsonl"
    source_events_path = ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl"
    source_targets_path = ROOT / "outputs/stage3c2/config/frozen_targets.json"
    source_config = read_json(ROOT / "outputs/stage3c2/config/stage3c2_config.json")
    source_rows = read_jsonl(source_manifest_path)
    source_pairs = read_jsonl(source_pairs_path)
    events = {str(row["base_problem_id"]): row for row in read_jsonl(source_events_path)}
    bases = [str(row["base_problem_id"]) for row in source_rows]
    split = split_validation_primary(bases, validation_count=VALIDATION_COUNT, seed=SEED)
    validation = set(split["validation"])
    primary = set(split["primary"])
    if len(validation) != 7 or len(primary) != 24 or validation & primary:
        raise RuntimeError("The frozen Stage 3C.3 split must be disjoint 7/24")

    pairs_by_base: dict[str, list[dict[str, Any]]] = {base: [] for base in bases}
    for pair in source_pairs:
        base = str(pair["base_problem_id"])
        if base in pairs_by_base:
            event = events[base]
            context = [int(value) for value in event["history_before_ed_token_ids"]]
            mention = int(pair["mention_only_generated_index"])
            retrieval = int(pair["retrieval_generated_index"])
            ed = int(event["ed_generated_index"])
            if not (1 <= mention < retrieval <= ed <= len(context)):
                raise RuntimeError(f"Invalid M/R causal order for base {base}")
            pairs_by_base[base].append({
                **pair,
                "state_M": {
                    "generated_index": mention,
                    "prefix_token_count": mention,
                    "prefix_sha256": token_hash(context[:mention]),
                },
                "state_R": {
                    "generated_index": retrieval,
                    "prefix_token_count": retrieval,
                    "prefix_sha256": token_hash(context[:retrieval]),
                },
                "evidence_bridge_rule": "history_before_Ed[state_index:E_d] followed by the frozen divergent suffix; score only divergent-suffix token rows",
                "annotation_used_attention": False,
                "stage3c3_outcomes_observed_before_freeze": False,
            })
    if any({row["target_id"] for row in rows} != {"target_a", "target_b"} for rows in pairs_by_base.values()):
        raise RuntimeError("Every retained base must have both frozen target state pairs")

    def manifest_row(row: dict[str, Any], role: str) -> dict[str, Any]:
        base = str(row["base_problem_id"])
        return {
            **row,
            "cohort_role": role,
            "state_pairs": pairs_by_base[base],
            "selection_seed": SEED,
            "selection_used_attention": False,
            "selection_used_stage3c3_outcomes": False,
            "frozen_at": created,
        }

    validation_rows = [manifest_row(row, "validation") for row in source_rows if str(row["base_problem_id"]) in validation]
    primary_rows = [manifest_row(row, "primary") for row in source_rows if str(row["base_problem_id"]) in primary]
    write_jsonl(OUT / "cohort/validation_manifest.jsonl", validation_rows)
    write_jsonl(OUT / "cohort/primary_manifest.jsonl", primary_rows)
    write_jsonl(OUT / "cohort/exclusions.jsonl", [])

    frozen_target_bytes = source_targets_path.read_bytes()
    target_path = OUT / "config/frozen_targets.json"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(frozen_target_bytes)
    if sha256(target_path) != sha256(source_targets_path):
        raise RuntimeError("Frozen target copy changed")

    state_rules = {
        "frozen_at": created,
        "source": str(source_pairs_path.relative_to(ROOT)),
        "source_sha256": sha256(source_pairs_path),
        "state_M": "Stage 3C.2 attention-blind mention-only coordinate, exactly 16 generated-token positions before the target-specific retrieval coordinate",
        "state_R": "the exact Stage 3C.2 target-specific retrieval coordinate",
        "causal_order_required": "1 <= M < R <= E_d",
        "evidence_score": "append the native bridge from the state through E_d, then the frozen divergent suffix; compute length-normalized log probability only across suffix tokens",
        "lexical_subset_rule": "manual prospective review of local 16-token windows; strong only when the same content phrase or a close paraphrase is active in both M and R",
        "selection_used_attention": False,
        "stage3c3_outcomes_observed_before_freeze": False,
    }
    write_json(OUT / "config/state_pair_rules.json", state_rules)

    primary_family = {
        "frozen_at": created,
        "statistical_unit": "base_problem_id",
        "targets": ["target_a", "target_b"],
        "multiplicity": "Each listed contrast is evaluated for both frozen targets; Holm correction covers all 26 target-specific hypotheses when Phase B runs, or treats gated-unrun Phase-B p-values as 1.0.",
        "phase_a": [
            "necessity effect on T-vs-M scaled-logit gap",
            "necessity effect on target attention density",
            "necessity effect on target alpha-V norm",
            "necessity effect on evidence preference",
            "sufficiency effect on T-vs-M scaled-logit gap",
            "sufficiency effect on target attention density",
            "sufficiency effect on target alpha-V norm",
            "sufficiency effect on evidence preference",
            "causal-vs-noncausal reciprocal query-patch effect",
        ],
        "phase_b_gated": [
            "h_pre R-to-M effect on target routing",
            "h_pre M-to-R effect on target routing",
            "h_pre reciprocal effect on evidence preference",
            "query-only versus h_pre recovery",
        ],
        "phase_a_gate_per_target": {
            "necessity_and_sufficiency_routing_median": ">0",
            "necessity_and_sufficiency_routing_positive_fraction": ">=2/3",
            "necessity_and_sufficiency_target_alpha_v_median": ">0",
            "necessity_and_sufficiency_evidence_median": ">0",
            "causal_minus_noncausal_reciprocal_median": ">0",
            "self_query": "bit-exact",
            "pass_rule": "all conditions above; at least one target must pass before Phase B",
        },
        "summary_statistics": ["mean", "median", "bootstrap 95% CI", "positive-direction fraction", "unnormalized effect"],
        "bootstrap_seed": 20260903,
        "bootstrap_resamples": 10000,
        "selection_used_attention": False,
    }
    write_json(OUT / "config/primary_family.json", primary_family)

    rope = {
        "frozen_at": created,
        "status": "pending_validation",
        "candidate_forms": {
            "direct_post_rope": "copy the exact donor post-RoPE logical-head Q vector into the recipient position",
            "content_recipient_rope": "copy donor pre-RoPE normalized Q content and apply the recipient position's multimodal RoPE",
        },
        "selection_order": ["content_recipient_rope", "direct_post_rope"],
        "selection_rule": "choose the first form with exact self patch, exact recipient K/V, exact nonselected heads, and bit-exact repeatability; never use routing/evidence effect magnitude for formulation choice",
        "validation_direction_gate": "for the mechanically selected form, more than half of causal reciprocal target/base directions must move T-vs-M RDS as predicted",
        "selected_form": None,
        "primary_scoring_started": False,
    }
    write_json(OUT / "config/rope_query_formulation.json", rope)

    config = {
        "created_at": created,
        "source_plan": str(plan.relative_to(ROOT)),
        "source_plan_sha256": sha256(plan),
        "model": "Qwen3-VL-4B-Thinking",
        "model_checkpoint": source_config["model_checkpoint"],
        "dataset_root": source_config["dataset_root"],
        "seed": 1234,
        "split_seed": SEED,
        "validation_base_count": 7,
        "primary_base_count": 24,
        "primary_condition": "O",
        "validation_conditions": ["O"],
        "condition_control_bases": split["validation"][:2],
        "condition_control_conditions": ["O", "O_sham", "C", "C_sham"],
        "optional_phase_c_alpha": {"run": False, "reason": "Phase A/B directly test the prespecified causal chain; off-manifold alpha manipulation is not needed for the primary classification and cannot rescue a null Phase A."},
        "architecture_expected": source_config["architecture_expected"],
        "targets": {
            "target_a": {"coordinate": "E_d", "layer_index": 29, "causal_heads": [11, 6, 15, 12], "noncausal_heads": [0, 1, 2, 3]},
            "target_b": {"coordinate": "E_d-1", "layer_index": 28, "causal_heads": [16, 0, 3, 6], "noncausal_heads": [1, 2, 4, 5]},
        },
        "gpu": {"required_class": "A5000", "gpus": 2, "slurm_job_id": "106936", "tmux_session": "8"},
        "selection_used_attention": False,
        "sink_manipulated": False,
        "stage3c4_authorized": False,
    }
    write_json(OUT / "config/stage3c3_config.json", config)
    write_json(OUT / "config/cohort_split.json", {"frozen_at": created, **split, "disjoint": not bool(validation & primary), "source_cohort_sha256": sha256(source_manifest_path)})
    print(json.dumps({"validation": split["validation"], "primary_count": len(primary_rows), "frozen_target_sha256": sha256(target_path)}, indent=2))


if __name__ == "__main__":
    main()
