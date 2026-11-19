"""Gather immutable G2 technical evidence without gold-aware grading."""
import argparse
import math
from collections import defaultdict
from scripts.stage14c.common import *
from scripts.stage14c.response_protocol import extract,repetition
from scripts.stage14c.oom_policy import missing_path


def checked(task):
    p=checked_result(task)
    if not p:return None
    inp=load(p.parent/'input.json');g=load(p.parent/'generation.json')
    cfg=load(ROOT/'spec/model_and_recipe_identity.json')
    assert inp['task']==task and g['task_sha256']==fingerprint(task)
    assert inp['image_present']==bool(task['image_reference'])==(g['visual_tokens']>0)
    assert g['seed']==task['seed'] and g['sampling']==dict(cfg['models'][task['model_key']]['recipe'],max_tokens=task['cap'])
    assert g['tokens']==len(g['generated_token_ids'])<=task['cap']
    assert g['finish_reason'] in ['stop','length']
    assert g['cap_hit']==(g['finish_reason']=='length')
    assert g['config_sha256']==sha(ROOT/'spec/model_and_recipe_identity.json')
    return p,inp,g


def collect():
    tasks=all_tasks('preflight');items=[];pending=[]
    for t in tasks:
        result=checked(t)
        if not result:
            if not missing_path(t).exists():pending.append(t['task_id']);continue
            items.append(dict(task_id=t['task_id'],benchmark=t['benchmark'],model=t['model_key'],technical_missing=True,committed=False));continue
        p,inp,g=result
        if t['condition']=='seed_replay':continue
        x=extract(g['raw_decoded_response'],t['model_key'],t['answer_kind'],g['finish_reason'])
        rep=repetition(g['generated_token_ids'])
        item=dict(task_id=t['task_id'],benchmark=t['benchmark'],model=t['model_key'],condition=t['condition'],
                  generation_sha256=sha(p.parent/'generation.json'),extraction=x,committed=x['committed'],
                  cap_hit=g['cap_hit'],finish_reason=g['finish_reason'],repetition=rep,tokens=g['tokens'],
                  latency=g['request_latency_seconds'],technical_missing=False,source_kind=t['answer_kind'],
                  final_body=g['raw_decoded_response'].rsplit('</think>',1)[-1],correctness_used=False)
        items.append(item)
    if pending:
        print('PENDING',len(pending),'of',len(tasks));return
    save(ROOT/'audit/g2_technical_response_packet_v1.json',dict(at=now(),rows=items,correctness_used=False))
    print('Collected',len(items),'science responses. Manual response-only review required before close.')


def close():
    packet=load(ROOT/'audit/g2_technical_response_packet_v1.json');review=load(ROOT/'audit/g2_response_review_v1.json')
    assert review['packet_sha256']==sha(ROOT/'audit/g2_technical_response_packet_v1.json') and not review['correctness_used']
    decisions={r['task_id']:r for r in review['rows']}
    assert set(decisions)=={r['task_id'] for r in packet['rows']}
    groups=defaultdict(list)
    for r in packet['rows']:
        d=decisions[r['task_id']];assert d['response_only_reviewed']
        groups[r['benchmark']+'|'+r['model']].append(dict(r,**d))
    gates={};overall=True
    for name,rs in groups.items():
        n=len(rs);committed=sum(r['committed'] for r in rs);caps=sum(r.get('cap_hit',False) and not r['committed'] for r in rs)
        repetitions=sum(r['repetition_pathology'] for r in rs);missing=sum(r['technical_missing'] for r in rs)
        passed=committed>=math.ceil(.9*n) and caps<=1 and repetitions<=1 and missing==0
        gates[name]=dict(n=n,committed=committed,minimum=math.ceil(.9*n),prefinal_caps=caps,repetition_pathologies=repetitions,technical_missing=missing,passed=passed);overall &= passed
    replay={}
    for m in ['I','T']:
        ts=[t for t in all_tasks('preflight') if t['model_key']==m and t['condition']=='seed_replay']
        records=[checked(t) for t in ts]
        replay[m]=len(records)==2 and all(records) and records[0][2]['generated_token_ids']==records[1][2]['generated_token_ids']
    overall &= all(replay.values())
    save(ROOT/'audit/preflight_validation.json',dict(at=now(),**{'pass':bool(overall)},groups=gates,exact_synthetic_seed_replay=replay,
        correctness_used=False,integrity_checks_fraction=1.,score_schema_coverage=1.,review_sha256=sha(ROOT/'audit/g2_response_review_v1.json'),
        failure_action='STOP scientific release; preserve outputs and no recipe tuning by correctness'))
    print(json.dumps(dict(passed=bool(overall),groups=gates,replay=replay),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['collect','close']);a=p.parse_args()
    collect() if a.action=='collect' else close()
