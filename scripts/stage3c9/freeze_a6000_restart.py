#!/usr/bin/env python3
"""Validate and freeze the clean A6000 Stage 3C.9 restart at trajectory 0."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"
OLD = ROOT / "outputs/stage3c9_a5000_provenance"
CAL = ROOT / "outputs/a6000_calibration_v2"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_screen_hash(rows: list[dict[str, Any]]) -> str:
    normalized = [{key: value for key, value in row.items() if key != "frozen_at"} for row in rows]
    payload = "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in normalized)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    if not OLD.is_dir() or not OUT.is_dir():
        raise RuntimeError("Both preserved A5000 provenance and clean A6000 roots are required")
    acceptance = read_json(CAL / "summaries/a6000_calibration_v2_acceptance.json")
    if acceptance["status"] != "PASS — A6000 CANONICAL PATH READY" or not acceptance["passed"]:
        raise RuntimeError("Calibration v2 has not authorized the A6000 restart")

    config = read_json(OUT / "config/stage3c9_config.json")
    runtime = config["runtime"]
    canonical = runtime["canonical_scoring"]
    config_checks = {
        "gpu_class_A6000": runtime["gpu_class"] == "A6000",
        "four_allocated_ranks": int(runtime["allocated_gpus"]) == 4 and int(config["screening"]["shards"]) == 4,
        "existing_allocation_only": runtime["slurm_allocation"] == "108085" and runtime["tmux_session"] == "9",
        "canonical_P2_path": canonical["path"] == "P2_fixed_streaming_cached",
        "fixed_chunk_2048": int(canonical["chunk_size"]) == 2048,
        "allocator_release": canonical["release_allocator_cache_between_chunks"] is True,
        "no_chunk_switching": canonical["per_example_chunk_switching"] is False,
        "restart_from_zero": int(runtime["clean_restart"]["trajectory_start"]) == 0,
        "no_A5000_outcome_reuse": runtime["clean_restart"]["a5000_outcomes_reused"] is False,
    }

    old_screen_path = OLD / "cohort/prospective_screen_manifest.jsonl"
    new_screen_path = OUT / "cohort/prospective_screen_manifest.jsonl"
    old_screen, new_screen = read_jsonl(old_screen_path), read_jsonl(new_screen_path)
    old_hash, new_hash = normalized_screen_hash(old_screen), normalized_screen_hash(new_screen)
    initial = [row for row in new_screen if int(row["screen_order"]) < 600]
    shard_rows = [read_jsonl(OUT / f"cohort/initial_generation_shard_{index:02d}.jsonl") for index in range(4)]
    selection_checks = {
        "same_outcome_blind_screen_as_preserved_tree": old_hash == new_hash,
        "screen_size_1000": len(new_screen) == 1000,
        "initial_size_600": len(initial) == 600,
        "initial_unique_bases_600": len({row["base_problem_id"] for row in initial}) == 600,
        "four_equal_shards": [len(rows) for rows in shard_rows] == [150, 150, 150, 150],
        "selection_is_attention_blind": all(not row["selection_used_attention"] for row in new_screen),
        "selection_is_outcome_blind": all(not row["selection_used_generation_outcome"] for row in new_screen),
        "selection_is_carrier_blind": all(not row["selection_used_carrier_outcome"] for row in new_screen),
    }
    new_raw = sorted((OUT / "prospective_generation/raw").glob("**/examples/*/generation.json"))
    old_raw = sorted((OLD / "prospective_generation/raw").glob("**/examples/*/generation.json"))
    restart_checks = {
        "clean_root_has_zero_generation_bundles": len(new_raw) == 0,
        "A5000_bundles_preserved_separately": len(old_raw) > 0,
        "A5000_primary_mix_impossible_at_freeze": OUT.resolve() != OLD.resolve(),
    }

    implementation_paths = [
        ROOT / "code/visual_reasoning/stage3c9/protocol.py",
        ROOT / "code/visual_reasoning/stage3c9/streaming.py",
        ROOT / "scripts/stage3c9/prepare_config.py",
        ROOT / "scripts/stage3c9/run_initial_generation.py",
        ROOT / "scripts/stage3c9/run_initial_generation_tmux.sh",
        ROOT / "scripts/stage3c9/run_source_sensitivity.py",
        ROOT / "scripts/stage3c9/run_checkpoint_rescue.py",
        ROOT / "scripts/stage3c9/run_lifetime.py",
        ROOT / "scripts/stage3c9/run_routes.py",
        ROOT / "scripts/stage3c9/validate_mechanics.py",
        ROOT / "scripts/stage3c9/run_validation_tmux.sh",
        ROOT / "scripts/stage3c9/run_primary_tmux.sh",
        ROOT / "tests/stage3c9/test_protocol.py",
        ROOT / "tests/stage3c9/test_streaming.py",
        Path(__file__),
    ]
    missing = [str(path) for path in implementation_paths if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing restart implementation files: {missing}")
    source_text = {path.name: path.read_text(encoding="utf-8") for path in implementation_paths}
    static_checks = {
        "generation_launch_uses_four_ranks": "--nproc_per_node=4" in source_text["run_initial_generation_tmux.sh"],
        "causal_launches_use_four_ranks": source_text["run_validation_tmux.sh"].count("--nproc_per_node=4") == 3
        and source_text["run_primary_tmux.sh"].count("--nproc_per_node=4") == 4,
        "all_causal_runners_resolve_frozen_runtime": all(
            "canonical_streaming_kwargs(config)" in source_text[name]
            for name in ("run_source_sensitivity.py", "run_checkpoint_rescue.py", "run_lifetime.py", "run_routes.py")
        ),
        "all_patch_runners_force_shared_boundaries": all(
            "forced_generated_boundaries=forced_boundaries" in source_text[name]
            for name in ("run_checkpoint_rescue.py", "run_lifetime.py", "run_routes.py")
        ),
        "cross_path_equality_not_mechanics_gate": "cross_path_exactness_is_readiness_gate\": False" in source_text["validate_mechanics.py"],
    }

    all_checks = {**config_checks, **selection_checks, **restart_checks, **static_checks}
    if not all(all_checks.values()):
        failures = [name for name, passed in all_checks.items() if not passed]
        raise RuntimeError(f"A6000 restart freeze failed: {failures}")
    frozen_at = datetime.now(timezone.utc).isoformat()
    freeze = {
        "frozen_at": frozen_at,
        "status": "AUTHORIZED — CLEAN A6000 STAGE 3C.9 RESTART FROM 0/600",
        "calibration_acceptance_sha256": sha256(CAL / "summaries/a6000_calibration_v2_acceptance.json"),
        "config": str((OUT / "config/stage3c9_config.json").relative_to(ROOT)),
        "config_sha256": sha256(OUT / "config/stage3c9_config.json"),
        "normalized_screen_sha256": new_hash,
        "raw_screen_file_sha256": sha256(new_screen_path),
        "preserved_A5000_screen_file_sha256": sha256(old_screen_path),
        "preserved_A5000_generation_bundles": len(old_raw),
        "clean_A6000_generation_bundles_at_freeze": len(new_raw),
        "checks": all_checks,
        "implementation_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in implementation_paths},
        "canonical_execution": {
            "hardware": "NVIDIA RTX A6000",
            "device_indices": [0, 1, 2, 3],
            "path": "P2_fixed_streaming_cached",
            "chunk_size": 2048,
            "release_allocator_cache_between_chunks": True,
            "per_example_chunk_switching": False,
            "same_path_tolerance": 1e-6,
        },
    }
    write_json(OUT / "config/a6000_execution_freeze.json", freeze)

    provenance = f"""# Stage 3C.9 A6000 Clean-Restart Provenance

