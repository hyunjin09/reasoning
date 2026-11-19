"""Prospective source, output-contract and execution freeze; CPU only."""
import hashlib
from pathlib import Path
from scripts.stage12a.common import ROOT,CAPS,ANALYSIS_SEED,load,save,sha,now
from scripts.stage12a.protocol import build_prompt,D_MC,D_OPEN,C_MC,C_OPEN

def main():
    source=ROOT/'stage12a_frozen_e_star_manifest.json';m=load(source)
    assert not list(ROOT.glob('generations/*/*/generation.json'))
    plan=Path('plan/stage12a_multimodal_lost_keys_pilot_plan.md')
    assert sha(plan)==m['plan_sha256'] and len(m['rows'])==61
    archive=ROOT/'audit/spec_versions';archive.mkdir(parents=True,exist_ok=True)
    with (archive/'stage12a_plan_v1.md').open('xb') as f:f.write(plan.read_bytes())
    with (archive/'frozen_e_star_manifest_v1.json').open('xb') as f:f.write(source.read_bytes())
    amendment=dict(at=now(),version=2,status='USER_APPROVED_BEFORE_GENERATION',
        reason='Prospective specification repair:37 of61 original problems are open-ended.',
        original_plan_sha256=sha(plan),original_manifest_sha256=sha(source),
        multiple_choice_D=D_MC,open_ended_D=D_OPEN,multiple_choice_C=C_MC,open_ended_C=C_OPEN,
        preserved=['61 families','exact original images/questions','157 frozen E* facts','E prompt principle and requests',
            'E128/D16/C8192 caps','12 sealed technical IDs','numerical technical gates','GO/NO-GO thresholds'],
        no_stage12a_generation_or_outcomes_exist=True,options_invented=False,families_dropped=False)
    save(archive/'output_contract_v2.json',amendment)
    old=load('outputs/qwen3vl_official_eval/v1/qwen3vl_official_sanity_manifest.json')
    code=[str(p) for p in Path('scripts/stage12a').glob('*.py') if p.name not in ['analyze.py','finish.py']]
    code+=['scripts/stage12a/run.sh','code/visual_reasoning/stage8b/v2_scoring.py','code/visual_reasoning/stage8b/scoring.py',
        'scripts/stage11cr/protocol.py','outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision/run_mathv.py']
    config=dict(at=now(),model=old['models']['instruct'],environment=old['environment'],
        recipe=dict(temperature=.7,top_p=.8,top_k=20,repetition_penalty=1.,presence_penalty=1.5),caps=CAPS,
        runtime=dict(engine_seed=42,tensor_parallel_size=1,gpu_memory_utilization=.9,max_model_len=128000,max_images_per_prompt=10),
        seed_policy='int(SHA256(stage12a-gen-v1|family_id)[:8],16) mod2**31, same family seed for E/D/C',
        analysis_seed=ANALYSIS_SEED,bootstrap_draws=4000,independent_unit='conservative problem/image family',
        source_manifest_sha256=sha(source),amendment_sha256=sha(archive/'output_contract_v2.json'),
        source_sha256={p:sha(p) for p in code},
        resource=dict(target_gpu_hours=2.5,hard_gpu_hours=4,max_concurrent_gpus=8),
        technical_gate=dict(E='>=10 schema,<=1 severe reasoning',D='>=10 native answer-only,<=1 reasoning,0 pathology',
            C='>=10 committed finals,<=2 cap hits,<=1 severe pathology',wording_repairs_max=1),
        inference=dict(P1='all61 families;all required facts correct',P2='E+ and D- /61',P3='C+ among E+D-',P4='P3 minus C+ among E-D-',
            wilson='95% two-sided P1/P2',bootstrap='4000 resamples of61 whole families; percentile95%; undefined denominators retained as missing, never zero',
            type_robustness='For Strong GO, positive selectivity in at least2 evaluable subject/evidence-type strata and positive leave-one-type-out selectivity for every evaluable omission. Undefined or single-stratum support cannot certify Strong GO.',
            conflicting_gate_clauses='NO_GO exclusions take precedence; Strong GO requires all criteria; remaining positive but incomplete evidence is Limited GO',
            technical_failure='TECHNICAL_STOP; scientific endpoints not estimated, not a biological/scientific null'))
    save(ROOT/'config.json',config)
    tasks=[]
    for row in m['rows']:
        for arm in 'EDC':
            task=dict(task_id=f'{arm}_{row["item_id"]}_v1',item_id=row['item_id'],family_id=row['family_id'],arm=arm,
                prompt_version=1,image=row['image'],image_sha256=row['image_sha256'],prompt=build_prompt(row,arm),
                n_facts=len(row['facts']),answer_type=row['answer_type'],cap=CAPS[arm],
                seed=int(hashlib.sha256(('stage12a-gen-v1|'+row['family_id']).encode()).hexdigest()[:8],16)%(2**31))
            tasks.append(task)
    save(ROOT/'audit/primary_v1.json',dict(at=now(),frozen=True,config_sha256=sha(ROOT/'config.json'),rows=tasks))
    tech=m['technical_selection']['ids']
    selected=[next(t for t in tasks if t['item_id']==i and t['arm']==a) for i in tech for a in 'EDC']
    save(ROOT/'audit/technical_v1.json',dict(at=now(),frozen=True,config_sha256=sha(ROOT/'config.json'),phase='technical',rows=selected))
    (ROOT/'stage12a_prompt_templates.md').write_text('# Stage12A frozen prompts\n\nProspective output-contract amendment v2 is user approved. Original question text is unchanged. D/C use one user message with original image first, original question, then `Solve the original problem.` and the relevant suffix. No system message.\n\n'+
        '\n\n'.join(f'## {label}\n\n{text}' for label,text in [('D multiple choice',D_MC),('D open ended',D_OPEN),('C multiple choice',C_MC),('C open ended',C_OPEN)])+
        '\n\n## E — exact template\n\nInspect the image and report only the requested visual facts.\nDo not solve the original problem.\nDo not explain or show reasoning.\nRequested facts:\nE1: <frozen probe_request1>\n...\nReturn exactly:\nE1: [value]\n...\n\nOne line per frozen fact,1–4 facts. No original task question, choices, gold evidence or final answer is included. Full instantiated prompts are frozen in audit/primary_v1.json.\n')
    (ROOT/'stage12a_multimodal_lost_keys_spec.md').write_text(f'''# Stage12A execution specification — amended v2

Approved source plan: plan/stage12a_multimodal_lost_keys_pilot_plan.md, SHA256 {sha(plan)}; exact original archived in audit/spec_versions/stage12a_plan_v1.md.
User approved native-answer-format clarification before any Stage12A generation or outcome inspection. Amendment: audit/spec_versions/output_contract_v2.json. This is prospective specification repair, not post-outcome adaptation. Original evidence manifest remains immutable, including its historical pending-clarification note; this approved amendment resolves that note.

Use all61 Stage11A families and157 E* atoms unchanged:24 multiple-choice and37 open-ended. E only requests frozen evidence; D requires native answer only; C requests reasoning and a terminal `Final answer: X`. Exact templates: stage12a_prompt_templates.md. Original question/image bytes retained; no canonical-TSV substitution.

Same local Qwen3-VL-2B-Instruct checkpoint, processor, image preprocessing, vLLM0.11.0/BF16 backend, family-seed policy and official Instruct sampling for all three arms. Temperature0.7,top-p0.8,top-k20,repetition1.0,presence1.5. No native Thinking. Caps E128/D16/C8192. No added stopping criteria or logits constraints. Engine seed42; per-request family seeds recorded. Pixel bounds602112–4014080,patch16,images before text,native template/add_generation_prompt=True.

Technical subset exactly {', '.join(tech)}; source-only hash rule in frozen manifest. First36 calls are reviewed only for formatting, terminal commitment, caps and severe repetition. Single native final values/expressions are valid for open-ended D, with no intermediate equations/reasoning. Mathematical markup and trailing punctuation can normalize; multiple alternatives, explanatory text, and working equations cannot. E requires all E1..Ek lines with no extra explanation. C follows terminal Final answer contract; terminal commitments and format compliance are recorded separately if manual review identifies a discrepancy. All manual technical overrides require literal evidence and no correctness lookup.

Unchanged technical gates: E>=10/12 schema and<=1 severe reasoning; D>=10/12 compliant,<=1 intermediate reasoning,0 repetition; C>=10/12 committed final,<=2 caps,<=1 severe repetition. At most one bounded wording-repair round on failed arm(s), using same12 IDs before full correctness. Preserve superseded outputs. Reuse unchanged technical calls in final61-family cohort. If repaired gate fails, STOP without interpreting P1–P4.

After technical pass, run remaining families with frozen protocol. STOP before rescue interpretation if >20% of all61 C responses cap without committed final; never increase8192. Atom-level evidence correctness is manually reviewed using frozen gold; E+ iff every required atom is correct, with partial recovery retained. D/C format-invalid/no-final count as task failures, separate from valid wrong answers. Literal extraction and format reviews precede correctness. Open-ended mathematical correctness uses unchanged code/visual_reasoning/stage8b/v2_scoring.py equivalent (bounded numeric1e-6); unresolved equivalence stays explicit and cannot be silently imputed wrong.

Freeze P1=P(E+),P2=P(E+D-),P3=P(C+|E+D-),P4=P3-P(C+|E-D-). Family-equal weighting, Wilson95% P1/P2,4000 family bootstrap draws, fixed seed{ANALYSIS_SEED}. Undefined conditional denominators remain undefined. F1=E-D-,F2=E+D-,F3=E+D-C+,F4=E+D-C-; F3/F4 partition F2, not extra disjoint categories.

Strong GO:>=12 Lost Keys,>=6 C rescues,selectivity>=.15,positive multi-type support and technical validity. Type robustness is frozen in config.json. NO_GO if L<8 or rescued<4 or selectivity<=0; these exclusions take priority over overlapping Limited-GO examples. Otherwise positive incomplete evidence is Limited GO; no undefined contrast is promoted. Technical stop means scientific endpoints NOT_ESTIMATED. No optional trace annotation unless needed after primary results; no automatic follow-on.

Target<2.5/hard4 allocated GPUh including failed startup and any wording repair. All CUDA through project scheduler/Slurm, at most8 authorized GPUs,allowed nodes02/03/06/07. Exact job durations and terminal receipts retained; workers exit when finite queues finish. No Thinking,oracle,benchmark discovery,replication,or recommendation execution.
''')
    save(ROOT/'audit/spec_freeze.json',dict(at=now(),generation_calls=0,correctness_opened=False,
        files={str(ROOT/p):sha(ROOT/p) for p in ['stage12a_frozen_e_star_manifest.json','stage12a_multimodal_lost_keys_spec.md','stage12a_prompt_templates.md','config.json','audit/primary_v1.json','audit/technical_v1.json']}))
    print('SPEC_FROZEN',len(tasks),'logical calls;',len(selected),'technical calls')

if __name__=='__main__':main()
