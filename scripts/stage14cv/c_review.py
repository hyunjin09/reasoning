"""Explicit response-mode and two-pass source-fidelity review; no auto labels."""
import argparse
from scripts.stage14cv.common import *
from scripts.stage14c.d1_scoring_v2 import validate_review,metrics

MODES={'BARE_ANSWER','EVIDENCE_ONLY','MIXED','REFUSAL_OR_OTHER','UNRESOLVED'}


def targets():return {r['family_id']:r for r in rows(ROOT/'source_qc/frozen_fidelity_targets.jsonl')}


def response(t):
    p=checked(t);assert p,t['task_id'];g=load(p.parent/'generation.json');raw=g['raw_decoded_response']
    closed=t['model_key']!='T' or '</think>' in raw
    return dict(body=raw.rsplit('</think>',1)[-1].replace('<|im_end|>','').strip() if closed else '',
                closed=closed,finish_reason=g['finish_reason'],cap_hit=g['cap_hit'],tokens=g['tokens'],
                generation_sha256=sha(p.parent/'generation.json'))


def freeze():
    assert (ROOT/'audit/R_primary_seal_v1.json').exists()
    files={};responses=[]
    for t in tasks('C'):
        p=checked(t);assert p,t['task_id']
        for q in [p,p.parent/'generation.json',p.parent/'input.json']:files[str(q)]=sha(q)
        responses.append(dict(task_id=t['task_id'],review_id=fingerprint(['stage14cv-C-review',t['task_id']]),**response(t)))
    save(ROOT/'audit/C_raw_seal_v1.json',dict(at=now(),calls=800,files=files))
    write_rows(ROOT/'scoring/C_response_index_v1.jsonl',sorted(responses,key=lambda r:r['review_id']))


def modes_packet():
    assert (ROOT/'audit/C_raw_seal_v1.json').exists()
    groups={}
    for r in rows(ROOT/'scoring/C_response_index_v1.jsonl'):
        value={k:r[k] for k in ['body','closed','finish_reason','cap_hit']};key=fingerprint(value)
        if key not in groups:groups[key]=dict(mode_review_id=key,**value,task_ids=[])
        groups[key]['task_ids'].append(r['task_id'])
    save(ROOT/'scoring/C_mode_packet_v1.json',dict(at=now(),groups=sorted(groups.values(),key=lambda r:r['mode_review_id']),
         source_gold_and_condition_absent_from_review_display=True))
    print('Mode groups',len(groups))


def modes_apply(path):
    groups={r['mode_review_id']:r for r in load(ROOT/'scoring/C_mode_packet_v1.json')['groups']}
    for d in load(path)['decisions']:
        g=groups[d['mode_review_id']];assert d['mode'] in MODES and d['reason'].strip()
        assert g['closed'] or d['mode']=='UNRESOLVED'
        for tid in g['task_ids']:
            save(ROOT/'scoring/C_contract_modes'/f'{tid}.json',dict(at=now(),task_id=tid,mode=d['mode'],reason=d['reason'],
                 mode_review_id=d['mode_review_id'],reviewer='main_agent',source_or_gold_used=False))


def modes_close():
    files={}
    for t in tasks('C'):
        p=ROOT/'scoring/C_contract_modes'/f"{t['task_id']}.json";assert p.exists();files[str(p)]=sha(p)
    save(ROOT/'audit/C_contract_modes_seal_v1.json',dict(at=now(),files=files,calls=800,
         classification_precedes_source_fidelity_review=True))


def fidelity_packet(review_pass,start,count,path):
    assert (ROOT/'audit/C_contract_modes_seal_v1.json').exists()
    selected=rows(ROOT/'scoring/C_response_index_v1.jsonl');by={t['task_id']:t for t in tasks('C')};target=targets();out=[]
    for r in selected[start:start+count]:
        t=by[r['task_id']];v=dict(r,source_target=target[t['family_id']],
            mode=load(ROOT/'scoring/C_contract_modes'/f"{t['task_id']}.json")['mode'],image_reference=t['image_reference'],image_sha256=t['image_sha256'])
        if review_pass==2:v['first_review']=load(ROOT/'scoring/C_fidelity_pass1'/f"{t['task_id']}.json")
        out.append(v)
    save(path,dict(at=now(),review_pass=review_pass,start=start,rows=out,model_condition_gold_hidden_in_display=True))


