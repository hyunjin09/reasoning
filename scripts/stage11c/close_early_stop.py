"""Close the prescribed early-completion STOP; never estimate full-cohort effects."""
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from scripts.stage11c.common import ROOT, ARMS, load, save, sha, now
from scripts.stage11c.results import assemble
from scripts.stage11c.resources import account

RECOMMENDATION = ('Keep Thinking-vs-Instruct as an unresolved performance observation and finalize '
                  'the paper around the established causal retrieval and visual-to-text lifecycle claims.')


def parquet(path, rows):
    assert not path.exists()
    pq.write_table(pa.Table.from_pylist(rows), path)


def main():
    gate_path = ROOT/'audit/early_native_completion_gate.json'
    gate = load(gate_path)
    assert gate['status'] == 'STOP' and gate['n_calls'] == 32
    assert max(gate['cap_hits'].values()) > 4
    split = load(ROOT/'stage11c_primary_split.json')
    review = load(ROOT/'stage11c_e_star_sufficiency_review.json')
    cap = load(ROOT/'stage11c_cap_validation.json')
    assert split['primary_n'] >= 64 and cap['cap'] == 8192
    assert not list(ROOT.glob('oracle*/results/*/generation.json'))
    assert not list(ROOT.glob('neutral*/results/*/generation.json'))
    assert not list(ROOT.glob('cot*/results/*/generation.json'))
    resources = account('early_stop_final', final=True)
    assert resources['allocated_gpu_hours_observed'] <= 8
    rows = assemble('native_early_tasks.json', 'native_early')
    completed = [r for r in rows if r['status'] == 'COMPLETE']
    assert len(completed) == 32 and len({r['family_id'] for r in completed}) == 16
    assert all(r['status']=='COMPLETE' or r['correct'] is None for r in rows)
    parquet(ROOT/'stage11c_native_td_results.parquet', rows)
    diagnosis = {arm: dict(n=16, cap_hits=gate['cap_hits'][arm],
        no_committed_final=sum(r['answer_status']=='NO_COMMITTED_FINAL' for r in completed if r['arm']==arm),
        literal_scored_correct=sum(r['correct'] is True for r in completed if r['arm']==arm),
        unscorable=sum(r['correct'] is None for r in completed if r['arm']==arm)) for arm in ARMS}
    save(ROOT/'stage11c_native_gate.json', dict(at=now(), frozen=True,
        status='STOP_COMPLETION', completion_gate_sha256=sha(gate_path),
        criterion='More than4/16 cap hits in either mode on the fixed first16 matched families.',
        primary_families=split['primary_n'], completed_families=16, completed_calls=32,
        not_run_calls=len(rows)-32, technical_diagnostics=diagnosis,
        performance_gate='NOT_EVALUATED', primary_accuracy=None, primary_gap=None,
        reason='Completion gate failed before remaining native or oracle execution. Partial subset is not a full primary estimate.'))
    oracle_rows = [dict(item_id=s['item_id'], family_id=s['family_id'], arm=arm,
        condition='oracle', status='NOT_RUN', correct=None,
        reason='Early native completion gate failed') for s in split['primary'] for arm in ARMS]
    parquet(ROOT/'stage11c_oracle_td_results.parquet', oracle_rows)
    save(ROOT/'stage11c_oracle_validity.json', dict(at=now(), status='NOT_RUN', valid=None,
        reason='Early native completion gate failed; oracle never launched.',
        source_evidence_frozen=True, runtime_image_independence_check='NOT_APPLICABLE_NOT_RUN'))
    save(ROOT/'stage11c_primary_inference.json', dict(at=now(), frozen=True, status='NOT_ESTIMATED',
        reason='Only16/80 matched native families executed before the prescribed technical STOP; oracle unrun.',
        P1=None, P2=None, P3=None, closure_fraction=None, outcome='UNRESOLVED_COMPLETION_LIMITED',
        primary_independent_families=split['primary_n'], observed_native_families=16,
        bootstrap_draws_executed=0, claim3_supported=False, no_null_effect_claim=True,
        recommendation=RECOMMENDATION))
    save(ROOT/'stage11c_neutral_control.json', dict(at=now(), status='NOT_RUN',
        frozen_families=split['subsets']['neutral'], planned_n=24, executed_calls=0,
        reason='Oracle gate not reached'))
    save(ROOT/'stage11c_reserve_extension.json', dict(at=now(), status='NOT_OPENED',
        frozen_n=split['reserve_n'], executed_calls=0, reason='Completion failure cannot trigger reserve rescue'))
    save(ROOT/'audit/conditional_blocks.json', dict(at=now(), cot=dict(status='NOT_RUN', planned_families=48),
        secondary_native_states=dict(status='NOT_RUN', planned_families=32),
        reason='Primary inference not estimable; prescribed STOP', no_new_study_launched=True))
    from scripts.stage11c.stop_figures import make_figures
    make_figures(gate, split)
    rel = review['original_reliability']
    diag = '\n'.join(f'| {arm} | 16 | {d["cap_hits"]} | {d["no_committed_final"]} | {d["literal_scored_correct"]} |'
                     for arm,d in diagnosis.items())
    text=f'''# Stage11C — completed with prescribed technical STOP

Stage11C could not localize the Thinking-versus-Instruct advantage. The common 8,192-token primary completion gate failed before the oracle. This is a completion-limited result, not evidence for a zero native gap or an upstream/downstream mechanism. Noncompletion cause remains unknown.

## Frozen design and source evidence

The development rule used levels 2–4 across all subjects: 47 eligible earlier families (Thinking 19/47; Direct 11/47), with no fallback. The original 300-source manifest, original reviews, and source-only alias exclusions 1887/814 are preserved. No heldout outcomes selected sources or repaired E*.

We reviewed {review['reviewed']} source entries twice and retained {review['eligible']} eligible families. Frozen split: {split['primary_n']} primary and {split['reserve_n']} reserve, plus subset IDs for 24 neutral, 48 CoT, and 32 native-state families. E* and all subsets were frozen before primary inference. No reserve opened.

Two AI agents reviewed the evidence independently; these agreement measurements are not human inter-rater reliability. Each reviewer constructed a disjoint portion before reviewing the common proposals. In the final single-source batches, only reviewer A constructed proposals; reviewer B reviewed them without construction exposure. Raw all-proposal sufficiency agreement {rel['all']['sufficiency']['agreement']:.1%},kappa {rel['all']['sufficiency']['kappa']:.3f}; nonempty-proposal agreement {rel['nonempty']['sufficiency']['agreement']:.1%},kappa {rel['nonempty']['sufficiency']['kappa']:.3f}. Nonempty quality-conjunction agreement {rel['nonempty']['quality']['agreement']:.1%},kappa {rel['nonempty']['quality']['kappa']:.3f}. Low conditional kappa under strongly positive prevalence and all disputes remain disclosed; strict dual-pass eligibility excludes disagreements. No post-outcome evidence repair.

## Execution and stop

Calibration: 12 non-primary cases × 2 modes × 2 caps = 48 exact valid calls. Thinking hit the cap on 12/12 and Direct on 11/12 cases at both 4,096 and 8,192 tokens. The plan therefore selected 8,192 and marked the stage completion-limited. Batch size 1, BF16, TF32 off, greedy decoding, repetition penalty 1, native image preprocessing, and pinned model revisions were preserved.

The fixed first 16 matched primary families produced 32 valid calls. The prespecified criterion stops further native/oracle work if either mode has more than 4 cap hits.

| Arm | Completed calls | Cap hits | No committed final | Literal-scored correct |
|---|---:|---:|---:|---:|
{diag}

These are technical diagnostics for the fixed 16-family gate only. They are not primary-cohort accuracy estimates. The remaining {len(rows)-32} native calls are explicitly NOT_RUN, not incorrect. No full native performance gate was evaluated.

Oracle, neutral text, CoT, secondary native-state annotation and reserve execution: NOT_RUN. P1/P2/P3 and closure fraction: NOT_ESTIMATED; no confidence interval or upstream/downstream/mixed claim. Figures 2–4 explicitly display the stop and missing estimates; no fictitious zeros or CoT figure.

A fixed calibration-case check found valid image inputs and native templates, unfinished Thinking and repeated Direct text. It did not establish the cause or justify a decoding/cap rescue. No extra benchmark or mechanism search was launched.

## Resources and evidence

All {len(resources['jobs'])} Stage11C Slurm jobs terminal and GPUs released. Total allocated **{resources['allocated_gpu_hours_observed']:.6f} GPU-hours**, including startup and the safe partial calibration shard; hard limit 8. Calibration reused 39 completed calls when its remaining 9 were repartitioned. No duplicate valid generations. Source annotation burden: {review['reviewed']} construction records and {2*review['reviewed']} semantic reviews by AI agents, separate from GPU accounting.

Artifacts: [native gate](stage11c_native_gate.json), [cap calibration](stage11c_cap_validation.json), [sufficiency review](stage11c_e_star_sufficiency_review.json), [primary split](stage11c_primary_split.json), [inference status](stage11c_primary_inference.json), [resources](stage11c_resource_accounting.json). Raw logs/receipts, output-only literal-answer reviews and source construction records are retained.

## Recommendation

{RECOMMENDATION}

STOP. The recommendation is not executed as a new research action.
'''
    path=ROOT/'stage11c_summary.md'
    assert not path.exists()
    path.write_text(text)
    print('STAGE11C_TECHNICAL_STOP_ARTIFACTS_WRITTEN', diagnosis)


if __name__ == '__main__':
    main()
