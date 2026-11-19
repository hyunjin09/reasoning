"""Seal response-only sanity/full validity before releasing any correctness packets."""
import argparse
import json
import pandas as pd
from scripts.stage12c.common import ROOT,load,save,sha,now
from scripts.stage12c.review import checked_generation
from scripts.stage12c.protocol import technical_gate
from scripts.stage12br.protocol import validity


def preservation():
    groups=dict(history=load(ROOT/'audit/preserved_history_hashes.json')['files'],
                freeze=load(ROOT/'audit/prospective_freeze.json')['files'],
                source=load(ROOT/'config.json')['source_sha256'])
    for mapping in groups.values():
        for p,h in mapping.items():assert sha(p)==h,p
    return {k:len(v) for k,v in groups.items()}


def seal(phase):
    full=load(ROOT/'stage12c_frozen_bottleneck_manifest.json')
    ids=set(full['sanity_ids']) if phase=='sanity' else {r['item_id'] for r in full['rows']}
    dest=ROOT/('stage12c_technical_sanity.json' if phase=='sanity' else 'audit/denominator_seal.json')
    assert not dest.exists()
    preserved=preservation();rows=[];hashes={}
    for t in full['tasks']:
        if t['item_id'] not in ids:continue
        tid=t['task_id'];g,checks=checked_generation(t)
        p=ROOT/'audit/technical_annotations'/f'{tid}.json';a=load(p)
        assert a['generation_sha256']==sha(ROOT/'generations'/tid/'generation.json')
        hashes[str(p)]=sha(p);labels=a['labels']
        v=validity(bool(all(checks.values())),a['scoreable'],g['cap_hit'],labels['R5'])
        rows.append(dict(task_id=tid,item_id=t['item_id'],family_id=t['family_id'],arm=t['arm'],**v,
            CAP_AFTER_OUTCOME=v['cap_after_outcome'],stop_reason=g['finish_reason'],tokens=g['tokens'],
            cap_hit=g['cap_hit'],normal_stop=g['normal_stop'],extracted_outcome=a['extracted_outcome'],
            reason=a['reason'],**labels,checks_json=json.dumps(checks,sort_keys=True),
            generation_sha256=a['generation_sha256']))
    gate=technical_gate({a:[r for r in rows if r['arm']==a] for a in 'CT'})
    result=dict(at=now(),phase=phase,correctness_opened=False,**gate,rows=rows,
                annotation_hashes=hashes,preservation=preserved,
                decision='PASS' if gate['pass'] else 'TECHNICAL_STOP')
    if phase=='full':
        for arm,name in [('C','cot'),('T','thinking')]:
            pd.DataFrame([r for r in rows if r['arm']==arm]).to_parquet(ROOT/f'stage12c_{name}_results.parquet',index=False)
        result['result_hashes']={str(ROOT/f'stage12c_{name}_results.parquet'):sha(ROOT/f'stage12c_{name}_results.parquet') for name in ['cot','thinking']}
    save(dest,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['rows','annotation_hashes']},indent=2))


def packets():
    ds=load(ROOT/'audit/denominator_seal.json');assert ds['pass']
    assert (ROOT/'audit/trace_seal.json').exists(), 'Visible evidence annotation precedes correctness opening'
    for p,h in {**ds['annotation_hashes'],**ds['result_hashes']}.items():assert sha(p)==h
    full=load(ROOT/'stage12c_frozen_bottleneck_manifest.json');source={r['item_id']:r for r in full['rows']}
    for arm in 'CT':
        path=ROOT/'audit/correctness_packets'/f'{arm}.jsonl';assert not path.exists();records=[]
        for t in full['tasks']:
            if t['arm']!=arm:continue
            r=source[t['item_id']];g=load(ROOT/'generations'/t['task_id']/'generation.json')
            records.append(dict(task_id=t['task_id'],family_id=t['family_id'],item_id=t['item_id'],
                question=r['question'],gold=r['answer'],answer_type=r['answer_type'],options=r['options'],response=g['raw_decoded_response']))
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    save(ROOT/'audit/correctness_opened.json',dict(at=now(),denominator_seal_sha256=sha(ROOT/'audit/denominator_seal.json'),
        arm_separated=True,packet_hashes={a:sha(ROOT/'audit/correctness_packets'/f'{a}.jsonl') for a in 'CT'}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['sanity','full','packets']);a=p.parse_args()
    packets() if a.action=='packets' else seal(a.action)
