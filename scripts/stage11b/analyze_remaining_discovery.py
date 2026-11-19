"""Original discovery GO on the sole source-feasible rule; preserve missingness."""
import argparse
from collections import Counter
from pathlib import Path
import pandas as pd
from scripts.stage11b.common import ROOT, load, save, sha, now
from scripts.stage11b.protocol import discovery_gate, in_stratum
from scripts.stage11b.futility import forward_upper_bound
from visual_reasoning.stage8b.v2_scoring import score_answer


def reviewed_results():
    source = {r['item_id']: r for r in load(ROOT/'stage11b_discovery_manifest_v2.json')['rows']}
    tasks = {r['task_id']: r for r in load(ROOT/'discovery_tasks.json')['rows']}
    reviewed = {}
    for path in sorted((ROOT/'annotations').glob('partial_answers_v*.json')):
        version = path.stem.rsplit('_v', 1)[1]
        packet = ROOT/'packets'/f'partial_answer_review_v{version}.json'
        review = load(path)
        assert review['sealed'] and review['gold_or_correctness_opened'] is False
        assert sha(packet) == review['packet_sha256']
        assert load(packet)['evidence_sha256'] == sha(ROOT/'annotations/discovery_evidence_final.json')
        keys = {r['packet_id']: r for r in load(ROOT/'audit'/f'partial_answer_key_v{version}.json')['rows']}
        assert len(review['rows']) == len(keys)
        packets = {r['packet_id']: r for r in load(packet)['rows']}
        for answer in review['rows']:
            key = keys[answer['packet_id']]
            ident = key['task_id']
            assert ident not in reviewed
            receipt_path = Path(key['path'])
            receipt = load(receipt_path)
            assert not receipt['budget_interrupted']
            assert sha(receipt_path.parent/'generation.json') == receipt['generation_sha256']
            if answer['answer'] is not None:
                assert answer['quote'] in packets[answer['packet_id']]['text']
            task = tasks[ident]
            text = '' if answer['answer'] is None else '\\boxed{'+answer['answer']+'}'
            scored = score_answer(text, source[task['item_id']])
            reviewed[ident] = dict(task_id=ident, item_id=task['item_id'], family_id=task['family_id'],
                arm=task['arm'], condition=task['condition'], correct=scored['correct'] is True,
                benchmark_label=scored['benchmark_label'], reviewed_answer=answer['answer'],
                no_literal_final=answer['answer'] is None, tokens=receipt['tokens'],
                normal_eos=receipt['normal_eos'], at_length_cap=receipt['at_length_cap'],
                receipt_path=str(receipt_path), review_path=str(path), status='COMPLETED_REVIEWED')
    return reviewed


def analyze(final=False):
    evidence = load(ROOT/'annotations/discovery_evidence_final.json')
    assert evidence['sealed']
    gold = {r['item_id']: r for r in evidence['rows']}
    source_gate = load(ROOT/'audit/source_only_necessary_gate.json')
    feasible = [r for r in source_gate['strata'] if r['possible']]
    assert len(feasible) == 1 and feasible[0]['rule']['id'] == 'middle_all'
    stratum = feasible[0]
    eligible = [r for r in evidence['rows'] if r['eligible'] and in_stratum(r, stratum['rule'])]
    results = reviewed_results()
    pairs = []
    for r in eligible:
        t = results.get('thinking_'+r['item_id'])
        c = results.get('instruct_cot_'+r['item_id'])
        pairs.append((t['correct'] if t else None, c['correct'] if c else None))
    complete = all(t is not None and c is not None for t, c in pairs)
    maximum_forward = forward_upper_bound(pairs)
    t_correct = sum(t is True for t, c in pairs)
    c_correct = sum(c is True for t, c in pairs)
    forward = sum(t is True and c is False for t, c in pairs)
    reverse = sum(t is False and c is True for t, c in pairs)
    observed = dict(thinking_n=sum(t is not None for t, c in pairs), cot_n=sum(c is not None for t, c in pairs),
        observed_thinking_correct=t_correct, observed_cot_correct=c_correct,
        observed_forward=forward, observed_reverse=reverse, maximum_possible_forward=maximum_forward)
    gate = discovery_gate(stratum['n'], len(eligible), t_correct, c_correct, forward) if complete else None
    if maximum_forward < 12:
        status, reason = 'NO_GO', 'Original12-forward gate is impossible even if every unobserved eligible pair were favorable'
    elif complete:
        status = 'GO' if gate['pass'] else 'NO_GO'
        reason = 'Complete native evaluation of sole source-feasible stratum under all original gates'
    else:
        status, reason = 'INCOMPLETE', 'Native gates unresolved; no full-cohort accuracy estimate or imputation'
    output = dict(at=now(), status=status, reason=reason, eligible=len(eligible), reviewed=stratum['n'],
        observed=observed, complete_native_pairs=complete, original_gate=gate,
        thinking_accuracy=t_correct/len(eligible) if complete else None,
        cot_accuracy=c_correct/len(eligible) if complete else None,
        forward_rate=forward/len(eligible) if complete else None,
        source_only_strata=source_gate['strata'], primary=stratum['rule'] if status=='GO' else None,
        secondary_fallback=None, heldout_outcomes_opened=False,
        evidence_sha256=sha(ROOT/'annotations/discovery_evidence_final.json'),
        source_pruning_sha256=sha(ROOT/'audit/source_pruning_compute_record_v1.json'),
        frozen=final, no_claim3_inference_from_discovery=True)
    if final:
        assert status != 'INCOMPLETE', 'Use an explicit resource-stop artifact rather than mislabel incomplete discovery NO_GO'
        jobs = [j for j in load('state/gpu_experiment_queue.json')['jobs'] if j['id'].startswith('stage11b_feasible_')]
        assert all(j['status'] in ['succeeded', 'failed', 'cancelled'] for j in jobs)
        for queue in ['discovery', 'source_feasible']:
            for p in (ROOT/queue/'results').glob('*/result.json'):
                r = load(p)
                assert r['budget_interrupted'] or r['task_id'] in results, 'Every completed scientific trace requires literal answer review'
        save(ROOT/'stage11b_selection_rule.json', output)
        rows = []
        for task in load(ROOT/'discovery_tasks.json')['rows']:
            r = results.get(task['task_id'])
            required = gold[task['item_id']]['eligible'] and in_stratum(gold[task['item_id']], stratum['rule'])
            if r is None:
                r = dict(task_id=task['task_id'], item_id=task['item_id'], family_id=task['family_id'], arm=task['arm'],
                    condition=task['condition'], correct=None,
                    status='NOT_SCORED_AT_LOGICAL_STOP' if required else 'NOT_SCORED_SOURCE_GATE_PRUNED')
            rows.append(dict(r, e_star_eligible=gold[task['item_id']]['eligible'], required_for_remaining_gate=required))
        path = ROOT/'stage11b_discovery_mode_results.parquet'
        assert not path.exists()
        pd.DataFrame(rows).to_parquet(path, index=False)
        save(ROOT/'audit/discovery_scored.json', dict(at=now(), rows=rows,
            missing_never_imputed=True, no_final_scored_no_credit_but_separately_labeled=True))
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--final', action='store_true')
    analyze(p.parse_args().final)
