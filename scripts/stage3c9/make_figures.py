#!/usr/bin/env python3
"""Create the required Stage 3C.9 causal-checkpoint figures."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"
FIG = OUT / "analysis/figures"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def save(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=180)
    plt.close()


def bar(title: str, labels: list[str], values: list[float], name: str, ylabel: str = "count") -> None:
    plt.figure(figsize=(max(5, 0.8 * len(labels)), 4))
    plt.bar(labels, values, color="#4472C4")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    save(name)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    accounting = read_json(OUT / "cohort/screening_accounting.json")
    manifest = read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    source = read_jsonl(OUT / "phase_a_source/w8_source_sensitivity.jsonl") + read_jsonl(OUT / "phase_a_source/w16_source_sensitivity.jsonl")
    spans = read_jsonl(OUT / "phase_b_checkpoint/event_span_rescue.jsonl")
    neighbors = read_jsonl(OUT / "phase_b_checkpoint/neighbor_controls.jsonl")
    classes = read_json(OUT / "phase_b_checkpoint/checkpoint_classification.json")["bases"]
    repeated = read_json(OUT / "phase_c_lifetime/repeated_checkpoint_classification.json")
    lifetime = read_jsonl(OUT / "phase_c_lifetime/lifetime_readouts.jsonl")
    reinstatement = read_jsonl(OUT / "phase_c_lifetime/same_evidence_reinstatement.jsonl")
    lexical = read_json(OUT / "phase_e_enrichment/checkpoint_type_enrichment.json")
    roles = read_json(OUT / "phase_e_enrichment/reasoning_role_enrichment.json")

    funnel_labels = ["attempted", "correct", "long_enough", "multi_segment", "multi_event", "edit_valid", "ROI_valid", "retained"]
    bar("Prospective long-horizon screening funnel", funnel_labels, [accounting.get(label, 0) for label in funnel_labels], "01_screening_funnel.png")

    locations = []
    lengths = {str(row["base_problem_id"]): int(row["final_use_readout"]["token_index"]) for row in manifest}
    for row in manifest:
        locations.extend(int(event["span_start_token"]) / max(lengths[str(row["base_problem_id"])], 1) for event in row["events"])
    plt.figure(figsize=(6, 4)); plt.hist(locations, bins=np.linspace(0, 1, 11), color="#70AD47"); plt.xlabel("normalized reasoning position"); plt.ylabel("events"); plt.title("Frozen event locations"); save("02_event_locations.png")

    source_groups = defaultdict(list)
    for row in source:
        source_groups[row["window"]].append(float(row["local_use"]["source_loss_mean"]))
    plt.figure(figsize=(6, 4)); plt.boxplot([source_groups["W8"], source_groups["W16"]], tick_labels=["W8", "W16"], showfliers=False); plt.axhline(0, color="black", lw=0.8); plt.ylabel("sign-aligned source loss (nats/token)"); plt.title("Event-local visual source sensitivity"); save("03_w8_w16_source_sensitivity.png")

    if neighbors:
        plt.figure(figsize=(5, 5)); plt.scatter([row["neighbor_gain_mean"] for row in neighbors], [row["event_gain_mean"] for row in neighbors], alpha=0.6); limits=plt.gca().get_xlim(); plt.plot(limits, limits, "k--", lw=0.8); plt.xlabel("matched-neighbor rescue"); plt.ylabel("event-span rescue"); plt.title("Checkpoint span vs matched neighbor"); save("04_span_vs_neighbor.png")
    else:
        bar("No source-sensitive checkpoint-rescue events", ["event", "neighbor"], [0, 0], "04_span_vs_neighbor.png")

    distinct_final = [row for row in spans if row["final_rescue_gain_mean"] is not None]
    if distinct_final:
        plt.figure(figsize=(5, 5)); plt.scatter([row["rescue_gain_mean"] for row in distinct_final], [row["final_rescue_gain_mean"] for row in distinct_final], alpha=0.6); plt.axhline(0, color="black", lw=0.7); plt.axvline(0, color="black", lw=0.7); plt.xlabel("local-use rescue"); plt.ylabel("distinct final-use rescue"); plt.title("Local versus distinct final checkpoint rescue"); save("05_local_vs_final_rescue.png")
    else:
        bar("No qualifying rescue events", ["local", "final"], [0, 0], "05_local_vs_final_rescue.png")

    counts = Counter(str(row["checkpoint_count_bin"]) for row in repeated["bases"])
    bar("Confirmed checkpoints per trajectory", ["0", "1", "2", "3+"], [counts.get(key, 0) for key in ("0", "1", "2", "3+")], "06_checkpoint_count.png")
    bar("Repeated-checkpoint classification", ["no", "yes"], [len(repeated["bases"]) - repeated["repeated_checkpoint_count"], repeated["repeated_checkpoint_count"]], "07_repeated_fraction.png")

    life_counts = Counter(row["lifetime_phenotype"] for row in lifetime)
    bar("Checkpoint lifetime phenotypes", ["L-Short", "L-Medium", "L-Persistent"], [life_counts.get(key, 0) for key in ("L-Short", "L-Medium", "L-Persistent")], "08_lifetime_distribution.png")
    pair_comparisons = [
        (row["base_problem_id"], comparison)
        for row in reinstatement
        for comparison in row["comparisons"]
    ]
    if pair_comparisons:
        plt.figure(figsize=(6, 5))
        x = [float(row["earlier_checkpoint_gain_at_later_readout"]) for _, row in pair_comparisons]
        y = [float(row["later_checkpoint_local_gain"]) for _, row in pair_comparisons]
        colors = ["#ED7D31" if row["reinstatement_pattern"] else "#A5A5A5" for _, row in pair_comparisons]
        plt.scatter(x, y, c=colors, alpha=0.75)
        plt.axhline(0.05, color="black", ls="--", lw=0.8)
        plt.axvline(0.05, color="black", ls="--", lw=0.8)
        plt.xlabel("earlier checkpoint gain at later readout")
        plt.ylabel("later checkpoint local gain")
        plt.title("Same-evidence checkpoint reinstatement pairs")
        save("09_same_evidence_reinstatement.png")
    else:
        bar("No evaluable same-evidence checkpoint pairs", ["pairs"], [0], "09_same_evidence_reinstatement.png")

    temporal = defaultdict(list)
    class_lookup = {(str(row["base_problem_id"]), int(event["event_id"])): event["temporal_location"] for row in classes for event in row["events"]}
    for row in spans:
        temporal[class_lookup[(str(row["base_problem_id"]), int(row["event_id"]))]].append(float(row["rescue_gain_mean"]))
    labels = ["EARLY", "MIDDLE", "LATE"]
    bar("Checkpoint rescue across reasoning time", labels, [float(np.mean(temporal[label])) if temporal[label] else 0.0 for label in labels], "10_temporal_checkpoint_rescue.png", ylabel="mean rescue gain")

    lexical_matched = lexical["matched_control_inference"]
    bar("Checkpoint lexical-type enrichment after matching", list(lexical_matched), [row["mean"] or 0.0 for row in lexical_matched.values()], "11_checkpoint_type_enrichment.png", ylabel="matched indicator difference")
    role_matched = roles["matched_control_inference"]
    bar("Checkpoint reasoning-role enrichment after matching", list(role_matched), [row["mean"] or 0.0 for row in role_matched.values()], "12_reasoning_role_enrichment.png", ylabel="matched indicator difference")

    route_path = OUT / "phase_d_routes/route_classification.json"
    route = read_json(route_path)
    if route.get("bases"):
        route_bases = route["bases"]
        labels = ["direct", "prior_checkpoint", "short_history", "joint"]
        bar("Route intervention deficits", labels, [float(np.mean([row["effects"][label] for row in route_bases])) for label in labels], "13_route_effects.png", ylabel="mean sign-aligned deficit")
        route_counts = Counter(row["route_phenotype"] for row in route_bases)
        names = ["R-Direct", "R-Inherited", "R-Mixed", "R-Redundant", "R-Unresolved"]
        bar("Route phenotype distribution", names, [route_counts.get(name, 0) for name in names], "14_route_phenotypes.png")

    representative = sorted(classes, key=lambda row: (-int(row["repeated_checkpoint"]), -int(row["checkpoint_count"]), int(row["base_problem_id"])))[:6]
    plt.figure(figsize=(10, max(3, 0.7 * len(representative))))
    colors = {"C0": "#BFBFBF", "C1": "#FFC000", "C2": "#5B9BD5", "C3": "#ED7D31"}
    for y, row in enumerate(representative):
        length = lengths[str(row["base_problem_id"])]
        plt.plot([0, 1], [y, y], color="#DDDDDD")
        for event in row["events"]:
            x = int(event["span_start_token"]) / max(length, 1)
            plt.scatter([x], [y], color=colors[event["classification"]], s=55, label=event["classification"] if y == 0 else None)
    plt.yticks(range(len(representative)), [f"base {row['base_problem_id']}" for row in representative])
    plt.xlabel("normalized reasoning position"); plt.title("Representative frozen event/checkpoint timelines")
    handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=color, label=name, markersize=7) for name, color in colors.items()]
    plt.legend(handles=handles, loc="upper right", ncol=4)
    save("15_representative_timelines.png")

    files = sorted(path.name for path in FIG.glob("*.png"))
    (FIG / "figure_manifest.json").write_text(json.dumps({"figures": files, "route_figures_required": bool(route.get("bases")), "attention_overlay_omitted": True}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"figures": len(files), "route_figures": bool(route.get("bases"))}, indent=2))


if __name__ == "__main__":
    main()
