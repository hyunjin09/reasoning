"""Materialize the approved stopping branch only after a verified discovery NO_GO."""
from collections import Counter
import json
import pyarrow as pa
import pyarrow.parquet as pq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage11b.common import ROOT, load, save, sha, now

RECOMMENDATION = ('Keep Thinking-vs-CoT as a discussion-level open question and finalize the paper '
                  'around the established causal retrieval and visual-to-text lifecycle claims.')


def empty_parquet(name, fields, reason):
    path = ROOT/name
    assert not path.exists()
    schema = pa.schema(fields, metadata={b'status': b'NOT_RUN_DISCOVERY_NO_GO', b'reason': reason.encode()})
    pq.write_table(pa.Table.from_pylist([], schema=schema), path)


def figure_save(fig, name):
    for suffix in ['png', 'pdf']:
        path = ROOT/'figures'/f'{name}.{suffix}'
        assert not path.exists()
        fig.savefig(path, dpi=180, bbox_inches='tight')
    plt.close(fig)


def not_run_figure(name, title, body):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.axis('off')
    ax.text(.5, .78, title, ha='center', fontsize=16, transform=ax.transAxes)
    ax.text(.5, .49, 'NOT RUN — discovery GO gate failed', ha='center', fontsize=14,
            color='#963c37', transform=ax.transAxes)
    ax.text(.5, .22, body, ha='center', va='center', fontsize=11, transform=ax.transAxes)
    figure_save(fig, name)


def build_discovery_figure(selection):
    observed = selection['observed']
    strata = selection['source_only_strata']
    labels = ['3–5 / all', '4–5 / all', '3–4 / all', '3–5 / geometry', '3–5 / other', '4–5 / geometry']
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), gridspec_kw={'width_ratios': [1.25, 1]})
    ax = axes[0]
    ax.barh(labels, [100*r['eligibility_rate'] for r in strata], color=['#2a7f62' if r['possible'] else '#9ba8b8' for r in strata])
    ax.axvline(40, color='#963c37', ls='--', zorder=0)
    for i, r in enumerate(strata):
        ax.text(100*r['eligibility_rate']+.5, i, f"{r['eligible']}/{r['n']}", va='center',
                bbox=dict(facecolor='white', edgecolor='none', pad=.6), zorder=4)
    ax.invert_yaxis()
    ax.set(xlim=(0, 53), xlabel='Source eligibility (%)', title='Six frozen discovery strata')
    ax.spines[['top', 'right']].set_visible(False)
    ax = axes[1]
    total = selection['eligible']
    correct = [observed['observed_thinking_correct'], observed['observed_cot_correct']]
    n = [observed['thinking_n'], observed['cot_n']]
    wrong = [a-b for a, b in zip(n, correct)]
    unknown = [total-a for a in n]
    ax.barh(['Thinking', 'CoT'], correct, color='#2a7f62', label='Correct')
    ax.barh(['Thinking', 'CoT'], wrong, left=correct, color='#b18d84', label='No credit (wrong/no final)')
    ax.barh(['Thinking', 'CoT'], unknown, left=n, color='#dce4ef', label='Unobserved/unscored')
    ax.set(xlim=(0, total), xlabel=f'Families within the {total}-family eligible stratum', title='Native observations; missingness retained')
    handles, legend_labels = ax.get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc='lower center', bbox_to_anchor=(.5, .12), ncol=3, fontsize=9, frameon=False)
    ax.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Stage11B discovery stop: no stratum passes all original GO requirements', fontsize=14)
    fig.subplots_adjust(left=.13, right=.98, top=.80, bottom=.31, wspace=.27)
    fig.text(.02, .015, f"Observed forward discordances: {observed['observed_forward']}; maximum still possible: {observed['maximum_possible_forward']}; required: 12.\n"
             'Source feasibility alone is not GO. Unknown outcomes are never imputed as incorrect.', fontsize=9)
    figure_save(fig, 'figure2_discovery_yield_map')


