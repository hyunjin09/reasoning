"""FULL-only relative exposure descriptions, with explicit right censoring."""
import os
import numpy as np
from scripts.stage9a5.common import ROOT,COT,load,save,now


def describe(rows):
    n=np.array([r['tokens'] for r in rows],dtype=float)
    complete=[r['tokens'] for r in rows if r['normal_eos']]
    result=dict(n_queries=len(rows),median_observed_tokens=float(np.median(n)),mean_observed_tokens=float(n.mean()),
        normally_ended=len(complete),capped=sum(r['at_length_cap'] for r in rows),
        median_completed_tokens=float(np.median(complete)) if complete else None,cutoffs={})
    for t in (64,128,256):
        result['cutoffs'][str(t)]=dict(ratio_to_median=t/float(np.median(n)),median_item_fraction=float(np.median(t/n)),
            median_clipped_item_fraction=float(np.median(np.minimum(1,t/n))),
            fraction_ended_before_mask=sum(r['normal_eos'] and r['tokens']-1<=t for r in rows)/len(rows),
            fraction_observed_reaching_mask=float(np.mean(n-1>t)),
            item_fractions=(t/n).tolist())
    return result


def main():
    assert os.environ.get('SLURM_JOB_ID')
    think=load(ROOT/'stage9a5_thinking_full_baseline.json');cot=load(COT/'stage9a4_qwen3_4b_full_baseline.json')
    assert {r['query_id'] for r in think['rows']}=={r['query_id'] for r in cot['rows']}
    output=dict(at=now(),status='descriptive_only' if not think['gates']['pass'] else 'complete',
        arms=dict(cot=describe(cot['rows']),thinking=describe(think['rows'])),
        observed_horizon='FULL generated-token length including final/EOS, not uncensored latent reasoning length.',
        censoring='For capped traces, t/N is an upper bound on the complete-horizon fraction. They remain included and marked.',
        invalid_baseline=not think['gates']['pass'],causal_relative_time_effect=None,
        rows=[dict(arm=arm,query_id=r['query_id'],image_id=r['image_id'],tokens=r['tokens'],normal_eos=r['normal_eos'],
                  capped=r['at_length_cap'],native_reasoning_tokens=r.get('reasoning_tokens'))
              for arm,rs in [('cot',cot['rows']),('thinking',think['rows'])] for r in rs])
    save(ROOT/'stage9a5_relative_time_analysis.json',output)
    print({a:{k:v for k,v in r.items() if k!='cutoffs'} for a,r in output['arms'].items()})


if __name__=='__main__':main()
