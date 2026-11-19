"""Compile the completed Stage8A evidence; no fitting or GPU execution."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path("outputs/stage8a")


def read(relative):
    return json.loads((ROOT / relative).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    release = read("audit/allocation_released_verified_v2.json")
    proof = read("audit/gpu_work_complete_v1.json")
    assert release["allocation_released"] and proof["required_gpu_work_complete"]
    gate0 = read("audit/gate0_pass_v1.json")
    retrieval = read("analysis/confirmation_v1/retrieval_confirmation.json")
    transport = read("analysis/transport_v1/transport_analysis.json")
    value = read("analysis/value_v1/value_summary.json")
    freeze = read("analysis/discovery_freeze_v1/freeze.json")
    reviews = read("audit/all_annotations_complete_v1.json")
    native = read("audit/native_main_completion_verified_v1.json")
    gates = dict(gate0=gate0["status"] == "PASS", gate1=retrieval["gate1"]["pass"],
                 gate2=transport["gate2"]["pass"], gate3=value["gate3"]["pass"])
    assert gates == dict(gate0=True, gate1=True, gate2=False, gate3=True)
    sources = ["audit/allocation_released_verified_v2.json", "audit/gpu_work_complete_v1.json",
               "audit/gate0_pass_v1.json", "analysis/confirmation_v1/retrieval_confirmation.json",
               "analysis/transport_v1/transport_analysis.json", "analysis/value_v1/value_summary.json",
               "analysis/discovery_freeze_v1/freeze.json", "audit/all_annotations_complete_v1.json",
               "audit/native_main_completion_verified_v1.json"]
    # Revalidate the raw evidence actually used by each completed analysis.
    checked = {}
    for report, key in ((retrieval, "raw_sha256"), (transport, "raw_sha256"),
                        (proof, "value_artifact_sha256"), (reviews, "active_annotation_sha256")):
        for path, expected in report[key].items():
            assert sha(path) == expected, path
            checked[path] = expected
    assert sha("plan/stage8a_plan.md") == sha(ROOT / "audit/approved_stage8a_plan_snapshot.md")
    manifest = [json.loads(line) for line in (ROOT / "cohort/main_manifest_v1.jsonl").read_text().splitlines()]
    assert len(manifest) == 96 and len({row["family_id"] for row in manifest}) == 96
    costs, cost_paths, peaks = {}, {}, {}
    for name, pattern, nested in (
        ("calibration_native", "native/calibration_v2/worker*/examples/*/generation.json", True),
        ("main_native", "native/main_v1/worker*/examples/*/generation.json", True),
        ("localization_profile", "localization/profile_v1/worker*/events/*.json", False),
        ("localization_joint", "localization/joint_v1/worker*/events/*.json", False),
        ("discovery_measurements", "measurement/discovery_v1/worker*/bases/*.json", False),
        ("confirmation_measurements", "measurement/confirmation_v1/worker*/bases/*.json", False),
        ("value_assays", "value/main_v1/worker*/events/*.json", False),
        ("mechanics_v2", "mechanics/v2/worker*/completed.json", False),
        ("measurement_smoke_v1", "measurement/smoke_v1/worker*/bases/*.json", False),
        ("measurement_smoke_v2", "measurement/smoke_v2/worker*/bases/*.json", False),
    ):
        paths = sorted(ROOT.glob(pattern))
        assert paths, pattern
        data = [json.loads(p.read_text()) for p in paths]
        rows = [d["runtime"] if nested else d for d in data]
        costs[name] = sum(d["elapsed_seconds" if nested else "runtime_seconds"] for d in rows) / 3600
        peaks[name] = max(d.get("peak_gpu_allocated_bytes", 0) for d in rows)
        cost_paths[name] = {str(p): sha(p) for p in paths}
    reserved = 2 * (datetime.fromisoformat(release["cancelled_kst"]) - datetime.fromisoformat("2026-09-16T10:42:44+09:00")).total_seconds() / 3600
    resource = dict(at=datetime.now(timezone.utc).isoformat(), measured_worker_gpu_hours=costs,
                    measured_total_worker_gpu_hours=sum(costs.values()), peak_gpu_allocated_bytes=peaks,
                    node02_reserved_gpu_hours=reserved, active_gpu_allocations=0,
                    annotation_bases=96, reviewed_prefix_tokens=reviews["total_reviewed_prefix_tokens"],
                    whole_trajectory_reviews=reviews["whole_trajectory_reviews"], active_annotation_labor_hours=None,
                    limitations="Measured worker intervals exclude loading/launcher overhead. Reserved hours include idle/CPU annotation time and overhead; do not add them to worker hours. Earlier node03 blocked reservation is excluded from node02 accounting. No reliable active annotation labor timer was recorded.",
                    input_sha256=cost_paths, remaining_gpu_hours=0, remaining_experiments=0)
    out = ROOT / "summaries"
    final = out / "stage8a_summary.json"
    assert not final.exists()
    recommendation = "Stop the Value-reinjection branch under the current Stage8A calibration and preserve this mechanistic boundary."
    summary = dict(at=resource["at"], status="COMPLETE_STOP", scientific_controller_success=False,
                   gates=gates, native_bases=96, reviews=96, discovery_events=113, confirmation_events=114,
                   value_assays=36, retrieval_primary=retrieval["models"]["joint"],
                   highR_lowG=transport["combined_highR_lowG"], value_semantics=value["gate3"],
                   recommendation=recommendation, recommendation_count=1, reinjection_started=False,
                   new_experiment_started=False, allocation_released=True,
                   evidence_sha256={str(ROOT / p): sha(ROOT / p) for p in sources},
                   raw_records_reverified=len(checked), original_plan_sha256=sha("plan/stage8a_plan.md"),
                   compiler_sha256=sha(__file__))
    final.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    (out / "stage8a_resource_final.json").write_text(json.dumps(resource, indent=2, allow_nan=False) + "\n")
    table = []
    for kind, model in retrieval["models"].items():
        m = model["metrics"]
        table.append(f"| {kind} | {m['auroc']:.3f} | {m['t_vs_m_auroc']:.3f} | {m['auprc']:.3f} | {m['recall']:.3f} | {m['mention_fpr']:.3f} |")
    cheap_table = []
    for kind, row in transport["cheap"]["confirmation"].items():
        m, c = row["metrics"], row["correlations"]
        cheap_table.append(f"| {kind} | {m['auroc']:.3f} | {m['auprc']:.3f} | {m['recall']:.3f} | {m['fpr']:.3f} | {c['JS']:.3f} / {c['CE']:.3f} / {c['composite_G']:.3f} |")
    cost_table = [f"| {name} | {hours:.4f} |" for name, hours in costs.items()]
    report = f"""# Stage8A complete — retrieval observable, selective reinjection not justified

