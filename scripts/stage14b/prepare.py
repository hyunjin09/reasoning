"""Freeze Stage14B populations, settings and technical source IDs before calls."""
import copy
import re
from pathlib import Path
from scripts.stage14b.common import *
from scripts.stage14b.protocol import native_prompt,clean_verse,seed,VERSIONS,verse_options


def task(row,model,replicate,collection,phase,condition):
    identity=row['identity'];tid=f'{identity}_{condition}_{model}_r{replicate}'.replace(':','_').replace(' ','_')
    return dict(task_id=tid,identity=identity,family_id=row['family_id'],item_id=row['item_id'],
        phase=phase,collection=collection,model_key=model,condition=condition,replicate=replicate,
        cap=32768 if model=='I' else 81920,seed=seed(identity,replicate),
        prompt=row['prompt'],image=row['image'],image_sha256=row['image_sha256'],
        source_record_sha256=row['source_record_sha256'],source_version=row.get('version'),
        prompt_version='stage14b-v1')


def main():
    assert not (ROOT/'spec/frozen_run_config.json').exists()
    release=load(SOURCE/'audit/final_release_receipt.json');assert release['status']=='COMPLETE_STOP'
    assert sha(SOURCE/'stage14a_preservation_manifest.json')==release['preservation_manifest_sha256']
    preserve=stage14a('preservation_manifest')['final_files']
    source_names=['mathvision3040_manifest','mathvision_e_star1000_manifest','mathvision_e_star_annotations',
        'mathvision_equal_evidence_renderings','mathvision_confirm300_manifest','mathverse788_family_manifest',
        'mathverse_variant_mapping','mathverse_source_metadata','mathverse_confirm300_manifest']
    source_hashes={}
    for name in source_names:
        p=SOURCE/f'stage14a_{name}.json';h=sha(p);assert preserve[str(p)]==h,(p,preserve[str(p)])
        source_hashes[str(p)]=h
    mv=stage14a('mathvision3040_manifest')['rows'];e=stage14a('mathvision_e_star1000_manifest')['rows']
    annotations={r['item_id']:r for r in stage14a('mathvision_e_star_annotations')['rows']}
    renderings={r['item_id']:r for r in stage14a('mathvision_equal_evidence_renderings')['rows']}
    vf=stage14a('mathverse788_family_manifest')['rows'];variants=stage14a('mathverse_variant_mapping')['rows']
    vm={r['family_id']:r for r in vf};native=[];equal=[];verse=[]
    for r in mv:
        assert sha(r['image'])==r['image_hash']
        native.append(dict(identity='mv:'+r['item_id'],item_id=r['item_id'],family_id=r['family_id'],
            prompt=native_prompt(r),image=r['image'],image_sha256=r['image_hash'],gold_answer=r['gold_answer'],options=r['options'],
            subject=r['subject'],difficulty=r['difficulty'],answer_type=r['answer_type'],source_record_sha256=fingerprint(r),
            alias_member_item_ids=r['alias_member_item_ids'],source=r['source']))
    byid={r['item_id']:r for r in native}
    for r in e:
        a=annotations[r['item_id']];v=renderings[r['item_id']]
        assert r['final_qc_status']==a['final_qc_status']=='PASS'
        assert v['text']==a['equal_evidence_rendering']
        assert hashlib.sha256(v['text'].encode()).hexdigest()==v['sha256']
        equal.append(dict(byid[r['item_id']],prompt=v['text'],image=None,image_sha256=None,
            evidence_sha256=v['sha256'],source_record_sha256=fingerprint(a),num_e_star_atoms=a['num_e_star_atoms'],
            atom_metadata=a['atom_metadata'],has_structured_atom=any(m['atom_type']=='structured_layout' for m in a['atom_metadata']),
            evidence_types={k:a[k] for k in ['requires_entity_binding','requires_quantity_reading','requires_spatial_relation','requires_diagram_label_reading','requires_graph_table_reading']}))
    td={r['family_id']:r for r in variants if r['version']=='Text Dominant'}
    for r in variants:
        if r['image']:assert sha(r['image'])==r['image_hash']
        # Parse native choices only for grading; never reconstruct or edit query_wo.
        options=verse_options(r,td[r['family_id']])
        if r['answer_type']=='multi-choice':assert 2<=len(options)<=10,(r['family_id'],r['version'],options)
        family=vm[r['family_id']]
        verse.append(dict(identity='verse:'+r['problem_index']+':'+r['version'].replace(' ','_'),item_id=r['problem_index'],family_id=r['family_id'],
            prompt=r['query_wo'],image=r['image'],image_sha256=r['image_hash'],gold_answer=r['gold_answer'],options=options,
            answer_type=r['answer_type'],subject=r['source_metadata']['subject'],version=r['version'],
            grading_options_policy='Own visible text choices, or Text Dominant grading-only reference when native choices are raster-only. Never added to prompt.',
            clean_paired=clean_verse(family),source_validity_status=family['source_validity_status'],
            source_checks=family['consistency_checks'],source_repeat_problem_indices=family['source_repeat_problem_indices'],
            source_record_sha256=fingerprint(r)))
    assert (len(native),len(equal),len(verse))==(3040,1000,4728)
    assert len({r['family_id'] for r in equal})==1000
    cm={r['item_id'] for r in stage14a('mathvision_confirm300_manifest')['rows']}
    cv={r['family_id'] for r in stage14a('mathverse_confirm300_manifest')['rows']}
    assert len(cm)==len(cv)==300 and cm<={r['item_id'] for r in equal}
    cn=[r for r in native if r['item_id'] in cm];ce=[r for r in equal if r['item_id'] in cm];vv=[r for r in verse if r['family_id'] in cv]
    manifests={'mathvision_3040_eval_manifest':native,'mathvision_e1000_eval_manifest':equal,'mathverse_788_eval_manifest':verse,
        'confirm300_mathvision':[dict(r,condition='native') for r in cn]+[dict(r,condition='equal') for r in ce],
        'confirm300_mathverse':vv}
    main_tasks=[];confirm=[]
    for records,collection,phase,condition in [(native,'mathvision_native','native','image'),(equal,'mathvision_e1000','equal','evidence'),(verse,'mathverse','mathverse','native')]:
        main_tasks.extend(task(r,m,0,collection,phase,condition) for r in records for m in 'IT')
        sub=cn if phase=='native' else ce if phase=='equal' else vv
        confirm.extend(task(r,m,rep,'confirmatory','confirmatory',condition) for rep in (1,2) for r in sub for m in 'IT')
    # Exactly two MATH-Vision source-only cases, one per format, outside confirm300.
    tech=[];chosen=[]
    for answer_type in ('open_ended','multiple_choice'):
        candidates=[r for r in equal if r['item_id'] not in cm and bool(r['options'])==(answer_type=='multiple_choice')]
        chosen.append(min(candidates,key=lambda r:fingerprint(['stage14b-technical-v1',r['family_id']])))
    vfamily=min([r for r in vf if r['family_id'] not in cv and clean_verse(r)],key=lambda r:fingerprint(['stage14b-technical-v1',r['family_id']]))
    for r in chosen:
        for rr,c in [(byid[r['item_id']],'image'),(r,'evidence')]:
            for m in 'IT':tech.append(task(rr,m,99,'preflight','preflight',c))
    for r in verse:
        if r['family_id']==vfamily['family_id']:
            for m in 'IT':tech.append(task(r,m,99,'preflight','preflight','native'))
    for m in 'IT':
        for j in range(2):
            r=dict(identity=f'seedcheck:{j}',item_id=f'seedcheck{j}',family_id='technical_synthetic',prompt='Reply with exactly the word READY.',
                image=None,image_sha256=None,source_record_sha256=fingerprint('Reply with exactly the word READY.'))
            t=task(r,m,99,'preflight','preflight','seedcheck');t.update(seed=1410405,cap=64);tech.append(t)
    assert len(main_tasks)==17536 and len(confirm)==9600 and len(tech)==24
    assert len({t['task_id'] for t in main_tasks+confirm+tech})==27160
    for name,value in manifests.items():write_rows(ROOT/'manifests'/f'{name}.jsonl',value)
    for name,value in [('main',main_tasks),('confirmatory',confirm),('preflight',tech)]:write_rows(ROOT/'manifests'/f'{name}_tasks.jsonl',value)
    old=load('outputs/stage13a/v1/config.json')
    cfg=dict(at=now(),version='stage14b-v1',models=old['models'],runtime=old['runtime'],environment=old['environment'],
        precision='bfloat16',attention_backend='vLLM automatic backend, actual backend in job log; inherited validated runtime',
        image_preprocessing=dict(min_pixels=768*28*28,max_pixels=5120*28*28,helper='pinned Qwen MathVision build_mathv_prompt/prepare_inputs_for_vllm'),
        stop=dict(stop_token_ids=[],stop_strings=[],ignore_eos=False,model_native_eos=True),
        cap_policy='Explicit prospective inheritance: I32768/T81920 for every corresponding native/evidence/modality condition. Native intended recipes; not a compute-matched causal comparison.',
        system_message=None,chat_template='pinned checkpoint, tokenize=False/add_generation_prompt=True; native Thinking <think> prefix',
        prompts=dict(mathvision='Original question verbatim, then Options:\\nA. ... if present; no additional reasoning/output instruction.',
            equal='Exact frozen Stage14A rendering bytes. Ordinary <image1> source text remains verbatim, without image payload or special image tokens.',
            mathverse='Native query_wo verbatim for both variants, including Vision Only and Text Only. No query_cot.'),
        seeds=dict(main_replicate=0,confirmation_replicates=[0,1,2],extra_replicates=[1,2],engine_seed=42,
            rule='SHA256(stage14b-v1|identity|r{replicate}) mod 2**31; same logical problem seed across models/native-E*, version-specific MathVerse identity'),
        timeout_policy=dict(worker_hours=72,per_request_wall_seconds=14400,preflight_worker_minutes=120),
        retry_policy='At most one infrastructure retry of incomplete logical calls, unchanged input/seed/cap; completed generation, cap hit, refusal or wrong answer never retried.',
        oom_policy='Preserve failed attempt; retry incomplete rows once in fresh worker with batch_size1, unchanged image pixels/model settings. Then technical missing.',
        technical_missingness='No completion after bounded retries/infrastructure/input receipt failure => TECHNICAL_MISSING. Truncated-before-final/ambiguous response => UNSCORABLE. Neither is wrong.',
        schedule='Main phase order native/equal/MathVerse within each finite model shard; phase views reuse native outputs. No confirmation launch before primary and secondary seals.',
        optional_evidence_recovery=False,confirmation_new_calls=9600,main_calls=17536,preflight_calls=24,
        stats=dict(analysis_seed=120220260929,bootstrap_draws=10000,ci=.95,
            primary=['G_img','R_I','G_post','MathVerse mean gap(VD,VO)-mean gap(TD,TL)'],
            mathverse_primary_layer='all788; source-only clean350 is predeclared sensitivity',
            mathverse_clean_fields=['same_task','gold_consistency','text_only_sufficient','visual_versions_sufficient','answer_safe'],
            mathverse_contrast_complete_unit='all8 model×version outcomes for VD,VO,TD,TL must be scoreable in a family',
            weighting='Raw item accuracy plus paired complete-case differences; known-family cluster bootstrap preserving item weights, and family-equal sensitivity. MathVerse native family paired; known-repeat clusters sensitivity.',
            missingness='Four-way outcome counts; resolved-denominator accuracies, correct/N coverage lower bounds, worst/best bounds and common-pair estimates. Rescue denominator is native WRONG; report E* missing numerator/denominator separately and rescue bounds.',
            formal_multiplicity='None; no familywise significance claim. Report unadjusted95% intervals and all primary endpoints.',
            substantial_rescue_rule='Prospective descriptive threshold R_I>=20%, lower95% bootstrap bound>=10%; also disclose continuous estimate/interval and regressions.',
            positive_gain='Point estimate>0; call robust only if95%CI lower>0 and missingness bounds do not reverse sign.',
            confirmation='Main seed0 reused on fixed subsets; add seeds1,2 with same config. All four MVconditions/sixVerseversions for bothmodels; no independent-heldout claim.',
            secondary=['Thinking rescue/transitions','source-validity strata','format','difficulty','structured atoms','atom count','subject','evidence flags','answer/reasoning length','cap/unscorable/technical rates']),
        resources=dict(max_concurrent_gpus=8,allowed_nodes=sorted(ALLOWED_NODES),estimated_gpu_hours=[400,600],
            estimate_basis='Stage13A576 calls/8.5686GPUh =53.55GPU sec/call;27136science calls ~404GPUh before image/modality variability.',no_follow_on=True))
    save(ROOT/'spec/frozen_run_config.json',cfg)
    save(ROOT/'spec/model_revisions.json',cfg['models'])
    write_text(ROOT/'spec/stage14b_plan.md',Path('plan/stage14b_large_scale_math_phenomenon_plan.md').read_text())
    save(ROOT/'audit/source_manifest_hashes.json',dict(at=now(),files=source_hashes,stage14a_release_sha256=sha(SOURCE/'audit/final_release_receipt.json')))
    save(ROOT/'audit/technical_selection.json',dict(at=now(),rule='Fixed hash min within open/MC E* nonconfirmation, plus one all-source-checks-pass nonconfirmation MathVerse family; no outcomes',
        mathvision=[r['item_id'] for r in chosen],mathverse=vfamily['family_id'],task_count=24,model_outcomes_used=False))
    save(ROOT/'audit/source_clean_layer.json',dict(at=now(),clean_families=[r['family_id'] for r in vf if clean_verse(r)],
        known_repeat_groups=stage14a('mathverse788_family_manifest')['source_repeat_groups'],source_fields_immutable=True))
    print(dict(main=len(main_tasks),confirmation=len(confirm),technical=len(tech),technical_mv=[r['item_id'] for r in chosen],technical_verse=vfamily['family_id']))

if __name__=='__main__':main()
