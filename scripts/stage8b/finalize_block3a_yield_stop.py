"""CPU-only reporting of the frozen Block3A finite-cohort yield stop.

Consumes sealed judgments; never assigns labels, captures routing, or launches jobs.
Run from the project root with PYTHONPATH=code:.:infra.
"""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import subprocess

import pandas as pd

from visual_reasoning.stage8b.block1_data import digest
from visual_reasoning.stage8b.block3a_review import align_read

ROOT = Path("outputs/stage8b_block3a/v1")
AUDIT = ROOT / "audit"
PREFIX = "stage8b_block3a_"
RECOMMENDATION = "stop routing branch"


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    """Regenerate only this reporter's derived outputs, never input evidence."""
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def verify(seal, gate):
    """Recompute alignment and pairing independently of the sealing helper."""
    records = seal["records"]
    assert seal["annotation_complete"] and not seal["source_measurements_opened"]
    assert len(records) == 128 and len({r["task_id"] for r in records}) == 128
    assert len({r["item_id"] for r in records}) == 32
    assert len({r["analysis_family_id"] for r in records}) == 31
    assert not gate["pass_gate"] and gate["finite_cohort_complete"]
    assert gate["minimum_pairs"] == 20 and gate["minimum_families"] == 16
    for path, expected in seal["review_sha256"].items():
        assert digest(path) == expected, path
    expected_pairs = []
    for item in sorted({r["item_id"] for r in records}):
        group = [r for r in records if r["item_id"] == item]
        assert sorted(r["seed"] for r in group) == [1235, 1236, 1237, 1238]
        assert len({r["subgoal"] for r in group}) == 1
        assert all(r["sources"] == group[0]["sources"] for r in group)
        plus = sorted((r for r in group if r["eligible"] and r["local"] == "L+"), key=lambda r: r["seed"])
        minus = sorted((r for r in group if r["eligible"] and r["local"] == "L-"), key=lambda r: r["seed"])
        expected_pairs.extend((p["event_id"], m["event_id"]) for p, m in zip(plus, minus))
    assert expected_pairs == [(p["success"], p["failure"]) for p in seal["pairs"]]
    assert gate["pairs"] == len(expected_pairs)
    assert gate["items"] == len({p["item_id"] for p in seal["pairs"]})
    assert gate["families"] == len({p["analysis_family_id"] for p in seal["pairs"]})
    used = [event for pair in expected_pairs for event in pair]
    assert len(used) == len(set(used))
    for r in records:
        packet_path = ROOT / "annotations/packets" / f"{r['task_id']}.json"
        assert digest(packet_path) == r["packet_sha256"]
        p = read(packet_path)
        assert digest(p["token_file"]) == p["token_sha256"]
        assert digest(Path(p["native_dir"]) / "result.json") == p["receipt_sha256"]
        assert r["sources"] == p["anchor"]["sources"]
        assert r["source_image_reviewed"] and not r["source_routing_opened"]
        if r["local"] is None:
            assert not r["eligible"] and r["exclusion_reason"]
            continue
        pieces = [json.loads(line)["decoded_token"] for line in Path(p["token_file"]).read_text().splitlines()][:p["reasoning_tokens"]]
        aligned = align_read(pieces, r, p["episodes"])
        for key, value in aligned.items():
            assert r[key] == value, (r["task_id"], key)
        # A separate direct check of the episode association boundary.
        candidates = [e for e in p["episodes"] if e["start_token"] - 16 <= r["claim_start_token"] <= e["end_token"] + 128]
        assert bool(candidates) == r["retrieval_eligible"]
        assert r["eligible"] == (r["local"] in ("L+", "L-") and bool(candidates))
    upstream = Path("outputs/stage8b_block2/v1/stage8b_block2_freeze.json")
    assert digest(upstream) == "b12c4588fadd08bb13253b7e4bc96aaf3437a84563ed0f783d86073691f2893e"
    freeze = read(upstream)
    dependencies = {**freeze["artifacts_sha256"], **freeze["supporting_sha256"]}
    for path, expected in dependencies.items():
        assert digest(path) == expected, path
    source_checks = 0
    for filename in ("native_replay_manifest.json", "native_config.json", "resume_four_v1/config.json"):
        for path, expected in read(AUDIT / filename)["source_sha256"].items():
            assert digest(path) == expected, path
            source_checks += 1
    # The manifest is checked against both native configurations, not a copied literal.
    for filename in ("native_config.json", "resume_four_v1/config.json"):
        config = read(AUDIT / filename)
        assert digest(config["manifest"]) == config["manifest_sha256"]
    return dict(review_hashes=128, packet_and_token_alignment_checks=128,
                upstream_frozen_artifacts=len(dependencies), frozen_code_checks=source_checks,
                independent_pairing_matches=True, source_geometry_unchanged=True,
                new_source_measurements_opened=False)