def validate_decision(target,review,body):
    validate_review(target,review)
    if review['status']!='SCORED':return
    for a,r in zip(target['atoms'],review['atoms']):
        assert set(r['recovered_units'])<=set(a['subfact_keys'])
        assert all(q in body for q in r['evidence_quotes'])
    assert all(c['text'] in body for c in review['claims'])


def fidelity_apply(path):
    batch=load(path);rp=batch['review_pass'];assert rp in [1,2]
    assert (ROOT/'audit/C_contract_modes_seal_v1.json').exists()
    index={r['review_id']:r for r in rows(ROOT/'scoring/C_response_index_v1.jsonl')}
    by={t['task_id']:t for t in tasks('C')};target=targets()
    for d in batch['decisions']:
        r=index[d['review_id']];tid=r['task_id'];t=by[tid];tg=target[t['family_id']]
        assert d['target_sha256']==fingerprint(tg) and d['generation_sha256']==r['generation_sha256']
        assert r['closed'] or d['review']['status']=='UNRESOLVED'
        mode=load(ROOT/'scoring/C_contract_modes'/f'{tid}.json')['mode']
        assert mode!='UNRESOLVED' or d['review']['status']=='UNRESOLVED'
        validate_decision(tg,d['review'],r['body'])
        if rp==2:
            first=load(ROOT/'scoring/C_fidelity_pass1'/f'{tid}.json')
            assert d['first_review_sha256']==fingerprint(first) and d['reread_response_and_source'] is True
        save(ROOT/f'scoring/C_fidelity_pass{rp}'/f'{tid}.json',dict(d,at=now(),task_id=tid,
             reviewer='main_agent',independent_interrater_reliability=False,review_pass=rp,batch_sha256=sha(path)))


def fidelity_close():
    out=[];files={};target=targets()
    for t in tasks('C'):
        tid=t['task_id'];ps=[ROOT/f'scoring/C_fidelity_pass{rp}'/f'{tid}.json' for rp in [1,2]]
        first,second=map(load,ps);assert second['first_review_sha256']==fingerprint(first)
        rv=second['review'];m=metrics(target[t['family_id']],rv)
        mode=load(ROOT/'scoring/C_contract_modes'/f'{tid}.json')['mode']
        bound_units=rv['atoms'][0]['recovered_units'] if rv['status']=='SCORED' else None
        out.append(dict(task_id=tid,family_id=t['family_id'],model=t['model_key'],condition=t['condition'],
             stratum=t['stratum'],mode=mode,bound_source_units=bound_units,**m))
        files.update({str(p):sha(p) for p in ps})
    write_rows(ROOT/'scoring/C_scored_outcomes.jsonl',out)
    files[str(ROOT/'scoring/C_scored_outcomes.jsonl')]=sha(ROOT/'scoring/C_scored_outcomes.jsonl')
    save(ROOT/'audit/C_fidelity_scoring_seal_v1.json',dict(at=now(),files=files,two_pass_same_agent=True,
         independent_interrater_reliability=False,frozen_five_subfact_atom=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['freeze','modes_packet','modes_apply','modes_close','fidelity_packet','fidelity_apply','fidelity_close'])
    p.add_argument('--path');p.add_argument('--review-pass',type=int,default=1);p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=20);a=p.parse_args()
    if a.action=='freeze':freeze()
    elif a.action=='modes_packet':modes_packet()
    elif a.action=='modes_apply':modes_apply(a.path)
    elif a.action=='modes_close':modes_close()
    elif a.action=='fidelity_packet':fidelity_packet(a.review_pass,a.start,a.count,a.path)
    elif a.action=='fidelity_apply':fidelity_apply(a.path)
    else:fidelity_close()