Completed {resource['at']}. Qwen3-VL-2B-Thinking / MathVerse. Execution is complete; the overall scientific controller criterion is **not met**. The retrieval proxy passes held-out confirmation and eligible weak-transport states retain Value semantics, but the frozen cohort misses Gate2 and cheap transport gating does not generalize.

The two node02 GPUs in tmux10 were cancelled at **2026-09-16 22:00:42 KST**, immediately after final GPU validation. Slurm subsequently confirmed CANCELLED and no queued/running allocation. The original tmux10:0 shell remains. [Verified release](../audit/allocation_released_verified_v2.json). No new allocation, reinjection, controller or next experiment is running.

## Gate decision

| Gate | Result | Evidence |
|---|---|---|
| 0: technical validity | PASS | Exact cached BF16/native, capture, cache, self and fixed-routing checks; 2B functional layers19–22/all16heads |
| 1: retrieval proxy | PASS | Held-out AUROC0.9776; mention FPR0.1277; positive paired advantages over lexical/position |
| 2: weak-transport cohort | FAIL | 19 events /18 families; requires24 events /12 families;9 held-out events persist |
| 3: usable Value semantics | PASS, conditional | 16/16 evaluable events positive /15 families; family median8.3125nats,95%CI[7.1314,10.2163] |

Gate3 covers16/19 frozen states (84.2%). Three locally wrong claims lack an appropriately oriented semantic contrast and are excluded, not scored zero. Gate3 does not override Gate2. Four of the16 evaluable states are semantic mention-only negatives, rather than true retrieval-required events.

## Cohort, annotation and technical validity

Twelve separate calibration traces produced11 normalEOS and one cap; ten source/readout-eligible events localized the model's own functional late window. Joint calibration Value-semantic effects were positive10/10, median10.199nats. Calibration is not held-out replication. Target-relative suppression was positive9/10 but tiny (median2.02e-5nats).

The main cohort has48 discovery and48 disjoint confirmation families,96 fresh native traces,71 normalEOS and25 length-cap completions,1,507,425 generated tokens. All96 bases received source/prefix review:93,749 tokens examined, only4 complete trajectories. The remaining review coverage ends after explicitly recorded prefixes. Missing events are unavailable within that coverage, not certified absent from the full trajectory. One primary-agent annotator; no independent agreement estimate or active labor timer. Final-answer accuracy was not evaluated by this local-state study.

| Split | T | Mention-only | Nearby | Nonvisual | Total |
|---|---:|---:|---:|---:|---:|
| Discovery |41|48|12|12|113|
| Confirmation |44|47|11|12|114|

