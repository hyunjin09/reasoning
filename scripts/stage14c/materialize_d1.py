"""Materialize already-frozen D1 membership; no launch or model-output access."""
from scripts.stage14c.common import *

def main():
    membership=load(ROOT/'manifests/D1_source_membership_v1.json');spec=load(ROOT/'spec/diagnostic_authorization.json')['D1'];cfg=load(ROOT/'spec/model_and_recipe_identity.json')
    cohort={r['family_id']:r for r in rows(ROOT/'source/cohort_manifest.jsonl')};evidence={r['family_id']:r for r in rows(ROOT/'source/evidence_atoms.jsonl')}
    math_e={r['family_id']:r for r in rows('outputs/stage14b/manifests/mathvision_e1000_eval_manifest.jsonl')}
    math_native={r['identity']:r for r in rows('outputs/stage14b/manifests/mathvision_3040_eval_manifest.jsonl')}
    math_render={r['family_id']:r for r in load('outputs/stage14a/v1/stage14a_mathvision_equal_evidence_renderings.json')['rows']}
    calls=[];targets=[]
    for bench,ids in membership['families'].items():
        for fid in ids:
            if bench=='math':
                e=math_e[fid];r=math_native[e['identity']];prompt=r['prompt'];ref=dict(path=r['image']);ih=r['image_sha256'];item=r['item_id'];category=r.get('subject')
                target=dict(source_evidence_prompt=e['prompt'],atom_metadata=e['atom_metadata'],rendering=math_render[fid])
            else:
                r=cohort[fid];prompt=r['question'];ref=dict(parquet=r['parquet'],row_index=r['row_index']);ih=r['image_sha256'];item=r['item_id'];category=r['category'];target=evidence[fid]
            targets.append(dict(benchmark=bench,family_id=fid,source_target=target,review_policy='Two-pass same-agent semantic atom and internal-subfact matching; no target facts shown in probe input.'))
            query=spec['prompt'].format(native_question_with_options=prompt)
            seed=int(hashlib.sha256(f'stage14c-v1|{bench}|{fid}|r0|D1'.encode()).hexdigest(),16)%2**31
            for model in 'IT':
                calls.append(dict(task_id=f'D1_{model}_{fid.replace(":","_")}',benchmark=bench,family_id=fid,item_id=item,category=category,model_key=model,
                    condition='D1',collection='optional_diagnostics',prompt=query,prompt_sha256=hashlib.sha256(query.encode()).hexdigest(),
                    image_reference=ref,image_sha256=ih,seed=seed,cap=cfg['models'][model]['cap'],answer_kind='source_facts'))
    assert len(calls)==600 and len(targets)==300
    write_rows(ROOT/'manifests/D1_tasks.jsonl',calls);write_rows(ROOT/'source/D1_scoring_targets.jsonl',targets)
    save(ROOT/'audit/D1_materialization_seal_v1.json',dict(at=now(),membership_hash=sha(ROOT/'manifests/D1_source_membership_v1.json'),
        files={str(p):sha(p) for p in [ROOT/'manifests/D1_tasks.jsonl',ROOT/'source/D1_scoring_targets.jsonl']},
        selected_by_existing_preoutcome_membership=True,model_outputs_used=False,launch_gate='After primary_analysis_seal only',max_GPUh=12,calls=600))
    print('Frozen600D1calls; NOT_LAUNCHED')
if __name__=='__main__':main()
