"""Publish the predeclared development no-go branch without held-out inference."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from scripts.stage8c.prepare import save, sha
from visual_reasoning.stage8c.analysis_fp32 import summarize, transitions

ROOT = Path('outputs/stage8c_v3/v1')


def main():
    at = datetime.now(timezone.utc).isoformat()
    reviewed = ROOT/'stage8c_v3_dev_dose_results_reviewed_v1.json'
    result = json.loads(reviewed.read_text())
    freeze = json.loads((ROOT/'stage8c_v3_dose_freeze.json').read_text())
    assert freeze['status'] == 'stop_dev_no_go' and freeze['dose'] is None
    assert freeze['development_results_sha256'] == sha(reviewed)
    assert result['extraction_review_closed'] and not result['blind_extraction_pending']
    verification = json.loads((ROOT/'audit/dev_completion_verification_v1.json').read_text())
    assert verification['status'] == 'pass' and verification['trajectories'] == 512
    arms = result['rows']; summaries = result['summaries']; base = arms['1.0']
    manifest = json.loads((ROOT/'stage8c_v3_dev128_manifest.json').read_text())
    metadata = {r['item_id']: r for r in manifest['rows']}
    stop = dict(at=at, status='not_run_dev_no_go', reason='All non-native doses fail accuracy and rescue-balance development guards.',
                dose=None, observed_items=0, dose_freeze_sha256=sha(ROOT/'stage8c_v3_dose_freeze.json'))
    for name, count in [('test_primary_accuracy',512), ('family_clustered_inference',512), ('timing_control256',256)]:
        save(ROOT/f'stage8c_v3_{name}.json', dict(stop, planned_items=count))
    import pyarrow as pa
    import pyarrow.parquet as pq
    schema = pa.schema([(n, pa.string()) for n in ['item_id','family_id','condition','retrieval_episode','demand_label','local_read_label','claim_change']],
                       metadata={b'status': b'not_run_dev_no_go', b'planned_items': b'128', b'observed_items': b'0'})
    pq.write_table(pa.Table.from_pylist([], schema=schema), ROOT/'stage8c_v3_local_read_audit128.parquet')
    save(ROOT/'stage8c_v3_local_read_audit128_status.json', dict(stop, planned_items=128,
        annotation_rows=0, note='Empty typed table is a not-run marker, not negative local-read evidence.'))

    strata = {}
    for field in ['subject','level','answer_format','problem_type']:
        groups = {}
        for value in sorted({str(r[field]) for r in metadata.values()}):
            ids = [i for i, r in metadata.items() if str(r[field]) == value]
            b = {i: base[i] for i in ids}; bacc = summarize(b)['accuracy']
            effects = {}
            for gain in ['1.25','1.5','2.0']:
                a = {i: arms[gain][i] for i in ids}
                effects[gain] = dict(accuracy=summarize(a)['accuracy'], delta=summarize(a)['accuracy']-bacc,
                                     unresolved=summarize(a)['unresolved'], transitions=transitions(b,a))
            groups[value] = dict(n=len(ids), major=len(ids)>=15, baseline_accuracy=bacc, effects=effects)
        strata[field] = groups
    save(ROOT/'stage8c_v3_subtype_heterogeneity.json', dict(at=at, status='development_descriptive_only',
        heldout_status='not_run_dev_no_go', strata=strata, inferential_claim=False))

    changed = []
    for gain in ['1.25','1.5','2.0']:
        for item in base:
            a, b = base[item], arms[gain][item]
            if a['correct'] is None or b['correct'] is None or a['correct'] == b['correct']:
                continue
            changed.append(dict(item_id=item, family_id=a['family_id'], gain=float(gain),
                transition='WtoC' if b['correct'] else 'CtoW',
                baseline_extracted=a['extracted'], intervention_extracted=b['extracted'],
                reasoning_tokens_delta=b['reasoning_tokens']-a['reasoning_tokens'],
                retrieval_episodes_baseline=a['retrieval_episode_count'],
                retrieval_episodes_intervention=b['retrieval_episode_count'],
                interventions=b['actual_interventions'],
                baseline_generation=a['artifact_dir']+'/generation.json',
                intervention_generation=b['artifact_dir']+'/generation.json',
                causal_mechanism='unknown', local_visual_claim_review='not_performed_dev_stop'))
    save(ROOT/'stage8c_v3_rescue_collateral_review.json', dict(at=at,
        status='development_answer_transition_accounting_only', rows=changed,
        counts={g:summaries[g]['transitions'] for g in ['1.25','1.5','2.0']},
        heldout_semantic_review='not_run_dev_no_go',
        interpretation='Paired final-answer changes do not establish local correction, source confusion or downstream failure mechanisms.'))

    active = sum(s['elapsed_seconds'] for s in summaries.values())/3600
    allocation = 4*(42*3600+2*60+31)/3600
    cancelled = 2*(21*60+19)/3600
    reserved = max(r['runtime']['peak_gpu_reserved_bytes'] for a in arms.values() for r in a.values())
    runtime = dict(at=at, phase='development', summaries=summaries, active_inference_gpu_hours=active,
        approximate_completed_allocation_gpu_hours=allocation, cancelled_allocation_gpu_hours=cancelled,
        approximate_total_allocated_gpu_hours=allocation+cancelled,
        duration_basis='118545 EXIT snapshot RunTime 1-18:02:31 times four GPUs; 118529 cancellation snapshot 00:21:19 times two GPUs. EXIT snapshot precedes final Slurm release, so allocation total is approximate.',
        cancelled_completed_trajectories=0, cancelled_interrupted_attempts=2,
        peak_allocated_bytes=max(s['peak_gpu_allocated_bytes'] for s in summaries.values()),
        peak_reserved_bytes=reserved, precision='float32', tf32=False, autocast=False,
        remaining_gpu_hours=0, allocation_released=True,
        baseline_overhead_note='Baseline includes frozen-policy observation. No plain-native runtime comparator was collected; report measured throughput, not a pure intervention overhead estimate.')
    save(ROOT/'stage8c_v3_runtime_overhead_final_v1.json', runtime)
    save(ROOT/'audit/analysis_repair_v1.json', dict(at=at,
        original='code/visual_reasoning/stage8c/analysis_fp32.py',
        repaired='code/visual_reasoning/stage8c/analysis_fp32_reviewed.py',
        issue='Original helper blocks even declared-unresolvable answers and subtype arithmetic cannot accept None.',
        repair='Require explicit closed extraction review; preserve unresolved transitions; use correct-is-True accuracy credit including subtypes.',
        source_preserved=True, scorer_changed=False, scientific_gates_changed=False,
        tests='5 focused CPU tests passed: pending-review block, unresolved transition preservation, no fabricated rescue, parity/tie-breaking, existing FP32 rules.',
        analysis_sha256=sha('code/visual_reasoning/stage8c/analysis_fp32_reviewed.py')))
    plot(summaries, strata)
    # Preserve the automatic summary and figures; reviewed figures use a new directory.
    save(ROOT/'audit/automatic_summary_preserved_v1.json', dict(at=at,
        sha256=sha(ROOT/'stage8c_v3_summary.md'), text=(ROOT/'stage8c_v3_summary.md').read_text()))
    table = ['| Gain | Correct / 128 | Accuracy | Δ pp | W→C | C→W | Unresolved answers / pairs | EOS | Cap | Mean / median reasoning tokens | Episodes / interventions | GPU-h |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for g, s in summaries.items():
        tr = s['transitions']; delta = 100*(s['accuracy']-summaries['1.0']['accuracy'])
        table.append(f"| {g} | {s['correct']} | {100*s['accuracy']:.2f}% | {delta:+.2f} | {tr['WtoC'] if tr else '—'} | {tr['CtoW'] if tr else '—'} | {s['unresolved']} / {tr['unresolved'] if tr else '—'} | {100*s['eos_rate']:.2f}% | {100*s['cap_rate']:.2f}% | {s['mean_reasoning_tokens']:.1f} / {s['median_reasoning_tokens']:.1f} | {s['retrieval_episodes']} / {s['interventions']} | {s['active_gpu_hours']:.2f} |")
    summary = f'''# Stage8C v3 — completed at development no-go

Updated {at}. **Stop the intervention branch under plan §18.** All 512 trajectories
(128 frozen items and 128 visual families × four doses) completed in FP32. Every
non-native dose has lower accuracy than baseline and W→C ≤ C→W. No dose is selected.
Held-out512, timing256, semantic128 and the optional extension were not run.

{chr(10).join(table)}

Accuracy uses all 128 items; unresolved answers receive no correct credit but remain
unresolved in paired transitions. W→C−C→W therefore need not equal the change in
total correct answers. Reviewed data: [dose results](stage8c_v3_dev_dose_results_reviewed_v1.json).
The originally named `stage8c_v3_dev_dose_results.json` and original runtime file
remain immutable automatic-stage evidence; use the reviewed/final versions here.

The gain trajectory is descriptively negative. At 2×, algebra falls 12.5pp (n=16);
the two other major subjects change by −4pp (area, n=25) and +4.55pp (length, n=22).
These development subgroup results are descriptive. No held-out confirmation,
confidence interval, timing-specificity or local-read improvement is established.
The mechanism behind answer changes remains unknown. The fixed inherited detector
was not recalibrated or validated for FP32 transfer; no BF16 equivalence claim is made.

All 78 automatic extraction/equivalence exceptions were reviewed with gold/dose
masked, then sealed before gold comparison. 28 literal answers were retained:
15 correct, 10 wrong and 3 unsupported/non-unique under the unchanged equivalence
adapter. Another 50 remained unresolved at extraction. The resulting 53 unresolved
arm outcomes are reported explicitly. This was a single main-agent review with
previously visible aggregate scores, not independent blinding. Quotes, character
spans and reasons are preserved in [the extraction seal](annotations/dev_extraction_v1/manual_extraction_seal.json).
The local scorer does not reproduce an upstream external-judge fallback.

The reporting helper required a versioned repair to distinguish completed review
from unresolved answers; the original helper, generation code, scoring tolerance,
dose ordering and scientific guards remain unchanged. Five focused CPU tests pass.
All 512 completion receipts, 4,608 referenced output artifacts, 171 historical
hashes and frozen execution sources passed verification. Ordinary inference
receipts show FP32 attention/logits/cache/observed activations, TF32 off and no
autocast. No OOM or worker failure was found in the completed-run log.

Slurm118545 exited0 after about42h03m; four node02 GPUs are released. Active
inference consumed {active:.2f} GPU-h; approximate allocated compute was
{allocation:.2f} GPU-h plus {cancelled:.2f} GPU-h for the user-cancelled initial run.
Peak allocated/reserved memory was {runtime['peak_allocated_bytes']/2**30:.2f}/
{reserved/2**30:.2f} GiB. Throughput was 15.45–16.64 tokens/s per GPU.
Remaining authorized compute: **0 GPU-h**. [Final runtime](stage8c_v3_runtime_overhead_final_v1.json).

Reviewed figures: [dose response](figures/reviewed_v1/figure1_dev_dose_response.png),
[major-subject effects](figures/reviewed_v1/figure4_dev_subtype_heterogeneity.png),
[rescues and collateral damage](figures/reviewed_v1/figure6_dev_rescue_collateral.png).
Figures 2/3/5/7 are not applicable because their held-out stages were not run.
Not-run artifacts and an empty status-tagged semantic Parquet preserve that boundary.

**One recommendation:** close this visual-gain branch and return Block3B
post-read recovery/wandering dynamics for the user's next-action decision, as
specified by the plan. Block3B has not been launched or implemented by this action.
'''
    (ROOT/'stage8c_v3_summary.md').write_text(summary)
    save(ROOT/'stage8c_v3_completion.json', dict(at=at, status='completed_dev_no_go',
        scientific_plan_complete=True, decision='stop_dev_no_go', dose=None,
        complete_trajectories=512, reviewed_cases=78, remaining_gpu_hours=0,
        heldout_launched=False, next_experiment_launched=False, allocation_released=True,
        canonical_development_results=str(reviewed), canonical_runtime=str(ROOT/'stage8c_v3_runtime_overhead_final_v1.json'),
        recommendation='Close visual-gain branch; return Block3B for user selection, do not execute it automatically.'))
    print(json.dumps(dict(status='completed_dev_no_go', active_gpu_hours=active,
                         allocated_gpu_hours=allocation+cancelled, remaining_gpu_hours=0)))


def plot(summaries, strata):
    os.environ['MPLCONFIGDIR'] = str(ROOT/'audit/matplotlib_cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    dest = ROOT/'figures/reviewed_v1'; dest.mkdir(parents=True, exist_ok=False)
    gains = [1.,1.25,1.5,2.]; ss = [summaries[str(g)] for g in gains]
    fig, axes = plt.subplots(2,2,figsize=(9,6),constrained_layout=True)
    curves = [('Accuracy (%)',[100*s['accuracy'] for s in ss]),
              ('W→C − C→W',[0]+[s['transitions']['WtoC']-s['transitions']['CtoW'] for s in ss[1:]]),
              ('Cap rate (%)',[100*s['cap_rate'] for s in ss]),
              ('Median reasoning tokens',[s['median_reasoning_tokens'] for s in ss])]
    for ax, (label, vals) in zip(axes.flat, curves):
        ax.plot(gains,vals,'o-'); ax.set_xticks(gains); ax.set_xlabel('Visual gain'); ax.set_ylabel(label)
    fig.suptitle('Reviewed FP32 development: 128 items; stop at no-go')
    for ext in ['png','pdf']: fig.savefig(dest/f'figure1_dev_dose_response.{ext}',dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8,4),constrained_layout=True)
    major = {k:v for k,v in strata['subject'].items() if v['major']}; x=np.arange(len(major))
    for offset, g in enumerate(['1.25','1.5','2.0']):
        ax.bar(x+(offset-1)*.24,[100*v['effects'][g]['delta'] for v in major.values()],.24,label=f'{g}×')
    ax.axhline(0,color='black',linewidth=.7); ax.set_xticks(x,[f"{k}\n(n={v['n']})" for k,v in major.items()])
    ax.set_ylabel('Accuracy change (percentage points)'); ax.legend(); ax.set_title('Development major subjects; descriptive only')
    for ext in ['png','pdf']: fig.savefig(dest/f'figure4_dev_subtype_heterogeneity.{ext}',dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7,4),constrained_layout=True); x=np.arange(3)
    for offset,(k,label) in enumerate([('WtoC','Wrong → correct'),('CtoW','Correct → wrong')]):
        ax.bar(x+(offset-.5)*.32,[s['transitions'][k] for s in ss[1:]],.32,label=label)
    ax.set_xticks(x,['1.25×','1.5×','2×']); ax.set_xlabel('Visual gain'); ax.set_ylabel('Paired items'); ax.legend()
    ax.set_title('Development rescues / collateral damage; unresolved pairs separate')
    for ext in ['png','pdf']: fig.savefig(dest/f'figure6_dev_rescue_collateral.{ext}',dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    main()
