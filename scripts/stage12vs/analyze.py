"""Assemble sealed family evidence without changing the prospective gates."""
import json
import pandas as pd
from scripts.stage12vs.common import ROOT, load, save, sha, now
from scripts.stage12vs.advance import scored
from scripts.stage12vs.protocol import majority
from scripts.stage12vs.inference import causal_step, decision
from scripts.stage12us.inference import conjunction, neg
from scripts.stage12us.analyze import interval


RECOMMENDATIONS = {
    'DERIVED_STATE_CAUSAL_SIGNAL': 'Compare the localized portable deductions to the causal visual-retrieval and Value-transfer events in the same trajectories to connect evidence acquisition to portable reasoning-state construction.',
    'PORTABILITY_LOCALIZED_BUT_DISTRIBUTED': 'Test block-wise reasoning-prefix necessity rather than single-step necessity.',
    'PORTABILITY_NONMONOTONIC': 'Characterize why textual-state usability appears and disappears before attempting hidden-state interventions.',
    'PORTABILITY_UNSTABLE': 'Stop fine localization and retain Stage12U-S state production as the strongest supported result.',
    'UNRESOLVED': 'Review the unresolved localization pattern before authorizing a further mechanism experiment.',
}


def assemble():
    for seal in ['source_seal.json', 'analysis_rules_before_results.json']:
        for path, digest in load(ROOT / 'audit' / seal)['hashes'].items():
            assert sha(path) == digest, path
    phases = ['phaseA'] + [f'phaseB{i}' for i in range(1, 8)] + ['adjacentT', 'contentC', 'optionalE']
    rows = [row for phase in phases for row in scored(phase)]
    assert len(rows) == len({r['task_id'] for r in rows}) == 162
    cf_review = load(ROOT / 'audit/counterfactual_following_review.json')
    assert cf_review['readout_source_sha256'] == sha(ROOT / 'audit/manual_intervention_edits.json')
    for r in cf_review['rows']:
        path = ROOT / 'generations' / r['task_id'] / 'generation.json'
        assert sha(path) == r['generation_sha256']
        assert load(path)['raw_decoded_response'][r['quote_start']:r['quote_end']] == r['evidence_quote']
    edits = {r['item_id']: r for r in load(ROOT / 'stage12vs_critical_step_interventions.json')['rows']}
    primary = []
    for loc in load(ROOT / 'stage12vs_fine_localization.json')['families']:
        item = loc['item_id']
        stable = True if loc['status'] == 'STABLE' else None if loc['status'] == 'MISSING_BOUNDARY' else False
        selected = [r for r in rows if r['item_id'] == item]

        def condition(name, step=None):
            rr = sorted((r for r in selected if r['condition'] == name and (step is None or r['step_index'] == step)), key=lambda r: r['replicate'])
            assert len(rr) in (0, 3)
            return dict(task_ids=[r['task_id'] for r in rr], outcomes=[r['correct'] for r in rr],
                        final_values=[r['outcome'] for r in rr], majority=majority([r['correct'] for r in rr]) if rr else None)

        conditions = {c: condition(c) for c in ['C1_DROP', 'C2_CF', 'C3_PARA', 'C4_CTRL_DROP', 'C5_ESTAR', 'E_PLUS_STEP']}
        t_checks = {side: condition('T_ADJ', loc[key]) if stable is True else dict(task_ids=[], outcomes=[], final_values=[], majority=None)
                    for side, key in [('before', 'a'), ('after', 'b')]}
        follow = [r['cf_following'] for r in sorted(cf_review['rows'], key=lambda r: r['replicate']) if r['item_id'] == item]
        redirect = majority(follow) if follow else None
        mm = {c: v['majority'] for c, v in conditions.items()}
        causal = causal_step(stable, mm['C1_DROP'], mm['C2_CF'], mm['C3_PARA'], mm['C4_CTRL_DROP'], redirect)
        sensitive = True if mm['C2_CF'] is False or redirect is True else None if mm['C2_CF'] is None or redirect is None else False
        primary.append(dict(item_id=item, family_id=loc['family_id'], localization=loc, stable=stable,
                            nonmonotonic=loc['status'] == 'NONMONOTONIC_PORTABILITY', conditions=conditions,
                            thinking=t_checks, cf_following=follow, cf_following_majority=redirect,
                            critical_step=edits.get(item), causal=causal, oracle=mm['C5_ESTAR'],
                            necessity=conjunction(stable, neg(mm['C1_DROP'])),
                            semantic_sensitivity=conjunction(stable, sensitive),
                            paraphrase_preserved=conjunction(stable, mm['C3_PARA']),
                            specificity=conjunction(stable, neg(mm['C1_DROP']), mm['C4_CTRL_DROP'])))
    eligible = [r for r in primary if r['stable'] is True]
    result = decision(primary, load(ROOT / 'audit/replication_gate.json')['full_failures'])
    result.update(recommendation=RECOMMENDATIONS[result['decision']], next_experiment_launched=False,
                  classification_caveat='One family is nonmonotonic and one has an unresolved capped boundary; the missing family is not relabeled nonmonotonic. Two adjacent transitions satisfy the frozen search rule, but their deletion replications must independently establish necessity.')
    endpoints = {'V_P1_localization': interval([r['stable'] for r in primary])}
    for name, key in [('V_P2_necessity', 'necessity'), ('V_P3_semantic_sensitivity', 'semantic_sensitivity'),
                      ('V_P4_paraphrase', 'paraphrase_preserved'), ('V_P5_specificity', 'specificity')]:
        endpoints[name] = dict(confirmed_of_four=sum(r[key] is True for r in primary),
                               frozen_cohort=4, eligible_stable_only=interval([r[key] for r in eligible]),
                               untested_families=[r['item_id'] for r in primary if r['stable'] is not True])
    info = dict(at=now(), independent_unit='conservative visual family', n_primary=4, primary=primary,
                endpoints=endpoints, decision=result, all_seed_rows=rows,
                interval_note='Exact Clopper-Pearson intervals are descriptive for resolved/eligible families; retain n=4 and missingness bounds. No population prevalence or asymptotic inference.',
                limitations=['Three seeds per condition; fresh-seed DROP duplicates the before prefix and may reverse its search majority.',
                             'Both critical steps repeat earlier propositions; frozen source-cue annotations are not independent exhaustive semantic certification.',
                             'Two stable, one nonmonotonic, one unresolved family; no shared causal step property can be claimed.',
                             'Image-free externalized text only; checkpoint, recipe and caps differ; no hidden-state or pure reasoning-mode mechanism identified.'])
    return info


def main():
    info = assemble()
    rows = info['all_seed_rows']
    panels = {'adjacent_thinking_checks': ('adjacentT', None, 12),
              'content_ablation_results': ('contentC', False, 24),
              'replicated_evidence_oracle': ('contentC', True, 6),
              'evidence_plus_step_results': ('optionalE', None, 6)}
    for name, (phase, oracle, count) in panels.items():
        chosen = [r for r in rows if r['phase'] == phase and (oracle is None or (r['condition'] == 'C5_ESTAR') == oracle)]
        assert len(chosen) == count
        path = ROOT / f'stage12vs_{name}.parquet'
        assert not path.exists(), path
        pd.DataFrame(chosen).to_parquet(path, index=False)
    save(ROOT / 'stage12vs_primary_inference.json', info)
    save(ROOT / 'audit/decision_candidate.json', info['decision'])
    print(json.dumps(info['decision'], indent=2))


if __name__ == '__main__':
    main()
