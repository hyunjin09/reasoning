"""Immutable selected Stage13A replicate reuse, with supplemental Stage13B QC."""
from pathlib import Path
from scripts.stage13b.execution import ROOT,load,save,sha,now
from scripts.stage13b.scoring import guard

OLD=Path('outputs/stage13a/v1')


def tasks(mode):return [t for t in load(ROOT/'stage13b_4b_equal_evidence_reuse.json')['tasks'] if t['model_key']==mode]


def technical_path(tid):
    p=OLD/'audit/technical_adjudications'/f'{tid}.json'
    return p if p.exists() else OLD/'audit/technical_decisions'/f'{tid}.json'


def score_path(tid):
    p=OLD/'audit/score_adjudications'/f'{tid}.json'
    return p if p.exists() else OLD/'audit/first_scores'/f'{tid}.json'


def prepare(mode):
    cell='4B_'+mode+'_EQ';guard(cell);selected=tasks(mode);assert len(selected)==144
    source={r['family_id']:r for r in load(ROOT/'stage13b_frozen48_manifest.json')['rows']}
    files={};prior_review=[];random=load(ROOT/'audit/random_review_manifest.json')['tasks'][cell]
    old_seal=load(OLD/'audit'/f'{mode}_EQ_scoring_closed.json');assert old_seal['n_first']==288
    for t in selected:
        tid=t['task_id'];folder=OLD/'generations'/tid;r=load(folder/'result.json');g=load(folder/'generation.json')
        assert r['generation_sha256']==sha(folder/'generation.json') and r['input_sha256']==sha(folder/'input.json')
        assert t['prompt']==source[t['family_id']]['prompts']['O'] and not t['image']
        assert g['seed']==t['seed'] and g['sampling']['max_tokens']==(32768 if mode=='I' else 81920)
        assert g['visual_tokens']==0
        for p in [folder/'generation.json',folder/'input.json',folder/'result.json',technical_path(tid),score_path(tid)]:files[str(p)]=sha(p)
        s=load(score_path(tid));assert (s['label']=='UNSCOREABLE_TECHNICAL')==(not load(technical_path(tid))['validity']['TECHNICALLY_VALID'])
        if s.get('ambiguity'):
            p=OLD/'audit/second_scores'/f'{tid}.json';assert p.exists();files[str(p)]=sha(p);prior_review.append(tid)
    # Redo every preselected random task in the new arm-separated same-agent pass;
    # old ambiguity QC remains immutable evidence and is not discarded.
    save(ROOT/'audit/reuse_first_seals'/f'{cell}.json',dict(at=now(),cell=cell,n=144,files=files,
        random_tasks=random,prior_ambiguity_qc=prior_review,paired_outcomes_opened=False,regenerated_calls=0))


def show_second(mode,n=16,start=0):
    cell='4B_'+mode+'_EQ';guard(cell);seal=load(ROOT/'audit/reuse_first_seals'/f'{cell}.json')
    pending=[tid for tid in seal['random_tasks'] if not (ROOT/'audit/reuse_second_scores'/f'{tid}.json').exists()]
    indexed={t['task_id']:t for t in tasks(mode)};source={r['family_id']:r for r in load(ROOT/'stage13b_frozen48_manifest.json')['rows']}
    for tid in pending[start:start+n]:
        t=indexed[tid];r=source[t['family_id']];a=load(technical_path(tid));g=load(OLD/'generations'/tid/'generation.json')
        print('\nTASK',tid,'GOLD',r['answer'],'COMMITMENT',a['outcome'],'VALID',a['validity']['TECHNICALLY_VALID'])
        print('RESPONSE_END',g['raw_decoded_response'][-800:])
    print('REUSE_SECOND_PENDING',cell,len(pending))


def record(tid,label,reason):
    t=next(t for t in load(ROOT/'stage13b_4b_equal_evidence_reuse.json')['tasks'] if t['task_id']==tid)
    guard('4B_'+t['model_key']+'_EQ');a=load(technical_path(tid))
    assert label in ['CORRECT','INCORRECT','UNSCOREABLE_TECHNICAL']
    assert (label=='UNSCOREABLE_TECHNICAL')==(not a['validity']['TECHNICALLY_VALID'])
    save(ROOT/'audit/reuse_second_scores'/f'{tid}.json',dict(at=now(),task_id=tid,label=label,reason=reason,
        technical_sha256=sha(technical_path(tid)),scope='Supplemental Stage13B own-arm same-agent QC; old label not displayed'))


def close(mode):
    cell='4B_'+mode+'_EQ';guard(cell);seal=load(ROOT/'audit/reuse_first_seals'/f'{cell}.json')
    for p,h in seal['files'].items():assert sha(p)==h,p
    reviews=[]
    for tid in seal['random_tasks']:
        p=ROOT/'audit/reuse_second_scores'/f'{tid}.json';a=load(p);b=load(score_path(tid))
        assert a['label']==b['label'],f'Explicit prospective adjudication needed before reuse: {tid}'
        reviews.append(dict(task_id=tid,agreement=True,second_sha256=sha(p)))
    save(ROOT/'audit/scoring_closed'/f'{cell}.json',dict(at=now(),cell=cell,n=144,reused=True,files=seal['files'],
        reviews=reviews,prior_ambiguity_qc=seal['prior_ambiguity_qc'],paired_outcomes_opened=False,
        scope='Immutable Stage13A scores plus Stage13B same-agent random QC; no regeneration'))
