"""Freeze finite main and outcome-blind G2 memberships from sealed source facts."""
from scripts.stage14c.common import *

def main():
    seal=load(ROOT/'audit/g1_final_source_seal_v1.json');assert seal['status']=='G1_PASS'
    for group in ['input_hashes','artifact_hashes']:
        for p,h in seal[group].items():assert sha(p)==h,p
    cfg=load(ROOT/'spec/model_and_recipe_identity.json')
    cohort=rows(ROOT/'source/cohort_manifest.jsonl');eligible={r['family_id']:r for r in rows(ROOT/'source/evidence_atoms.jsonl')}
    qc={r['family_id']:r for r in rows(ROOT/'source/estar_eligibility_manifest.jsonl')}
    calls=[];native_pre=set();e_pre=set()
    for bench in ['MMStar','BlindTest']:
        group=[r for r in cohort if r['benchmark']==bench]
        def order(r):return (hashlib.sha256(f'stage14c-g0-v1-20261008|technical|{r["family_id"]}'.encode()).hexdigest(),r['family_id'])
        clean=[r for r in group if not qc[r['family_id']]['source_validity_flags']]
        for category in sorted({r['category'] for r in group}):
            native_pre.add(min([r for r in clean if r['category']==category],key=order)['family_id'])
        for r in sorted([r for r in group if r['family_id'] in eligible],key=order)[:2]:
            native_pre.add(r['family_id']);e_pre.add(r['family_id'])
    for r in cohort:
        fid=r['family_id'];seed=int(hashlib.sha256(f'stage14c-v1|{r["benchmark"]}|{fid}|r0'.encode()).hexdigest(),16)%2**31
        for condition in ['native']+(['equal_evidence'] if fid in eligible else []):
            prompt=r['question'] if condition=='native' else 'Task-critical visual evidence:\n'+eligible[fid]['serialized_evidence']+'\n\n'+r['question']
            for model in ['I','T']:
                calls.append(dict(task_id=f'{model}_{condition}_{fid.replace(":","_")}',benchmark=r['benchmark'],family_id=fid,
                    item_id=r['item_id'],category=r['category'],model_key=model,condition=condition,collection=condition,
                    prompt=prompt,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),seed=seed,cap=cfg['models'][model]['cap'],
                    image_reference=dict(parquet=r['parquet'],row_index=r['row_index']) if condition=='native' else None,
                    image_sha256=r['image_sha256'] if condition=='native' else None,answer_kind=qc[fid]['answer_kind']))
    assert len(calls)==4588 and len({t['task_id'] for t in calls})==len(calls)
    pre=[t for t in calls if t['family_id'] in (native_pre if t['condition']=='native' else e_pre)]
    science_count=len(pre)
    for model in ['I','T']:
        for repeat in [0,1]:
            prompt='Continue this fixed sequence: alpha beta gamma. Print the next three repeated words only.'
            pre.append(dict(task_id=f'seed_replay_{model}_{repeat}',benchmark='SYNTHETIC',family_id='synthetic_seed_replay',item_id='synthetic',category='seed_replay',model_key=model,condition='seed_replay',collection='seed_replay',prompt=prompt,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),seed=172903,cap=128,image_reference=None,image_sha256=None,answer_kind=None))
    write_rows(ROOT/'manifests/main_tasks.jsonl',calls);write_rows(ROOT/'manifests/preflight_tasks.jsonl',pre)
    save(ROOT/'audit/g2_membership_arithmetic_v1.json',dict(at=now(),G0_proposed_max=42,exact_science_calls=science_count,synthetic_calls=4,
         reason='Author release has9 task labels (7 generator families); retain every-task coverage rather than the preliminary7-task arithmetic. Deduplication reduces exact total.',
         rule='SHA256(stage14c-g0-v1-20261008|technical|family_id), then family_id; first source-valid native/category and first2eligible/benchmark; no outcome use.',
         native_family_ids=sorted(native_pre),equal_evidence_family_ids=sorted(e_pre),model_outcomes_used=False,main_reuse=True))
    save(ROOT/'audit/resource_estimate_g1_v1.json',dict(at=now(),main_unique_calls=len(calls),preflight_science_reused=science_count,
        synthetic_extra=4,D1_max=600,total_max=len(calls)+604,naive_GPUh=(len(calls)+604)*.007120354651165635,
        estimate_limit='Stage14B throughput proxy; update from G2, not a measured new-task ETA.',hard_GPUh=120,D1_GPUh=12,max_concurrent_gpus=8,actual_GPUh=0))
    print('main',len(calls),'preflight',science_count,'plus4replay')
if __name__=='__main__':main()
