"""Branch-specific technical seals; Thinking correctness cannot be opened."""
import argparse,json
import pandas as pd
from scripts.stage12cr.common import ROOT,OLD,load,save,sha,now
from scripts.stage12cr.review import checked_generation,folder_for
from scripts.stage12cr.protocol import thinking_gate
from scripts.stage12br.protocol import validity

def preservation():
    groups=dict(history=load(ROOT/'audit/preserved_history_hashes.json')['files'],freeze=load(ROOT/'audit/prospective_freeze.json')['files'],source=load(ROOT/'config.json')['source_sha256'])
    for mapping in groups.values():
        for p,h in mapping.items():assert sha(p)==h,p
    return {k:len(v) for k,v in groups.items()}

def seal(phase):
    tasks=load(ROOT/'stage12cr_cot_manifest.json')['tasks'] if phase=='cot' else load(ROOT/f'stage12tr_{phase}_manifest.json')['rows']
    rows=[];hashes={};integrity=[]
    for t in tasks:
        tid=t['task_id'];g,checks=checked_generation(t);folder=folder_for(t)
        p=ROOT/'audit/technical_annotations'/f'{tid}.json';a=load(p)
        assert a['generation_sha256']==sha(folder/'generation.json')
        hashes[str(p)]=sha(p);v=validity(all(checks.values()),a['scoreable'],g['cap_hit'],a['labels']['R5'])
        raw=g['raw_decoded_response'];closed='</think>' in raw
        rows.append(dict(task_id=tid,item_id=t['item_id'],family_id=t['family_id'],arm=t['arm'],**v,
            tokens=g['tokens'],cap_hit=g['cap_hit'],normal_stop=g['normal_stop'],finish_reason=g['finish_reason'],
            closed_think=closed,final_channel_present=bool(raw.rsplit('</think>',1)[-1].strip()) if closed else t['arm']=='C',
            extracted_outcome=a['extracted_outcome'],reason=a['reason'],**a['labels'],generation_sha256=a['generation_sha256'],
            generation_path=str(folder/'generation.json'),latency_seconds=g['request_latency_seconds']))
        integrity.append(dict(task_id=tid,**checks))
    preserved=preservation()
    if phase=='cot':
        counts={k:sum(r[k] for r in rows) for k in ['INPUT_VALID','SCOREABLE','TRUNCATED_BEFORE_OUTCOME']}
        passed=counts['INPUT_VALID']==61 and counts['SCOREABLE']>=51 and counts['TRUNCATED_BEFORE_OUTCOME']<=5
        gate=dict(counts=counts,**{'pass':passed},decision='PASS' if passed else 'COT_TECHNICAL_BREAKDOWN')
        pd.DataFrame(rows).to_parquet(ROOT/'stage12cr_cot_results.parquet',index=False)
        pd.DataFrame(integrity).to_parquet(ROOT/'stage12cr_cot_integrity.parquet',index=False)
        pd.DataFrame([{k:r[k] for k in ['task_id','family_id','item_id','R1','R2','R3','R4','R5']} for r in rows]).to_parquet(ROOT/'stage12cr_cot_pathology.parquet',index=False)
        path=ROOT/'audit/denominator_seal.json'
    else:
        gate=thinking_gate(rows,phase);path=ROOT/f'stage12tr_{phase}_decision.json'
        pd.DataFrame(rows).to_parquet(ROOT/f'stage12tr_{phase}_results.parquet',index=False)
    result={**dict(at=now(),phase=phase,correctness_opened=False),**gate,
            'rows':rows,'annotation_hashes':hashes,'preservation':preserved}
    save(path,result);print({k:v for k,v in result.items() if k not in ['rows','annotation_hashes']})

def packets():
    ds=load(ROOT/'audit/denominator_seal.json');assert ds['pass']
    assert (ROOT/'audit/trace_seal.json').exists()
    for p,h in ds['annotation_hashes'].items():assert sha(p)==h
    full=load(ROOT/'stage12cr_cot_manifest.json');source={r['item_id']:r for r in full['rows']};records=[]
    for t in full['tasks']:
        r=source[t['item_id']];g=load(folder_for(t)/'generation.json')
        records.append(dict(task_id=t['task_id'],family_id=t['family_id'],item_id=t['item_id'],question=r['question'],gold=r['answer'],answer_type=r['answer_type'],options=r['options'],response=g['raw_decoded_response']))
    path=ROOT/'audit/correctness_packets/C.jsonl';assert not path.exists();path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    save(ROOT/'audit/correctness_opened.json',dict(at=now(),thinking_correctness_opened=False,packet_sha256=sha(path),denominator_seal_sha256=sha(ROOT/'audit/denominator_seal.json')))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['cot','same12','fresh12','packets']);a=p.parse_args()
    packets() if a.action=='packets' else seal(a.action)
