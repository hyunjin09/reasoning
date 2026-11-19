#!/usr/bin/env python3
"""Fit uncentered Stage 3B.8 semantic and sham SVD bases on discovery only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from visual_reasoning.stage0.io import ensure_directory, write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def svd_payload(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    _, singular_values, vh = np.linalg.svd(matrix.astype(np.float64), full_matrices=False)
    energy = np.square(singular_values)
    fraction = energy / energy.sum() if energy.sum() else np.zeros_like(energy)
    return vh.T, singular_values, {
        "row_count": int(matrix.shape[0]),
        "dimension": int(matrix.shape[1]),
        "matrix_rank": int(np.linalg.matrix_rank(matrix)),
        "singular_values": singular_values.tolist(),
        "explained_energy_fraction": fraction.tolist(),
        "cumulative_explained_energy_fraction": np.cumsum(fraction).tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--expected-bases", type=int, required=True)
    args = parser.parse_args()
    if args.expected_bases < 16 or args.expected_bases > 20:
        raise ValueError("Discovery SVD requires the frozen 16--20 base cohort")
    directories = [args.raw_root / f"{args.prefix}_{rank:02d}" for rank in range(2)]
    if not all((path / "result.json").is_file() for path in directories):
        raise RuntimeError("Both completed discovery-capture shards are required")
    results = [row for path in directories for row in read_jsonl(path / "results.jsonl")]
    if len(results) != args.expected_bases or len({row["base_problem_id"] for row in results}) != args.expected_bases:
        raise RuntimeError("Discovery capture is incomplete or duplicated")
    if not all(row["cohort_role"] == "discovery" and row["experiment"] == "capture" for row in results):
        raise RuntimeError("Only discovery capture outputs may fit Stage 3B.8 subspaces")
    protected = read_json(OUT / "config/discovery_confirmation_split.json")
    protected_bases = set(protected["primary_confirmation"]["base_problem_ids"])
    protected_bases.update(protected["protected_diagnostic"]["old_stage3b7_base_problem_ids"])
    protected_bases.update(protected["protected_diagnostic"]["stage3b7r_base_problem_ids"])
    bases = sorted([str(row["base_problem_id"]) for row in results], key=int)
    if set(bases) & protected_bases:
        raise RuntimeError("Discovery fitting set overlaps a protected cohort")
    by_base_dir = {
        str(row["base_problem_id"]): next(
            path / "examples" / str(row["base_problem_id"])
            for path in directories
            if (path / "examples" / str(row["base_problem_id"]) / "vectors.npz").is_file()
        )
        for row in results
    }
    config = read_json(OUT / "config/stage3b8_config.json")
    target_ids = [target["target_id"] for target in config["targets"]]
    candidate_ranks = [int(value) for value in config["subspace"]["candidate_ranks"]]
    ensure_directory(OUT / "subspace/discovery_delta_matrix")
    ensure_directory(OUT / "analysis/figures")
    arrays: dict[str, np.ndarray] = {}
    statistics = []
    for target_id in target_ids:
        semantic = np.stack([
            np.load(by_base_dir[base] / "vectors.npz")[f"{target_id}__semantic_delta"]
            for base in bases
        ])
        sham = np.stack([
            np.load(by_base_dir[base] / "vectors.npz")[f"{target_id}__sham_delta"]
            for base in bases
        ])
        semantic_basis, semantic_values, semantic_stats = svd_payload(semantic)
        sham_basis, sham_values, sham_stats = svd_payload(sham)
        eligible = [rank for rank in candidate_ranks if rank <= semantic_basis.shape[1]]
        if not eligible:
            raise RuntimeError(f"No frozen rank is supported for {target_id}")
        for rank in eligible:
            arrays[f"{target_id}__semantic_rank_{rank}"] = semantic_basis[:, :rank]
            arrays[f"{target_id}__sham_rank_{rank}"] = sham_basis[:, :rank]
        np.savez_compressed(
            OUT / f"subspace/discovery_delta_matrix/{target_id}.npz",
            base_problem_ids=np.asarray(bases),
            semantic_delta=semantic,
            sham_delta=sham,
        )
        statistics.append({
            "target_id": target_id,
            "base_problem_ids": bases,
            "candidate_ranks": eligible,
            "semantic": semantic_stats,
            "sham": sham_stats,
        })
        fig, axis = plt.subplots(figsize=(6.4, 4.2))
        axis.plot(np.arange(1, len(semantic_values) + 1), semantic_values, marker="o", label="semantic delta")
        axis.plot(np.arange(1, len(sham_values) + 1), sham_values, marker="s", label="sham delta")
        axis.set(xlabel="singular component", ylabel="singular value", title=f"Discovery Value spectrum — {target_id}")
        axis.legend()
        fig.tight_layout()
        fig.savefig(OUT / f"analysis/figures/discovery_singular_spectrum_{target_id}.png", dpi=180)
        plt.close(fig)
    np.savez_compressed(OUT / "subspace/discovery_fitted_bases.npz", **arrays)
    write_json(OUT / "subspace/svd_statistics.json", {
        "fit_cohort_role": "fresh_discovery_only",
        "base_count": len(bases),
        "base_problem_ids": bases,
        "primary_bases_used": False,
        "old_validation_bases_used": False,
        "stage3b7r_validation_bases_used": False,
        "fit": "uncentered SVD",
        "targets": statistics,
    })
    print(json.dumps({"base_count": len(bases), "targets": target_ids, "array_count": len(arrays)}, indent=2))


if __name__ == "__main__":
    main()