def main():
    selection = load(ROOT/'stage11b_selection_rule.json')
    resource = load(ROOT/'stage11b_resource_accounting.json')
    assert selection['frozen'] and selection['status'] == 'NO_GO'
    assert resource['final'] and resource['all_stage_allocations_released'] and resource['under_hard_limit']
    evidence = load(ROOT/'annotations/discovery_evidence_final.json')
    review = load(ROOT/'stage11b_e_star_sufficiency_review.json')
    observed = selection['observed']
    total = selection['eligible']
    reason = selection['reason']
    common = dict(at=now(), status='NOT_RUN_DISCOVERY_NO_GO', reason=reason,
                  selection_sha256=sha(ROOT/'stage11b_selection_rule.json'))
    save(ROOT/'stage11b_heldout_manifest.json', dict(common, frozen=False, rows=[], n=0,
        untouched_reserve=689, primary_rule=None, scientific_outcomes_used_to_select_heldout=False))
    id_fields = [('item_id', pa.string()), ('family_id', pa.string())]
    empty_parquet('stage11b_heldout_e_star_gold.parquet', id_fields+[('facts', pa.list_(pa.string()))], reason)
    result_fields = id_fields+[('arm', pa.string()), ('condition', pa.string()), ('correct', pa.bool_())]
    empty_parquet('stage11b_native_results.parquet', result_fields, reason)
    empty_parquet('stage11b_oracle_results.parquet', result_fields, reason)
    save(ROOT/'stage11b_oracle_validity.json', dict(common,
        V1_sufficiency='NOT_TESTED_HELDOUT', V2_leakage='NOT_TESTED_HELDOUT',
        V3_image_independence='TECHNICAL_PREFLIGHT_ONLY_NOT_HELDOUT',
        V4_same_evidence='SPECIFIED_NOT_TESTED_HELDOUT', V5_neutral_control='NOT_RUN',
        oracle_validity_pass=None, technical_preflight='audit/technical_preflight.json'))
    save(ROOT/'stage11b_primary_inference.json', dict(common, claim3_promoted=False,
        P1=None, P2=None, P3=None, P4=None, native_gap=None, oracle_gap=None, closure_fraction=None,
        heldout_families=0, bootstrap_draws_executed=0, bootstrap_draws_planned=4000,
        interpretation='Discovery stop does not localize upstream versus downstream advantage, and is not evidence of equivalence.',
        recommendation=RECOMMENDATION))
    save(ROOT/'stage11b_discordant_analysis.json', dict(at=now(), status='DISCOVERY_COUNTS_ONLY',
        observed=observed, complete_native_pairs=selection['complete_native_pairs'],
        heldout_discordant_analysis='NOT_RUN', secondary_native_evidence_analysis='NOT_RUN',
        upstream_downstream_classification=None, no_mechanism_assigned_from_noncompletion=True))
    save(ROOT/'audit/conditional_artifact_status.json', dict(at=now(), reason=reason,
        heldout_native_and_oracle_parquets='Empty tables with NOT_RUN metadata; no fabricated zero accuracy.',
        optional_native_evidence_states='NOT_RUN', optional_direct_subset='NOT_RUN',
        figures_3_4_5='Explicit not-run status panels, not empirical result plots.'))

    build_discovery_figure(selection)
    not_run_figure('figure3_native_vs_oracle', 'Held-out native versus oracle accuracy',
                  'Native Thinking / Native CoT / Oracle Thinking / Oracle CoT\nNo held-out accuracy estimates are available.')
    not_run_figure('figure4_gap_decomposition', 'Held-out gap decomposition',
                  'Native gap, oracle gap and gap closure are not estimated.\nNo upstream, downstream or mixed mechanism is established.')
    not_run_figure('figure5_secondary_native_evidence', 'Secondary native evidence explanation',
                  'Secondary mechanism annotation was not launched.\nLength-capped outputs are not assigned a visual-access mechanism.')

    raw = review['raw_summary']['agreement']
    categories = Counter(r['eligibility'] for r in evidence['rows'])
    scored = load(ROOT/'audit/discovery_scored.json')['rows']
    completed = [r for r in scored if r['status']=='COMPLETED_REVIEWED']
    capped = sum(r['at_length_cap'] for r in completed)
    no_final = sum(r['no_literal_final'] for r in completed)
    batch_check = load(ROOT/'audit/batch_single_interpretation.json')
    batch_note = (f"A bounded technical replay reproduced {batch_check['same_batch_prefix_reproduced']}/8 original batch prefixes exactly. "
        f"Single-item prefixes diverged after {batch_check['common_prefix_range'][0]}–{batch_check['common_prefix_range'][1]} tokens "
        f"despite matching source inputs and small prefill KL (maximum {batch_check['max_prefill_kl']:.6f}). "
        'Batch-size sensitivity is observed; equivalence to single-item inference and its contribution to long noncompletion are not established. '
        'These discovery observations apply to the frozen batch4 protocol. No diagnostic output substitutes for native evidence.')
    stop_record = ROOT/'audit/logical_stop_decision.json'
    sensitivity_note = ''
    if stop_record.exists():
        stop = load(stop_record)
        sensitivity_note = (f"Allowing every explicitly flagged ambiguous literal extraction to favor a Thinking-correct/CoT-failed result "
            f"raises the maximum possible forward count to {stop['generous_maximum_possible_forward']}, still below12. "
            'This conservative stopping check does not change the frozen answer labels or estimate an alternative full-cohort accuracy.')
    table = '\n'.join(f"| {r['rule']['id']} | {r['n']} | {r['eligible']} | {r['eligibility_rate']:.1%} | {'Native gate required' if r['possible'] else 'Fails source gate'} |" for r in strata)
    if selection['complete_native_pairs']:
        native = (f"All {total} eligible pairs are scored: Thinking {observed['observed_thinking_correct']}/{total}, "
                  f"CoT {observed['observed_cot_correct']}/{total}; forward/reverse discordances "
                  f"{observed['observed_forward']}/{observed['observed_reverse']}. These are discovery descriptions, not held-out Claim3 estimates.")
    else:
        native = (f"Thinking has {observed['observed_thinking_correct']} correct among {observed['thinking_n']} reviewed outputs; "
                  f"CoT has {observed['observed_cot_correct']} among {observed['cot_n']}. "
                  f"There are {observed['observed_forward']} observed forward discordances and at most "
                  f"{observed['maximum_possible_forward']} possible after every unobserved result, below the required12. "
                  'Full-stratum accuracies and the native gap are not estimated. This is a logical feasibility stop, not a sequential significance claim.')
    summary = f'''# Stage11B — completed at the discovery stopping gate

**NO_GO / STOP.** {reason}. No held-out cohort, equal-evidence oracle, neutral control, optional Direct arm or next experiment was launched. The Thinking–CoT mechanism remains unresolved.

128 fresh conservative MathVision families (levels3–5) received source-only construction and two independent model-agent semantic reviews before any native answer was opened.49 families are E*-eligible:41 unchanged and8 after one bounded independently re-reviewed representation repair. Categories: `{dict(categories)}`. Reviewers had prior exposure to their own construction halves; this is not human reliability evidence.

Raw sufficiency agreement is {raw['all']['sufficiency']['agreement']:.1%}, kappa {raw['all']['sufficiency']['kappa']:.3f} across128. Among54 nonempty proposals, agreement is {raw['proposed_nonempty_evidence']['sufficiency']['agreement']:.1%}, kappa {raw['proposed_nonempty_evidence']['sufficiency']['kappa']:.3f}; the latter is prevalence-sensitive, and quality-conjunction kappa is {raw['proposed_nonempty_evidence']['eligible_quality_conjunction']['kappa']:.3f}. Raw disagreement and five unresolved nonempty proposals are preserved; repairs do not replace the raw agreement estimate.

| Frozen rule | Source-reviewed | E*-eligible | Eligibility | Necessary source gate |
|---|---:|---:|---:|---|
{table}

Only levels3–4/all remained source-feasible (36/88). Before native outcomes were opened, execution was narrowed to its72 native comparisons; five failed-source strata could not be rescued by any native result. The original256-task manifest remains immutable.16 completed broad-queue outputs were preserved,6 reusable for this stratum;66 unfinished required calls plus6 original batch fillers were frozen under the unchanged models, prompts, BF16, greedy decoding,16384-token cap and batch4. No individual native outcome selected a family or changed E*.

{native}

{sensitivity_note}

{len(completed)} valid native outputs were literally reviewed; {capped} reached the length cap and {no_final} lack a committed final answer. No-final receives no credit and remains separately labeled; resource-interrupted/unrun outputs remain unknown. Long repetitive noncompletion is observed. The greedy configuration and incremental KV cache checks passed, but the cause of noncompletion is unresolved. It is not evidence of absent encoding or a specific upstream/downstream mechanism.

{batch_note}

An initial source-only family audit identified a redrawn prior-family alias and conservatively repaired12 discovery entries before inference, retaining the same sampling strata;689 untouched reserve families remain. The initial manifest and drafts are preserved. Broad source-similarity merging may overmerge and limits the available reserve. Active cohort: `stage11b_discovery_manifest_v2.json`; the unsuffixed manifest is historical.

Allocated compute: **{resource['allocated_gpu_hours_observed']:.4f} GPU-hours**, including startup, one preserved technical preflight failure, validation, cancelled broad calls and in-flight work. All Stage11B GPU allocations are released. The sole preflight failure was an overly strict text-input-key assertion; all-zero auxiliary modality tags were validated and the technical validator repaired. No model, dataset, token-cap or generation-semantic repair was made. All completed and partial evidence is retained.

P1–P4 and gap closure are **not estimated**. Empty held-out result tables carry explicit NOT_RUN metadata; Figures3–5 are status panels. Figure1 is the prospective design, and Figure2 reports the discovery evidence with missingness visible. No Claim3 promotion or mechanism-specific attribution is justified by this stopped discovery screen.

**Recommendation:** {RECOMMENDATION}

The recommendation has not been executed. Stop here.
'''
    path = ROOT/'stage11b_summary.md'
    assert not path.exists()
    path.write_text(summary)
    print('NO_GO report, conditional artifacts and remaining figures created; no next experiment launched')


if __name__ == '__main__':
    main()
