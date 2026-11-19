#!/usr/bin/env python3
"""Freeze Stage 3B.9 protocol, protected cohorts, and historical rank families."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b9.geometry import fit_uncentered_rank_family, random_rank_family


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
STAGE3B8 = ROOT / "outputs/stage3b8"
RANKS = [1, 2, 4, 8, 16, 24, 32, 48]
TARGET_IDS = ["target_a", "target_b_r"]
RANDOM_COUNT = 100
RANDOM_SEED = 12_340


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def vector_path(base: str, *, discovery: set[str]) -> Path:
    prefix = "discovery_capture" if base in discovery else "primary_dose"
    matches = sorted((STAGE3B8 / "scoring/raw").glob(f"{prefix}_*/examples/{base}/vectors.npz"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one historical vector file for base {base}, found {len(matches)}")
    return matches[0]


def save_npz_once(path: Path, arrays: dict[str, np.ndarray]) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to replace frozen basis file: {path}")
    ensure_directory(path.parent)
    np.savez_compressed(path, **arrays)


def main() -> None:
    plan_path = ROOT / "plan/stage3b9_plan.md"
    stage3b8_config = read_json(STAGE3B8 / "config/stage3b8_config.json")
    split = read_json(STAGE3B8 / "config/discovery_confirmation_split.json")
    discovery_rows = read_jsonl(STAGE3B8 / "discovery_cohort/discovery_manifest.jsonl")
    discovery = {str(row["base_problem_id"]) for row in discovery_rows}
    primary = {str(value) for value in split["primary_confirmation"]["base_problem_ids"]}
    old_stage3b7 = {str(value) for value in split["protected_diagnostic"]["old_stage3b7_base_problem_ids"]}
    stage3b7r = {str(value) for value in split["protected_diagnostic"]["stage3b7r_base_problem_ids"]}
    if len(discovery) != 20 or len(primary) != 37 or discovery & primary:
        raise RuntimeError("The immutable Stage 3B.8 20+37 geometry split is not intact")
    historical = sorted(discovery | primary, key=int)
    if len(historical) != 57 or (set(historical) & old_stage3b7) or (set(historical) & stage3b7r):
        raise RuntimeError("Historical and protected validation cohorts are not disjoint")
    targets = stage3b8_config["targets"]
    if [row["target_id"] for row in targets] != TARGET_IDS:
        raise RuntimeError("Stage 3B.8 targets differ from the frozen Stage 3B.9 target family")
    if [(row["layer_index"], row["heads"]) for row in targets] != [
        (29, [11, 6, 15, 12]),
        (28, [16, 0, 3, 6]),
    ]:
        raise RuntimeError("Frozen layers/heads do not match the approved Stage 3B.9 plan")

    frozen_at = datetime.now(timezone.utc).isoformat()
    manifest = []
    semantic_rows: dict[str, list[np.ndarray]] = {target: [] for target in TARGET_IDS}
    sham_rows: dict[str, list[np.ndarray]] = {target: [] for target in TARGET_IDS}
    for base in historical:
        path = vector_path(base, discovery=discovery)
        with np.load(path) as payload:
            for target in TARGET_IDS:
                semantic = np.asarray(payload[f"{target}__semantic_delta"], dtype=np.float64)
                sham = np.asarray(payload[f"{target}__sham_delta"], dtype=np.float64)
                if semantic.shape != (512,) or sham.shape != (512,):
                    raise RuntimeError(f"Unexpected vector shape in {path}")
                semantic_rows[target].append(semantic)
                sham_rows[target].append(sham)
        manifest.append({
            "base_problem_id": base,
            "historical_role": "stage3b8_discovery" if base in discovery else "stage3b8_primary_confirmation",
            "vector_file": str(path.relative_to(ROOT)),
            "vector_file_sha256": sha256(path),
            "used_for_stage3b9_training_only": True,
            "eligible_as_fresh_stage3b9_evidence": False,
        })

    basis_root = OUT / "phase_a_shared/basis"
    ensure_directory(basis_root)
    semantic_stats: dict[str, Any] = {}
    sham_stats: dict[str, Any] = {}
    sham_arrays: dict[str, np.ndarray] = {}
    random_arrays: dict[str, np.ndarray] = {}
    random_seed_rows = []
    basis_paths: dict[str, Path] = {}
    for target_index, target in enumerate(TARGET_IDS):
        semantic_matrix = np.stack(semantic_rows[target])
        sham_matrix = np.stack(sham_rows[target])
        semantic_family, semantic_audit = fit_uncentered_rank_family(semantic_matrix, frozen_ranks=RANKS)
        sham_family, sham_audit = fit_uncentered_rank_family(sham_matrix, frozen_ranks=RANKS)
        if list(semantic_family) != RANKS or list(sham_family) != RANKS:
            raise RuntimeError(f"All frozen ranks through 48 must be identifiable for {target}")
        target_path = basis_root / f"{target}_rank_bases.npz"
        save_npz_once(target_path, {f"rank_{rank}": basis for rank, basis in semantic_family.items()})
        basis_paths[target] = target_path
        semantic_stats[target] = semantic_audit
        sham_stats[target] = sham_audit
        for rank, basis in sham_family.items():
            sham_arrays[f"{target}__rank_{rank}"] = basis
        for random_index in range(RANDOM_COUNT):
            seed = RANDOM_SEED + target_index * 100_000 + random_index
            family = random_rank_family(dimension=512, ranks=RANKS, seed=seed)
            random_seed_rows.append({"target_id": target, "random_index": random_index, "seed": seed})
            for rank, basis in family.items():
                random_arrays[f"{target}__random_{random_index:03d}__rank_{rank}"] = basis.astype(np.float32)

    sham_path = basis_root / "sham_bases.npz"
    random_path = basis_root / "random_bases.npz"
    save_npz_once(sham_path, sham_arrays)
    save_npz_once(random_path, random_arrays)
    write_json(basis_root / "random_basis_seeds.json", {
        "construction": "one deterministic Gaussian QR draw per target/random_index; ranks are nested prefixes",
        "ambient_dimension": 512,
        "frozen_ranks": RANKS,
        "random_basis_count_per_target": RANDOM_COUNT,
        "master_seed": RANDOM_SEED,
        "rows": random_seed_rows,
        "basis_file": str(random_path.relative_to(ROOT)),
        "basis_file_sha256": sha256(random_path),
    })

    target_payload = {
        "source": "outputs/stage3b8/config/stage3b8_config.json",
        "source_sha256": sha256(STAGE3B8 / "config/stage3b8_config.json"),
        "targets": targets,
        "representation": stage3b8_config["representation"],
    }
    write_json(OUT / "config/frozen_targets.json", target_payload)
    write_json(OUT / "config/frozen_rank_family.json", {
        "fit": "uncentered SVD on all 57 historical Stage 3B.8 bases; fresh Stage 3B.9 bases excluded",
        "frozen_ranks": RANKS,
        "semantic_statistics": semantic_stats,
        "sham_statistics": sham_stats,
        "semantic_basis_files": {
            target: {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
            for target, path in basis_paths.items()
        },
        "sham_basis_file": {"path": str(sham_path.relative_to(ROOT)), "sha256": sha256(sham_path)},
        "random_basis_file": {"path": str(random_path.relative_to(ROOT)), "sha256": sha256(random_path)},
    })
    write_jsonl(OUT / "phase_a_shared/historical_training_manifest.jsonl", manifest)
    write_json(OUT / "config/cohort_split.json", {
        "historical_training": {"count": 57, "base_problem_ids": historical},
        "protected_stage3b7": {"count": len(old_stage3b7), "base_problem_ids": sorted(old_stage3b7, key=int)},
        "protected_stage3b7r": {"count": len(stage3b7r), "base_problem_ids": sorted(stage3b7r, key=int)},
        "phase_a_and_phase_b": "must be fresh, mutually disjoint, and disjoint from all IDs above",
    })
    decision_rules = {
        "phase_a": {
            "pass": "smallest k with median SR>=0.80, median CR<=0.30, robust positive learned effect, learned>sham, learned>95th random percentile, bidirectional consistency>=0.75",
            "labels": {"16-24": "Shared-Moderate-Dimensional", "32-48": "Shared-High-Dimensional", "none": "No-Robust-Shared-Compression"},
        },
        "phase_b": {
            "applicability": "usable full V-only transfer for at least 3 of 4 alternative values per base and target",
            "local_low_dimensional": "rank 1 or 2 with median held-out Local_SR>=0.80, median Local_CR<=0.30, learned>random, bidirectional consistency>=0.75",
            "ranks": [1, 2, 3],
        },
        "primary_unit": "base_problem_id",
        "attention_role": "secondary only after primary causal results freeze",
    }
    write_json(OUT / "config/decision_rules.json", decision_rules)
    write_json(OUT / "config/stage3b9_config.json", {
        "frozen_at": frozen_at,
        "source_plan": str(plan_path.relative_to(ROOT)),
        "source_plan_sha256": sha256(plan_path),
        "model": stage3b8_config["model"],
        "model_checkpoint": stage3b8_config["model_checkpoint"],
        "locked_generation_protocol": stage3b8_config["locked_generation_protocol"],
        "targets_file": "outputs/stage3b9/config/frozen_targets.json",
        "rank_family_file": "outputs/stage3b9/config/frozen_rank_family.json",
        "cohort_split_file": "outputs/stage3b9/config/cohort_split.json",
        "decision_rules_file": "outputs/stage3b9/config/decision_rules.json",
        "selection_blinding": {"attention": False, "stage3b9_value_vectors": False, "causal_outcomes": False},
    })
    write_text(OUT / "history/immutable_stage3b8_result.md", """# Immutable Stage 3B.8 result\n\nStage 3B.8 is input evidence only and remains unmodified. Its 20 discovery and 37 primary bases form the 57-base Stage 3B.9 historical training pool. They are not fresh confirmation evidence.\n\nFrozen result: graded causal Value transport at both late-W4 targets, but no robust shared rank-8 compression on the untouched Stage 3B.8 cohort.\n\nSource: `outputs/stage3b8/summaries/stage3b8_summary.md`.\n""")
    print(json.dumps({
        "historical_bases": len(historical),
        "ranks": RANKS,
        "random_bases_per_target": RANDOM_COUNT,
        "basis_files": [str(path.relative_to(ROOT)) for path in [*basis_paths.values(), sham_path, random_path]],
    }, indent=2))


if __name__ == "__main__":
    main()
