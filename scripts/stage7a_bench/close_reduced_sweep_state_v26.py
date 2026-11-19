"""Close compact state after successful reduced-sweep artifact acceptance."""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

root = Path.cwd()
base = root / "outputs/stage7a_bench_v2"
stamp = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
acceptance = json.loads((base / "summaries/stage7a_bench_v2_acceptance.json").read_text())
assert acceptance["status"] == "COMPLETE_STOP_WITH_DOCUMENTED_LIMITS"
assert len(acceptance["criteria"]) == 23
assert acceptance["recommendation_executed"] is False

paths = [
    "workspace/phase_memory/phase_7a_bench_v2_mirage_track.md",
    "workspace/workflow_state.md", "workspace/research_plan.md",
    "workspace/decision_log.md", "workspace/env_state.md",
    "plan/stage7a_bench_v2_execution_checklist.md", "reports/index.md",
    "outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_summary.md",
    "outputs/stage7a_bench_v2/summaries/reduced_figure_acceptance_map_v6.md",
]
history = base / "audit/pre_final_state_v26"
history.mkdir(exist_ok=False)
old = {}
for relative in paths:
    source = root / relative
    content = source.read_text()
    target = history / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    old[relative] = content
(history / "manifest.json").write_text(json.dumps({
    "recorded_at": stamp,
    "files": {p: hashlib.sha256(s.encode()).hexdigest() for p, s in old.items()},
    "purpose": "Exact immediately preceding state retained; original plans, freezes and historical execution artifacts remain unchanged.",
}, indent=2) + "\n")

phase_path = paths[0]
phase = old[phase_path]


def section(text, title, body):
    pattern = re.compile(r"(## " + re.escape(title) + r"\n).*?(?=\n## |\Z)", re.S)
    assert len(pattern.findall(text)) == 1, title
    return pattern.sub(lambda match: match.group(1) + "\n" + body.strip() + "\n", text)


