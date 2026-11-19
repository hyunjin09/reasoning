"""Gold-free literal review packets and sealed FULL baseline scoring."""
import argparse
import numpy as np
from scripts.stage9a4.common import ROOT,OLD,load,save,sha,now
from scripts.stage9a4.decisions import baseline_gates
from scripts.stage9a3.literal_review import terminal_option
from visual_reasoning.stage9a3.analysis import extract_option


def packet(stage):
    mpath=ROOT/f'audit/{stage}_manifest.json';m=load(mpath);rows=[]
    base={r['query_id']:r for r in load(ROOT/'audit/full_review.json')['rows']} if stage!='full' else {}
    for r in m['rows']:
        g=load(r['generation_path']);receipt=load(r['result_path'])
        assert receipt['generation_sha256']==sha(r['generation_path'])
        auto=base[r['query_id']]['option'] if r['execution']=='reuse_full' else terminal_option(g['text'])
        rows.append(dict(query_id=r['query_id'],policy=r['policy'],text=g['text'],tokens=g['tokens'],normal_eos=g['normal_eos'],
            at_length_cap=g['at_length_cap'],automatic_option=auto,raw_option=extract_option(g['text']),
            requires_manual=stage=='full' or (r['execution']!='reuse_full' and auto is None),
            generation_sha256=sha(r['generation_path']),result_sha256=sha(r['result_path'])))
    save(ROOT/f'audit/{stage}_review_packet.json',dict(at=now(),rows=rows,manifest_sha256=sha(mpath),gold_omitted=True,
         literal_adapter_sha256=sha('scripts/stage9a3/literal_review.py')))
    print('PACKET',stage,len(rows),'manual',sum(r['requires_manual'] for r in rows))


def seal(stage):
    ppath=ROOT/f'audit/{stage}_review_packet.json';p=load(ppath)
    assert p['literal_adapter_sha256']==sha('scripts/stage9a3/literal_review.py')
    needed={(r['query_id'],r['policy']) for r in p['rows'] if r['requires_manual']}
    manual=load(ROOT/f'audit/{stage}_manual_review.json') if needed else dict(rows=[],gold_opened=False,sealed=True)
    assert manual['sealed'] and not manual['gold_opened']
    if needed:assert manual['packet_sha256']==sha(ppath)
    decisions={(r['query_id'],r['policy']):r for r in manual['rows']};assert set(decisions)==needed
    rows=[]
    for r in p['rows']:
        d=decisions.get((r['query_id'],r['policy']),dict(option=r['automatic_option'],note='Frozen terminal adapter or sealed FULL reuse.'))
        assert d['option'] in list('ABCDE')+[None]
        if stage=='full':assert isinstance(d['cot'],bool)
        rows.append(dict(r,**{k:v for k,v in d.items() if k not in r or k in ('option','cot','note')}))
    save(ROOT/f'audit/{stage}_review.json',dict(at=now(),rows=rows,sealed=True,gold_opened=False,packet_sha256=sha(ppath)))


def scored_rows(stage):
    mpath=ROOT/f'audit/{stage}_manifest.json';m=load(mpath)
    ppath=ROOT/f'audit/{stage}_review_packet.json';p=load(ppath);v=load(ROOT/f'audit/{stage}_review.json')
    assert v['sealed'] and v['packet_sha256']==sha(ppath) and p['manifest_sha256']==sha(mpath)
    gold={r['query_id']:r for r in load(OLD/'stage9a3_synthetic_dataset_manifest.json')['queries']}
    reviewed={(r['query_id'],r['policy']):r for r in v['rows']};out=[]
    assert set(reviewed)=={(r['query_id'],r['policy']) for r in m['rows']}
    for r in m['rows']:
        d=reviewed[r['query_id'],r['policy']];assert sha(r['generation_path'])==d['generation_sha256']
        assert sha(r['result_path'])==d['result_sha256'];q=gold[r['query_id']]
        out.append(dict(r,**{k:d[k] for k in ['option','raw_option','tokens','normal_eos','at_length_cap','generation_sha256']},
            answer=q['answer'],attribute=q['attribute'],correct=d['option']==q['answer'],raw_correct=d['raw_option']==q['answer'],
            cot=d.get('cot'),unscorable=d['option'] is None))
    return out


def score_full():
    rows=scored_rows('full');n=len(rows);assert n==64
    c=dict(correct=sum(r['correct'] for r in rows),cot=sum(r['cot'] for r in rows),
        valid_final=sum(r['option'] is not None for r in rows),normal_eos=sum(r['normal_eos'] for r in rows),
        capped=sum(r['at_length_cap'] for r in rows),unscorable=sum(r['unscorable'] for r in rows))
    lengths=[r['tokens'] for r in rows];noop=load(ROOT/'audit/full_noop_validation.json')
    result=dict(at=now(),n_queries=n,n_images=32,counts=c,rates={k:v/n for k,v in c.items()},
        gates=baseline_gates(rows,noop['pass_all']),rows=rows,raw_accuracy=sum(r['raw_correct'] for r in rows)/n,
        length_summary=dict(mean=float(np.mean(lengths)),median=float(np.median(lengths)),min=min(lengths),max=max(lengths)),
        review_sha256=sha(ROOT/'audit/full_review.json'),noop_sha256=sha(ROOT/'audit/full_noop_validation.json'))
    save(ROOT/'stage9a4_qwen3_4b_full_baseline.json',result);print({k:v for k,v in result.items() if k!='rows'})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['packet','seal','score_full']);p.add_argument('stage',nargs='?',default='full');a=p.parse_args()
    if a.action=='score_full':score_full()
    else:globals()[a.action](a.stage)