Labels and source/readout eligibility were sealed independently of main features/effects. Some M controls reuse text-given or previously unbound numerical information and precede the selected T; they are not all later matched mentions. Nearby controls must follow T within256 tokens. Local source/type errors remain wrong semantic candidates; candidate-label ROIs are not certified demanded-source ROIs. All main native/self/off readouts reproduce exactly across measurement and Value runs. [GPU completion proof](../audit/gpu_work_complete_v1.json), [annotation coverage](../audit/all_annotations_complete_v1.json).

Inference used BF16, temperature0.6/top-p0.95/top-k20/seed1234, max40960, EOS stopping, text eager/visionSDPA. Raw logits are converted to FP32 for log-probabilities and higher precision for distribution/statistical calculations; this is not FP32 model inference. Fresh native cached query-by-query prefixes were retained. No model or dataset download was needed. The original plan and historical runs/manifests are preserved.

## Retrieval proxy: held-out results

Discovery chose joint QK/attention, max aggregation, C0.01, tauR=0.5478025981 (strict greater-than). The nominal window4 variant contains no temporal features in this chosen joint model. Grouped five-fold normalization/model selection used discovery only. Its selected OOF AUROC0.9211 is a selection statistic. Features, models and R/G thresholds were frozen at12:45:40UTC before confirmation measurement/evaluation; no S effect informed selection. [Frozen rule](../analysis/discovery_freeze_v1/freeze.json).

| Model | AUROC all | AUROC T/M | AUPRC all | T recall | M FPR |
|---|---:|---:|---:|---:|---:|
{chr(10).join(table)}

Primary AUROC95%CI[0.9536,0.9931], T/M AUROC95%CI[0.9314,0.9898]. At the frozen threshold, recall38/44=86.4% and M false positives6/47=12.8%; their95%CIs are[75.6%,95.6%] and[4.2%,23.4%]. Gate1 uses the preregistered point thresholds; the upper M-FPR interval exceeds20%. Recall at empirical confirmation FPR10%/20% is90.9%/97.7%; these curve summaries do not replace the frozen operating point.

Paired family-bootstrap AUROC advantages: lexical+0.3271 [0.2480,0.4053], position+0.2656 [0.1806,0.3369]. All intervals use4000 family resamples/seed1234. Primary ECE(5 equal-width bins)=0.2971 and Brier=0.1557: ranking is strong, probability calibration is poor. Attention/QK perform similarly; their algebraic relation means they are not independent mechanistic replications. The extended alternative's held-out score does not authorize replacing the selected model.

The prespecified source-eligible T causal subset is24 events/24 families,12 per split; semantic Value exceeds sham24/24, family median8.1647nats [6.6250,11.3750]. This supports label validity in the eligible subset, not every annotated T. The primary R uses no ROI, Value magnitude or future-token feature. Continuous whole-trajectory false alarms, online implementation latency and deployment robustness remain untested. [Full metrics](../analysis/confirmation_v1/retrieval_confirmation.json), [ROC/PR figure](../analysis/confirmation_v1/retrieval_confirmation.png).

## Native transport and the frozen state

Discovery G is broad, continuous/skewed, without a certified mixture. Weakness requires **JS<6.149830919e-6 AND |mean full-span CE effect|<1.169726089e-5**, the lower quartiles among43 discovery OOF high-R events. This is relative weakness of the tested layers/readout, not absence of grounding. The absolute CE guard excludes both strong positive and negative influence; a common leading token alone cannot certify full-span weakness.

| Split | High R | High R / low G | Families | Fraction of high R | T / M | S eligible |
|---|---:|---:|---:|---:|---:|---:|
| Discovery |43|10|9|23.3%|8 /2|8|
| Confirmation |44|9|9|20.5%|7 /2|8|
| Combined |87|19|18|21.8%|15 /4|16|

T-only states number15 from15 families. The JS-only secondary screen yields11 discovery +14 confirmation events, but its25 cannot replace the frozen dual criterion to rescue Gate2. Families/events remain nested in [transport analysis](../analysis/transport_v1/transport_analysis.json). Target-relative suppression among eligible weak states has median4.47e-7nats, positive10/16; these very small BF16-path effects should not be inflated into strong native source dependence.

Cheap transport models were fitted only on discovery high-R events. Held-out results use44 high-R events,9 weak; lower-than-chance AUROCs are reported in their frozen learned orientation, without post hoc flipping.

| Cheap metric | Weakness AUROC | AUPRC | Recall | FPR | Spearman JS / signed CE / composite G |
|---|---:|---:|---:|---:|---:|
{chr(10).join(cheap_table)}

The discovery-selected cancellation candidate does not generalize (AUROC0.425, recall22.2%, FPR37.1%). It remains exploratory. None supplies a validated cheap online weakness gate. No new causal threshold, model, sign flip or cohort expansion was selected after these results.

## Value semantics and interpretation

