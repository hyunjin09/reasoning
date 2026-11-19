"""Descriptive D1 recovery and precision, joined to already-sealed main outcomes."""
from collections import Counter,defaultdict
from scripts.stage14c.common import *


def ratio(a,b):return a/b if b else None
def mean(values):
    values=[v for v in values if v is not None]
    return sum(values)/len(values) if values else None


def summarize(items):
    scored=[r for r in items if r['status']=='SCORED'];counts=Counter(r['status'] for r in items)
    return dict(n=len(items),statuses=dict(counts),scored_families=len(scored),
         full_E_star_recovery=sum(r['full_E_star_recovery'] for r in scored),
         exact_atom_recall_macro=mean([r['exact_atom_recall'] for r in scored]),
         exact_atom_recall_micro=ratio(sum(r['exact_atoms'] for r in scored),sum(r['atoms'] for r in scored)),
         subfact_recall_macro=mean([r['subfact_recall'] for r in scored]),
         subfact_recall_micro=ratio(sum(r['recovered_subfacts'] for r in scored),sum(r['subfacts'] for r in scored)),
         structured_subfact_recall_macro=mean([ratio(r['recovered_structured_subfacts'],r['structured_subfacts']) for r in scored]),
         structured_subfact_recall_micro=ratio(sum(r['recovered_structured_subfacts'] for r in scored),sum(r['structured_subfacts'] for r in scored)),
         targeted_precision_macro=mean([r['targeted_precision'] for r in scored]),
         targeted_precision_macro_n=sum(r['targeted_precision'] is not None for r in scored),
         targeted_precision_micro=ratio(sum(r['required_visual_facts'] for r in scored),sum(r['asserted_visual_facts'] for r in scored)),
         asserted_visual_facts=sum(r['asserted_visual_facts'] for r in scored),
         claim_classes=dict(sum((Counter(r['claim_classes']) for r in scored),Counter())),
         full_recovery_bounds=[sum(r['full_E_star_recovery'] for r in scored)/len(items),
             (sum(r['full_E_star_recovery'] for r in scored)+len(items)-len(scored))/len(items)] if items else None)


def main():
    for name in ['primary_analysis_seal.json','D1_scoring_seal.json']:
        for p,h in load(ROOT/'audit'/name)['files'].items():assert sha(p)==h,p
    data=rows(ROOT/'scoring/D1_scored_outcomes.jsonl');assert len(data)==600
    targets={r['family_id']:r for r in rows(ROOT/'source/D1_review_schema_v1.jsonl')}
    tasks={t['task_id']:t for t in all_tasks('D1')}
    primary={(r['benchmark'],r['family_id'],str(r['item_id'])):r for r in rows(ROOT/'scoring/scored_outcomes.jsonl')}
    joined=[];groups=defaultdict(list);tabs=Counter()
    for row in data:
        r=dict(row);t=tasks[r['task_id']];target=targets[r['family_id']]
        score=load(ROOT/'scoring/D1_pass2'/f"{r['task_id']}.json")['review']
        if r['status']=='SCORED':
            structural=[(a,z) for a,z in zip(target['atoms'],score['atoms']) if a['atom_type']=='structured_layout']
            r['structured_subfacts']=sum(a['subfact_count'] for a,z in structural)
            r['recovered_structured_subfacts']=sum(len(z['recovered_units']) for a,z in structural)
            recovery='FULL' if r['full_E_star_recovery'] else 'PARTIAL' if r['recovered_subfacts'] else 'NONE'
        else:recovery=r['status']
        main_row=primary[(r['benchmark'],r['family_id'],str(t['item_id']))];m=r['model']
        r.update(native_outcome=main_row[m+'_img'],E_star_outcome=main_row[m+'_E'],recovery_class=recovery)
        tabs[(r['benchmark'],m,recovery,r['native_outcome'],r['E_star_outcome'])]+=1
        joined.append(r);groups[(r['benchmark'],m)].append(r)
    result=dict(at=now(),panels=[dict(benchmark=b,model=m,**summarize(rr)) for (b,m),rr in sorted(groups.items())],
        crosstabs=[dict(benchmark=b,model=m,recovery_class=rc,native_outcome=n,E_star_outcome=e,n=count)
                  for (b,m,rc,n,e),count in sorted(tabs.items())],
        interpretation='Separate prompted evidence elicitation. A recovered fact is not proof that the original native solver internally knew it. Recovery/rescue associations are descriptive, not a causal mechanism.',
        review='Two-pass same-agent; no independent annotation reliability. Missing/unresolved probes excluded from scored means and shown explicitly; no recovery imputation.',
        aggregation='Each source family appears once per model/task. Macro means weight families equally; micro rates show internal information volume. Undefined precision has no asserted-fact denominator and stays undefined.')
    save(ROOT/'analysis/optional_diagnostics.json',result)
    write_rows(ROOT/'analysis/D1_joined_outcomes.jsonl',joined)
    paths=[ROOT/'analysis/optional_diagnostics.json',ROOT/'analysis/D1_joined_outcomes.jsonl']
    save(ROOT/'audit/D1_analysis_seal.json',dict(at=now(),files={str(p):sha(p) for p in paths}))


if __name__=='__main__':main()