phase = section(phase, "Current Objective", """
COMPLETE — the user-authorized reduced Stage7A-Bench v2 sweep is finished. Native review, all four fixed causal pilots, the five-benchmark/three-axis comparison, 25 figure requirements (26 plots/78 exports), technical acceptance and exactly one recommendation are complete. STOP; no next research action is active. The controlled-construction recommendation is a proposal only and has not been executed.

Final report: `outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_summary.md`. Acceptance: `outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_acceptance.json`. Immediately preceding state is archived under `outputs/stage7a_bench_v2/audit/pre_final_state_v26/`.
""")
phase = section(phase, "Current State", """
- Phantom: 400 reviewed conditions/200 bases preserved; behavioral no-valid-source reference, causal states N/A. CharXiv: 200 native reviews and 64 pilot events preserved, with 1 strong wrong-source, 6 strong faithful, 25 weaker faithful and 32 unresolved.
- MathWild: unchanged 96-review semantic gate A passed with 19 localizable candidates/12 bases; original 264 conditions fully reviewed. Fixed 48-event pilot: 3 strong faithful, 3 weaker faithful, 42 unresolved, no strong unfaithful state. No effects-based expansion.
- MMMU: 328 full reviews (200 image/64 silent/64 explicit), paired behavior retained. Fixed 33-event pilot: 1 strong faithful, 24 weaker faithful, 8 unresolved. Image-absent correctness and unsupported visual claims remain behavioral evidence, not PRIOR_FILL certificates.
- MMLong: all 200 native rows accounted, 190 full reviews, 10 exclusions (5 OOM/2 missing PDF/3 context), 7 caps. Final correctness 89/169 plus 21 unknown; local errors 103/189 plus 1 unknown; 73 binding candidates; 70 F0 candidates. Frozen 42-event pilot (36 bases/29 families; 15 failure/27 control candidates) completed on both authorized GPUs, including both approximately 199k-token events. Result: 2 strong WRONG_SOURCE_READ, 7 strong FAITHFUL_READ, 14 weaker faithful, 19 unresolved. Two strong failures span two bases/families; one is a table-field error, one a chart-binding error within a PDF.
- Total: 1,382 reviewed/1,392 frozen native conditions; 187 pilot events; 17 strong faithful, 66 weaker faithful, 3 strong wrong-source and 101 unresolved. Eighteen anomaly flags are nested within unresolved events. Zero other assigned states do not establish their absence: all selected targets are intact, absent-image PRIOR_FILL certificates were not tested, downstream-integration eligibility is sparse, and alternative semantic-control coverage is limited.
- Final accounted GPU cost 156.03 hours, or 160.77 including separately recorded MMLong native wrapper/startup/OOM overhead. Full overhead and human annotation labor remain unavailable. Remaining experiment compute: zero. Allocation 114451/node02/tmux10 remains retained with two idle A6000 GPUs; no new workload was launched after completion.
""")
phase = section(phase, "Open Candidates", """
No research action is active. Exactly one proposal awaits the user's choice: Controlled Confusable-Source Construction anchored to the verified MMLong table-field case. No natural primary benchmark is frozen for expansion. Sparse control preparation may be a major yield bottleneck; intrinsic natural-benchmark failure scarcity is not established. Deferred benchmarks, model-scale studies, monitor training and interventions remain unstarted.
""")
phase = section(phase, "Next-Step Decision", """
STOP and return the completed reduced sweep for user review. The proposed controlled construction is not authorized for execution by this stage. Do not automatically run a new benchmark, expand a cohort, change model scale, train a monitor or begin rollback/decoding. Preserve all positive, negative and unresolved evidence and retain the existing allocation until instructed otherwise.
""")
evidence = """
- Completed MMLong wrapper `causal_pilot/wrappers/mmlong_causal_v15_20260915.json`: successful two-worker aggregation at 2026-09-15 15:27KST; all 42 fixed events and exact device mechanics passed. `audit/mmlong_certified_case_validity_review_v25.json` binds the two source-verified wrong-source cases and signed semantic-versus-sham effects.
- Canonical completed comparison `analysis/benchmark_comparison.json`, nested accounting `analysis/reduced_sweep_complete_accounting_v20.json`, control coverage `analysis/reduced_semantic_control_coverage_v24.json`, decision `analysis/selected_benchmark.json`, figure coverage `analysis/reduced_final_figure_coverage_v26.json`, and `summaries/stage7a_bench_v2_acceptance.json` establish completion. Historical raw comparison/render status strings remain unchanged and are superseded by the explicit final review index/receipts.
- Exact memory-repair parity is against immutable native `document_runtime_v2`, not dense full-prompt tensors. Earlier dense/document nonparity and v12–v14 failed preflights remain preserved. Both longest cases completed; the first used about 43.79GiB GPU memory and 58.64GiB host RSS. Early CPU cache-path binding omission remains explicitly unverified for outside-root effects (`audit/cpu_reporting_cache_binding_v20.json`).

"""
phase = phase.replace("## Evidence That Matters\n\n", "## Evidence That Matters\n\n" + evidence)
phase = phase.replace("## Step Results\n\n", "## Step Results\n\n- " + stamp + ": all authorized work COMPLETE; 23 technical criteria accepted under the explicit scope amendment/O6, 25 figure requirements verified, exactly one unexecuted proposal recorded. No follow-up experiment launched. Earlier progress/ETA entries below are historical.\n\n")
(root / phase_path).write_text(phase)

dashboard = """**CURRENT — COMPLETE / STOP ({stamp}).** The reduced Stage7A-Bench v2 sweep is finished. Phantom/CharXiv preserved; gated MathWild, MMMU and MMLong reviews/pilots complete. Across 187 pilot events: 17 strong faithful, 66 weaker faithful, 3 strong wrong-source and 101 unresolved. MMLong contributes 2 strong wrong-source, 7 strong faithful, 14 weaker faithful and 19 unresolved across 42 events. All 25 figure requirements and 23 technical acceptance criteria are covered with explicit limitations.

Exactly one recommendation: **Controlled Confusable-Source Construction**, anchored to the MMLong table-field case; proposal only, not started. No natural primary benchmark is frozen. Sparse semantic-control coverage limits the negative interpretation. MathSight/MicroVQA/MedXpertQA-MM remain deferred; no new benchmark/model/cohort/monitor/intervention is active. Remaining authorized GPU work: zero. Two GPUs remain allocated in node02/tmux10 (Slurm114451); science has finished.

[Final report](../outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_summary.md) · [Acceptance](../outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_acceptance.json) · [Recommendation](../outputs/stage7a_bench_v2/summaries/next_stage_recommendation.md).

The dated execution entries below are preserved history and do not authorize pending work.

""".format(stamp=stamp)
for relative in ["workspace/workflow_state.md", "workspace/research_plan.md"]:
    first, rest = old[relative].split("\n", 1)
    (root / relative).write_text(first + "\n\n" + dashboard + rest.lstrip("\n"))