def figures(taxonomy, gate):
    os.environ["MPLCONFIGDIR"] = str((AUDIT / "matplotlib_cache").resolve())
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = ROOT / "figures"
    directory.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    paths = []

    def write(fig, stem):
        for suffix in ("png", "pdf"):
            path = directory / f"{stem}.{suffix}"
            fig.savefig(path, dpi=160, bbox_inches="tight")
            paths.append(path)
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    for ax, metric in zip(axes, ("QK target minus confuser", "Attention-share target minus confuser")):
        ax.set_axis_off()
        ax.set_title(metric, fontweight="bold")
        ax.text(.5, .59, "NOT MEASURED", ha="center", transform=ax.transAxes, color="#9a4e20", fontsize=15)
        ax.text(.5, .34, "Prerequisite pair-yield gate failed\nNo paired effect or confidence interval", ha="center", transform=ax.transAxes)
    fig.suptitle("Block3A same-item routing replication", fontsize=15)
    fig.text(.5, .01, f"{gate['pairs']} pairs / {gate['families']} independent families; required 20 / 16. All 128 trajectories reviewed.", ha="center")
    fig.tight_layout(rect=(0, .06, 1, .94))
    write(fig, "figure1_same_item_routing")

    fig, ax = plt.subplots(figsize=(9, 4.6))
    names = ["R1", "R2", "R3", "R4", "SELECTIVE_LPLUS"]
    bottom = [0] * len(names)
    for label, color in (("L+", "#4477aa"), ("L-", "#cc6677"), ("L?", "#aaaaaa")):
        values = [taxonomy["counts_by_local"][label].get(name, 0) for name in names]
        ax.bar(names, values, bottom=bottom, label=label, color=color)
        for x, value, y in zip(range(len(names)), values, bottom):
            if value:
                ax.text(x, y + value / 2, str(value), ha="center", va="center", color="white", fontweight="bold")
        bottom = [a + b for a, b in zip(bottom, values)]
    ax.set_xticks(range(5), ["R1\nT top, low margin", "R2\nConfuser top", "R3\nT top, high, L−", "R4\nUnresolved", "Selective L+\nT top, high"])
    ax.set_ylabel("Original Block2 events")
    ax.set_title("Frozen native taxonomy: 117 original events", fontweight="bold")
    ax.legend(title="Local read")
    fig.text(.5, .01, "100 routing captures (21 reused + 79 supplemental); R4 also retains unavailable measurements.\nThese are pre-outcome discovery records, not routing measurements of the 128 new rollouts.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .09, 1, 1))
    write(fig, "figure2_routing_subtypes")

    for number, title, detail, stem in (
        (3, "Causal weakening dose response", "No doses or causal heads activated\nNo evidence-preference effects measured", "weakening"),
        (4, "Causal rescue dose response", "No sharpening or oracle target boost executed\nNo rescue effects measured", "rescue"),
        (5, "Selectivity controls", "No low-margin, high-margin, confuser-top, or timing assays\nNo subtype intervention contrasts measured", "selectivity_controls"),
    ):
        fig, ax = plt.subplots(figsize=(8.5, 3.5))
        ax.set_axis_off()
        ax.set_title(title, fontsize=15, fontweight="bold")
        ax.text(.5, .67, "NOT RUN — PAIR-YIELD GATE FAILED", ha="center", color="#9a4e20", transform=ax.transAxes, fontsize=14)
        ax.text(.5, .37, detail, ha="center", transform=ax.transAxes)
        ax.text(.5, .1, "Absence of an assay is not a zero effect or an intervention null.", ha="center", transform=ax.transAxes, fontsize=10)
        write(fig, f"figure{number}_{stem}")
    return paths


def main():
    stamp = datetime.now(timezone.utc).isoformat()
    seal = read(ROOT / "annotations/semantic_seal.json")
    gate = read(AUDIT / "yield_gate.json")
    native = read(AUDIT / "resume_four_v1/completion_audit.json")
    taxonomy_path = ROOT / f"{PREFIX}routing_subtypes.json"
    taxonomy_sha = digest(taxonomy_path)
    taxonomy = read(taxonomy_path)
    checks = verify(seal, gate)
    records = seal["records"]
    lookup = {r["event_id"]: r for r in records}
    pairs = []
    for index, pair in enumerate(seal["pairs"]):
        row = dict(pair, pair_id=f"block3a_pair_{index:02d}", source_routing_status="not_measured_yield_gate_failed")
        for side in ("success", "failure"):
            r = lookup[pair[side]]
            for key in ("task_id", "seed", "native_dir", "episode_index", "episode_start", "episode_end", "claim_start_token", "claim_end_token", "quote", "readout", "packet_sha256"):
                row[f"{side}_{key}"] = r[key]
        row["sources_json"] = json.dumps(lookup[pair["success"]]["sources"], sort_keys=True)
        pairs.append(row)
    frame = pd.DataFrame(pairs)
    for metric in ("qk_T_X", "share_T_X"):
        for side in ("success", "failure", "difference"):
            frame[f"{side}_{metric}"] = pd.array([None] * len(frame), dtype="Float64")
    frame.to_parquet(ROOT / f"{PREFIX}same_item_pairs.parquet", index=False)

    item_rows = []
    for item in sorted({r["item_id"] for r in records}, key=int):
        group = [r for r in records if r["item_id"] == item]
        counts = Counter(str(r["local"]) for r in group)
        eligible = Counter(r["local"] for r in group if r["eligible"])
        item_rows.append(dict(item_id=item, analysis_family_id=group[0]["analysis_family_id"], category=group[0]["category"],
                              subgoal=group[0]["subgoal"], reviewed=len(group), local_counts=dict(counts), eligible_counts=dict(eligible),
                              primary_pairs=sum(p["item_id"] == item for p in pairs)))
    save(AUDIT / "review_yield_by_item.json", item_rows)
    assert sum(row["primary_pairs"] for row in item_rows) == gate["pairs"]
    failure_records = [r for r in records if r["eligible"] and r["local"] == "L-"]
    no_match = Counter(r["exclusion_reason"] for r in records if r["local"] is None)
    outside = Counter(r["local"] for r in records if r["local"] in ("L+", "L-") and not r["retrieval_eligible"])
    semantic_mixed_items = [r["item_id"] for r in item_rows if r["local_counts"].get("L+", 0) and r["local_counts"].get("L-", 0)]
    semantic_pairs = sum(min(r["local_counts"].get("L+", 0), r["local_counts"].get("L-", 0)) for r in item_rows)
    counts = dict(reviewed=128, items=32, independent_families=31, local=seal["counts"], eligible=seal["eligible_counts"],
                  eligible_failure_items=len({r["item_id"] for r in failure_records}),
                  eligible_failure_families=len({r["analysis_family_id"] for r in failure_records}),
                  unresolved_exact_read=seal["counts"].get("L?", 0), unmatched_reasons=dict(no_match), resolved_outside_episode=dict(outside),
                  semantic_mixed_items=semantic_mixed_items, semantic_only_pairs=semantic_pairs,
                  semantic_only_note="Attrition accounting only; does not relax retrieval eligibility or define a new analysis cohort.")
    save(AUDIT / "review_yield_summary.json", counts)
    common = dict(at=stamp, status="not_run_insufficient_pair_yield", reason="Frozen minimum is 20 pairs / 16 independent families; observed 4 / 3.",
                  yield_gate=gate, semantic_seal_sha256=digest(ROOT / "annotations/semantic_seal.json"),
                  results=[], effects=None, confidence_intervals=None, p_values=None, causal_claim_supported=False)
    save(ROOT / f"{PREFIX}routing_replication.json", dict(common, scientific_result="not_evaluated", replication_gate_pass=None,
         measured_pairs=0, primary_metrics={name: dict(estimate=None, bootstrap_ci95=None, sign_test_p=None, wilcoxon_p=None,
         standardized_effect=None, holm_p=None) for name in ("qk_T_X", "share_T_X")}, review_yield=counts))
    for name, criterion in (("weakening_results", "C1"), ("rescue_results", "C2"), ("selectivity_controls", "C3")):
        save(ROOT / f"{PREFIX}{name}.json", dict(common, criterion=criterion, criterion_pass=None, events_run=0, doses_tested=[]))
    save(ROOT / f"{PREFIX}intervention_manifest.json", dict(at=stamp, status="not_activated_yield_gate_failed",
         prerequisite_yield_gate=gate, replication_gate_pass=None, interventions_run=0, doses=None, verified_causal_heads=None,
         plan_candidate_layers=[19, 20, 21, 22], candidate_window_is_not_causal_verification=True,
         readout_contrasts=None, recommendation=RECOMMENDATION, recommendation_count=1, next_experiment_started=False,
         no_op_or_control_assays_run=False, source_routing_opened_for_new_rollouts=False,
         protocol_sha256=digest("plan/stage8b_block3a_execution_protocol_v1.md")))
    gpu_hours = .405 + 3038 * 2 / 3600 + native["four_gpu_hours_approx"]
    resources = dict(at=stamp, supplemental_replay=dict(job="118093", gpus=2, seconds=729, gpu_hours=.405),
         cancelled_native=dict(job="118099", gpus=2, seconds=3038, gpu_hours=3038 * 2 / 3600, includes_technical_checks_and_partial_attempts=True),
         resumed_native=dict(job="118116", gpus=4, seconds_approx=native["four_gpu_wall_seconds_approx"], gpu_hours_approx=native["four_gpu_hours_approx"]),
         total_gpu_hours_approx=gpu_hours, future_gpu_hours=0, future_native_trajectories=0, future_annotation_reviews=0,
         annotation=dict(review_count=128, annotators=1, independent_agreement_measured=False, human_annotation_hours=None,
                         method="Single main-agent image review plus native prefix and targeted subgoal-context review; per-record prior_context_check documents coverage."),
         accounting_limit=native["slurm_terminal_accounting_note"])
    gpu_status = subprocess.run(["squeue", "-u", "hyunjin", "-h", "-o", "%i %T %N %b"], check=True, capture_output=True, text=True).stdout
    (AUDIT / "final_squeue.txt").write_text(gpu_status)
    assert not any(job in gpu_status for job in ("118093", "118099", "118116"))
    resources["stage_allocations_released"] = True
    resources["all_user_squeue_empty_at_check"] = not gpu_status.strip()
    save(AUDIT / "resource_accounting_final.json", resources)
    figure_paths = figures(taxonomy, gate)
    assert digest(taxonomy_path) == taxonomy_sha
    paired_table = "\n".join(f"| {p['item_id']} | {p['category']} | {p['success_seed']} | {p['failure_seed']} |" for p in pairs)
    subtype_table = "\n".join(f"| {subtype} | {taxonomy['counts_by_local']['L+'].get(subtype, 0)} | {taxonomy['counts_by_local']['L-'].get(subtype, 0)} | {taxonomy['counts_by_local']['L?'].get(subtype, 0)} |" for subtype in ("R1", "R2", "R3", "R4", "SELECTIVE_LPLUS"))
    summary = f"""# Stage8B Block3A — complete at the finite-cohort yield stop

Completed {stamp}. The approved execution is complete; its scientific confirmation criterion is **not met**.

All **128/128** frozen trajectories were generated and semantically reviewed. The sealed same-item cohort contains **4 disjoint L+/L− pairs from 3 items / 3 independent visual families**, below the frozen minimum **20 pairs / 16 families**. The yield gate fails. New-rollout source-routing replication, weakening, rescue and selectivity assays were **not run**. No routing effect was estimated, and no causal-intervention null was observed.

## Scope and verified execution

The question was whether reduced target-vs-confuser routing reproducibly separates successful and failed reads of the same exact visual subgoal, and, conditional on confirmation, causally controls read quality. The hypothesis remains untested causally in this stage.

The frozen sample contains 32 MathVision items / 31 independent visual families and four new seeds (1235–1238). Items1707/1245 share a rescaled drawing; their original IDs, labels and source geometry remain unchanged. Original seed1234 remains discovery evidence and was not inserted into primary pairs. Selection included all11 original source-localizable failure families plus21 low-margin controls before new outcomes. This enriched sample does not estimate population failure prevalence.

Canonical Qwen3-VL-2B-Thinking BF16, temperature1.0, top-p0.95, top-k20, repetition1.0, presence0, frozen preprocessing and 40960-token cap were preserved. Native results comprise14 preserved completions plus114 resumed completions, **1,511,000 generated tokens**,126 normal EOS and2 capped trajectories (`756_s1236`, `510_s1238`). Both caps and four interrupted old attempts remain preserved. All128 receipts,640 native artifact hashes and token/passive-array alignments passed the completion audit. Original and resumed worker layout checks passed exact parity. Terminal accounting for118116 expired; saved batch completion, worker receipts and artifact integrity establish completion.

## Sealed semantic and retrieval yield

| First exact-subgoal judgment | All trajectories | Eligible active-retrieval reads |
|---|---:|---:|
| L+ | 79 | 62 |
| L− | 28 | 20 |
| L? | 1 | 0 |
| No matched committed/source-resolved claim | 20 | 0 |
| Total | 128 | 82 |

The20 eligible L− reads span9 items /9 families. There are25 resolved claims outside the frozen episode-association window (17 L+,8 L−),1 unresolved exact read, and20 unmatched claims. Unmatched reasons:8 no-committed-exact-subgoal,6 ambiguous source positions,3 same-subgoal-not-committed,3 same-subgoal-not-identified. Categories preserve their original review codes in the seal.

Reviews use the first committed claim addressing the frozen subgoal, not final-answer correctness or a later error. Hypothetical geometry, unanswered questions, unbound values and different visual properties cannot create a pair. Readout spans are aligned to native tokens and associated using the unchanged gap4 detector window [episode start−16, episode end+128]. A single main agent reviewed images, prefixes and targeted subgoal contexts; per-record coverage and rationale are recorded. These are single-annotator judgments with no inter-rater agreement estimate. Ambiguous commitment/source boundaries remain a limitation. New source-routing values remained unopened throughout review and after the yield stop.

| Item | Frozen category | L+ seed | L− seed |
|---|---|---:|---:|
{paired_table}

One pair includes the early valid local read in capped trajectory756_s1236; no final answer is required for this local subgoal. As attrition accounting only, ignoring retrieval eligibility would yield5 disjoint pairs across4 items (the additional item is1128), still far below the minimum. That accounting does not relax the primary gate. No original-new pairing, new seed, changed anchor, or ROI retuning was used to increase yield.

The immediate confirmed bottleneck is **insufficient within-item outcome variation under exact semantic and active-retrieval matching**, rather than the complete absence of failures. Many source-resolved items remain locally correct or locally wrong across seeds. The deeper reason for the low switching yield is unknown. This result does not distinguish routing from extraction/content errors, falsify the Block2 association, or establish that natural benchmarks never yield such pairs.

## Preserved pre-outcome native routing taxonomy

All117 original Block2 source-localizable records are retained verbatim. Routing inventory uses21 existing plus79 exact supplemental captures;17 records lack a usable capture (13 L+,4 L?). Those17 records and2 measured but unresolved routing cases constitute R4. The operational low-margin boundary remains QK T−X≤1.0 nat for target-top cases, with the frozen native observational window (layers19–22/all16 heads). This does not verify every head as causal.

| Native subtype | L+ | L− | L? |
|---|---:|---:|---:|
{subtype_table}

R1 and R2 among L+ are control strata, not unfaithfulness diagnoses. R3 is an extraction/content candidate, not a causal diagnosis. These subtype counts describe the original inventory and are not new-rollout routing measurements. Block2 activation confidence intervals including zero do not establish equivalence.

## Gate disposition and resources

Yield: **FAIL**. Routing replication: **not evaluated**. C1 weakening, C2 rescue, C3 selectivity: **not run**. Required JSON artifacts use null effect estimates and explicit status, rather than fabricated zeros. The five figures include the actual original subtype map plus explicit unperformed panels for unavailable paired/causal analyses.

Approximate allocated compute:0.405 GPU-hours for supplemental replay;1.688 for the cancelled two-GPU native allocation (including technical checks and partial attempts);13.468 for the four-GPU continuation. **Total≈{gpu_hours:.3f} GPU-hours**. Single-agent annotation burden:128 trajectory reviews with32 source images; human labor hours were not measured. CPU reporting/review required no allocation. All stage GPUs are released, and remaining authorized GPU work is zero. No download or environment installation was needed.

## Exactly one recommendation

**Stop routing branch under the current frozen cohort.** Preserve Block2's descriptive routing evidence and this negative feasibility result. This stage does not support promoting routing to a causal mechanism or anchoring an intervention story on it. No next experiment, larger sample, model change, intervention controller, or Block3B was launched.

## Evidence and deliverables

- [Semantic seal](annotations/semantic_seal.json), [yield gate](audit/yield_gate.json), [item-level yield](audit/review_yield_by_item.json).
- [Same-item pairs]({PREFIX}same_item_pairs.parquet), [routing replication status]({PREFIX}routing_replication.json).
- [Original native taxonomy]({PREFIX}routing_subtypes.json), [intervention manifest]({PREFIX}intervention_manifest.json).
- [Weakening]({PREFIX}weakening_results.json), [rescue]({PREFIX}rescue_results.json), [selectivity]({PREFIX}selectivity_controls.json).
- Figures: [paired routing](figures/figure1_same_item_routing.png), [subtypes](figures/figure2_routing_subtypes.png), [weakening](figures/figure3_weakening.png), [rescue](figures/figure4_rescue.png), [controls](figures/figure5_selectivity_controls.png); PDF exports accompany each.
- [Native integrity audit](audit/resume_four_v1/completion_audit.json), [final resource accounting](audit/resource_accounting_final.json), [acceptance](audit/final_acceptance.json), [freeze]({PREFIX}freeze.json).

Historical manifests and original protocol/resource estimates remain unchanged. Earlier state entries describing1/128 review or running jobs are superseded by this final checkpoint. STOP.
"""
    (ROOT / f"{PREFIX}summary.md").write_text(summary)
    outputs = [ROOT / f"{PREFIX}{suffix}" for suffix in ("routing_subtypes.json", "same_item_pairs.parquet", "routing_replication.json", "weakening_results.json", "rescue_results.json", "selectivity_controls.json", "intervention_manifest.json", "summary.md")]
    assert all(path.is_file() and path.stat().st_size for path in outputs + figure_paths)
    assert len(pd.read_parquet(outputs[1])) == gate["pairs"]
    assert pd.read_parquet(outputs[1]).filter(regex="_(qk_T_X|share_T_X)$").isna().all().all()
    acceptance = dict(at=stamp, pass_validation=True, execution_complete=True, scientific_confirmation=False,
                      conditional_stop="insufficient_pair_yield", eight_required_outputs=len(outputs) == 8,
                      five_figures=len(figure_paths) == 10, figure_formats=["png", "pdf"], validation=checks,
                      original_taxonomy_unchanged=True, native_integrity_audit_sha256=digest(AUDIT / "resume_four_v1/completion_audit.json"),
                      review_counts=seal["counts"], eligible_counts=seal["eligible_counts"], yield_gate=gate,
                      recommendation=RECOMMENDATION, recommendation_count=1, stage_allocations_released=True,
                      limitations=["Single-annotator semantic labels; no independent agreement estimate.", "Insufficient mixed-outcome yield; routing and causal effects not evaluated.", "118116 terminal accounting expired; artifact and batch completion verified."])
    save(AUDIT / "final_acceptance.json", acceptance)
    support = [ROOT / "annotations/semantic_seal.json", AUDIT / "yield_gate.json", AUDIT / "semantic_pairs.parquet", AUDIT / "review_yield_by_item.json", AUDIT / "review_yield_summary.json", AUDIT / "resource_accounting_final.json", AUDIT / "final_squeue.txt", AUDIT / "final_acceptance.json", Path(__file__)]
    support.extend(Path(path) for path in seal["review_sha256"])
    support.extend(sorted((ROOT / "annotations/review_batches").glob("*.json")))
    save(ROOT / f"{PREFIX}freeze.json", dict(at=stamp, execution_complete=True, scientific_success=False,
         stop_reason="insufficient_pair_yield", artifacts_sha256={str(p): digest(p) for p in outputs + figure_paths},
         supporting_sha256={str(p): digest(p) for p in support}, recommendation=RECOMMENDATION))
    print(json.dumps(dict(execution_complete=True, scientific_success=False, counts=counts,
                         yield_gate=gate, gpu_hours_approx=gpu_hours, outputs=len(outputs), figures=5), indent=2))


if __name__ == "__main__":
    main()
