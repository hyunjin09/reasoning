import json
from pathlib import Path

from scripts.stage3b9.collect_all_prospective_generations import frozen_generation_rows


ROOT = Path(__file__).resolve().parents[2]


def test_corrected_prospective_generation_pool_is_fresh_and_disjoint():
    rows = frozen_generation_rows()
    split = json.loads((ROOT / "outputs/stage3b9/config/cohort_split.json").read_text())
    protected = {
        str(base)
        for key in ("historical_training", "protected_stage3b7", "protected_stage3b7r")
        for base in split[key]["base_problem_ids"]
    }
    bases = [str(row["base_problem_id"]) for row in rows]

    assert len(rows) == 75
    assert len(set(bases)) == 75
    assert "751" not in bases
    assert set(bases).isdisjoint(protected)
    assert sum(row["phase"] == "phase_a" for row in rows) == 53
    assert sum(row["phase"] == "phase_b" for row in rows) == 22


def test_applicability_repair_expansion_is_frozen_and_disjoint():
    shards = ROOT / "outputs/stage3b9/config/generation_applicability_expansion_shards"
    rows = [
        json.loads(line)
        for path in sorted(shards.glob("shard_*.jsonl"))
        for line in path.read_text().splitlines()
        if line.strip()
    ]
    prior = {str(row["base_problem_id"]) for row in frozen_generation_rows()}
    split = json.loads((ROOT / "outputs/stage3b9/config/cohort_split.json").read_text())
    protected = {
        str(base)
        for key in ("historical_training", "protected_stage3b7", "protected_stage3b7r")
        for base in split[key]["base_problem_ids"]
    }
    bases = {str(row["base_problem_id"]) for row in rows}
    mappings = [
        json.loads(line)
        for line in (
            ROOT / "outputs/stage3b9/roi_validation_applicability_expansion_v2/roi_token_mapping.jsonl"
        ).read_text().splitlines()
        if line.strip()
    ]

    assert len(rows) == len(bases) == 7
    assert bases.isdisjoint(prior | protected)
    assert bases == {str(row["base_problem_id"]) for row in mappings}
    assert all(row["manual_overlay_validation"]["status"] == "pass" for row in mappings)
