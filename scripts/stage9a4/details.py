"""Completion, extraction, and exposure context for the final causal estimates."""
from scripts.stage9a4.common import ROOT,load,save,now


def main():
    rows=load(ROOT/'stage9a4_qwen3_4b_full_baseline.json')['rows']
    for stage in ['r1','t128','t256']:
        p=ROOT/f'audit/{stage}_scored.json'
        if p.exists():rows+=load(p)['rows']
    result={}
    for policy in sorted(set(r['policy'] for r in rows)):
        rs=[r for r in rows if r['policy']==policy]
        result[policy]=dict(n=len(rs),correct=sum(r['correct'] for r in rs),raw_correct=sum(r['raw_correct'] for r in rs),
            normal_eos=sum(r['normal_eos'] for r in rs),capped=sum(r['at_length_cap'] for r in rs),
            unscorable=sum(r['unscorable'] for r in rs),exact_full_reuses=sum(r['execution']=='reuse_full' for r in rs),
            mask_exposed_queries=sum(r['execution']=='run' for r in rs) if policy!='full' else 0,
            mean_tokens=sum(r['tokens'] for r in rs)/len(rs))
    save(ROOT/'audit/completion_and_exposure.json',dict(at=now(),primary=result,
        caveat='Mask exposure counts describe whether native rollout reaches the intervention, not independent causal observations.'))
    print(result,flush=True)


if __name__=='__main__':main()
