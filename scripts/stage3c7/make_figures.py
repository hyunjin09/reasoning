#!/usr/bin/env python3
"""Create the 14 required Stage 3C.7 figures from frozen aggregates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c7"
FIG = OUT / "analysis/figures"
TARGETS = ("target_a", "target_b")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rows(path: str, target: str) -> list[dict[str, Any]]:
    return [r for r in read_jsonl(OUT / path) if r.get("target_id") == target and r.get("base_problem_id")]


def gains(path: str, target: str) -> list[float]:
    return [float(r["sign_aligned"]["rescue_gain"]) for r in rows(path, target)]


def ratios(path: str, target: str) -> list[float]:
    return [float(r["sign_aligned"]["rescue_ratio"]) for r in rows(path, target)]


def save(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIG / name, dpi=180)
    plt.close()


def cache_component(target: str, filename: str) -> None:
    labels = ["K", "V", "K+V"]
    values = [np.median(ratios(path, target)) for path in ("phase_a_cache/k_only_results.jsonl", "phase_a_cache/v_only_results.jsonl", "phase_a_cache/kv_results.jsonl")]
    plt.figure(figsize=(5.2, 3.6)); plt.bar(labels, values, color=["#5b8ff9", "#61d9a7", "#65789b"])
    plt.axhline(0.5, color="black", linestyle="--", linewidth=1); plt.ylabel("Median unclipped rescue ratio"); plt.title(f"{target}: prior-cache components")
    save(filename)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    cache_component("target_a", "01_target_a_cache_components.png")
    cache_component("target_b", "02_target_b_cache_components.png")
    plt.figure(figsize=(7, 4)); data=[]; labels=[]
    for target in TARGETS:
        for label, path in (("K", "phase_a_cache/k_only_results.jsonl"), ("V", "phase_a_cache/v_only_results.jsonl"), ("KV", "phase_a_cache/kv_results.jsonl")):
            data.append(ratios(path, target)); labels.append(f"{target[-1].upper()}-{label}")
    plt.boxplot(data, tick_labels=labels, showfliers=True); plt.axhline(0, color="black", linewidth=.8); plt.ylabel("Unclipped RR"); plt.title("Per-base cache rescue distributions")
    save("03_per_base_cache_rescue.png")
    plt.figure(figsize=(7, 4)); plotted=[]; labels=[]
    for target in TARGETS:
        target_rows=rows("phase_a_cache/kv_results.jsonl", target)
        for state in ("aligned_native", "aligned_suppressed", "aligned_rescued"):
            plotted.append([np.mean([r["conditions"][c][state] for c in ("O","C")]) for r in target_rows]); labels.append(f"{target[-1].upper()}-{state.split('_')[1]}")
    plt.boxplot(plotted, tick_labels=labels, showfliers=True); plt.ylabel("Sign-aligned evidence score"); plt.title("Native, suppressed, and full-cache-rescued evidence")
    save("04_evidence_scores.png")
    for index, target in enumerate(TARGETS, start=5):
        paths=("phase_b_joint/residual_only_results.jsonl","phase_b_joint/downstream_cache_only_results.jsonl","phase_b_joint/joint_results.jsonl")
        vals=[np.median(ratios(p,target)) for p in paths]
        plt.figure(figsize=(5.5,3.6)); plt.bar(["Residual","Downstream cache","Joint"],vals,color=["#f6bd16","#5ad8a6","#5d7092"]); plt.axhline(.5,color="black",linestyle="--",linewidth=1); plt.ylabel("Median unclipped RR"); plt.title(f"{target}: residual/cache joint rescue")
        save(f"{index:02d}_{target}_joint_rescue.png")
    plt.figure(figsize=(6,3.8)); plt.boxplot([ratios("phase_b_joint/joint_results.jsonl",t) for t in TARGETS],tick_labels=["Target A","Target B"],showfliers=True); plt.axhline(.5,color="black",linestyle="--"); plt.axhline(.8,color="gray",linestyle=":"); plt.ylabel("Unclipped joint RR"); plt.title("Joint rescue ratio distribution")
    save("07_joint_rr_distribution.png")
    resid={t:np.asarray(gains("phase_b_joint/residual_only_results.jsonl",t)) for t in TARGETS}; down={t:np.asarray(gains("phase_b_joint/downstream_cache_only_results.jsonl",t)) for t in TARGETS}; joint={t:np.asarray(gains("phase_b_joint/joint_results.jsonl",t)) for t in TARGETS}
    plt.figure(figsize=(6,3.8)); plt.boxplot([joint[t]-resid[t] for t in TARGETS],tick_labels=["Target A","Target B"],showfliers=True); plt.axhline(0,color="black",linewidth=.8); plt.ylabel("Joint gain - residual gain"); plt.title("Increment over residual-only")
    save("08_joint_over_residual.png")
    plt.figure(figsize=(6,3.8)); plt.boxplot([joint[t]-down[t] for t in TARGETS],tick_labels=["Target A","Target B"],showfliers=True); plt.axhline(0,color="black",linewidth=.8); plt.ylabel("Joint gain - downstream cache gain"); plt.title("Increment over cache-only")
    save("09_joint_over_cache.png")
    plt.figure(figsize=(6.5,3.8)); values=[]; labels=[]
    for target in TARGETS:
        values += [ratios("phase_a_cache/kv_results.jsonl",target),ratios("phase_b_joint/downstream_cache_only_results.jsonl",target)]; labels += [f"{target[-1].upper()} full",f"{target[-1].upper()} downstream"]
    plt.boxplot(values,tick_labels=labels,showfliers=True); plt.ylabel("Unclipped RR"); plt.title("Full versus downstream prior cache")
    save("10_full_vs_downstream_cache.png")
    classification=read_json(OUT/"analysis/two_query_classification.json")
    plt.figure(figsize=(7,3.8)); x=np.arange(2); width=.24
    for offset,(label,key,color) in enumerate((("Residual","residual_median_RR","#f6bd16"),("Cache","downstream_cache_median_RR","#5ad8a6"),("Joint","joint_median_RR","#5d7092"))):
        plt.bar(x+(offset-1)*width,[classification["targets"][t][key] for t in TARGETS],width,label=label,color=color)
    plt.xticks(x,["Target A","Target B"]); plt.ylabel("Median RR"); plt.title("Target-specific handoff mechanism"); plt.legend()
    save("11_target_mechanism_comparison.png")
    delta=read_json(OUT/"audit/primary_native_suppressed_cache_deltas.json")["rows"]
    kv=read_jsonl(OUT/"phase_a_cache/kv_results.jsonl")
    plt.figure(figsize=(6,4))
    for target,color in (("target_a","#5b8ff9"),("target_b","#f6903d")):
        by={}
        for r in delta:
            if r["target"]==target: by.setdefault(r["base_problem_id"],[]).append(r["key_delta_l2"]+r["value_delta_l2"])
        yy={r["base_problem_id"]:r["sign_aligned"]["rescue_gain"] for r in kv if r["target_id"]==target}
        bases=sorted(set(by)&set(yy)); plt.scatter([np.mean(by[b]) for b in bases],[yy[b] for b in bases],label=target,alpha=.75,color=color)
    plt.xlabel("Mean P4 t_pre cache delta L2 (K+V)"); plt.ylabel("Full-cache rescue gain"); plt.title("Cache delta magnitude vs rescue"); plt.legend()
    save("12_cache_delta_vs_rescue.png")
    s35=read_json(OUT/"secondary/stage3c5_r_last1_comparison.json")
    plt.figure(figsize=(6,3.8)); plt.bar(["Stage3C.5\nR_last1","Stage3C.7\nA cache","Stage3C.7\nB cache"],[s35["stage3c5_pooled_median_CRR_R_last1"],s35["stage3c7_within_condition_full_cache_median_RR"]["target_a"],s35["stage3c7_within_condition_full_cache_median_RR"]["target_b"]],color=["#b7b7b7","#5b8ff9","#f6903d"]); plt.ylabel("Median descriptive rescue ratio"); plt.title("Cross-image versus within-condition cache rescue")
    save("13_stage3c5_vs_stage3c7_cache.png")
    plt.figure(figsize=(5.5,4.2))
    for target,color in (("target_a","#5b8ff9"),("target_b","#f6903d")):
        plt.scatter(resid[target],joint[target],label=target,alpha=.75,color=color)
    limits=plt.xlim(); lo=min(limits[0],plt.ylim()[0]); hi=max(limits[1],plt.ylim()[1]); plt.plot([lo,hi],[lo,hi],"k--",linewidth=1); plt.xlabel("Residual-only gain"); plt.ylabel("Joint gain"); plt.title("Stage 3C.6 residual vs Stage 3C.7 joint"); plt.legend()
    save("14_residual_vs_joint.png")
    print(json.dumps({"figure_count":len(list(FIG.glob('*.png'))),"directory":str(FIG)},indent=2))


if __name__ == "__main__":
    main()