checklist = """# Stage7A-Bench v2 reduced execution checklist

Updated {stamp}: **COMPLETE / STOP**. Original broad plan and user scope amendment remain preserved. The immediately previous checklist is archived in `outputs/stage7a_bench_v2/audit/pre_final_state_v26/plan/`.

- [x] Phantom: 400 conditions preserved; no rerun or causal relabeling.
- [x] CharXiv: 200 native reviews/64 pilot events preserved; 1 strong wrong-source, 6 strong faithful, 25 weaker faithful, 32 unresolved.
- [x] MathWild: fixed 96-review semantic gate A passed with 19 localizable candidates/12 bases; original 264 conditions reviewed; fixed 48-event causal pilot complete.
- [x] MMMU: 328 native conditions reviewed with image/silent/guess separation; fixed 33-event causal pilot and qualified paired behavioral accounting complete.
- [x] MMLong native: 200 rows accounted, 190 full reviews, 10 exclusions, 7 caps; source/readout/control review complete.
- [x] MMLong scientific selection: 42 events/36 bases/29 families sealed before effects; 11 token-overlap exclusions preserved.
- [x] Authorized node02 replacement: two A6000/16 CPUs/100G, Slurm114451/tmux10; no additional resource request.
- [x] Exact cache-residency repair validated against immutable native backend on both GPUs; dense/document tensor nonparity retained as a qualification.
- [x] Full 42-event MMLong pilot completed, including both approximately 199k-token cases; successful canonical aggregation at 2026-09-15 15:27KST.
- [x] MMLong result: 2 strong wrong-source, 7 strong faithful, 14 weaker faithful, 19 unresolved; both strong wrong-source cases source/effect-reviewed.
- [x] Five-benchmark/three-axis comparison, nested accounting, eligibility/control coverage, measured costs and interpretation limits complete.
- [x] All 25 figure requirements covered by 26 plots/78 PNG/PDF/SVG exports; visual review and export hashes verified.
- [x] All 23 technical criteria accepted with documented limits under the user amendment and plan O6.
- [x] Exactly one recommendation: Controlled Confusable-Source Construction; proposal only, no natural primary frozen, no follow-up executed. STOP.

Deferred: MathSight, MicroVQA, MedXpertQA-MM. No new benchmark, model-scale study, cohort, monitor, rollback or decoding intervention.

Resource completion: 156.03 accounted GPU-hours across the retained sweep, or 160.77 including separately measured MMLong native wrapper/startup/OOM overhead. MMLong causal runtime sums 27,549.97 one-GPU worker seconds (7.653 GPU-hours), not two-worker wall time; initial mechanics and native work are separately accounted. Full overhead/human annotation cost remains unavailable. Remaining authorized experiment compute is zero. Two GPUs remain allocated through the current Slurm limit (2026-09-18 08:35KST), subject to cluster policy; no maintenance workload or follow-up experiment launched.

Final evidence: `outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_acceptance.json`, `analysis/benchmark_comparison.json`, and `audit/resource_summary.json` under the same output root. Earlier preflight failures, original source snapshots, manifests and state histories remain preserved.
""".format(stamp=stamp)
(root / "plan/stage7a_bench_v2_execution_checklist.md").write_text(checklist)

