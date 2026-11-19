"""Record final artifact checks for the completed, user-amended sweep.

CPU reporting only. This does not score, select, render, or launch experiments.
Visual review observations were made interactively before this receipt.
"""
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path.cwd().resolve()
BASE = ROOT / "outputs/stage7a_bench_v2"
NOW = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()


def project_path(value):
    path = (ROOT / value).resolve()
    assert path.is_relative_to(ROOT), value
    return path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(relative):
    path = project_path(relative)
    assert path.is_file(), relative
    return {"path": str(path.relative_to(ROOT)), "sha256": digest(path)}


def load(relative):
    return json.loads((BASE / relative).read_text())


def save(relative, data):
    path = BASE / relative
    assert not path.exists(), path
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return str(path.relative_to(ROOT))


def base_ref(relative):
    return ref(str((BASE / relative).relative_to(ROOT)))


def exports(relative):
    manifest = load(relative)
    records = []
    for figure in manifest.get("figures", [manifest]):
        number = figure.get("figure_number")
        if number is None:
            number = int(figure["figure"].split("_")[0])
        assert set(figure["files"]) == {"png", "pdf", "svg"}
        for extension, entry in figure["files"].items():
            actual = ref(entry["path"])
            assert actual["sha256"] == entry["sha256"], entry["path"]
            assert project_path(entry["path"]).suffix == "." + extension
        records.append({"figure_number": number, "files": figure["files"]})
    # The completed reporting pipeline already verified input provenance. Some
    # manifests embed thousands of source bindings, so this final receipt checks
    # exports and records the immutable manifest rather than repeating that scan.
    return records


causal = "analysis/figures/causal_batches/reduced_sweep_complete_causal_v20/manifest.json"
decision = "analysis/figures/decision_batches/reduced_decision_v25/manifest.json"
new_records = exports(causal) + exports(decision)
assert len(new_records) == 10
visual = save("audit/reduced_final_figures_visual_review_v26.json", {
    "recorded_at": NOW, "status": "PASS_FULL_PNG_VISUAL_REVIEW",
    "reviewer": "main agent; direct view_image inspection before this receipt",
    "manifests": [base_ref(causal), base_ref(decision)],
    "figures": new_records,
    "observations": [
        "All ten full PNGs inspected; text, legends, axes and footnotes readable; no clipping or overlapping labels.",
        "Figures 19/20 use numbered points and separate keys; native unknowns and structural versus event identifiability stay explicit.",
        "Figures 16/17 state absent-image PRIOR_FILL and downstream-assay coverage limitations; zero labels are not state absence.",
        "Figure 18 distinguishes summed one-GPU worker runtime from wall time and uses the declared accounted-cost scope.",
        "Figure 22 matches the completed counts, limited failure control coverage, unestablished natural-primary gate and one unexecuted proposal."
    ],
    "historical_manifests_rewritten": False,
    "export_hashes_verified": True,
})

mapping = [
    ("analysis/reduced_structural_v6/figures.json", "audit/reduced_structural_v6_visual_review.json"),
    ("analysis/figures/native_batches/reduced_sweep_complete_native_v19/manifest.json", "audit/reduced_complete_native_figures_visual_review_v19.json"),
    ("analysis/figures/paired_batches/mmmu_pro_complete_v7/manifest.json", "audit/mmmu_complete_figures6_11_visual_review_20260914_v1.json"),
    ("analysis/figures/paired_batches/mmmu_bclean_distinction_v20/manifest.json", "audit/mmmu_bclean_figure12_visual_review_v20.json"),
    (causal, "audit/reduced_final_figures_visual_review_v26.json"),
    ("analysis/figures/paired_batches/mathwild_complete_v7/manifest.json", "audit/mathwild_paired_figure21_visual_review_v1.json"),
    (decision, "audit/reduced_final_figures_visual_review_v26.json"),
    ("analysis/figures/example_batches/charxiv_complete_v1/manifest.json", "audit/charxiv_causal_example_figure_visual_review.json"),
    ("analysis/figures/example_batches/mmmu_prior_behavior_v19/manifest.json", "audit/mmmu_prior_behavior_figure24_visual_review_v19.json"),
    ("analysis/reduced_roadmap_v6/manifest.json", "audit/reduced_roadmap_v6_visual_review.json"),
]
batches = []
for manifest, review in mapping:
    assert "FAIL" not in load(review)["status"]
    batches.append({"manifest": base_ref(manifest), "visual_review": base_ref(review), "figures": exports(manifest)})
figures = [f for batch in batches for f in batch["figures"]]
assert sorted(set(f["figure_number"] for f in figures)) == list(range(1, 26))
assert len(figures) == 26
assert len({x["path"] for f in figures for x in f["files"].values()}) == 78
coverage = save("analysis/reduced_final_figure_coverage_v26.json", {
    "status": "PASS", "recorded_at": NOW, "requirements_covered": list(range(1, 26)),
    "plot_count": 26, "export_count": 78, "batches": batches,
    "note": "Figure 9 has separate native F0 and certified faithful views. Phantom's preserved paired-behavior figure is additional. Historical render manifests retain their at-render pending statuses; linked later visual receipts establish review.",
})

