"""Audit raw independent evidence judgments before any repair or outcome opening."""
from collections import Counter
from scripts.stage11b.common import ROOT,load,save,sha,now

FIELDS=['sufficiency','facts_true','atomic_and_minimal','no_answer_leak','question_requires_image']
def agreement(a,b):
    n=len(a);ca=Counter(a);cb=Counter(b)
    observed=sum(x==y for x,y in zip(a,b))/n if n else None
    expected=sum(ca[k]*cb[k] for k in ca.keys()|cb.keys())/n**2 if n else None
    return dict(n=n,agreement=observed,kappa=(observed-expected)/(1-expected) if n and expected<1 else None,
        counts_a=dict(ca),counts_b=dict(cb),kappa_undefined=n==0 or expected==1)

def accepted(row):
    return row['sufficiency']=='SUFFICIENT' and all(row[k] for k in FIELDS[1:])

def main():
    proposal=ROOT/'packets/discovery_sufficiency.json';packet=load(proposal)['rows'];by={r['item_id']:r for r in packet}
    reviews={}
    for who in ['a','b']:
        p=ROOT/'annotations'/f'discovery_sufficiency_{who}.json';x=load(p)
        assert x['sealed'] and not x['model_outcomes_opened'] and x['proposal_sha256']==sha(proposal)
        assert len(x['rows'])==len(by)==128 and len({r['item_id'] for r in x['rows']})==128
        for r in x['rows']:
            assert r['family_id']==by[r['item_id']]['family_id'] and r['image_inspected']
            assert r['sufficiency'] in ['SUFFICIENT','INSUFFICIENT','AMBIGUOUS']
            assert all(isinstance(r[k],bool) for k in FIELDS[1:])
            assert r['reason'] and r['solution_check']
        reviews[who]={r['item_id']:r for r in x['rows']}
    positives=[r['item_id'] for r in packet if r['facts']]
    summaries={}
    for label,ids in [('all',list(by)),('proposed_nonempty_evidence',positives)]:
        summaries[label]={k:agreement([reviews['a'][i][k] for i in ids],[reviews['b'][i][k] for i in ids]) for k in FIELDS}
        summaries[label]['eligible_quality_conjunction']=agreement([accepted(reviews['a'][i]) for i in ids],[accepted(reviews['b'][i]) for i in ids])
    needs=[dict(item_id=i,proposal=by[i],a=reviews['a'][i],b=reviews['b'][i]) for i in positives if not all(accepted(reviews[w][i]) for w in ['a','b'])]
    save(ROOT/'audit/raw_sufficiency_summary.json',dict(at=now(),agreement=summaries,
        proposed_evidence_count=len(positives),both_passed_before_adjudication=len(positives)-len(needs),
        review_sha256={w:sha(ROOT/'annotations'/f'discovery_sufficiency_{w}.json') for w in ['a','b']},
        model_text_or_correctness_opened=False,reviewer_description='Two independent model-agent passes; own prior proposal exposure disclosed, no human-reliability claim'))
    save(ROOT/'audit/evidence_quality_decisions_needed.json',dict(at=now(),rows=needs,source_outcomes_opened=False))
    print('PROPOSED',len(positives),'BOTH_QUALITY_PASS',len(positives)-len(needs),'NEED_DECISION',len(needs))

if __name__=='__main__':main()
