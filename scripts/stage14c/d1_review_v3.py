"""D1 review entrypoint binding both passes to the common source-only unit map."""
import argparse
from scripts.stage14c.common import *
from scripts.stage14c import d1_review_arm as original


def unit_maps():
    seal=load(ROOT/'audit/D1_shared_unit_map_seal_v1.json')
    for p,h in seal['files'].items():assert sha(p)==h,p
    return {r['family_id']:r for r in rows(ROOT/'source/D1_shared_unit_map_v1.jsonl')}


def validate_units(unit_map,decision):
    assert decision['unit_map_sha256']==fingerprint(unit_map)
    if decision['review']['status']!='SCORED':return
    assert len(unit_map['atoms'])==len(decision['review']['atoms'])
    for a,r in zip(unit_map['atoms'],decision['review']['atoms']):
        assert set(r['recovered_units'])<=set(a['subfact_keys'])


def packet(model,review_pass,start,count):
    value=original.packet(model,review_pass,start,count);maps=unit_maps()
    for r in value['rows']:
        r['shared_source_unit_map']=maps[r['task']['family_id']]
        r['unit_map_sha256']=fingerprint(r['shared_source_unit_map'])
    return value


def apply(path):
    batch=load(path);maps=unit_maps();tasks={t['task_id']:t for t in all_tasks('D1')}
    for r in batch['rows']:validate_units(maps[tasks[r['task_id']]['family_id']],r)
    original.apply(path)


def close():
    maps=unit_maps()
    for t in all_tasks('D1'):
        for rp in [1,2]:validate_units(maps[t['family_id']],load(ROOT/f'scoring/D1_pass{rp}'/f"{t['task_id']}.json"))
    original.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['raw_freeze','packet','apply','close'])
    p.add_argument('--model',choices=['I','T']);p.add_argument('--review-pass',type=int,choices=[1,2],default=1)
    p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=10);p.add_argument('--path')
    a=p.parse_args()
    if a.action=='raw_freeze':original.raw_freeze()
    elif a.action=='packet':
        value=packet(a.model,a.review_pass,a.start,a.count)
        if a.path:save(a.path,value)
        else:print(json.dumps(value,ensure_ascii=False,indent=2))
    elif a.action=='apply':apply(a.path)
    else:close()
