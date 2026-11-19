#!/usr/bin/env python3
"""Persist the score-blind text audit of ambiguous and representative Stage 3A rollouts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROLLOUTS = ROOT / "outputs/stage3a/scoring/rollout_results.jsonl"
FACTS = ROOT / "outputs/stage3a/scoring/fact_preference.jsonl"
OUT_JSONL = ROOT / "outputs/stage3a/analysis/rollout_manual_audit.jsonl"
OUT_MD = ROOT / "outputs/stage3a/analysis/rollout_manual_audit.md"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# These decisions were made by reading the 128-token continuations. They do not
# change the frozen cohort or any probability score.
OVERRIDES: dict[tuple[str, str], tuple[str, str]] = {
    ("2", "sham"): ("neither_detected", "No target value was stated within 128 tokens."),
    ("3", "original"): ("neither_detected", "The entity was discussed, but neither target value was stated."),
    ("3", "counterfactual"): ("neither_detected", "The entity was discussed, but neither target value was stated."),
    ("3", "sham"): ("neither_detected", "The entity was discussed, but neither target value was stated."),
    ("9", "original"): ("neither_detected", "AB was discussed, but neither target length was stated."),
    ("9", "counterfactual"): ("neither_detected", "AB was discussed, but neither target length was stated."),
    ("9", "sham"): ("neither_detected", "AB was discussed, but neither target length was stated."),
    ("103", "counterfactual"): (
        "counterfactual_fact",
        "The first evidence statement is 125 degrees; the later 130 occurs in the answer-choice range.",
    ),
    ("118", "sham"): ("neither_detected", "The sector was discussed, but its target radius was not stated."),
    ("140", "original"): ("neither_detected", "AO was discussed, but neither target height was stated."),
    ("140", "sham"): ("original_fact", "The rollout states AO is 1.52 m; the suffix m defeated the automatic boundary regex."),
    ("141", "sham"): ("original_fact", "The first target statement is AB=15; 18 is subsequently derived as 3+15."),
    ("147", "original"): ("original_fact", "The first target statement is DF=1.5 m."),
    ("147", "sham"): ("original_fact", "The first target statement is DF=1.5 m."),
    ("613", "counterfactual"): (
        "counterfactual_fact",
        "The graph is first described as horizontal/flat and then steadily rising.",
    ),
    ("613", "sham"): ("original_fact", "The graph is first described as one straight rising line."),
    ("614", "original"): ("original_fact", "The graph is first described as shallow and then steeper."),
    ("614", "counterfactual"): ("counterfactual_fact", "The graph is first described as rising to a peak and falling."),
    ("614", "sham"): ("original_fact", "The graph is first described as gentle and then steeper."),
    ("616", "original"): (
        "neither_detected",
        "The word constant occurs only in a generic explanation; the target graph shape is not yet stated.",
    ),
    ("616", "sham"): (
        "neither_detected",
        "The word constant occurs only in a generic explanation; the target graph shape is not yet stated.",
    ),
    ("617", "original"): ("original_fact", "The graph is described as rising and then becoming horizontal."),
    ("617", "sham"): ("original_fact", "The graph is described as rising and then becoming horizontal."),
    ("753", "counterfactual"): (
        "counterfactual_direction_inexact_value",
        "The rollout replaces original length 6 with 5, not the exact edited 5.4; direction changes but exact fact is misstated.",
    ),
}


def main() -> None:
    rows = read_jsonl(ROLLOUTS)
    facts = read_jsonl(FACTS)
    by_key = {(str(row["base_problem_id"]), str(row["condition"])): row for row in rows}
    required = {
        key for key, row in by_key.items() if bool(row.get("automatic_annotation_requires_manual_audit"))
    }
    if not required.issubset(set(OVERRIDES)):
        raise RuntimeError(f"Manual audit map misses ambiguous rows: {sorted(required-set(OVERRIDES))}")
    records = []
    for key in sorted(OVERRIDES, key=lambda item: (int(item[0]), item[1])):
        label, note = OVERRIDES[key]
        source = by_key[key]
        records.append(
            {
                "base_problem_id": key[0],
                "condition": key[1],
                "automatic_label": source["first_entity_or_fact_statement"],
                "manual_label": label,
                "manual_note": note,
                "continuation_token_count": source["generated_token_count"],
                "manual_audit_scope": "full persisted 128-token continuation",
                "changes_frozen_score_or_cohort": False,
            }
        )
    OUT_JSONL.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")

    corrected = []
    for row in rows:
        key = (str(row["base_problem_id"]), str(row["condition"]))
        corrected.append((row["condition"], OVERRIDES.get(key, (row["first_entity_or_fact_statement"], ""))[0]))
    counts = Counter(corrected)
    ranked = sorted(facts, key=lambda row: float(row["CE_controlled"]))
    representatives = ranked[:2] + ranked[-2:]
    lines = [
        "# Stage 3A Short-Rollout Manual Audit",
        "",
        "The full persisted continuations were read for all 22 automatically ambiguous condition-rollouts and two targeted false-positive checks. "
        "This audit was performed after the cohort and primary probability scores were frozen. It changes neither.",
        "",
        "## Corrected qualitative counts",
        "",
        "| Condition | Original fact | Counterfactual fact | Inexact counterfactual direction | Neither |",
        "|---|---:|---:|---:|---:|",
    ]
    for condition in ("original", "counterfactual", "sham"):
        lines.append(
            f"| {condition} | {counts[(condition, 'original_fact')]} | {counts[(condition, 'counterfactual_fact')]} | "
            f"{counts[(condition, 'counterfactual_direction_inexact_value')]} | {counts[(condition, 'neither_detected')]} |"
        )
    lines.extend(["", "The rollouts are one matched stochastic seed and are qualitative validation, not frequency estimates.", "", "## Manual resolutions", ""])
    for record in records:
        lines.append(
            f"- Base {record['base_problem_id']} / {record['condition']}: "
            f"`{record['automatic_label']}` -> `{record['manual_label']}`. {record['manual_note']}"
        )
    lines.extend(["", "## Strongest/weakest representative inspection", ""])
    for row in representatives:
        base = str(row["base_problem_id"])
        conditions = {condition: by_key[(base, condition)] for condition in ("original", "counterfactual", "sham")}
        final_labels = {
            condition: OVERRIDES.get(
                (base, condition), (conditions[condition]["first_entity_or_fact_statement"], "")
            )[0]
            for condition in conditions
        }
        lines.append(
            f"- Base {base}: controlled CE={float(row['CE_controlled']):.6f}. "
            f"Final audited rollout labels: original={final_labels['original']}, "
            f"counterfactual={final_labels['counterfactual']}, sham={final_labels['sham']}."
        )
    lines.extend(
        [
            "",
            "Base 2 is the weakest controlled case: most of its raw target effect is also present in the sham, leaving a near-zero positive controlled effect. "
            "Base 613 is the next weakest but its structural counterfactual rollout changes in the intended semantic direction. "
            "Bases 80 and 78 are the strongest and explicitly state the edited versus original numeric facts under counterfactual versus original/sham images.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"manual_condition_rollouts": len(records), "representative_bases": [str(row["base_problem_id"]) for row in representatives]}, indent=2))


if __name__ == "__main__":
    main()
