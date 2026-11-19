from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from piqd.utils.io import read_json


@dataclass(frozen=True)
class Phase2Event:
    event_type: str
    generated_token_index: int
    token_id: int
    source: str
    fallback_used: bool = False


@dataclass(frozen=True)
class Phase2ArtifactRow:
    sample_id: str
    image_path: str
    prompt: str
    generated_token_ids: list[int]
    generated_text: str
    retained_visual_token_indices: list[int]
    num_visual_tokens_full: int
    num_visual_tokens_retained: int
    decoding_config: dict[str, Any]
    fastv_status: str
    pruning_mode: str
    retention_ratio: float
    events: list[Phase2Event]
    sample_row: dict[str, Any]
    generation_row: dict[str, Any]
    event_row: dict[str, Any]


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(read_json_text(line))
    return rows


def read_json_text(value: str) -> dict[str, Any]:
    import json

    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("JSONL row is not an object")
    return parsed


def load_phase1_artifacts(phase1_dir: str | Path) -> tuple[list[Phase2ArtifactRow], list[str]]:
    phase1 = Path(phase1_dir)
    samples = {row.get("sample_id"): row for row in read_jsonl(phase1 / "phase1_samples.jsonl")}
    generations = {row.get("sample_id"): row for row in read_jsonl(phase1 / "phase1_generation_logs.jsonl")}
    events = {row.get("sample_id"): row for row in read_jsonl(phase1 / "phase1_event_logs.jsonl")}
    config = read_json(phase1 / "phase1_config.json")

    blockers: list[str] = []
    rows: list[Phase2ArtifactRow] = []
    sample_ids = sorted(set(samples) | set(generations) | set(events))
    for sample_id in sample_ids:
        sample = samples.get(sample_id)
        generation = generations.get(sample_id)
        event = events.get(sample_id)
        if not sample or not generation or not event:
            blockers.append(f"{sample_id}: missing sample/generation/event row")
            continue

        row_blockers = validate_phase1_row(sample, generation, event)
        if row_blockers:
            blockers.extend(f"{sample_id}: {item}" for item in row_blockers)
            continue

        generated_token_ids = [int(token_id) for token_id in generation["generated_prefix_token_ids"]]
        retained_indices = [int(idx) for idx in generation["active_visual_token_indices"]]
        row_events = build_candidate_events(generation, event)
        if not row_events:
            blockers.append(f"{sample_id}: no candidate Phase 2 event positions")
            continue

        rows.append(
            Phase2ArtifactRow(
                sample_id=str(sample_id),
                image_path=str(sample["image_path"]),
                prompt=str(sample["prompt"]),
                generated_token_ids=generated_token_ids,
                generated_text=str(generation.get("generated_text") or ""),
                retained_visual_token_indices=retained_indices,
                num_visual_tokens_full=int(generation["num_visual_tokens_full"]),
                num_visual_tokens_retained=int(generation["num_visual_tokens_retained"]),
                decoding_config=dict(generation["decoding_config"]),
                fastv_status=str(generation.get("fastv_status") or config.get("fastv_status") or ""),
                pruning_mode=str(generation.get("pruning_mode") or config.get("pruning_mode") or ""),
                retention_ratio=float(generation.get("retention_ratio") or config.get("retention_ratio")),
                events=row_events,
                sample_row=sample,
                generation_row=generation,
                event_row=event,
            )
        )
    return rows, blockers