The partial A5000 tree was moved intact to `outputs/stage3c9_a5000_provenance/` and is excluded from primary inference. It contains {len(old_raw)} generated artifact bundles; no generated bundle was copied into the clean A6000 tree.

The prospective candidate identities and ordering remain unchanged. After excluding the timestamp-only `frozen_at` field, the preserved and clean 1,000-row screens have the same SHA-256 `{new_hash}`. The initial tranche remains 600 unique base problems, now split into four equal 150-example shards.

The A6000 primary root was frozen with zero generated bundles. All later causal conditions must use fixed 2,048-token streaming, allocator-cache release between chunks, and condition-invariant intervention boundaries. A5000 and A6000 outcomes must never be pooled.
"""
    (OUT / "config/a6000_restart_provenance.md").write_text(provenance, encoding="utf-8")

    authorization = f"""# Stage 3C.9 Restart Authorization

**AUTHORIZED — CLEAN A6000 STAGE 3C.9 RESTART FROM 0/600**

Calibration v2 passed all 17 readiness criteria. The canonical protocol is fixed 2,048-token cached streaming on the four NVIDIA RTX A6000 devices in existing Slurm allocation 108085 / tmux session 9, with allocator-cache release between chunks and no per-example path switching.

The prior A5000 work remains immutable provenance at `outputs/stage3c9_a5000_provenance/`. Its {len(old_raw)} generated bundles are not part of the restarted cohort. The clean A6000 root contained 0 generated bundles when frozen, and the outcome-blind 600-example prospective selection matches the preserved selection exactly apart from its new freeze timestamp.

Cross-path BF16 differences are retained as diagnostics. Every primary within-event contrast must use the same A6000 streaming path. No new mechanism stage is authorized by this document.
"""
    path = CAL / "summaries/stage3c9_restart_authorization.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(authorization, encoding="utf-8")
    print(json.dumps({
        "status": freeze["status"],
        "checks_passed": sum(all_checks.values()),
        "checks_total": len(all_checks),
        "old_A5000_bundles": len(old_raw),
        "new_A6000_bundles": len(new_raw),
        "normalized_screen_sha256": new_hash,
    }, indent=2))


if __name__ == "__main__":
    main()
