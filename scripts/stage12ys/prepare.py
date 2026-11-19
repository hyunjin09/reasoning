"""Freeze Stage12Y-S before generation; reused outcomes remain historical screens."""
from pathlib import Path
from scripts.stage12ys.execution import *

SPEC='''# Stage12Y-S prospective execution specification

Execute the user-approved plan unchanged on the exact Stage12X-S final96 families.
This is paired role decomposition, not another held-out replication claim. All
source facts, images, questions, golds, evidence requests and oracle text remain
immutable. Historical Instruct E/N/O raw responses, technical decisions and
scores are reused unchanged as single-run screens; prior Thinking runs are not
substituted for the 288 newly specified Phase A calls.

## Inputs and runtime
Phase A arms E_T, T_img, T_E map exactly to frozen E/N/O prompts; first two have
original image, T_E is image-free. No extra suffix/system text. Official pinned
MathVision prompt helpers and native model templates; BF16 vLLM0.11, TP1,
batch18, max model128000, engine seed42. Instruct revision
ebb281ec70b05090aa6165b016eac8ec08e71b17, temperature.7/top-p.8/top-k20/
repetition1/presence1.5; Thinking revision
1de27d8c51f12e819435303b9e84c4e25ba8401e, temperature1/top-p.95/top-k20/
repetition1/presence0. Section7 model caps apply to ALL new calls: Instruct32768,
Thinking81920. Historical E_I had256; this historical screening difference is
reported and not retroactively changed. Fresh B evidence probes use section7.

## Prospective deterministic choices
All seeds int(full SHA256 hex,16) mod2**31. A domain:
stage12ys-v1|screen|family_id|condition|0. B exact plan domain:
stage12ys-v1|family_id|condition|replicate, replicate0..2. C exact plan domain:
stage12ys-v1|state-transfer|family_id|condition|replicate, replicate0..4.
Literal condition names: E_I,E_T,I_img,T_img,I_E,T_E; C RT_T,RT_I,Q_I,SH_I.
All seeds frozen before respective phase; no best-of selection or retry of an
attempted scientific call. Never-started calls may be launched once after a
documented infrastructure interruption without changing their frozen task.

Access candidates sorted SHA256(stage12ys-v1|ACCESS_SCREEN_STRONG|family_id),
first16. Only if fewer than8 strong exist, supplement weak-only up to16 using
role ACCESS_SCREEN_WEAK. Eight through15 strong receive no weak supplement.
Downstream candidates prioritize native-linked, then role DOWNSTREAM_SCREEN
hash within priority; cap16. B uses all six arms for access, two equal-evidence
arms for downstream plus two native arms when PhaseA native-linked. Unique
family-condition-replicate calls are deduplicated across panels.
C confirmed downstream order SHA256(stage12ys-v1|STATE_TRANSFER|family_id),
first10. Select first successful B T_E replicate ascending0..2. Maximal prefix
before FIRST explicit answer candidate, including tentative/wrong candidates;
strip model-control wrappers only. Hash/tokenize/audit cut and incidental gold
before replay. Deterministic next-family cyclic shuffle in frozen C order.
If K=1, no legal j!=i shuffle exists: C unexecutable and unresolved, no invented
donor. K=2 may be descriptive but cannot meet the three-family signal gate.

## Scoring and inference
Arm-separated own-response technical extraction before own-arm correctness;
do not display paired labels during annotation. Frozen MathVision equivalence,
all required E* atoms/subfields for E+. Complete EOS incomplete evidence is E−;
pre-outcome caps and no scoreable task answer are technical missingness, never
incorrect. Repetition alone is not exclusion. Unique cap-after-commitment may
remain valid. Explicit ambiguity adjudication preserves original annotations.
All ambiguous calls and deterministic20% unambiguous-family second pass using
SHA256(stage12ys-score-audit-v1|family_id). Same-agent QC is not independent
human reliability. Seal all arm scores before constructing paired role labels.

Phase A gaps on paired common-scoreable families. Attenuation on the common
four-task denominator, alongside pair-specific gaps; never subtract gaps on
different denominators as if they were paired mediation. Family-equal4000
bootstrap draws, inherited analysis seed120220260929,95% percentiles. No tokens,
events or seeds treated as independent families. A quantities descriptive only.
Confirmatory majority2/3 or3/5 on all frozen replicates: unresolved if missing
outcomes can reverse majority; known failures require enough observed incorrect
replicates. No denominator shrinkage or retries to resolve failed majorities.
Access/downstream gates use the frozen confirmed-panel size as denominator for
the conservative support fraction, also report resolved denominator and missing
upper bound; require n>=5, >=60% support and >=3 independent full signatures.
C requires >=3 entered, >=2 support, >=60% of eligible families with resolved
baseline/shuffle controls. Missing success arms remain unknown, not positive.
Report all three signals and multi-role flag; if both access/downstream pass,
decision MULTI_ROLE_THINKING_SIGNAL, with state flag explicitly reported. Sole
recommendation follows section33 priority: state > multi > access > downstream
> unresolved. Exactly the plan thresholds, no outcome-dependent changes.

## Resource and stop rules
Target<12/hard16 allocatedGPUh including startup/cleanup. Up to8 simultaneous
one-GPU Slurm jobs via project scheduler, allowed02/03/06/07 only. Finite queues,
no keepalive; capture terminal accounting and release all allocations. PhaseA
8x36 calls, 90minute each reservation (12GPUh maximum), actual expected4–7GPUh
based on prior long-form throughput; B/C depend on candidate yield. Assess full
remaining reservation against hard budget before every launch. No unapproved
scope/cap/recipe change if budget becomes insufficient.

No next stage, new cohort, model scale, CoT control or hidden-state experiment.
Produce all18 required artifacts/five figure pairs, exactly one recommendation,
then STOP. Preserve all earlier artifacts/source/QC seals.
'''

