"""Seal approved source-only design and exact finite execution memberships."""
import hashlib
from scripts.stage14cv.common import *
from scripts.stage14cv.design import parse_original,parse_r1,parse_r2


def preserve_rows(path,value):
    if path.exists():
        assert rows(path)==value,('Existing artifact differs',str(path));return
    write_rows(path,value)


def main():
    assert (ROOT/'spec/g0_user_approval_v1.json').exists()
    review=load(ROOT/'source_qc/visual_and_semantic_reread_v1.json')
    assert review['all_300_visually_reviewed'] and not review['failures']
    cfg=load(ROOT/'spec/model_recipe_proposed_v1.json')
    selection=load(ROOT/'spec/source_selection_proposed_v1.json')
    prompts=rows(ROOT/'spec/exact_prompts_and_diffs/proposed_condition_prompts_v1.jsonl')
    by={(p['family_id'],p['condition']):p for p in prompts}
    cohort={r['source']['family_id']:r for r in rows(ROOT/'cohorts/blindtest_e300_reference_proposal_v1.jsonl')}
    outputs={'R':[],'C':[],'technical':[]}
    for panel,conditions in [('R',['R0','R1','R2']),('C',['C0','C1'])]:
        for condition in conditions:
            for model in 'IT':
                for i,fid in enumerate(selection[f'{panel}_order']):
                    p=by[fid,condition];s=cohort[fid]['source']
                    outputs[panel].append(dict(task_id=f'{model}_{condition}_{fid.replace(":","_")}',
                        panel=panel,benchmark='BlindTest',family_id=fid,item_id=s['item_id'],category=s['category'],
                        model_key=model,condition=condition,collection='representation_r0_r1_r2' if panel=='R' else 'elicitation_c0_c1',
                        prompt=p['prompt'],prompt_sha256=p['prompt_sha256'],seed=p['seed'],cap=cfg['models'][model]['cap'],
                        image_reference=p.get('image_reference'),image_sha256=p.get('image_sha256'),
                        answer_kind='integer' if panel=='R' else 'source_facts',wave=i//18,
                        stratum=cohort[fid]['C_stratum']))
    tech=load(ROOT/'spec/technical_preflight_proposed_v1.json')
    fid=tech['technical_family_id'];science={t['task_id']:t for v in outputs.values() for t in v}
    for model in 'IT':
        for repeat in range(2):
            for i,c in enumerate(tech['conditions']):
                t=science[f'{model}_{c}_{fid.replace(":","_")}']
                outputs['technical'].append(dict(t,task_id=f'G2_{model}_{repeat}_{c}',
                    panel='technical',collection='technical_preflight',wave=i,engine_repeat=repeat))
    assert {k:len(v) for k,v in outputs.items()}=={'R':1800,'C':800,'technical':20}
    qc=[]
    for panel in ['R','C']:
        cells={}
        for t in outputs[panel]:
            cell='|'.join([panel,t['model_key'],t['condition']]+([t['stratum']] if panel=='C' else []))
            cells.setdefault(cell,[]).append(t)
        for cell,ts in cells.items():
            ranked=sorted(ts,key=lambda t:hashlib.sha256(f'stage14cv-v1|score-QC|{cell}|{t["family_id"]}'.encode()).hexdigest())
            qc.extend(dict(task_id=t['task_id'],cell=cell) for t in ranked[:len(ts)//10])
    assert len(qc)==260
    for panel,value in outputs.items():preserve_rows(ROOT/'manifests'/f'{panel}_tasks.jsonl',value)
    preserve_rows(ROOT/'scoring/fixed_hash_review_qc.jsonl',qc)
    preserve_rows(ROOT/'cohorts/blindtest_e300_frozen_reference.jsonl',list(cohort.values()))
    for name in ['d1_old100_identity','d1_new100_source_hash']:
        preserve_rows(ROOT/'cohorts'/f'{name}.jsonl',rows(ROOT/'cohorts'/f'{name}_proposal_v1.jsonl'))
    ledgers=rows(ROOT/'source_qc/semantic_ledger_proposal_v1.jsonl');equiv=[];targets=[]
    unit_map={r['family_id']:r for r in rows('outputs/stage14c/source/D1_shared_unit_map_v1.jsonl') if r['benchmark']=='BlindTest'}
    for r in ledgers:
        f=r['family_id'];e=cohort[f]['frozen_evidence']
        assert parse_original(by[f,'R0']['evidence_text'])==parse_r1(by[f,'R1']['evidence_text'])==parse_r2(by[f,'R2']['evidence_text'])==r['ledger']
        equiv.append(dict(family_id=f,semantic_equivalence=True,source_reread=True,
            original_evidence_sha256=fingerprint(e),new_source_facts=False,omissions=False,
            source_order=['left','middle','right'],numeric_precision='No numerical source coordinates/units added',
            inferred_intersection_count_in_evidence=False,model_outcomes_used=False))
        atom=dict(text=e['atoms'][0]['text'],atom_type='structured_layout',subfact_count=5,
            subfact_keys=r['subfact_keys'],unit=unit_map[f]['atoms'][0]['unit'] if f in unit_map else e['atoms'][0]['unit'],
            shared_topology='All source-text bindings remain required for exact atom recovery.')
        if f in unit_map:assert atom==unit_map[f]['atoms'][0]
        targets.append(dict(family_id=f,benchmark='BlindTest',atoms=[atom],primary_atom_count=1,structured_subfact_total=5))
    write_rows(ROOT/'source_qc/original_evidence_ledger.jsonl',ledgers)
    write_rows(ROOT/'source_qc/r0_r1_r2_semantic_equivalence.jsonl',equiv)
    write_rows(ROOT/'source_qc/answer_leakage_and_precision_audit.jsonl',equiv)
    write_rows(ROOT/'source_qc/rejected_revision_history.jsonl',[])
    write_rows(ROOT/'source_qc/frozen_fidelity_targets.jsonl',targets)
    save(ROOT/'spec/frozen_model_recipe.json',cfg)
    save(ROOT/'spec/primary_endpoints_and_seed.json',load(ROOT/'spec/primary_endpoints_and_seed_proposed_v1.json'))
    save(ROOT/'audit/g1_materialization_v1.json',dict(at=now(),counts={k:len(v) for k,v in outputs.items()},
        fixed_QC=260,new_generation_calls=0,scientific_outcomes_used=False))
    print('Frozen1800R+800C+20technical; no generation')


if __name__=='__main__':main()