Thirty-six unique assays cover the union of24 prespecified T controls and16 eligible weak states, with4 overlapping events. They patch semantic versus matched sham Values at fixed native routing/history in layers19–22. All self/no-op checks pass. Full-visual semantic-minus-sham is primary; ROI-only is secondary, because contextualized visual Values need not remain spatially local.

Within the16 weak states, all effects are positive; family median8.3125nats [7.1314,10.2163]. Discovery8 events/7 families: median9.6875 [7.4686,11.6875]; confirmation8/8:7.2238 [1.5000,14.2500]. T-only12/12 positive, median9.2812 [7.4218,12.9687]. ROI-only effects also positive16/16 (event median7.3933nats; secondary). Missing main265/main218/main743 are locally wrong claims requiring separate error-oriented controls; their semantics remain unresolved. The observed positives are locally correct eligible claims, not certified unfaithful failures or demonstrated correction opportunities. [Value summary](../analysis/value_v1/value_summary.json), [semantic/sham figure](../analysis/value_v1/value_semantics.png).

- **H1:** supported for selected MathVerse prefixes by held-out passive discrimination and eligible T causal validation.
- **H2:** a pure mention-only explanation is disfavored here, but annotation/source selection and absence of whole-trajectory evaluation limit generality.
- **H3:** uniform tight coupling is not established;9 held-out relative-weak states exist. Conversely, a relative quantile-defined state does not prove a natural bimodal failure regime.
- **H4:** supported at the eligible case level by retained Value semantics, but the required cohort size and deployable cheap gate are not achieved.

Counterfactual sensitivity does not establish that amplification of native Values improves accuracy, that extraction is intact for wrong claims, or that these events are MIRAGE/PRIOR_FILL. No intervention benefit was tested.

## Resources, preserved failures and reproducibility

| Recorded worker interval | GPU-hours |
|---|---:|
{chr(10).join(cost_table)}

Recorded worker intervals total **{sum(costs.values()):.4f} GPU-hours**; node02 allocation reservation was **{reserved:.4f} GPU-hours**, including CPU review/idle/loading overhead. These are alternative accounting scopes, not additive. Prior blocked node03 reservation is excluded. Main native inference alone took{costs['main_native']:.4f} workerGPU-hours. Active annotation labor was not timed. [Resource ledger](stage8a_resource_final.json).

Preserved failures: node03 pre-Python socket timeouts (cause unresolved); deliberate original-native no-overwrite exit during the approved tail handoff (not OOM), with all96 canonical results reconciled; prelaunch snapshot SameFileError repaired by making the snapshot path project-relative (no scientific work ran); release observer timed out at30 seconds while Slurm was COMPLETING, followed by confirmed CANCELLED/queue absence. The v1 release observation remains historical, superseded by verifiedv2. No scientific artifact was discarded to hide these failures.

Thirty-nine distinct CPU checks passed cumulatively, plus actual-model controls on both GPUs. Completed raw measurement, Value and active annotation hashes were reverified by this compiler. Primary analysis source/config snapshots remain unchanged. Final reporting is CPU-only. Figures and source code retain PNG/PDF/SVG and JSON evidence. [Machine-readable final result](stage8a_summary.json).

## Exactly one recommendation

**{recommendation}** Gate2 fails and no cheap transport rule generalizes, despite positive retrieval and conditional semantic evidence. Preserve those positives and limitations together. STOP for user review; do not launch reinjection or another experiment.
"""
    (out / "stage8a_summary.md").write_text(report)
    # A presentation-only redraw clips the impossible negative half of nonnegative G.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    for ax, split in zip(axes, ("discovery", "confirmation")):
        for label in ("T", "M", "nearby", "nonvisual"):
            rows = [e for e in transport["events"] if e["split"] == split and e["label"] == label]
            g = [max(e["JS"]/freeze["transport"]["tau_js"], abs(e["CE"])/freeze["transport"]["tau_abs_ce"]) for e in rows]
            ax.scatter([e["R"] for e in rows], g, label=label, alpha=.75)
        ax.axvline(freeze["retrieval"]["tau_R"], color="black", ls="--", lw=1)
        ax.axhline(1, color="black", ls="--", lw=1)
        ax.set_yscale("symlog", linthresh=.001)
        ax.set_ylim(bottom=0)
        ax.set(xlabel="Discovery OOF R" if split == "discovery" else "Frozen held-out R",
               ylabel="max(JS / threshold, |CE| / threshold)", title=f"{split}: weak transport below 1")
        ax.legend(fontsize=8)
    for suffix in ("png", "pdf", "svg"):
        fig.savefig(out / f"routing_transport_final.{suffix}", dpi=180)
    plt.close(fig)
    print(json.dumps(dict(gates=gates, resources=costs, reserved_gpu_hours=reserved,
                          raw_records_reverified=len(checked), report=str(out / "stage8a_summary.md")), indent=2))


if __name__ == "__main__":
    main()
