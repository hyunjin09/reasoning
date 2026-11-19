"""Gold-free review packets, followed by sealed baseline validity scoring."""
import argparse
import numpy as np
from scripts.stage9a3.prepare import ROOT,load,save,sha,now
from visual_reasoning.stage9a3.analysis import extract_option


def gates_and_lengths(rows):
    n=len(rows);lengths=np.array([r['tokens'] for r in rows])
    normal=np.array([r['tokens'] for r in rows if r['normal_eos']])
    cutoff=64
    if np.mean(lengths<64)>.9 and len(normal):
        cutoff=max(17,min(63,int(np.median(normal)//2)))
        if cutoff>np.quantile(normal,.95):cutoff=17
    counts=dict(cot=sum(r['cot'] for r in rows),valid_option=sum(r['option'] is not None for r in rows),
                correct=sum(r['correct'] for r in rows),normal_eos=sum(r['normal_eos'] for r in rows))
    gates=dict(cot_90pct=counts['cot']/n>=.9,valid_extraction_95pct=counts['valid_option']/n>=.95,
               accuracy_60pct=counts['correct']/n>=.6,normal_termination=counts['normal_eos']==n,
               suitable_lengths=bool(np.mean(lengths>16)>=.1))
    gates['pass']=all(gates.values())
    return dict(n_queries=n,counts=counts,accuracy=counts['correct']/n,cot_rate=counts['cot']/n,
        gates=gates,token_grid=[0,16,cutoff,None],length_summary=dict(min=int(lengths.min()),max=int(lengths.max()),
        mean=float(lengths.mean()),median=float(np.median(lengths)),p95=float(np.quantile(lengths,.95)),
        fraction_below64=float(np.mean(lengths<64)),fraction_above16=float(np.mean(lengths>16))))


def packet(key):
    tasks=[r for r in load(ROOT/'audit/inference_tasks.json')['rows'] if r['split']=='primary']
    rows=[]
    for t in tasks:
        path=ROOT/key/'full_primary/results'/t['query_id']/'full';g=load(path/'generation.json');r=load(path/'result.json')
        assert sha(path/'generation.json')==r['generation_sha256']
        rows.append(dict(query_id=t['query_id'],prompt=t['prompt'],text=g['text'],raw_option=extract_option(g['text']),
            tokens=g['tokens'],normal_eos=g['normal_eos'],generation_sha256=r['generation_sha256'],
            result_sha256=sha(path/'result.json')))
    assert len(rows)==64
    save(ROOT/f'audit/{key}_full_review_packet.json',dict(at=now(),rows=rows,blinding='No gold/count/image annotations included; model identity cannot be perfectly blinded.'))


def score(key):
    packet_path=ROOT/f'audit/{key}_full_review_packet.json';review_path=ROOT/f'audit/{key}_full_review.json'
    review=load(review_path);assert review['sealed'] and review['packet_sha256']==sha(packet_path)
    packet=load(packet_path);decisions={r['query_id']:r for r in review['rows']}
    assert set(decisions)=={r['query_id'] for r in packet['rows']}
    gold={r['query_id']:r for r in load(ROOT/'stage9a3_synthetic_dataset_manifest.json')['queries']}
    rows=[]
    for r in packet['rows']:
        d=decisions[r['query_id']];answer=gold[r['query_id']]['answer']
        assert d['option'] in ['A','B','C','D','E',None] and isinstance(d['cot'],bool)
        path=ROOT/key/'full_primary/results'/r['query_id']/'full'
        assert sha(path/'generation.json')==r['generation_sha256'] and sha(path/'result.json')==r['result_sha256']
        rows.append(dict(query_id=r['query_id'],image_id=gold[r['query_id']]['image_id'],attribute=gold[r['query_id']]['attribute'],
            cot=d['cot'],option=d['option'],raw_option=r['raw_option'],answer=answer,correct=d['option']==answer,
            raw_correct=r['raw_option']==answer,normal_eos=r['normal_eos'],tokens=r['tokens'],note=d['note']))
    result=gates_and_lengths(rows)
    save(ROOT/f'stage9a3_{key}_full_access.json',dict(at=now(),model=key,**result,rows=rows,n_images=len({r['image_id'] for r in rows}),
        raw_accuracy=sum(r['raw_correct'] for r in rows)/len(rows),review_sha256=sha(review_path),packet_sha256=sha(packet_path),
        scientific_cap=load(ROOT/f'stage9a3_mask_validation_{key}.json')['scientific_cap'],independent_unit='image'))
    print(result,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['packet','score']);ap.add_argument('--model',choices=['qwen25','qwen3'],required=True)
    args=ap.parse_args();(packet if args.action=='packet' else score)(args.model)
