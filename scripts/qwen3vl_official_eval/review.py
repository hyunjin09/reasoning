"""Completion-only evidence packets and user-specified decision gate."""
import argparse
from pathlib import Path
import numpy as np
from scripts.qwen3vl_official_eval.common import ROOT,load,save,sha,now
from scripts.stage11cr.protocol import repetition_metrics

def packet(condition):
    m=load(ROOT/'qwen3vl_official_sanity_manifest.json');rows=[]
    for r in m['cases']:
        p=ROOT/'results'/condition/r['item_id']/'generation.json'
        if not (p.parent/'result.json').exists():continue
        receipt=load(p.parent/'result.json');assert receipt['generation_sha256']==sha(p)
        assert receipt['input_sha256']==sha(p.parent/'input.json')
        g=load(p);assert g['manifest_sha256']==sha(ROOT/'qwen3vl_official_sanity_manifest.json')
        rows.append(dict(item_id=r['item_id'],condition=condition,generation_path=str(p),generation_sha256=sha(p),
            tokens=g['tokens'],cap=g['at_length_cap'],stop=g['normal_eos_or_official_stop'],
            repetition=repetition_metrics(g['generated_token_ids']),head=g['raw_decoded_response'][:500],
            tail=g['raw_decoded_response'][-2400:],think_end='</think>' in g['raw_decoded_response']))
    path=ROOT/'audit/review_packets'/f"{condition}_{now().replace(':','').replace('.','')}.json"
    save(path,dict(at=now(),condition=condition,rows=rows,expected=12,no_accuracy=True));print(path)
    for r in rows:print(r['item_id'],r['tokens'],'stop',r['stop'],'cap',r['cap'],r['repetition'])

def seal(condition,decisions):
    d=load(decisions);m=load(ROOT/'qwen3vl_official_sanity_manifest.json')
    expected={r['item_id'] for r in m['cases']};assert len(d['rows'])==12 and {r['item_id'] for r in d['rows']}==expected
    rows=[]
    for r in d['rows']:
        p=ROOT/'results'/condition/r['item_id']/'generation.json';g=load(p)
        assert r['generation_sha256']==sha(p) and not g['budget_interrupted']
        assert isinstance(r['committed_final'],bool) and isinstance(r['pathological_repetition'],bool) and r['reason']
        if r['committed_final']:
            text=g['raw_decoded_response'];assert r['quote'] and r['quote'] in text
            if condition=='official_thinking':assert '</think>' in text and r['quote'] in text.split('</think>')[-1]
        rows.append(dict(g,**{k:v for k,v in r.items() if k not in ['item_id','generation_sha256']},generation_sha256=sha(p)))
    summary=dict(n=12,caps=sum(r['at_length_cap'] for r in rows),stops=sum(r['normal_eos_or_official_stop'] for r in rows),
        finals=sum(r['committed_final'] for r in rows),pathologies=sum(r['pathological_repetition'] for r in rows),
        tokens=dict(median=float(np.median([r['tokens'] for r in rows])),
            q25_q75=np.percentile([r['tokens'] for r in rows],[25,75]).tolist(),max=max(r['tokens'] for r in rows)),
        request_latency_seconds_median=float(np.median([r['batch_request_latency_seconds'] for r in rows])),
        correctness_evaluated=False)
    save(ROOT/'annotations'/f'{condition}_review.json',dict(at=now(),frozen=True,rows=rows,summary=summary,accuracy_used=False))
    print(condition,summary)

def gate():
    d=load(ROOT/'annotations/official_instruct_direct_review.json');t=load(ROOT/'annotations/official_thinking_review.json')
    s=d['summary'];passed=s['finals']>=10 and s['caps']<=1 and s['pathologies']<=1
    save(ROOT/'audit/sanity_technical_gate.json',dict(at=now(),instruct_gate_pass=passed,conditions=dict(instruct=d['summary'],thinking=t['summary']),
        decision='OFFICIAL_PROTOCOL_VALID' if passed else 'OFFICIAL_PROTOCOL_STILL_INVALID',
        rule='12 required; committed finals>=10, cap hits<=1, repetition pathologies<=1. No gate changes.',
        correctness_used=False,next_action='Only frozen bounded ablation within remaining3GPUh' if passed else 'No further prompt/decoding tuning; review runtime faithfulness and stop'))
    print('OFFICIAL_GATE',passed)

if __name__=='__main__':
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
    a=s.add_parser('packet');a.add_argument('condition')
    a=s.add_parser('seal');a.add_argument('condition');a.add_argument('decisions')
    s.add_parser('gate');a=p.parse_args()
    if a.cmd=='packet':packet(a.condition)
    elif a.cmd=='seal':seal(a.condition,a.decisions)
    else:gate()
