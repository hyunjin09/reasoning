"""Seal all technical outcomes, then permit T-only correctness packets."""
import json
import pandas as pd
from scripts.stage12ts.common import ROOT,load,save,sha,now
from scripts.stage12ts.review import all_tasks,folder_for,checked_generation
from scripts.stage12br.protocol import validity

def preservation():
    groups=dict(history=load(ROOT/'audit/preserved_history_hashes.json')['files'],
                freeze=load(ROOT/'audit/prospective_freeze.json')['files'],source=load(ROOT/'config.json')['source_sha256'])
    for mapping in groups.values():
        for p,h in mapping.items():assert sha(p)==h,p
    return {k:len(v) for k,v in groups.items()}

def seal():
    assert not (ROOT/'audit/denominator_seal.json').exists()
    rows=[];hashes={};integrity=[]
    for t in all_tasks():
        tid=t['task_id'];g,checks=checked_generation(t);folder=folder_for(t)
        p=ROOT/'audit/technical_annotations'/f'{tid}.json';a=load(p)
        assert a['generation_sha256']==sha(folder/'generation.json')
        hashes[str(p)]=sha(p);v=validity(all(checks.values()),a['scoreable'],g['cap_hit'],a['labels']['R5'])
        raw=g['raw_decoded_response'];closed='</think>' in raw
        rows.append(dict(task_id=tid,item_id=t['item_id'],family_id=t['family_id'],arm='T',**v,
            tokens=g['tokens'],cap_hit=g['cap_hit'],normal_stop=g['normal_stop'],finish_reason=g['finish_reason'],
            closed_think=closed,final_channel_present=closed and bool(raw.rsplit('</think>',1)[-1].strip()),
            extracted_outcome=a['extracted_outcome'],reason=a['reason'],**a['labels'],generation_sha256=a['generation_sha256'],
            generation_path=str(folder/'generation.json'),latency_seconds=g['request_latency_seconds']))
        integrity.append(dict(task_id=tid,**checks))
    assert len(rows)==61
    counts={k:sum(r[k] for r in rows) for k in ['INPUT_VALID','SCOREABLE','TRUNCATED_BEFORE_OUTCOME']}
    gate=load(ROOT/'audit/analysis_rules.json')['full_gate']
    passed=counts['INPUT_VALID']==gate['input_valid'] and counts['SCOREABLE']>=gate['scoreable_minimum'] and counts['TRUNCATED_BEFORE_OUTCOME']<=gate['pre_outcome_caps_maximum']
    preserved=preservation()
    pd.DataFrame(rows).to_parquet(ROOT/'stage12ts_thinking_results.parquet',index=False)
    pd.DataFrame(integrity).to_parquet(ROOT/'stage12ts_integrity_results.parquet',index=False)
    pd.DataFrame([{k:r[k] for k in ['task_id','family_id','item_id','R1','R2','R3','R4','R5']} for r in rows]).to_parquet(ROOT/'stage12ts_pathology.parquet',index=False)
    result=dict(at=now(),correctness_opened=False,counts=counts,rows=rows,annotation_hashes=hashes,preservation=preserved,
                decision='PASS' if passed else 'THINKING_TECHNICAL_BREAKDOWN',**{'pass':passed})
    save(ROOT/'audit/denominator_seal.json',result);print('Technical seal',counts,result['decision'])

def packets():
    ds=load(ROOT/'audit/denominator_seal.json');assert ds['pass']
    ts=load(ROOT/'audit/trace_seal.json')
    for p,h in {**ds['annotation_hashes'],**ts['annotation_hashes']}.items():assert sha(p)==h,p
    full=load(ROOT/'stage12ts_thinking_manifest.json');source={r['item_id']:r for r in full['rows']};records=[]
    for t in full['tasks']:
        r=source[t['item_id']];g=load(folder_for(t)/'generation.json')
        records.append(dict(task_id=t['task_id'],family_id=t['family_id'],item_id=t['item_id'],question=r['question'],gold=r['answer'],answer_type=r['answer_type'],options=r['options'],response=g['raw_decoded_response']))
    p=ROOT/'audit/correctness_packets/T.jsonl';assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    save(ROOT/'audit/correctness_opened.json',dict(at=now(),packet_sha256=sha(p),
        denominator_seal_sha256=sha(ROOT/'audit/denominator_seal.json'),trace_seal_sha256=sha(ROOT/'audit/trace_seal.json')))

if __name__=='__main__':
    import sys
    packets() if sys.argv[1]=='packets' else seal()