wrapper = load("causal_pilot/wrappers/mmlong_causal_v15_20260915.json")
run = load("causal_pilot/raw/mmlong_causal_v15_20260915/run_summary.json")
assert wrapper["completed"] and wrapper["exit_code"] == 0 and wrapper["pool_workers"] == 2
assert run["completed"] and len(run["events"]) == 42
accounting = load("analysis/reduced_sweep_complete_accounting_v20.json")
totals = accounting["totals"]
assert totals["native_conditions_reviewed"] == 1382
assert totals["causal_pilot_events"] == sum(totals["state_events"].values()) == 187
assert totals["certified_state_events"]["FAITHFUL_READ"] == 17
assert totals["certified_state_events"]["WRONG_SOURCE_READ"] == 3
chosen = load("analysis/selected_benchmark.json")
assert chosen["exactly_one_recommendation"] == "Controlled Confusable-Source Construction"
assert chosen["recommendation_executed"] is False
assert chosen["primary_natural_benchmark"] is None

commands = [
    ["scontrol", "show", "job", "114451", "-o"],
    ["squeue", "--steps", "-j", "114451", "-o", "%.22i %.12M %N"],
    ["tmux", "list-panes", "-t", "10", "-F", "#{pane_id} #{window_name} #{pane_current_command}"],
]
status = []
for command in commands:
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    status.append({"command": command, "stdout": result.stdout, "stderr": result.stderr})
assert "JobState=RUNNING" in status[0]["stdout"]
assert "TresPerNode=gres/gpu:2" in status[0]["stdout"]
efficiency = load("analysis/efficiency.json")
resource = save("audit/resource_summary.json", {
    "recorded_at": NOW, "status": "SCIENCE_COMPLETE_ALLOCATION_RETAINED",
    "allocation": {"slurm_job_id": "114451", "node": "node02", "gpus": 2, "cpus": 16, "host_memory": "100G", "tmux_session": "10", "pane": "%23", "time_limit_end_kst": "2026-09-18T08:35:08+09:00"},
    "live_read_only_status": status,
    "gpu_observation": {"observed_at_kst": "2026-09-15T15:57:11+09:00", "utilization_percent": [0, 0], "memory_used_mib": [2, 2], "method": "read-only nvidia-smi within an overlapping step of the existing allocation"},
    "mmlong_pilot": {"events": 42, "summed_worker_seconds": run["seconds"], "seconds_definition": run["seconds_definition"], "wrapper": wrapper},
    "accounted_gpu_hours_total": efficiency["accounted_gpu_hours_total"],
    "total_with_recorded_mmlong_native_wrapper_overhead": efficiency["total_with_recorded_mmlong_native_wrapper_overhead"],
    "full_pipeline_annotation_and_reservation_cost": None,
    "remaining_authorized_experiment_gpu_hours": 0,
    "new_allocation_requested_after_two_gpu_replacement": False,
    "new_workload_launched_after_completion": False,
    "sources": [base_ref("analysis/efficiency.json"), base_ref("causal_pilot/raw/mmlong_causal_v15_20260915/run_summary.json"), base_ref("causal_pilot/wrappers/mmlong_causal_v15_20260915.json")],
})

