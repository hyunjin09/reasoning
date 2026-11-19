#!/usr/bin/env python3
"""Run Stage 3C.3 validation or primary query-only routing interventions."""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from pathlib import Path
from typing import Any, Sequence

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c3.metrics import summarize_routing_state
from visual_reasoning.stage3c3.runtime import (
    score_evidence_suffix,
    score_native_state_pair_preference,
    score_query_patched_preference,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3"
ALL_CONDITIONS = ("O", "O_sham", "C", "C_sham")
ALL_FORMS = ("direct_post_rope", "content_recipient_rope")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--forms", default="both")
    parser.add_argument("--conditions", default="O")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--max-bases", type=int, default=0)
    parser.add_argument("--repeat-first", action="store_true")
    parser.add_argument("--baseline-audit", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def condition_paths(base: str) -> dict[str, Path]:
    metadata = read_json(ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json")
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Four-condition validation failed for base {base}")
    return {name: ROOT / metadata["paths"][name] for name in ALL_CONDITIONS}


def selected_forms(argument: str) -> list[str]:
    if argument == "both":
        return list(ALL_FORMS)
    forms = [value.strip() for value in argument.split(",") if value.strip()]
    if not forms or any(value not in ALL_FORMS for value in forms):
        raise ValueError("Unknown query formulation")
    return forms


def selected_conditions(argument: str) -> list[str]:
    values = [value.strip() for value in argument.split(",") if value.strip()]
    if not values or any(value not in ALL_CONDITIONS for value in values):
        raise ValueError("Unknown image condition")
    return values


def tensor_error(left: torch.Tensor, right: torch.Tensor) -> float | None:
    if left.shape != right.shape:
        return None
    return float((left - right).abs().max().item())


def deterministic_view(value: Any) -> Any:
    """Remove wall-clock fields before an exact repeat comparison."""

    if isinstance(value, dict):
        return {
            key: deterministic_view(item)
            for key, item in value.items()
            if key != "runtime_seconds"
        }
    if isinstance(value, list):
        return [deterministic_view(item) for item in value]
    return value


def preference_public(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "L_o": float(row["L_o"]),
        "L_c": float(row["L_c"]),
        "D": float(row["D"]),
        "finite": bool(row["finite"]),
        "original_candidate": row["original_candidate"],
        "counterfactual_candidate": row["counterfactual_candidate"],
    }


def evidence_sequences(
    event: dict[str, Any], state_index: int
) -> tuple[list[int], list[int], list[int], list[int]]:
    context = [int(value) for value in event["history_before_ed_token_ids"]]
    ed = int(event["ed_generated_index"])
    index = int(state_index)
    if not 1 <= index <= ed == len(context):
        raise ValueError("Frozen state index is outside the evidence history")
    return (
        context[:index],
        context[index:ed],
        [int(value) for value in event["original_divergent_suffix_ids"]],
        [int(value) for value in event["counterfactual_divergent_suffix_ids"]],
    )


def routing_groups(
    *, target: Sequence[int], mention: Sequence[int], irrelevant: Sequence[int]
) -> dict[str, list[int]]:
    groups = {
        "T": sorted({int(value) for value in target}),
        "M": sorted({int(value) for value in mention}),
        "I": sorted({int(value) for value in irrelevant}),
        "sink": [0],
    }
    sets = [set(groups[name]) for name in ("T", "M", "I", "sink")]
    if any(not value for value in sets):
        raise ValueError("T/M/I/sink groups must be nonempty")
    if any(sets[i] & sets[j] for i in range(4) for j in range(i + 1, 4)):
        raise ValueError("T/M/I/sink routing groups must be disjoint")
    return groups


def compare_recipient_state(
    patched: dict[str, Any], native: dict[str, Any], visual_positions: Sequence[int]
) -> dict[str, Any]:
    visible = int(native["key"].shape[2])
    key_prefix = patched["key"][:, :, :visible, :]
    value_prefix = patched["value"][:, :, :visible, :]
    visual = torch.tensor(list(map(int, visual_positions)), dtype=torch.long, device=patched["key"].device)
    return {
        "recipient_prefix_key_max_abs_delta": tensor_error(key_prefix, native["key"]),
        "recipient_prefix_value_max_abs_delta": tensor_error(value_prefix, native["value"]),
        "visual_key_max_abs_delta": tensor_error(patched["key"][:, :, visual, :], native["key"][:, :, visual, :]),
        "visual_value_max_abs_delta": tensor_error(patched["value"][:, :, visual, :], native["value"][:, :, visual, :]),
        "recipient_native_query_max_abs_delta": tensor_error(patched["native_post_rope_query"], native["post_rope_query"]),
        "recipient_prefix_exact": bool(
            torch.equal(key_prefix, native["key"])
            and torch.equal(value_prefix, native["value"])
        ),
        "visual_kv_exact": bool(
            torch.equal(patched["key"][:, :, visual, :], native["key"][:, :, visual, :])
            and torch.equal(patched["value"][:, :, visual, :], native["value"][:, :, visual, :])
        ),
    }


def run_query_arm(
    *,
    model: Any,
    prepared: dict[str, Any],
    event: dict[str, Any],
    recipient_index: int,
    recipient_native: dict[str, dict[str, Any]],
    donor_native: dict[str, dict[str, Any]],
    layer_index: int,
    heads: Sequence[int],
    form: str,
    groups: dict[str, list[int]],
    visual_positions: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    prefix, bridge, original, counterfactual = evidence_sequences(event, recipient_index)
    scored = score_query_patched_preference(
        model=model,
        prepared=prepared,
        prefix_token_ids=prefix,
        bridge_token_ids=bridge,
        original_suffix_ids=original,
        counterfactual_suffix_ids=counterfactual,
        generated_index=recipient_index,
        layer_index=layer_index,
        selected_heads=heads,
        donor_states=donor_native,
        formulation=form,
        seed=seed,
    )
    original_state = scored["original_candidate_state"]
    counter_state = scored["counterfactual_candidate_state"]
    audits = [scored["original_candidate_audit"], scored["counterfactual_candidate_audit"]]
    routing_by_candidate = {
        "original_candidate": summarize_routing_state(
            original_state, groups=groups, selected_heads=heads
        ),
        "counterfactual_candidate": summarize_routing_state(
            counter_state, groups=groups, selected_heads=heads
        ),
    }
    return {
        "preference": preference_public(scored),
        "routing": routing_by_candidate["original_candidate"],
        "routing_by_candidate": routing_by_candidate,
        "query_patch_audits": audits,
        "recipient_state_invariance": {
            "original_candidate": compare_recipient_state(
                original_state, recipient_native["original_candidate"], visual_positions
            ),
            "counterfactual_candidate": compare_recipient_state(
                counter_state, recipient_native["counterfactual_candidate"], visual_positions
            ),
        },
        "candidate_branch_current_query_max_abs_delta": tensor_error(
            original_state["post_rope_query"], counter_state["post_rope_query"]
        ),
        "candidate_branch_attention_max_abs_delta": tensor_error(
            original_state["attention"], counter_state["attention"]
        ),
    }


def run_target(
    *,
    model: Any,
    prepared: dict[str, Any],
    event: dict[str, Any],
    pair: dict[str, Any],
    target: dict[str, Any],
    groups: dict[str, list[int]],
    visual_positions: Sequence[int],
    forms: Sequence[str],
    seed: int,
    baseline_audit: bool,
    repeat: bool,
) -> dict[str, Any]:
    layer = int(target["layer_index"])
    state_indices = {
        "M": int(pair["state_M"]["generated_index"]),
        "R": int(pair["state_R"]["generated_index"]),
    }
    earliest = min(state_indices.values())
    prefix, bridge, original_suffix, counterfactual_suffix = evidence_sequences(event, earliest)
    native_pair = score_native_state_pair_preference(
        model=model,
        prepared=prepared,
        prefix_token_ids=prefix,
        bridge_token_ids=bridge,
        original_suffix_ids=original_suffix,
        counterfactual_suffix_ids=counterfactual_suffix,
        generated_indices=state_indices,
        layer_index=layer,
        seed=seed,
    )
    capture_faithfulness: dict[str, Any] = {}
    if baseline_audit:
        for candidate_name, suffix in (
            ("original_candidate", original_suffix),
            ("counterfactual_candidate", counterfactual_suffix),
        ):
            baseline = score_evidence_suffix(
                model=model,
                prepared=prepared,
                prefix_token_ids=prefix,
                bridge_token_ids=bridge,
                suffix_token_ids=suffix,
                seed=seed,
            )
            captured = native_pair[candidate_name]
            errors = [
                abs(float(left) - float(right))
                for left, right in zip(
                    baseline["token_log_probabilities"],
                    captured["token_log_probabilities"],
                )
            ]
            capture_faithfulness[candidate_name] = {
                "token_log_probabilities_exact": baseline["token_log_probabilities"] == captured["token_log_probabilities"],
                "maximum_token_log_probability_absolute_error": max(errors),
            }

    native_captures = {
        state_name: {
            candidate_name: native_pair["attention_states"][candidate_name][state_name]
            for candidate_name in ("original_candidate", "counterfactual_candidate")
        }
        for state_name in state_indices
    }
    native_arms: dict[str, Any] = {}
    for state_name in state_indices:
        original_state = native_captures[state_name]["original_candidate"]
        counterfactual_state = native_captures[state_name]["counterfactual_candidate"]
        native_arms[state_name] = {
            "preference": preference_public(native_pair),
            "routing": {
                role: summarize_routing_state(
                    original_state,
                    groups=groups,
                    selected_heads=target[f"{role}_heads"],
                )
                for role in ("causal", "noncausal")
            },
            "routing_by_candidate": {
                candidate_name: {
                    role: summarize_routing_state(
                        native_captures[state_name][candidate_name],
                        groups=groups,
                        selected_heads=target[f"{role}_heads"],
                    )
                    for role in ("causal", "noncausal")
                }
                for candidate_name in ("original_candidate", "counterfactual_candidate")
            },
            "candidate_branch_state_drift": {
                "query_max_abs_delta": tensor_error(
                    original_state["post_rope_query"], counterfactual_state["post_rope_query"]
                ),
                "key_max_abs_delta": tensor_error(original_state["key"], counterfactual_state["key"]),
                "value_max_abs_delta": tensor_error(original_state["value"], counterfactual_state["value"]),
            },
        }

    form_results: dict[str, Any] = {}
    for form in forms:
        role_results: dict[str, Any] = {}
        for role in ("causal", "noncausal"):
            heads = target[f"{role}_heads"]
            arms = {
                "Q_R_to_Q_M": run_query_arm(
                    model=model, prepared=prepared, event=event,
                    recipient_index=state_indices["R"], recipient_native=native_captures["R"], donor_native=native_captures["M"],
                    layer_index=layer, heads=heads, form=form, groups=groups, visual_positions=visual_positions, seed=seed,
                ),
                "Q_M_to_Q_R": run_query_arm(
                    model=model, prepared=prepared, event=event,
                    recipient_index=state_indices["M"], recipient_native=native_captures["M"], donor_native=native_captures["R"],
                    layer_index=layer, heads=heads, form=form, groups=groups, visual_positions=visual_positions, seed=seed,
                ),
            }
            if role == "causal":
                arms["self_R"] = run_query_arm(
                    model=model, prepared=prepared, event=event,
                    recipient_index=state_indices["R"], recipient_native=native_captures["R"], donor_native=native_captures["R"],
                    layer_index=layer, heads=heads, form=form, groups=groups, visual_positions=visual_positions, seed=seed,
                )
                arms["self_M"] = run_query_arm(
                    model=model, prepared=prepared, event=event,
                    recipient_index=state_indices["M"], recipient_native=native_captures["M"], donor_native=native_captures["M"],
                    layer_index=layer, heads=heads, form=form, groups=groups, visual_positions=visual_positions, seed=seed,
                )
            role_results[role] = arms
        form_results[form] = role_results
    repeat_audit: dict[str, Any] | None = None
    if repeat:
        repeat_audit = {}
        for form in forms:
            first = form_results[form]["causal"]["Q_R_to_Q_M"]
            again = run_query_arm(
                model=model, prepared=prepared, event=event,
                recipient_index=state_indices["R"], recipient_native=native_captures["R"], donor_native=native_captures["M"],
                layer_index=layer, heads=target["causal_heads"], form=form, groups=groups, visual_positions=visual_positions, seed=seed,
            )
            repeat_audit[form] = {
                "D_max_abs_delta": abs(first["preference"]["D"] - again["preference"]["D"]),
                "RDS_max_abs_delta": abs(first["routing"]["RDS_T_vs_M"] - again["routing"]["RDS_T_vs_M"]),
                "exact": deterministic_view(first) == deterministic_view(again),
            }
    public_captures = {
        name: {
            "absolute_position": int(native_pair["absolute_positions"][name]),
            "pre_rope_query_shape": list(row["original_candidate"]["pre_rope_query"].shape),
            "post_rope_query_shape": list(row["original_candidate"]["post_rope_query"].shape),
            "key_shape": list(row["original_candidate"]["key"].shape),
            "value_shape": list(row["original_candidate"]["value"].shape),
            "h_pre_shape": list(native_pair["h_pre_states"]["original_candidate"][name].shape),
        }
        for name, row in native_captures.items()
    }
    return {
        "target_id": pair["target_id"],
        "layer_index": layer,
        "state_indices": state_indices,
        "native_capture_layout": public_captures,
        "capture_faithfulness": capture_faithfulness,
        "native": native_arms,
        "forms": form_results,
        "repeat_audit": repeat_audit,
    }


def main() -> None:
    args = parse_args()
    config = read_json(args.config)
    forms = selected_forms(args.forms)
    conditions = selected_conditions(args.conditions)
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", str(args.shard_index)))
    if world_size > 1:
        args.shard_index = local_rank
        args.shard_count = world_size
    torch.cuda.set_device(local_rank if world_size > 1 else 0)
    output_dir = args.output_dir.resolve()
    output_dir.relative_to(OUT.resolve())
    if world_size > 1:
        output_dir = output_dir / f"shard_{local_rank}"
    manifest = read_jsonl(args.manifest)[args.shard_index::args.shard_count]
    if args.max_bases:
        manifest = manifest[: args.max_bases]
    events = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")}
    mentions = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3c2/annotations/mention_roi_annotations.jsonl")}
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "run_config.json", {
        "manifest": str(args.manifest.resolve()), "forms": forms, "conditions": conditions,
        "shard_index": args.shard_index, "shard_count": args.shard_count,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "baseline_audit": args.baseline_audit, "repeat_first": args.repeat_first,
    })
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Stage 3C.3 requires A5000, observed {environment['gpu_name']}")
    observed = {
        "language_layers": int(model.config.text_config.num_hidden_layers),
        "logical_query_heads": int(model.config.text_config.num_attention_heads),
        "kv_heads": int(model.config.text_config.num_key_value_heads),
        "query_heads_per_kv_group": int(model.config.text_config.num_attention_heads // model.config.text_config.num_key_value_heads),
        "head_dimension": int(model.config.text_config.head_dim),
    }
    if observed != config["architecture_expected"]:
        raise RuntimeError(f"Architecture mismatch: {observed}")
    write_json(output_dir / "environment.json", {**environment, "architecture_observed": observed})
    completed = 0
    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume:
                raise FileExistsError(result_path)
            completed += 1
            print(f"[{completed}/{len(manifest)}] resume skip base {base}", flush=True)
            continue
        started = time.perf_counter()
        event, roi, mention = events[base], rois[base], mentions[base]
        source_row = data[str(item["example_id"])]
        prepared: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        paths = condition_paths(base)
        for condition in conditions:
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, source_row, paths[condition], device="cuda"
            )
        prompt_ids = [metadata[name]["prompt_token_ids"] for name in conditions]
        visuals = [metadata[name]["visual_token_indices"] for name in conditions]
        grids = [metadata[name]["image_grid_thw"] for name in conditions]
        layout_exact = bool(
            all(value == prompt_ids[0] for value in prompt_ids[1:])
            and all(value == visuals[0] for value in visuals[1:])
            and all(value == grids[0] for value in grids[1:])
            and visuals[0] == roi["absolute_source_groups"]["V_all"]
        )
        if not layout_exact:
            raise RuntimeError(f"Condition layout mismatch for base {base}")
        groups = routing_groups(
            target=roi["absolute_source_groups"]["V_target"],
            mention=mention["mention_absolute_source_positions"],
            irrelevant=roi["absolute_source_groups"]["V_irrelevant"],
        )
        pair_by_target = {row["target_id"]: row for row in item["state_pairs"]}
        target_results: dict[str, Any] = {}
        for target_id in ("target_a", "target_b"):
            frozen = config["targets"][target_id]
            target = {
                **frozen,
                "causal_heads": [int(value) for value in frozen["causal_heads"]],
                "noncausal_heads": [int(value) for value in frozen["noncausal_heads"]],
            }
            target_results[target_id] = {}
            for condition in conditions:
                target_results[target_id][condition] = run_target(
                    model=model, prepared=prepared[condition], event=event,
                    pair=pair_by_target[target_id], target=target, groups=groups,
                    visual_positions=visuals[0], forms=forms, seed=int(config["seed"]),
                    baseline_audit=bool(args.baseline_audit and item_index == 0 and condition == conditions[0]),
                    repeat=bool(args.repeat_first and item_index == 0 and condition == conditions[0]),
                )
        write_json(result_path, {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "cohort_role": item["cohort_role"],
            "forms": forms,
            "conditions": conditions,
            "condition_layout_exact": layout_exact,
            "visual_positions": visuals[0],
            "routing_groups": groups,
            "target_results": target_results,
            "runtime_seconds": time.perf_counter() - started,
            "selection_used_attention": False,
            "query_only_intervention": True,
            "visual_kv_directly_intervened": False,
            "candidate_sink_directly_intervened": False,
        })
        completed += 1
        print(f"[{completed}/{len(manifest)}] completed base {base} seconds={time.perf_counter()-started:.1f}", flush=True)
        del prepared, metadata, target_results
        gc.collect(); torch.cuda.empty_cache()
    print(json.dumps({"completed": completed, "requested": len(manifest)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
