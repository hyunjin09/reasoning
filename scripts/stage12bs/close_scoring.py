"""Verify immutable blind passes and seal final labels before any family join."""
import json
import pandas as pd
from scripts.stage12bs.common import ROOT, load, save, sha, now


def main():
    seal = load(ROOT/'audit/first_scoring_seal.json')
    assert all(sha(p) == h for p, h in seal['first_hashes'].items())
    first = {load(p)['task_id']: load(p) for p in seal['first_hashes']}
    second = {t: load(ROOT/'audit/second_scores'/f'{t}.json') for t in seal['second_tasks']}
    unresolved = []
    logs = []
    final = []
    for tid, a in first.items():
        b = second.get(tid)
        agree = b is None or (a['label'] == b['label'] and a['atoms'] == b['atoms'])
        decision = a
        if b is not None:
            log = dict(task_id=tid, first=a, second=b, agreement=agree,
                       mandatory=tid in seal['mandatory_tasks'],
                       random_audit=a['family_id'] in seal['random_families'])
            if not agree:
                path = ROOT/'audit/adjudications'/f'{tid}.json'
                if not path.exists():
                    unresolved.append(tid)
                else:
                    decision = load(path)
                    assert decision['label'] in ['CORRECT','INCORRECT','UNRESOLVED_TECHNICAL']
                    assert decision['reason'] and decision['own_arm_only']
                    assert decision['correct'] == (None if decision['label']=='UNRESOLVED_TECHNICAL' else decision['label']=='CORRECT')
                    log['adjudication'] = decision
            logs.append(log)
        final.append(dict(a, **{k:decision[k] for k in ['label','correct','atoms','reason']},
                          second_reviewed=b is not None, first_second_agreement=agree))
    assert not unresolved, f'Own-arm adjudications required: {unresolved}'
    assert len(final)==183
    audit = dict(at=now(),first_pass_calls=183,second_pass_calls=len(second),
                 mandatory_calls=len(seal['mandatory_tasks']),random_families=seal['random_families'],
                 unambiguous_family_count=seal['unambiguous_family_count'],
                 random_rule='Frozen hash order; ceil20% of otherwise unambiguous families; all3arms',
                 independent_reviewer=False,interpretation='Single-agent separate-pass QC, not independent human inter-rater reliability',
                 by_arm={})
    for arm in 'ENO':
        aa = [x for x in logs if x['task_id'].startswith(arm+'_')]
        def stats(rows):
            task = dict(agreements=sum(x['first']['label']==x['second']['label'] for x in rows),n=len(rows))
            atoms = [(a,b) for x in rows for a,b in zip(x['first']['atoms'] or [],x['second']['atoms'] or [])]
            return dict(task=task,atoms=dict(agreements=sum(a==b for a,b in atoms),n=len(atoms)))
        audit['by_arm'][arm] = dict(all_second=stats(aa),random_only=stats([x for x in aa if x['random_audit']]),
                                   mandatory_only=stats([x for x in aa if x['mandatory']]))
        rows = [x for x in final if x['task_id'].startswith(arm+'_')]
        name={'E':'evidence','N':'native','O':'oracle'}[arm]
        out = ROOT/f'stage12bs_{name}_scoring_blind.parquet'
        assert not out.exists()
        pd.DataFrame(rows).to_parquet(out,index=False)
    save(ROOT/'stage12bs_second_review_log.json',dict(at=now(),reviews=logs))
    save(ROOT/'stage12bs_scoring_audit.json',audit)
    paths=list((ROOT/'audit/first_scores').glob('*.json'))+list((ROOT/'audit/second_scores').glob('*.json'))+list((ROOT/'audit/adjudications').glob('*.json'))
    dest=ROOT/'audit/correctness_seal.json';assert not dest.exists()
    save(dest,dict(at=now(),paired_outcomes_opened=False,label_hashes={str(p):sha(p) for p in paths},
                   output_hashes={str(p):sha(p) for p in ROOT.glob('stage12bs_*_scoring_blind.parquet')}))
    print('Correctness sealed; all required second reviews and adjudications complete.')


if __name__=='__main__':main()
