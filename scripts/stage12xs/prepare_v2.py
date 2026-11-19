"""Seal the approved source amendment's Phase A; no model outputs accessed."""
from pathlib import Path
from scripts.stage12xs.execution_v2 import ROOT,load,save,sha,now,CAPS,native_seed,validate_tasks,authorize

def main():
    old=load('outputs/stage12ts/v1/config.json')
    sources=['scripts/stage12xs/'+x for x in ['common.py','protocol.py','execution_v2.py','worker_v2.py','run_v2.sh','prepare_v2.py','launch_v2.py','resources_v2.py']]
    sources+=['scripts/stage12us/protocol.py','scripts/stage12b/protocol.py','scripts/stage12br/protocol.py','code/visual_reasoning/stage8b/v2_scoring.py','code/visual_reasoning/stage8b/scoring.py','outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision/run_mathv.py']
    cfg=dict(at=now(),environment=old['environment'],runtime=old['runtime'],models={'I':old['arms']['C'],'T':old['arms']['T']},caps=CAPS,
        seed_policy='A/B: int(SHA256(stage12a-gen-v1|family_id)[:8],16) mod2**31; C: int(full SHA256(stage12xs-v1|family_id|condition|replicate),16) mod2**31; replicate0..4',
        resource=dict(target_gpu_hours=10,hard_gpu_hours=14,max_concurrent_gpus=8),source_sha256={p:sha(p) for p in sources},
        inherited_config_sha256=sha('outputs/stage12ts/v1/config.json'),source_seal_sha256=sha(ROOT/'audit/final_source_seal.json'))
    save(ROOT/'config.json',cfg)
    cohort=load(ROOT/'stage12xs_fresh96_manifest.json');rows=cohort['rows'];assert len(rows)==96
    tasks=[]
    for r in rows:
        assert r['seed']==native_seed(r['family_id'])
        for a in 'ENO':
            tasks.append(dict(task_id=f"{a}_{r['item_id']}_xs1",item_id=r['item_id'],family_id=r['family_id'],arm=a,model_key='I',
                cap=CAPS[a],prompt=r['prompts'][a],prompt_version='stage12xs-source-seal-v2',image=None if a=='O' else r['image'],
                image_sha256=None if a=='O' else r['image_sha256'],seed=r['seed']))
    ids=[r['item_id'] for r in rows];validate_tasks(tasks,ids,'A')
    save(ROOT/'audit/phaseA_execution.json',dict(at=now(),frozen=True,phase='A',ids=ids,tasks=tasks,config_sha256=sha(ROOT/'config.json')))
    paths=[]
    for k in range(4):
        selected={r['item_id'] for r in rows[k::4]}
        m=dict(at=now(),frozen=True,phase='A',model_key='I',rows=[t for t in tasks if t['item_id'] in selected],config_sha256=sha(ROOT/'config.json'))
        authorize(m);p=ROOT/'audit'/f'phaseA_{k}.json';save(p,m);paths.append(str(p))
    save(ROOT/'audit/prospective_analysis_rules.json',dict(at=now(),frozen=True,
        validity='INPUT_VALID & SCOREABLE & !TRUNCATED_BEFORE_OUTCOME; repetition is behavior, not exclusion; no inherited Stage12BS 61-family gate',
        labels=['CORRECT','INCORRECT','UNSCOREABLE_TECHNICAL'],e_all_fields_required=True,
        scoring='Response-only technical extraction before gold; score E/N/O separately. Existing MathVision equivalence. Missing never wrong.',
        audit='All ambiguous responses plus deterministic first ceil(.20*unambiguous family count) under SHA256(stage12xs-score-audit-v1|family_id); separate second pass, same-agent limitation disclosed.',
        b4_order=cohort['b4_order'],transfer_order=cohort['transfer_order'],
        phaseB='All complete scoreable N- E- O-; first24 if more. No retries.',
        phaseC='B4 C- T+, at least3; first10 if more. Report all eligible and tested denominators separately; thresholds applied to tested cohort as plan section24.',
        replay='Five seeds/condition; >=3/5 family majority; unresolved calls use lower/upper bounds, never incorrect. All five conditions required.',
        decision='Exact plan thresholds. Undefined K3-4 with fewer than2 support = UNRESOLVED_LOW_YIELD; unresolved missing bounds = UNRESOLVED_TECHNICAL. No forced null.',
        intervals='PhaseA Wilson; PhaseC descriptive Clopper-Pearson family intervals. No seed-level population inference.',
        recommendation='Exactly one conditional plan recommendation; no follow-on execution.'))
    spec='''# Stage12X-S held-out replication — sealed execution v2

The approved plan remains authoritative. The source-pool amendment is prospective and source-only. Original v1 manifests remain immutable; this version contains the final cohort and execution.

Exactly96 final-QC-passed families,193 evidence facts. Original83 provisional minus one source ambiguity plus14 accepted from the first28 approved extension candidates. Remaining36 extension candidates unused. Primary review covers all96; deterministic24 second-pass reviews and ambiguity checks are frozen. Reviews are separate passes by the same agent, not independent human reliability evidence.

PhaseA:96×E/N/O=288 calls. PhaseB: complete scoreable B4, maximum24×C/T. PhaseC: at least3 C−T+ candidates; deterministic maximum10, five conditions×five seeds. All recipes, caps, checkpoints, prompts, seeds, scoring and decision thresholds follow the approved plan and config.json. No outcome-based source selection. All193 facts and structured subfields are required for E+.

PhaseA uses four fixed one-GPU shards,72 calls each,24 families each, batch18. Each job has a90-minute limit:6GPUh maximum allocation envelope, expected approximately3–5GPUh including startup. Jobs stop when their queues finish. Subsequent phase reservations must fit the remaining14GPUh hard budget; target below10GPUh for the entire stage. No automatic new stage.

Arm-separated scoring and technical validity are specified in audit/prospective_analysis_rules.json. Repetition is a measured behavior. Missing or technically unscoreable is never treated as incorrect. Independent unit is conservative visual family. Source seals and generation receipts are immutable.
'''
    with (ROOT/'stage12xs_heldout_replication_spec.md').open('x') as f:f.write(spec)
    save(ROOT/'audit/resource_estimate_prelaunch.json',dict(at=now(),phaseA_calls=288,phaseB_max_calls=48,phaseC_max_calls=250,
        phaseA_expected_gpu_hours=[3,5],phaseA_allocation_envelope_gpu_hours=6,target_total_gpu_hours=10,hard_total_gpu_hours=14,
        uncertainty='Later phases depend on frozen scientific gates and output lengths; re-estimate before each phase; never reserve beyond remaining budget.'))
    save(ROOT/'audit/phaseA_freeze.json',dict(at=now(),files={str(p):sha(p) for p in [ROOT/'config.json',ROOT/'audit/phaseA_execution.json',ROOT/'audit/prospective_analysis_rules.json',ROOT/'stage12xs_heldout_replication_spec.md',*[Path(p) for p in paths]]},generation_started=False))
    print('Sealed',len(tasks),'calls in',len(paths),'shards')

if __name__=='__main__':main()
