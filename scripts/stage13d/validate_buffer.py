import numpy as np
from scripts.stage13d.common import *
def receipt(t):
    folder=ROOT/'generations'/t['task_id'];g=load(folder/'generation.json');r=load(folder/'result.json');i=load(folder/'input.json');f=load(folder/'forced_receipt.json')
    assert r['generation_sha256']==sha(folder/'generation.json') and r['input_sha256']==sha(folder/'input.json') and g['forced_receipt_sha256']==sha(folder/'forced_receipt.json')
    assert i['task']==t and g['task_sha256']==r['task_sha256']==fingerprint(t)
    assert g['generated_token_ids']==f['forced_token_ids']==t['forced_token_ids']
    assert f['forced_decoding_step_count']==g['tokens']==t['cap']
    assert f['close_marker_position']==f['reasoning_token_count']==t['reasoning_count']
    assert f['prefix_ids']==t['answer_prefix_ids'] and t['answer_prefix']=='Final answer:'
    assert f['free_generated_tokens']==0 and f['one_token_per_step'] and f['kv_request_continuation']
    assert g['visual_tokens']==0 and g['prompt_token_ids']==t['prompt_token_ids']
    assert not set([151652,151653,151655,151656]).intersection(g['prompt_token_ids'])
    assert f['candidate_ids']==t['candidate_ids'] and all(len(f['option_token_logprobs'][a])==len(ids) for a,ids in t['candidate_ids'].items())
    assert all(np.isfinite(v) and v<=0 for values in f['option_token_logprobs'].values() for v in values)
    return f
def main():
    tasks=[t for t in load(ROOT/'stage13d_buffer_forced_sequences.json')['tasks'] if t['phase']=='technical_buffer'];checks=[];comparisons=[]
    for t in tasks:
        f=receipt(t);checks.append(dict(task_id=t['task_id'],passed=True,reasoning_count=t['reasoning_count'],forced_steps=f['forced_decoding_step_count'],free_tokens=0,receipt_sha256=sha(ROOT/'generations'/t['task_id']/'forced_receipt.json')))
    for t in tasks:
        if t['replicate']!=1:continue
        prior=next(x for x in tasks if x['item_id']==t['item_id'] and x['condition']==t['condition'] and x['replicate']==0)
        a=receipt(prior);b=receipt(t);delta=max(abs(x-y) for k in a['option_token_logprobs'] for x,y in zip(a['option_token_logprobs'][k],b['option_token_logprobs'][k]))
        comparisons.append(dict(item_id=t['item_id'],max_abs_difference=delta,passed=delta<=1e-5))
    passed=all(x['passed'] for x in checks+comparisons)
    save(ROOT/'stage13d_buffer_technical_validation.json',dict(at=now(),passed=passed,status='VALID' if passed else 'IMMEDIATE_BUFFER_ASSAY_BLOCKED',checks=checks,reproducibility=comparisons,scientific_outcomes_used=False,open_ended_scope='Technical sequence scoring only; no scientific inclusion'))
    print('BUFFER_VALIDATION',passed,comparisons)
if __name__=='__main__':main()