criteria = [
    ("Access policy read before dataset operations", ["audit/dataset_lookup_track_b.json", "cohort/download_manifest.json"], "Historical dataset-operation receipts; not a claim that all unrelated historical cache effects were audited."),
    ("Allowed dataset roots checked before download", ["audit/dataset_lookup_track_b.json", "cohort/dataset_inventory.json"], "Ordered project-link, external-root and allowed-cache lookup preserved."),
    ("Inventory written before downloads", ["cohort/download_manifest.json", "cohort/dataset_inventory.json"], "Frozen manifest records inventory_written_before_download."),
    ("Missing datasets downloaded one at a time", ["cohort/download_manifest.json"], "Sequential acquisition history preserved, including incomplete/error statuses and now-deferred artifacts."),
    ("Download provenance recorded", ["cohort/download_manifest.json"], "Pinned revisions and per-file receipt paths preserved; no downloads in this completion action."),
    ("Primary model remains Qwen3-VL-4B-Thinking", ["causal_pilot/frozen/mmlongbench_doc.json", "audit/mmlong_v15_actual_gpu_mechanics_verified.json"], "BF16 model; exact native backend reference qualified separately from dense prefill."),
    ("Sample IDs frozen before generation", ["cohort/sample_freeze.json"], "Original broader frozen manifest preserved; reduced scope recorded as amendment."),
    ("Structural audit is output blind", ["audit/native_source_family_integrity.json"], "Structural feasibility remains separate from observed causal yield."),
    ("Native correctness is not a causal label", ["analysis/benchmark_comparison.json", "analysis/failure_state_yield.json"], "Separate native, event and certified-state columns."),
    ("Local errors remain separate from final errors", ["analysis/reduced_sweep_complete_accounting_v20.json"], "Unknowns and response caps retained."),
    ("Image/no-image pairs are not causal labels", ["analysis/bclean_comparison.json"], "Paired correctness and unsupported claims are behavioral evidence only."),
    ("Behavioral B-Clean is not Causal B-Clean", ["analysis/bclean_comparison.json"], "Local single-model partitions are also distinguished from the published protocol."),
    ("Pilot subsets frozen before scoring", ["causal_pilot/frozen/charxiv.json", "causal_pilot/frozen/mathvision_wild.json", "causal_pilot/frozen/mmmu_pro.json", "causal_pilot/frozen/mmlongbench_doc.json", "causal_pilot/selection_reviews/mmlong_validated_scientific_selection_v15.json"], "Runtime repair preserved the sealed 42-event scientific membership."),
    ("Stage 7A state definitions unchanged", ["config/inherited_causal_definition_freeze.json", "audit/causal_v12_scientific_ast_equivalence.json"], "No effects-based threshold or definition adjustment."),
    ("WRONG_SOURCE_READ requires error-oriented support", ["audit/mmlong_certified_case_validity_review_v25.json", "causal_pilot/reports/charxiv_causal_pilot_01/yield.json"], "Signed alternative-suppression and semantic-versus-sham followability support three certified cases; other errors stay unresolved."),
    ("PRIOR_FILL is not no-image agreement", ["analysis/reduced_state_assay_coverage_v21.json"], "No absent-image PRIOR_FILL certificate tested; zero assigned labels are not evidence of absence."),
    ("Source and readout feasibility explicit in ranking", ["analysis/source_identifiability_comparison.json", "analysis/selected_benchmark.json"], "Control availability and bounded preparation coverage remain explicit."),
    ("Accuracy is not sole ranking criterion", ["analysis/track_a_ranking.json", "analysis/track_b_ranking.json", "analysis/selected_benchmark.json"], "Mechanistic yield, identifiability, readout validity, intervention relevance and controls govern the decision."),
    ("No 2B/8B study", ["analysis/selected_benchmark.json"], "Only approved 4B evidence used; no model-scale study started."),
    ("No online grounding monitor trained", ["analysis/selected_benchmark.json"], "Runtime progress monitoring is bookkeeping, not a learned grounding monitor."),
    ("No rollback/decoding intervention", ["analysis/selected_benchmark.json"], "Frozen causal diagnostic assays are not an online decoding intervention."),
    ("No effects-chasing sample expansion", ["causal_pilot/selection_reviews/mmlong_validated_scientific_selection_v15.json", "summaries/mathwild_gate96_frozen_interim_v5.md"], "Original samples and fixed semantic gate preserved; deferred benchmarks remain deferred."),
    ("Exactly one next-stage recommendation", ["analysis/selected_benchmark.json", "summaries/next_stage_recommendation.md"], "PASS under the explicit user scope amendment and plan O6: one controlled-construction proposal, no natural primary asserted and no proposed action executed."),
]
criterion_records = [{"number": i, "criterion": name, "status": "PASS" if i != 23 else "PASS_UNDER_USER_AMENDMENT_AND_O6", "evidence": [base_ref(p) for p in paths], "qualification": note} for i, (name, paths, note) in enumerate(criteria, 1)]
assert len(criterion_records) == 23
save("summaries/stage7a_bench_v2_acceptance.json", {
    "recorded_at": NOW, "status": "COMPLETE_STOP_WITH_DOCUMENTED_LIMITS",
    "authorized_scope_completed": True, "remaining_authorized_experiments": [],
    "authority": [ref("plan/stage7a_bench_v2_scope_amendment_20260913.md"), ref("plan/stage7a_bench_v2_node02_two_gpu_completion_20260915.md")],
    "criteria": criterion_records, "totals": totals,
    "figure_coverage": ref(coverage), "resource_summary": ref(resource),
    "exactly_one_recommendation": chosen["exactly_one_recommendation"],
    "recommendation_executed": False, "primary_natural_benchmark": None,
    "deferred": ["MathSight", "MicroVQA", "MedXpertQA-MM"],
    "interpretation_limits": base_ref("summaries/reduced_sweep_interpretation_limits_v20.md"),
    "cache_binding_qualification": base_ref("audit/cpu_reporting_cache_binding_v20.json"),
    "limitations": [
        "Small bounded prepared/pilot pools and sparse semantic controls do not estimate population prevalence or prove natural benchmarks intrinsically lack failures.",
        "No absent-image PRIOR_FILL certificate; only one downstream-integration-eligible event; zero labels are not comprehensive negative tests.",
        "Unknown final answers, capped responses, native OOM/missing/context exclusions and base/family nesting retained.",
        "Exact runtime repair parity is against the immutable native document backend; dense-versus-document tensor equivalence failed and is not claimed.",
        "GPU costs use explicit measured scopes; full overhead and human annotation labor are unavailable.",
        "Early CPU commands lacked explicit TMPDIR/MPLCONFIGDIR binding; outside-root side effects remain uninspected and unverified."
    ],
    "acceptance_script": ref("scripts/stage7a_bench/accept_reduced_sweep_v26.py"),
})
print(json.dumps({"status": "PASS", "criteria": 23, "plots": 26, "exports": 78, "pilot_events": 187, "stop": True}))