def validate_phase1_row(sample: dict[str, Any], generation: dict[str, Any], event: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    sample_id = sample.get("sample_id")
    if not sample_id:
        blockers.append("missing sample_id")
    if not sample.get("prompt"):
        blockers.append("missing reconstructable prompt")
    image_path = sample.get("image_path")
    if not image_path:
        blockers.append("missing image_path")
    elif not Path(str(image_path)).exists():
        blockers.append(f"image_path does not exist: {image_path}")
    if generation.get("status") != "ok":
        blockers.append(f"generation status is not ok: {generation.get('status')}")
    if event.get("status") != "ok":
        blockers.append(f"event status is not ok: {event.get('status')}")

    tokens = generation.get("generated_prefix_token_ids")
    if not _is_int_list(tokens):
        blockers.append("missing exact generated_prefix_token_ids")
        tokens = []
    if not tokens:
        blockers.append("generated_prefix_token_ids is empty")

    retained = generation.get("active_visual_token_indices")
    if not _is_int_list(retained):
        blockers.append("missing retained active_visual_token_indices")
        retained = []
    if not retained:
        blockers.append("active_visual_token_indices is empty")

    full_count = generation.get("num_visual_tokens_full")
    retained_count = generation.get("num_visual_tokens_retained")
    if not isinstance(full_count, int) or full_count <= 0:
        blockers.append("missing valid num_visual_tokens_full")
    if not isinstance(retained_count, int) or retained_count <= 0:
        blockers.append("missing valid num_visual_tokens_retained")
    if isinstance(full_count, int) and retained and any(idx < 0 or idx >= full_count for idx in retained):
        blockers.append("retained visual token index outside full visual-token range")
    if isinstance(full_count, int) and isinstance(retained_count, int) and full_count <= retained_count:
        blockers.append("full visual token count is not greater than retained count")
    if isinstance(retained_count, int) and retained and len(retained) != retained_count:
        blockers.append("retained visual token count does not match retained index list")

    if not isinstance(generation.get("decoding_config"), dict):
        blockers.append("missing decoding_config")

    event_step = event.get("event_token_index")
    if not isinstance(event_step, int):
        blockers.append("missing event_token_index")
    elif tokens and not (0 <= event_step < len(tokens)):
        blockers.append("event_token_index outside generated token range")

    curve = event.get("similarity_curve")
    if not isinstance(curve, list) or not curve:
        blockers.append("missing active-bank similarity_curve")
    elif tokens:
        for record in curve:
            step = record.get("step")
            token_id = record.get("token_id")
            if isinstance(step, int) and 0 <= step < len(tokens) and token_id != tokens[step]:
                blockers.append(f"similarity_curve token mismatch at step {step}")
                break
    return blockers


def build_candidate_events(generation: dict[str, Any], event: dict[str, Any]) -> list[Phase2Event]:
    tokens = [int(token_id) for token_id in generation["generated_prefix_token_ids"]]
    candidates: list[Phase2Event] = []
    seen: set[tuple[str, int]] = set()

    def add_event(event_type: str, step: int, source: str, fallback_used: bool = False) -> None:
        if not (0 <= step < len(tokens)):
            return
        key = (event_type, step)
        if key in seen:
            return
        seen.add(key)
        candidates.append(
            Phase2Event(
                event_type=event_type,
                generated_token_index=step,
                token_id=int(tokens[step]),
                source=source,
                fallback_used=fallback_used,
            )
        )

    primary_step = event.get("event_token_index")
    primary_name = event.get("event_name")
    if isinstance(primary_step, int) and isinstance(primary_name, str):
        add_event(primary_name, primary_step, "phase1_event_log", bool(event.get("fallback_used")))

    curve = event.get("similarity_curve") or generation.get("active_bank_similarity_curve") or []
    valid_curve = [
        record for record in curve
        if isinstance(record.get("step"), int) and isinstance(record.get("risd_similarity_active"), (int, float))
    ]
    if valid_curve:
        min_record = min(valid_curve, key=lambda record: float(record["risd_similarity_active"]))
        add_event("minimum_active_similarity_step", int(min_record["step"]), "phase1_similarity_curve")

    if event.get("fallback_used") and isinstance(primary_step, int):
        add_event("fallback_event", primary_step, "phase1_event_log", True)

    return candidates


def event_context_token_ids(tokens: list[int], event_index: int, radius: int = 4) -> list[int]:
    start = max(0, event_index - radius)
    end = min(len(tokens), event_index + radius + 1)
    return tokens[start:end]


def _is_int_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, int) for item in value)