decisions = """

## D-068 — Exact operational repair is relative to the actual native backend

- Date: {stamp}. Both authorized node02 devices passed exact KV/logit/RoPE and original source/candidate/no-op/repeat mechanics against immutable native document_runtime_v2. CPU cache offload/reload allowed all 42 sealed MMLong events, including both approximately 199k-token prefixes, to complete without changing scientific selection or thresholds.
- Preserve the earlier dense-versus-document full-tensor mismatch. Exact repair parity does not establish dense/document equivalence; verify the backend actually used for native evidence. Evidence: `outputs/stage7a_bench_v2/audit/mmlong_v15_actual_gpu_mechanics_verified.json`, `audit/mmlong_v15_prefix_reference_scope_correction.json`, `audit/mmlong_first199k_event_capacity_verified_v23.json` and completed wrapper under the same output root.

## D-069 — Reduced sweep complete; control coverage qualifies low captured failure yield

- Date: {stamp}. Fixed pilots contain 187 events: 17 strong faithful, 66 weaker faithful, 3 strong wrong-source across three families and 101 unresolved. CharXiv's one strong failure and MMLong's two are preserved positive evidence. MMLong has alternative semantic controls for only 3/15 selected failure events (two bases), and two certify; limited preparation may therefore constrain captured yield. Its two certified cases are a financial table-field error and a chart-binding error within a PDF, not two independent pure document-field mechanisms.
- Do not infer population prevalence or intrinsic natural-benchmark scarcity from these bounded pools, or equate zero assigned PRIOR_FILL/extraction/integration states with comprehensive negative tests. The natural-primary scalable gate is not demonstrated; illustrative scaling from one/two families is not a validated yield forecast.
- Exactly one recommendation: Controlled Confusable-Source Construction anchored to the verified MMLong table-field case. Proposal only; no new action or natural primary frozen. STOP for user review. Evidence: `outputs/stage7a_bench_v2/analysis/selected_benchmark.json`, `analysis/reduced_semantic_control_coverage_v24.json`, `audit/mmlong_certified_case_validity_review_v25.json`, and final acceptance under the same output root.
""".format(stamp=stamp)
(root / "workspace/decision_log.md").write_text(old["workspace/decision_log.md"] + decisions)
(root / "workspace/env_state.md").write_text(old["workspace/env_state.md"] + "\n\n## Stage7A-Bench v2 completion — " + stamp + "\n\nSlurm114451/node02/tmux10 pane%23 retains two A6000 GPUs, 16 CPUs and100G host memory, limit through2026-09-18 08:35KST. MMLong's 42-event causal pilot and all CPU reporting/acceptance work are complete; scientific GPU processes exited. Final read-only observation: both GPUs 0% utilization and2MiB used. No follow-up or new allocation request. Project `.venv` packages unchanged; BF16 fixed4B model retained. All later CPU commands explicitly bind project TMPDIR/MPLCONFIGDIR and offline HF settings. Earlier omitted CPU cache bindings and unverified external effects remain recorded in `outputs/stage7a_bench_v2/audit/cpu_reporting_cache_binding_v20.json`. Final resource record: `outputs/stage7a_bench_v2/audit/resource_summary.json`.\n")

summary_path = "outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_summary.md"
summary = old[summary_path].replace("**Status: reporting complete; final figure/acceptance verification pending.**", "**Status: COMPLETE / STOP — " + stamp + ".**")
assert "final figure/acceptance verification pending" not in summary
(root / summary_path).write_text(summary)

map_path = "outputs/stage7a_bench_v2/summaries/reduced_figure_acceptance_map_v6.md"
(root / map_path).write_text(old[map_path] + "\n\n## Final acceptance — " + stamp + "\n\nAll historical pending cells are now superseded by `analysis/reduced_final_figure_coverage_v26.json`: requirements1–25 covered, 26 plots (separate native/certified Figure9) and78 hashed PNG/PDF/SVG exports. Each batch links its preserved render manifest and later visual-review receipt. Complete causal figures9/13–20 use batch `reduced_sweep_complete_causal_v20`; Figure22 uses `reduced_decision_v25`. Other final mappings are recorded in the coverage index. Phantom's paired-behavior figure remains an additional preserved export. No certified PRIOR_FILL example exists; Figure24 is explicitly behavioral. All23 technical criteria are recorded in `stage7a_bench_v2_acceptance.json`, including criterion23 under the explicit scope amendment and O6: one unexecuted controlled-construction proposal, no invented natural winner.\n")

report = old["reports/index.md"]
first, rest = report.split("\n", 1)
(root / "reports/index.md").write_text(first + "\n\n**Stage7A-Bench v2 complete / STOP — " + stamp + ".** [Final reduced-sweep report](../outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_summary.md) · [Acceptance](../outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_acceptance.json) · [One recommendation, unexecuted](../outputs/stage7a_bench_v2/summaries/next_stage_recommendation.md).\n\n" + rest.lstrip("\n"))
print(json.dumps({"status": "COMPLETE_STOP", "updated_files": paths, "timestamp": stamp, "recommended_action_started": False}))
