"""Stage14C-V response-only extraction and immutable, inherited answer scoring."""
import argparse
from collections import Counter
from scripts.stage14cv.common import *
from scripts.stage14c.response_protocol_v4 import extract,repetition
from scripts.stage14c.design_core import score_final


def cohort():
    return {r['source']['family_id']:r for r in rows(ROOT/'cohorts/blindtest_e300_frozen_reference.jsonl')}


def extract_available():
    sources=cohort();done=0
    for t in tasks('R'):
        out=ROOT/'scoring/R_extraction'/f"{t['task_id']}.json"
        if out.exists():continue
        p=checked(t)
        if p is None:continue
        g=load(p.parent/'generation.json')
        x=extract(g['raw_decoded_response'],t['model_key'],'integer',g['finish_reason'],sources[t['family_id']]['source']['question'])
        save(out,dict(at=now(),task_id=t['task_id'],task_sha256=fingerprint(t),extraction=x,
             generation_sha256=sha(p.parent/'generation.json'),cap_hit=g['cap_hit'],
             repetition=repetition(g['generated_token_ids']),correctness_used=False))
        done+=1
    print('New response-only extractions',done,flush=True)


def freeze_raw():
    files={}
    for t in tasks('R'):
        p=checked(t);assert p,('Missing primary response',t['task_id'])
        for q in [p,p.parent/'generation.json',p.parent/'input.json']:files[str(q)]=sha(q)
    save(ROOT/'audit/R_raw_seal_v1.json',dict(at=now(),calls=1800,files=files,
         context_replays_excluded=True,scientific_outcomes_used=False))


def review_packet(destination=None):
    grouped={}
    qc={r['task_id'] for r in rows(ROOT/'scoring/fixed_hash_review_qc.jsonl')}
    for t in tasks('R'):
        path=ROOT/'scoring/R_extraction'/f"{t['task_id']}.json"
        if not path.exists() or (ROOT/'scoring/R_response_reviews'/f"{t['task_id']}.json").exists():continue
        x=load(path)
        if not (x['extraction'].get('needs_review') or x['cap_hit'] or t['task_id'] in qc or x['extraction']['status']!='EXTRACTED'):continue
        p=checked(t);g=load(p.parent/'generation.json');raw=g['raw_decoded_response']
        closed=t['model_key']!='T' or '</think>' in raw
        body=raw.rsplit('</think>',1)[-1].replace('<|im_end|>','').strip() if closed else ''
        key=fingerprint(dict(body=body,closed=closed,finish=g['finish_reason'],extraction=x['extraction']))
        if key not in grouped:grouped[key]=dict(review_id=key,body=body,closed=closed,finish_reason=g['finish_reason'],
              extraction=x['extraction'],raw_tail_if_unclosed=raw[-1200:] if not closed else None,task_ids=[])
        grouped[key]['task_ids'].append(t['task_id'])
    dest=Path(destination) if destination else ROOT/'scoring/R_review_packet_v1.json'
    save(dest,dict(at=now(),groups=sorted(grouped.values(),key=lambda r:r['review_id']),
                  task_count=sum(len(g['task_ids']) for g in grouped.values()),gold_and_model_hidden_in_display=True))
    print('Review groups',len(grouped),'tasks',sum(len(g['task_ids']) for g in grouped.values()))


def final_extraction(tid):
    p=ROOT/'scoring/R_response_reviews'/f'{tid}.json'
    return load(p) if p.exists() else load(ROOT/'scoring/R_extraction'/f'{tid}.json')


def apply_review(path):
    packet=load(load(path).get('packet_path',ROOT/'scoring/R_review_packet_v1.json'));groups={g['review_id']:g for g in packet['groups']}
    for decision in load(path)['decisions']:
        group=groups[decision['review_id']]
        assert decision['status'] in {'EXTRACTED','UNSCORABLE','NO_ANSWER'}
        assert (decision['answer'] is not None)==(decision['status']=='EXTRACTED')
        assert decision['reason'].strip()
        for tid in group['task_ids']:
            original=load(ROOT/'scoring/R_extraction'/f'{tid}.json')
            save(ROOT/'scoring/R_response_reviews'/f'{tid}.json',dict(original,at=now(),
                 extraction=dict(answer=decision['answer'],status=decision['status'],needs_review=False,
                                 committed=decision['status']=='EXTRACTED'),
                 review_id=decision['review_id'],reason=decision['reason'],reviewer='main_agent',
                 correctness_used=False,original_extraction_sha256=fingerprint(original)))


def score():
    assert (ROOT/'audit/R_raw_seal_v1.json').exists()
    c=cohort();counts=Counter();files={}
    required={tid for p in (ROOT/'scoring').glob('R_review_packet_v*.json') for g in load(p)['groups'] for tid in g['task_ids']}
    for t in tasks('R'):
        e=load(ROOT/'scoring/R_extraction'/f"{t['task_id']}.json")
        if e['extraction'].get('needs_review') or e['cap_hit'] or e['extraction']['status']!='EXTRACTED':required.add(t['task_id'])
    required.update(r['task_id'] for r in rows(ROOT/'scoring/fixed_hash_review_qc.jsonl') if r['task_id'].split('_')[1].startswith('R'))
    for t in tasks('R'):
        tid=t['task_id'];r=final_extraction(tid);x=r['extraction']
        assert not x.get('needs_review'),tid
        if tid in required:assert (ROOT/'scoring/R_response_reviews'/f'{tid}.json').exists(),tid
        status='WRONG' if x['status']=='NO_ANSWER' else score_final(x['answer'],c[t['family_id']]['source']['gold'],'integer')
        assert status in {'CORRECT','WRONG','UNSCORABLE'},tid
        out=ROOT/'scoring/R_scores'/f'{tid}.json'
        value=dict(task_id=tid,family_id=t['family_id'],model=t['model_key'],condition=t['condition'],status=status,
                   answer=x['answer'],extraction_sha256=fingerprint(r),native_gold_unchanged=True)
        if out.exists():assert load(out)==value
        else:save(out,value)
        counts[t['model_key']+'_'+t['condition']+'_'+status]+=1;files[str(out)]=sha(out)
    save(ROOT/'audit/R_initial_scoring_v1.json',dict(at=now(),files=files,counts=dict(counts),
         response_reviews=len(required),QC_still_required=True,scoring_rule='Inherited exact integer equivalence'))
    print(dict(counts))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['extract','freeze','packet','apply','score']);p.add_argument('--path');a=p.parse_args()
    if a.action=='extract':extract_available()
    elif a.action=='freeze':freeze_raw()
    elif a.action=='packet':review_packet(a.path)
    elif a.action=='apply':apply_review(a.path)
    else:score()