def main():
    assert not (ROOT/'config.json').exists()
    old=load(OLD/'config.json');source=load(OLD/'stage12xs_fresh96_manifest.json')
    assert len(source['rows'])==len({r['family_id'] for r in source['rows']})==96
    for r in source['rows']:assert sha(r['image'])==r['image_sha256']
    for p,h in load(OLD/'audit/final_source_seal.json')['files'].items():assert sha(p)==h
    for m in old['models'].values():
        for name,h in m['model']['files_sha256'].items():assert sha(Path(m['model']['checkpoint'])/name)==h
    ROOT.mkdir(parents=True,exist_ok=True)
    (ROOT/'stage12ys_role_decomposition_spec.md').write_text(SPEC)
    save(ROOT/'stage12ys_frozen96_manifest.json',dict(at=now(),frozen=True,n_families=96,rows=source['rows'],
        reused_manifest=str(OLD/'stage12xs_fresh96_manifest.json'),reused_sha256=sha(OLD/'stage12xs_fresh96_manifest.json')))
    reused=[]
    for r in source['rows']:
        for a,new in [('E','E_I'),('N','I_img'),('O','I_E')]:
            folder=OLD/'generations'/f'{a}_{r["item_id"]}_xs1'
            files=[folder/f for f in ['input.json','generation.json','result.json']]
            files+=[OLD/'audit/first_scores'/f'{a}_{r["item_id"]}_xs1.json']
            reused.append(dict(item_id=r['item_id'],family_id=r['family_id'],arm=new,
                historical_task_id=f'{a}_{r["item_id"]}_xs1',files={str(p):sha(p) for p in files}))
    save(ROOT/'stage12ys_reused_stage12x_inputs.json',dict(at=now(),n=288,rows=reused,screening_only=True))
    preserved={}
    for directory in sorted(Path('outputs').glob('stage12*')):
        if directory.name=='stage12ys':continue
        for p in directory.rglob('*'):
            if p.is_file() and not any(x in p.parts for x in ['cache','__pycache__','.pytest_cache']):preserved[str(p)]=sha(p)
    save(ROOT/'audit/historical_preservation.json',dict(at=now(),files=preserved))
    inputs=[OLD/'audit/final_source_seal.json',ROOT/'stage12ys_frozen96_manifest.json',ROOT/'stage12ys_reused_stage12x_inputs.json',ROOT/'stage12ys_role_decomposition_spec.md']
    input_hashes={str(p):sha(p) for p in inputs}
    input_hashes.update(load(OLD/'audit/final_source_seal.json')['files'])
    save(ROOT/'audit/input_seal.json',dict(at=now(),files=input_hashes,generation_started=False))
    sources=[str(p) for p in Path('scripts/stage12ys').glob('*.py')]+['scripts/stage12ys/run.sh']
    sources+=['scripts/stage12xs/common.py','scripts/stage12xs/execution_v2.py','scripts/stage12us/protocol.py',
        'scripts/stage12br/protocol.py','code/visual_reasoning/stage8b/v2_scoring.py','code/visual_reasoning/stage8b/scoring.py',
        'outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision/run_mathv.py']
    cfg=dict(at=now(),environment=old['environment'],runtime=old['runtime'],models=old['models'],caps=CAPS,
        resource=dict(target_gpu_hours=12,hard_gpu_hours=16,max_concurrent_gpus=8),
        source_sha256={p:sha(p) for p in sources},plan_sha256=sha('plan/stage12ys_thinking_role_decomposition_vlm_math_plan.md'),
        inherited_config_sha256=sha(OLD/'config.json'),spec_sha256=sha(ROOT/'stage12ys_role_decomposition_spec.md'))
    save(ROOT/'config.json',cfg)
    tasks=[task(r,a,'A',0) for r in source['rows'] for a in ['E_T','T_img','T_E']]
    validate_tasks(tasks,[r['item_id'] for r in source['rows']],'A')
    save(ROOT/'audit/phaseA_execution.json',dict(at=now(),phase='A',ids=[r['item_id'] for r in source['rows']],tasks=tasks,config_sha256=sha(ROOT/'config.json')))
    paths=shards('A',tasks,8)
    save(ROOT/'audit/preflight.json',dict(at=now(),passed=True,n_families=96,new_A_calls=288,reused_I_calls=288,
        historical_files=len(preserved),shards=paths,phaseA_estimated_gpu_hours=[4,7],
        phaseA_reservation_gpu_hours=12,stage_target_gpu_hours=12,stage_hard_gpu_hours=16,downloads=False))
    print('PREFLIGHT PASS',len(preserved),'historical files',len(paths),'shards')

if __name__=='__main__':main()
