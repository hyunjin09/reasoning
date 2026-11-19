"""Descriptive source-judgment/outcome joins; no mediation or subgroup discovery claim."""
from collections import Counter
import json
from scripts.stage14e.common import P, load, save, sha, now
from scripts.stage14e.reporting import markdown_blocks


def transition(native, treated):
    if native is None or treated is None:
        return 'UNSCORABLE_PAIR'
    return {(False, True): 'RESCUE', (True, False): 'REGRESSION',
            (True, True): 'PRESERVED_CORRECT', (False, False): 'PRESERVED_WRONG'}[bool(native), bool(treated)]


def main():
    scored = load(P / 'analysis/final_scored_rows_v1.json')['records']
    acq = load(P / 'annotations/evaluation_source_review_v1.json')['records']
    by = {(r['item_id'], r['arm']): r for r in scored}
    source = {r['item_id']: r for r in load(P / 'offline/evaluation_source_references_v1.json')}
    qc = {r['item_id']: r for r in load(P / 'annotations/evaluation_source_QC_v1.json')['rows']}
    result = []
    for r in acq:
        arm, i = r['condition'], r['item_id']
        if arm == 'M_noimage':
            continue
        n, t = by[i, 'N'], by[i, arm]
        outcome = transition(n['correct'], t['correct'])
        if t['status'] != 'PHYSICAL':
            assert t['generation_path'] == n['generation_path']
            assert n['correct'] == t['correct']
        result.append(dict(item_id=i, family_id=r['family_id'], arm=arm,
            native_correct=n['correct'], treatment_correct=t['correct'], transition=outcome,
            evidence_label=r['label'], target_relevance=r['target_relevance'],
            evidence_notes=r['notes'], prefix_state=qc[i]['prefix_state'],
            structured_source=source[i]['has_structured_atom'], execution_status=t['status'],
            helper_path=r['generation_path'], solver_path=t['generation_path'], native_path=n['generation_path']))
    assert len(result) == 64
    groups = {}
    for arm in ['S', 'M']:
        groups[arm] = {}
        for field in ['evidence_label', 'prefix_state', 'structured_source', 'execution_status']:
            groups[arm][field] = {}
            for value in sorted({str(r[field]) for r in result if r['arm'] == arm}):
                rs = [r for r in result if r['arm'] == arm and str(r[field]) == value]
                groups[arm][field][value] = dict(families=len(rs),
                    transitions=dict(Counter(r['transition'] for r in rs)),
                    native_correct=sum(r['native_correct'] is True for r in rs),
                    treatment_correct=sum(r['treatment_correct'] is True for r in rs),
                    treatment_unscorable=sum(r['treatment_correct'] is None for r in rs))
    save(P / 'analysis/acquisition_outcome_associations_v1.json', dict(at=now(), records=result,
        groups=groups, descriptive_only=True, source_review_sha256=sha(P / 'annotations/evaluation_source_review_v1.json'),
        interpretation='Post-treatment evidence labels are neither randomized groups nor established causal mediators. '
            'Helper evidence novelty is not inferred from final-answer change.'))
    changed = [r for r in result if r['transition'] in ['RESCUE', 'REGRESSION', 'UNSCORABLE_PAIR']]
    report = ['# All final-answer changes and source judgments',
        'Every S/M change relative to N is listed. Source judgments were fixed before new final outcomes were opened. '
        'These are descriptive joins; no final change is attributed causally to a helper fact. '
        'See final32_casebook_v1.md for full questions, prefixes, original source references, raw prompts and outputs.',
        '| Family | Arm | Transition | Helper evidence | Target relevance | Execution | Source-review note |',
        '|---|---|---|---|---|---|---|']
    for r in changed:
        report.append('| ' + ' | '.join(str(r[k]).replace('|', '\\|').replace('\n', ' ') for k in
            ['item_id', 'arm', 'transition', 'evidence_label', 'target_relevance', 'execution_status', 'evidence_notes']) + ' |')
    report.extend(['\nLabels: U=new useful fact; R=valid useful reinspection; K=known/given; W=explicitly wrong; '
        '?=unknown/incomplete; I=irrelevant/derived; A=no attempt. The presence of K/?/A is not an acquisition-failure diagnosis.',
        '\n## Descriptive cross-tabulations\n\n```json\n' + json.dumps(groups, indent=2) + '\n```'])
    with (P / 'reports/final_answer_change_casebook_v1.md').open('x') as out:
        out.write(markdown_blocks(report))
    print('Joined64 treatment/native comparisons; changed or unscorable', len(changed))


if __name__ == '__main__':
    main()
