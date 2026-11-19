#!/usr/bin/env python3
"""Run fixed-path internal, intervention, and continuity validation on 12 bases."""

from __future__ import annotations

import argparse
import gc
import json
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.a6000_calibration.metrics import compare_scores
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image, summarize_candidate_log_probs
from visual_reasoning.stage3b5.boundaries import (
    CaptureCurrentBlockBoundaries,
    CurrentPositionBoundaryPatch,
)
from visual_reasoning.stage3c9.streaming import (
    StreamingPrefixState,
    advance_streaming_state,
    clone_streaming_state,
    patch_streaming_state,
    prefill_streaming_state,
    roll_streaming_prefix,
    score_preference_from_streaming_state,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/a6000_calibration_v2"
CANDIDATES = ("original_candidate", "counterfactual_candidate")
CONDITIONS = ("O", "C")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, required=True)
    parser.add_argument("--device-index", type=int, required=True)
    parser.add_argument("--bases", nargs="*", default=[])
    return parser.parse_args()


def condition_paths(base: str) -> dict[str, Path]:
    metadata = read_json(
        ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json"
    )
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Image validation failed for base {base}")
    return {condition: ROOT / metadata["paths"][condition] for condition in CONDITIONS}


def result_score(candidates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    lo = float(candidates[CANDIDATES[0]]["mean_log_probability"])
    lc = float(candidates[CANDIDATES[1]]["mean_log_probability"])
    return {
        "L_o": lo,
        "L_c": lc,
        "D": lo - lc,
        "finite": bool(all(candidates[name]["finite"] for name in CANDIDATES)),
        **candidates,
    }


def historical_result(base: str) -> dict[str, Any]:
    paths = list((ROOT / "outputs/stage3c7/raw/primary").glob(f"shard_*/examples/{base}/result.json"))
    if len(paths) != 1:
        raise RuntimeError(f"Expected one historical Stage 3C.7 result for base {base}, found {paths}")
    return read_json(paths[0])


def score_candidate_with_residual(
    *, model: Any, state: StreamingPrefixState, candidate: list[int], seed: int,
    layer: int, boundary: str, donor: torch.Tensor | None = None,
    capture: bool = False,
) -> tuple[dict[str, Any], torch.Tensor | None, list[dict[str, Any]]]:
    if not candidate:
        raise ValueError("Residual diagnostic candidate is empty")
    first = torch.log_softmax(state.last_logits.float(), dim=-1)
    logps = [float(first[int(candidate[0])].item())]
    captured = None
    patch_audit: list[dict[str, Any]] = []
    working = None
    if len(candidate) > 1:
        working = clone_streaming_state(state)
        capture_context: Any = (
            CaptureCurrentBlockBoundaries(model=model, position=0, layer_indices=[layer])
            if capture else nullcontext()
        )
        patch_context: Any = (
            CurrentPositionBoundaryPatch(
                model=model, position=0, layer_index=layer, boundary=boundary,
                source_state=donor,
            )
            if donor is not None else nullcontext()
        )
        with capture_context, patch_context:
            advance_streaming_state(
                model=model, state=working, token_ids=[candidate[0]], seed=seed,
                chunk_size=1, release_allocator_cache=True,
            )
        if capture:
            states = capture_context.complete_states()
            captured = states[boundary][layer]
        if donor is not None:
            patch_audit = list(patch_context.audit)
        for index, token in enumerate(candidate[1:-1], start=1):
            probabilities = torch.log_softmax(working.last_logits.float(), dim=-1)
            logps.append(float(probabilities[int(candidate[index])].item()))
            advance_streaming_state(
                model=model, state=working, token_ids=[token], seed=seed,
                chunk_size=1, release_allocator_cache=True,
            )
        probabilities = torch.log_softmax(working.last_logits.float(), dim=-1)
        logps.append(float(probabilities[int(candidate[-1])].item()))
    summary = summarize_candidate_log_probs(logps)
    summary.update({
        "candidate_token_ids": candidate,
        "finite": bool(torch.isfinite(torch.tensor(logps)).all().item()),
        "runtime_mode": "canonical_fixed_streaming_cached",
    })
    if working is not None:
        del working
    return summary, captured, patch_audit


def residual_scores(
    *, model: Any, state: StreamingPrefixState, suffixes: dict[str, list[int]], seed: int,
    layer: int, boundary: str, donors: dict[str, torch.Tensor] | None = None,
    capture: bool = False,
) -> tuple[dict[str, Any], dict[str, torch.Tensor], dict[str, list[dict[str, Any]]]]:
    candidates, captured, audits = {}, {}, {}
    for name in CANDIDATES:
        score, source, audit = score_candidate_with_residual(
            model=model, state=state, candidate=suffixes[name], seed=seed,
            layer=layer, boundary=boundary,
            donor=None if donors is None else donors.get(name), capture=capture,
        )
        candidates[name] = score
        if source is not None:
            captured[name] = source
        audits[name] = audit
    return result_score(candidates), captured, audits


def roll_residual_arm(
    *, model: Any, prefill: StreamingPrefixState, context: list[int],
    suffixes: dict[str, list[int]], seed: int, chunk_size: int,
    layers: list[int], heads: list[int], target_positions: list[int],
    tpre: int, layer: int, boundary: str, suppression_enabled: bool,
    donor: torch.Tensor | None = None, capture: bool = False,
) -> tuple[dict[str, Any], torch.Tensor | None, dict[str, Any]]:
    split = tpre + 1
    pre_state, pre_audit = roll_streaming_prefix(
        model=model, prefill=prefill, prefix_token_ids=context,
        end_generated_index=split, seed=seed, chunk_size=chunk_size,
        release_allocator_cache=True,
        layers=layers if suppression_enabled else [],
        selected_heads=heads if suppression_enabled else [],
        source_positions=target_positions if suppression_enabled else [],
        suppressed_generated_indices=[tpre] if suppression_enabled else [],
    )
    capture_context: Any = (
        CaptureCurrentBlockBoundaries(model=model, position=0, layer_indices=[layer])
        if capture else nullcontext()
    )
    patch_context: Any = (
        CurrentPositionBoundaryPatch(
            model=model, position=0, layer_index=layer, boundary=boundary,
            source_state=donor,
        )
        if donor is not None else nullcontext()
    )
    with capture_context, patch_context:
        advance_streaming_state(
            model=model, state=pre_state, token_ids=context[split:], seed=seed,
            chunk_size=chunk_size, release_allocator_cache=True,
        )
    source = None
    if capture:
        source = capture_context.complete_states()[boundary][layer]
    patch_audit = list(patch_context.audit) if donor is not None else []
    return score_state(model, pre_state, suffixes, seed), source, {
        "prefix_before_current": pre_audit,
        "residual_patch": patch_audit,
        "split_generated_index": split,
        "current_chunk_range": [split, len(context)],
    }


def score_state(model: Any, state: StreamingPrefixState, suffixes: dict[str, list[int]], seed: int) -> dict[str, Any]:
    return score_preference_from_streaming_state(
        model=model, state=state,
        original_suffix_ids=suffixes[CANDIDATES[0]],
        counterfactual_suffix_ids=suffixes[CANDIDATES[1]], seed=seed,
    )


def roll_state(
    *, model: Any, prefill: StreamingPrefixState, context: list[int], seed: int,
    chunk_size: int, layers: list[int] = [], heads: list[int] = [],
    target_positions: list[int] = [], suppressed: list[int] = [],
    forced_boundaries: list[int] = [], donor: StreamingPrefixState | None = None,
    patch_positions: list[int] = [], patch_layers: list[int] = [], patch_mode: str = "KV",
    visual_positions: list[int] = [],
) -> tuple[StreamingPrefixState, dict[str, Any]]:
    return roll_streaming_prefix(
        model=model, prefill=prefill, prefix_token_ids=context,
        end_generated_index=len(context), seed=seed, chunk_size=chunk_size,
        release_allocator_cache=True, layers=layers, selected_heads=heads,
        source_positions=target_positions, suppressed_generated_indices=suppressed,
        forced_generated_boundaries=forced_boundaries, donor=donor,
        patch_generated_indices=patch_positions, patch_selected_layers=patch_layers,
        patch_mode=patch_mode, visual_positions=visual_positions,
    )


def core_once(
    *, model: Any, prefill: StreamingPrefixState, context: list[int], suffixes: dict[str, list[int]],
    seed: int, chunk_size: int, cache_layers: list[int], heads: list[int],
    target_positions: list[int], irrelevant_positions: list[int],
    visual_positions: list[int], tpre: int,
) -> tuple[dict[str, Any], dict[str, StreamingPrefixState], dict[str, Any]]:
    boundary = tpre + 1
    native_state, native_audit = roll_state(
        model=model, prefill=prefill, context=context, seed=seed, chunk_size=chunk_size,
        forced_boundaries=[boundary],
    )
    suppressed_state, suppressed_audit = roll_state(
        model=model, prefill=prefill, context=context, seed=seed, chunk_size=chunk_size,
        layers=cache_layers, heads=heads, target_positions=target_positions, suppressed=[tpre],
        forced_boundaries=[boundary],
    )
    irrelevant_state, irrelevant_audit = roll_state(
        model=model, prefill=prefill, context=context, seed=seed, chunk_size=chunk_size,
        layers=cache_layers, heads=heads, target_positions=irrelevant_positions,
        suppressed=[tpre], forced_boundaries=[boundary],
    )
    rescue_state, rescue_audit = roll_state(
        model=model, prefill=prefill, context=context, seed=seed, chunk_size=chunk_size,
        layers=cache_layers, heads=heads, target_positions=target_positions, suppressed=[tpre],
        forced_boundaries=[boundary], donor=native_state, patch_positions=[tpre],
        patch_layers=cache_layers, patch_mode="KV", visual_positions=visual_positions,
    )
    scores = {
        "native": score_state(model, native_state, suffixes, seed),
        "suppressed": score_state(model, suppressed_state, suffixes, seed),
        "kv_rescue": score_state(model, rescue_state, suffixes, seed),
        "irrelevant_suppressed": score_state(model, irrelevant_state, suffixes, seed),
    }
    audits = {
        "native": native_audit,
        "suppressed": suppressed_audit,
        "kv_rescue": rescue_audit,
        "irrelevant_suppressed": irrelevant_audit,
        "partition_exact_across_native_and_suppressed": (
            native_audit["executed_chunk_ranges"] == suppressed_audit["executed_chunk_ranges"]
        ),
    }
    return scores, {"native": native_state, "suppressed": suppressed_state}, audits


def self_patch_controls(
    *, model: Any, prefill: StreamingPrefixState, context: list[int],
    states: dict[str, StreamingPrefixState], references: dict[str, Any],
    suffixes: dict[str, list[int]], seed: int, chunk_size: int,
    cache_layers: list[int], heads: list[int], target_positions: list[int],
    visual_positions: list[int], tpre: int, tolerance: float,
) -> dict[str, Any]:
    controls = {}
    event_span = list(range(max(0, tpre - 3), tpre + 1))
    for label, positions, mode in (
        ("K", [tpre], "K"), ("V", [tpre], "V"), ("KV", [tpre], "KV"),
        ("event_span_KV", event_span, "KV"),
    ):
        controls[label] = {}
        boundary = positions[-1] + 1
        for recipient in ("native", "suppressed"):
            patched, audit = roll_state(
                model=model, prefill=prefill, context=context, seed=seed,
                chunk_size=chunk_size,
                layers=cache_layers if recipient == "suppressed" else [],
                heads=heads if recipient == "suppressed" else [],
                target_positions=target_positions if recipient == "suppressed" else [],
                suppressed=[tpre] if recipient == "suppressed" else [],
                forced_boundaries=[boundary], donor=states[recipient],
                patch_positions=positions, patch_layers=cache_layers,
                patch_mode=mode, visual_positions=visual_positions,
            )
            score = score_state(model, patched, suffixes, seed)
            controls[label][f"{recipient}_to_{recipient}"] = {
                "comparison": compare_scores(references[recipient], score, tolerance=tolerance),
                "audit": audit,
            }
    return controls


def validation_readout(
    *, model: Any, prefill: StreamingPrefixState, context: list[int], suffixes: dict[str, list[int]],
    seed: int, chunk_size: int, layers: list[int], heads: list[int],
    target_positions: list[int], visual_positions: list[int], event_span: list[int],
    neighbor_span: list[int],
) -> dict[str, Any]:
    forced = sorted({neighbor_span[-1] + 1, event_span[-1] + 1})
    native_state, native_audit = roll_state(
        model=model, prefill=prefill, context=context, seed=seed, chunk_size=chunk_size,
        forced_boundaries=forced,
    )
    scores: dict[str, Any] = {"native": score_state(model, native_state, suffixes, seed)}
    audits: dict[str, Any] = {"native": native_audit}
    suppressed_states = {}
    for width in (8, 16):
        start = event_span[0]
        queries = list(range(start - width, start))
        state, audit = roll_state(
            model=model, prefill=prefill, context=context, seed=seed, chunk_size=chunk_size,
            layers=layers, heads=heads, target_positions=target_positions, suppressed=queries,
            forced_boundaries=forced,
        )
        suppressed_states[width] = state
        scores[f"W{width}_suppressed"] = score_state(model, state, suffixes, seed)
        audits[f"W{width}"] = audit
    event_state, event_audit = roll_state(
        model=model, prefill=prefill, context=context, seed=seed, chunk_size=chunk_size,
        layers=layers, heads=heads, target_positions=target_positions,
        suppressed=list(range(event_span[0] - 16, event_span[0])),
        forced_boundaries=forced, donor=native_state, patch_positions=event_span,
        patch_layers=layers, patch_mode="KV", visual_positions=visual_positions,
    )
    neighbor_state, neighbor_audit = roll_state(
        model=model, prefill=prefill, context=context, seed=seed, chunk_size=chunk_size,
        layers=layers, heads=heads, target_positions=target_positions,
        suppressed=list(range(event_span[0] - 16, event_span[0])),
        forced_boundaries=forced, donor=native_state, patch_positions=neighbor_span,
        patch_layers=layers, patch_mode="KV", visual_positions=visual_positions,
    )
    scores["event_rescued"] = score_state(model, event_state, suffixes, seed)
    scores["neighbor_rescued"] = score_state(model, neighbor_state, suffixes, seed)
    audits["event_patch"] = event_audit
    audits["neighbor_patch"] = neighbor_audit
    audits["partition_exact_across_native_W8_W16"] = bool(
        native_audit["executed_chunk_ranges"]
        == audits["W8"]["executed_chunk_ranges"]
        == audits["W16"]["executed_chunk_ranges"]
    )
    return {"scores": scores, "audits": audits}


def main() -> None:
    args = parse_args()
    output = args.output_dir.resolve()
    output.relative_to(OUT.resolve())
    torch.cuda.set_device(int(args.device_index))
    device = f"cuda:{int(args.device_index)}"
    frozen = read_json(OUT / "config/environment_freeze.json")
    chunking = read_json(OUT / "config/canonical_chunking.json")
    tolerances = read_json(OUT / "config/tolerances.json")
    c7 = read_json(ROOT / "outputs/stage3c7/config/stage3c7_config.json")
    cohort = read_json(ROOT / "outputs/a6000_calibration/config/calibration_cohort.json")["cells"]
    if args.bases:
        requested = {str(value) for value in args.bases}
        cohort = [row for row in cohort if str(row["base_problem_id"]) in requested]
        missing = requested - {str(row["base_problem_id"]) for row in cohort}
        if missing:
            raise ValueError(f"Cross-device bases are outside the frozen cohort: {sorted(missing)}")
    selected = cohort[args.shard_index::args.shard_count]
    validation_bases = {str(row["base_problem_id"]) for row in cohort[:8]}
    manifests = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3c7/cohort/primary_manifest.jsonl")
    }
    events = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")
    }
    rois = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")
    }
    dataset = {
        str(row["sample_index"]): row
        for row in load_mathverse_rows(Path(frozen["dataset_root"]))
    }
    processor, model = load_runtime(Path(frozen["model_checkpoint"]), device=device)
    environment = runtime_environment(Path(frozen["model_checkpoint"]), model, 40_960)
    environment.update({
        "selected_cuda_device_index": int(args.device_index),
        "selected_cuda_device_name": torch.cuda.get_device_name(int(args.device_index)),
    })
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "run_config.json", {
        "base_problem_ids": [str(row["base_problem_id"]) for row in selected],
        "shard_index": int(args.shard_index), "shard_count": int(args.shard_count),
        "device_index": int(args.device_index), "canonical_chunk_size": int(chunking["selected_chunk_size"]),
        "release_allocator_cache_between_chunks": True, "repeats": 3,
        "validation_event_bases": sorted(validation_bases, key=int),
    })
    write_json(output / "environment.json", environment)
    seed = int(c7["seed"])
    chunk_size = int(chunking["selected_chunk_size"])
    cache_layers = [int(value) for value in c7["cache_scope"]["layers"]]
    all_layers = list(range(int(model.config.text_config.num_hidden_layers)))
    heads = list(range(int(model.config.text_config.num_attention_heads)))
    tolerance = float(tolerances["same_path_aggregate_D_max_abs_delta"])
    started = time.perf_counter()
    for item_index, cell in enumerate(selected):
        base_started = time.perf_counter()
        base = str(cell["base_problem_id"])
        result_path = output / "examples" / base / "result.json"
        if result_path.exists():
            raise FileExistsError(result_path)
        item = manifests[base]
        event = events[base]
        pair = next(row for row in item["state_pairs"] if row["target_id"] == cell["target_id"])
        current = int(pair["state_R"]["generated_index"])
        tpre = current - 2
        context = [int(value) for value in event["history_before_ed_token_ids"]]
        if not 0 <= tpre < len(context) or len(context) > chunk_size:
            raise RuntimeError(f"Base {base} is outside canonical internal-validation bounds")
        suffixes = {
            CANDIDATES[0]: [int(value) for value in event["original_divergent_suffix_ids"]],
            CANDIDATES[1]: [int(value) for value in event["counterfactual_divergent_suffix_ids"]],
        }
        roi = rois[base]["absolute_source_groups"]
        visual_positions = [int(value) for value in roi["V_all"]]
        target_positions = [int(value) for value in roi["V_target"]]
        irrelevant_positions = [int(value) for value in roi["V_irrelevant"]]
        conditions = {}
        for condition, image_path in condition_paths(base).items():
            prepared, metadata = prepare_custom_image(
                processor, dataset[str(item["example_id"])], image_path, device=device
            )
            if visual_positions != [int(value) for value in metadata["visual_token_indices"]]:
                raise RuntimeError(f"Visual-token layout drift for base {base}")
            prefill, prefill_audit = prefill_streaming_state(model=model, prepared=prepared, seed=seed)
            repetitions, first_states, first_audits = [], None, None
            for repeat in range(3):
                scores, states, audits = core_once(
                    model=model, prefill=prefill, context=context, suffixes=suffixes,
                    seed=seed, chunk_size=chunk_size, cache_layers=cache_layers,
                    heads=heads, target_positions=target_positions,
                    irrelevant_positions=irrelevant_positions,
                    visual_positions=visual_positions, tpre=tpre,
                )
                repetitions.append(scores)
                if repeat == 0:
                    first_states, first_audits = states, audits
            assert first_states is not None and first_audits is not None
            replay = {
                name: [compare_scores(repetitions[0][name], row[name], tolerance=tolerance) for row in repetitions[1:]]
                for name in ("native", "suppressed", "kv_rescue", "irrelevant_suppressed")
            }
            controls = self_patch_controls(
                model=model, prefill=prefill, context=context, states=first_states,
                references=repetitions[0], suffixes=suffixes, seed=seed,
                chunk_size=chunk_size, cache_layers=cache_layers, heads=heads,
                target_positions=target_positions, visual_positions=visual_positions,
                tpre=tpre, tolerance=tolerance,
            )
            residual_spec = c7["residual_boundaries"][cell["target_id"]]
            residual_layer = int(residual_spec["layer"])
            residual_boundary = str(residual_spec["boundary"])
            residual_common = dict(
                model=model, prefill=prefill, context=context, suffixes=suffixes,
                seed=seed, chunk_size=chunk_size, layers=cache_layers, heads=heads,
                target_positions=target_positions, tpre=tpre, layer=residual_layer,
                boundary=residual_boundary,
            )
            native_residual, native_donor, _ = roll_residual_arm(
                **residual_common, suppression_enabled=False, capture=True,
            )
            suppressed_residual, suppressed_donor, _ = roll_residual_arm(
                **residual_common, suppression_enabled=True, capture=True,
            )
            assert native_donor is not None and suppressed_donor is not None
            native_self, _, native_self_audit = roll_residual_arm(
                **residual_common, suppression_enabled=False, donor=native_donor,
            )
            suppressed_self, _, suppressed_self_audit = roll_residual_arm(
                **residual_common, suppression_enabled=True, donor=suppressed_donor,
            )
            residual_rescue, _, residual_rescue_audit = roll_residual_arm(
                **residual_common, suppression_enabled=True, donor=native_donor,
            )
            residual_control = {
                "native_reference_comparison": compare_scores(repetitions[0]["native"], native_residual, tolerance=tolerance),
                "suppressed_reference_comparison": compare_scores(repetitions[0]["suppressed"], suppressed_residual, tolerance=tolerance),
                "native_to_native": compare_scores(native_residual, native_self, tolerance=tolerance),
                "suppressed_to_suppressed": compare_scores(suppressed_residual, suppressed_self, tolerance=tolerance),
                "native_patch_audit": native_self_audit,
                "suppressed_patch_audit": suppressed_self_audit,
                "rescue_patch_audit": residual_rescue_audit,
                "residual_rescue": residual_rescue,
                "applicable_candidates": list(CANDIDATES),
            }
            validation = None
            if base in validation_bases and condition == "O":
                event_span = list(range(tpre - 3, tpre + 1))
                if len(event_span) != 4:
                    raise RuntimeError("Mechanical validation event span must contain four tokens")
                neighbor_span = list(range(event_span[0] - 4, event_span[0]))
                local = validation_readout(
                    model=model, prefill=prefill, context=context, suffixes=suffixes,
                    seed=seed, chunk_size=chunk_size, layers=all_layers, heads=heads,
                    target_positions=target_positions, visual_positions=visual_positions,
                    event_span=event_span, neighbor_span=neighbor_span,
                )
                final_context = [*context, *suffixes[CANDIDATES[0]]]
                final = validation_readout(
                    model=model, prefill=prefill, context=final_context, suffixes=suffixes,
                    seed=seed, chunk_size=chunk_size, layers=all_layers, heads=heads,
                    target_positions=target_positions, visual_positions=visual_positions,
                    event_span=event_span, neighbor_span=neighbor_span,
                )
                validation = {
                    "mechanical_only": True,
                    "event_span": event_span,
                    "matched_neighbor_span": neighbor_span,
                    "local_readout_generated_index": len(context),
                    "final_readout_generated_index": len(final_context),
                    "local": local,
                    "final": final,
                }
            historical = historical_result(base)["target_results"][cell["target_id"]]["conditions"][condition]
            historical_effects = {
                "suppression_loss": float(historical["native"]["D"]) - float(historical["suppressed"]["D"]),
                "kv_rescue_gain": float(historical["arms"]["C4_KV"]["D"]) - float(historical["suppressed"]["D"]),
                "residual_rescue_gain": float(historical["arms"]["J1_residual"]["D"]) - float(historical["suppressed"]["D"]),
            }
            canonical_effects = {
                "suppression_loss": float(repetitions[0]["native"]["D"]) - float(repetitions[0]["suppressed"]["D"]),
                "kv_rescue_gain": float(repetitions[0]["kv_rescue"]["D"]) - float(repetitions[0]["suppressed"]["D"]),
                "residual_rescue_gain": float(residual_rescue["D"]) - float(suppressed_residual["D"]),
                "irrelevant_suppression_loss": float(repetitions[0]["native"]["D"]) - float(repetitions[0]["irrelevant_suppressed"]["D"]),
            }
            conditions[condition] = {
                "prefill_audit": prefill_audit,
                "canonical_scores": repetitions[0],
                "deterministic_replay": replay,
                "streaming_audits": first_audits,
                "self_patch_controls": controls,
                "residual_control": residual_control,
                "historical_effects": historical_effects,
                "canonical_effects": canonical_effects,
                "effect_sign_agreement": {
                    name: bool((historical_effects[name] > 0) == (canonical_effects[name] > 0))
                    for name in historical_effects
                },
                "mechanical_event_validation": validation,
            }
            del prefill, first_states
            gc.collect()
            torch.cuda.empty_cache()
        result = {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "target_id": cell["target_id"],
            "effect_stratum": cell["effect_stratum"],
            "context_length": len(context),
            "tpre_generated_index": tpre,
            "cache_layers": cache_layers,
            "conditions": conditions,
            "runtime_seconds": time.perf_counter() - base_started,
        }
        write_json(result_path, result)
        print(f"[{item_index + 1}/{len(selected)}] base={base} seconds={result['runtime_seconds']:.1f}", flush=True)
    write_json(output / "run_summary.json", {
        "status": "complete", "completed": len(selected),
        "runtime_seconds": time.perf_counter() - started,
        "peak_allocated_vram_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_reserved_vram_bytes": int(torch.cuda.max_memory_reserved()),
    })


if __name__ == "__main__":
    main()
