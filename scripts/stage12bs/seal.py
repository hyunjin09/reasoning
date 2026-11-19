"""Seal response-only validity and denominators before emitting any gold packets."""
import json
from pathlib import Path
import pandas as pd
from scripts.stage12bs.common import ROOT, load, save, sha, now
from scripts.stage12bs.review import checked_generation, origin_for
from scripts.stage12bs.protocol import full_gate
from scripts.stage12br.protocol import validity


def preservation():
    groups = {
        'history': load(ROOT/'audit/preserved_history_hashes.json')['files'],
        'freeze': load(ROOT/'audit/prospective_freeze.json')['files'],
        'source': load(ROOT/'config.json')['source_sha256'],
    }
    for hashes in groups.values():
        assert all(sha(p)==h for p,h in hashes.items())
    return {k:len(v) for k,v in groups.items()}


def main():
    dest=ROOT/'audit/denominator_seal.json'
    assert not dest.exists(), 'Never replace sealed denominators'
    preserved=preservation()
    full=load(ROOT/'stage12bs_full_manifest.json')
    assert len(full['tasks'])==183 and len(full['reuse'])==72
    reuse={r['task_id']:r for r in full['reuse']}
    rows=[]; hashes={}
    for t in full['tasks']:
        tid=t['task_id']; g,checks=checked_generation(t)
        p=ROOT/'audit/technical_annotations'/f'{tid}.json'; a=load(p)
        folder=origin_for(tid)/'generations'/tid
        assert a['generation_sha256']==sha(folder/'generation.json')
        if tid in reuse:
            for f in ['generation','input','result']:
                assert sha(folder/f'{f}.json')==reuse[tid][f'{f}_sha256']
        hashes[str(p)]=sha(p)
        labels=a.get('labels') or {f'R{i}':None for i in range(1,6)}
        assert t['arm']=='E' or all(isinstance(v,bool) for v in labels.values())
        v=validity(bool(all(checks.values())),a['scoreable'],g['cap_hit'],bool(labels['R5']))
        rows.append(dict(task_id=tid,item_id=t['item_id'],family_id=t['family_id'],arm=t['arm'],
            **v,CAP_AFTER_OUTCOME=v['cap_after_outcome'],stop_reason=g['finish_reason'],
            tokens=g['tokens'],cap_hit=g['cap_hit'],normal_stop=g['normal_stop'],
            extracted_outcome=a['extracted_outcome'],reason=a['reason'],**labels,
            checks_json=json.dumps(checks,sort_keys=True),reused=tid in reuse,
            generation_path=str(folder/'generation.json'),generation_sha256=a['generation_sha256']))
    assert len(rows)==183
    by_family={r['family_id']:{a:next(z for z in rows if z['family_id']==r['family_id'] and z['arm']==a) for a in 'ENO'} for r in rows}
    eligible=lambda r:r['INPUT_VALID'] and r['SCOREABLE']
    ns=sorted(f for f,aa in by_family.items() if eligible(aa['N']))
    complete=sorted(f for f,aa in by_family.items() if all(eligible(r) for r in aa.values()))
    gate=full_gate({a:[r for r in rows if r['arm']==a] for a in 'ENO'})
    out=ROOT/'stage12bs_integrity_results.parquet'
    pd.DataFrame(rows).to_parquet(out,index=False)
    seal=dict(at=now(),correctness_opened=False,generation_calls_complete=183,new_calls=111,reused_calls=72,
        native_scoreable_families=ns,complete_profile_families=complete,
        technical_unresolved_families=sorted(set(by_family)-set(complete)),full_gate=gate,
        annotation_hashes=hashes,integrity_sha256=sha(out),preservation=preserved)
    save(dest,seal)
    print(json.dumps({k:v for k,v in seal.items() if k not in ['annotation_hashes']},indent=2))


def packets():
    seal=load(ROOT/'audit/denominator_seal.json')
    assert sha(ROOT/'stage12bs_integrity_results.parquet')==seal['integrity_sha256']
    assert all(sha(p)==h for p,h in seal['annotation_hashes'].items())
    full=load(ROOT/'stage12bs_full_manifest.json'); source={r['item_id']:r for r in full['rows']}
    for arm in 'ENO':
        path=ROOT/'audit/correctness_packets'/f'{arm}.jsonl'
        assert not path.exists()
        records=[]
        for t in full['tasks']:
            if t['arm']!=arm:continue
            r=source[t['item_id']]; g=load(origin_for(t['task_id'])/'generations'/t['task_id']/'generation.json')
            packet=dict(task_id=t['task_id'],family_id=t['family_id'],item_id=t['item_id'],response=g['raw_decoded_response'])
            if arm=='E':packet.update(request=t['prompt'],facts=r['facts'])
            else:packet.update(question=t['prompt'],gold=r['answer'],answer_type=r['answer_type'],options=r['options'])
            records.append(packet)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    save(ROOT/'audit/correctness_opened.json',dict(at=now(),denominator_seal_sha256=sha(ROOT/'audit/denominator_seal.json'),
        arm_separated=True,packet_hashes={a:sha(ROOT/'audit/correctness_packets'/f'{a}.jsonl') for a in 'ENO'}))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['seal','packets']);a=p.parse_args()
    main() if a.action=='seal' else packets()
