"""Seal Stage13B prospectively, selecting from source metadata only."""
import hashlib,math,sys
from pathlib import Path
from scripts.stage13b.execution import *
from scripts.stage13b.protocol import select,digest

SPEC='''# Stage13B prospective execution specification

The approved Stage13B plan controls the scientific design and all numeric gates.
No model outcomes, response lengths, pathology, B labels or previous family effects
enter source selection. Exactly48 independent visual families are selected from
the sealed96. Strata: answer type, original MathVision level, E* atom count1/2+.
Hamilton proportional quotas (N_stratum/2), largest fractional remainder first,
lexicographic stratum tie break; within strata SHA256(stage13b-v1|family_id).
All strata can meet their quota. Selected order is the same global hash order.
Technical4: first4 remaining under SHA256(stage13b-v1|technical4|family_id).
Initial8: first8 scientific under SHA256(stage13b-v1|initial8|family_id).
All code/order/hashes sealed before any Stage13B call. Technical4 are excluded
from all scientific inference, regardless of their answers.

## Inputs, checkpoints, seeds and runtime
Original image plus frozen N question; or image-free frozen O Q+E*. No system,
CoT, output-contract or new suffix. Official pinned MathVision image helpers and
native processor templates with add_generation_prompt=True. Same semantic input
across scales; Thinking template opens <think>. Local refs/main for all six
checkpoints are frozen, including8B Thinking92f3c4b4feadd3a016ef468d103bb5f58b2a2c6b.
An older8B snapshot exists but is not selected or compared. No downloads.
New science three replicates0..2, full SHA256(stage13b-v1|scale|family_id|condition|replicate)
integer modulo2**31. Scale strings2B/4B/8B; condition I_img/T_img/I_EQ/T_EQ.
Technical calls use separate namespace stage13b-v1-technical and replicate0.
All288 selected4B EQ slots reuse exact Stage13A artifacts/seeds/labels, no calls.
I: temperature.7,top-p.8,top-k20,rep1,presence1.5,cap32768.
T: temperature1,top-p.95,top-k20,rep1,presence0,cap81920.
BF16 vLLM0.11/Torch2.8/Transformers4.57.1,TP1,batch18,maxmodel128000,
GPU memory utilization.9,engine seed42, checkpoint EOS defaults, no added stops.
Batch/runtime capacity changes require prospective technical evidence and an
additive receipt, never scientific decoding or input changes.

## Execution and stop gates
Phase0:48 technical calls (4families x6checkpoints x2inputs). Verify actual rendered
input, image tokens/pixels, no-image absence, output/stop/token receipts and own
response scoreability without correctness. Ordinary technical-case missingness is
reported; systematic input/recipe failures stop. The plan supplies no numeric
technical4 completion gate, so none is invented.
Phase1:2B/8B EQ initial8 first, then remaining40 only after each arm's24calls have
<=20% technical missingness. Apply the same initial8 audit to reused4B EQ before
Phase1 launches. Phase2 only after Phase1 and prospective compute gate; image
initial8 for allscales before remaining40. Any arm >20% missing stops the stage,
finishes already-submitted calls, preserves outputs; no cap/prompt changes.
No paired scientific outcomes opened until arm-separated scoring/QC closes.

## Scoring and statistical choices
Inherited frozen MathVision answer equivalence. Extract own unretracted final
before correctness; capped-before-outcome is missing, capped-after-clear-final
scoreable; normal-stop refusal/no-answer scientific incorrect. Repetition alone
never excludes. All ambiguous/capped/expression outputs get second review plus
ceil(.20*144)=29 deterministic random taskIDs in each scientific scale/mode/input
arm, hash SHA256(stage13b-v1|score-audit|task_id). Reused4B scores stay immutable;
their existing QC is retained and add Stage13B audit when required. Same-agent
QC is not independent-rater reliability. No technical accuracy-based selection.
Review arm order2B I_EQ,T_EQ;4B I_EQ,T_EQ;8B I_EQ,T_EQ; then2B I_img,T_img;
4B I_img,T_img;8B I_img,T_img. Response-only tranche review may precede full
scoring, but paired labels are never displayed during scoring.

Paired family bootstrap:10000 draws, inherited seed120220260929, percentile95%.
Integer replicate-count differences avoid floating residual at zero. Each scale/
condition primary uses all6 slots resolved. A(s) uses common complete families
across4cells; R uses common complete across8cells2B/8B. Apply all original gates:
2B EQ n>=40,gap>=5pp,lower>0; R n>=36,abs>=5pp,CIexcludes0. No token/seed
independence. Full48 least/most-favorable per-slot missing assignments, no imputation.
Guaranteed majority:>=2correct or>=2incorrect; otherwise unresolved. Near floor
means both resolved family means<=1/3; near ceiling both>=2/3; discordant means
opposite resolved majority. Report denominators and do not exclude these families.
32k sensitivity: sixresolved and every Thinking replicate's own scoreable final
before token32768; longer outputs require explicit token-boundary adjudication.
No new calls and no accuracy-driven sensitivity inclusion. No optional regression.

## Resources and closure
New science1440,technical48,reused4B288. Target<24/hard32 allocatedGPUh, at most8
concurrent1GPU finite Slurm workers, authorizedA6000nodes02/03/06/07. Reserve
walltime before launch; capture cleanup-inclusive terminal accounting. Stage13A
576calls cost8.5686GPUh including recovery; mixed-scale prospective total20–30
GPUh is provisional. Re-estimate after technical/tranche/Phase1. If projected
total>32 before Phase2, finish submittedcalls and report Phase1 only; never
reduce cohort/replicates. No keepalive,tmux,follow-on or extra controls.
Exactly one unlaunched recommendation by plan priority: confirmed2B post-evidence
=>matched text-only cross-scale control; else image-side signal=>cross-scale direct
evidence probe; else positive post-evidence only4B/8B=>matched text-only scale
threshold comparison; otherwise retain4B confirmed claim and stop scaling claims.
Deployed model comparisons, no pure Thinking-switch causality/formal mediation/
direct-visual-access proof or matched LLM-versus-VLM claim.
'''


def main():
    assert not (ROOT/'config.json').exists()
    old=load('outputs/stage13a/v1/config.json')
    source=OLD/'stage12xs_fresh96_manifest.json';rows=load(source)['rows']
    selection=select(rows);byid={r['family_id']:r for r in rows}
    seal=load(OLD/'audit/final_source_seal.json')
    for p,h in seal['files'].items():assert sha(p)==h,p
    ROOT.mkdir(parents=True,exist_ok=True)
    with (ROOT/'stage13b_cross_scale_role_spec.md').open('x') as f:f.write(SPEC)
    source_fields=['family_id','item_id','answer_type','level','subject','image_sha256','source_hash']
    order=[dict({k:r[k] for k in source_fields},atom_count=len(r['facts']),selection_hash=digest('stage13b-v1|'+r['family_id'])) for r in rows]
    save(ROOT/'stage13b_frozen48_manifest.json',dict(at=now(),source=str(source),source_sha256=sha(source),
        selection=selection,selection_code_sha256=sha('scripts/stage13b/protocol.py'),rows=[byid[f] for f in selection['scientific']],
        source_only_order=order,model_outcomes_used=False,generation_started=False))
    save(ROOT/'stage13b_technical4_manifest.json',dict(at=now(),rows=[byid[f] for f in selection['technical']],scientific=False))
    # Selection above is already immutable before any outcome-file reuse or generation.
    models={};base=Path('/data/dataset/huggingface/hub')
    required=['config.json','generation_config.json','preprocessor_config.json','tokenizer_config.json','tokenizer.json','chat_template.json']
    for scale in ['2B','4B','8B']:
        for mode in ['I','T']:
            name=f'Qwen3-VL-{scale}-'+('Instruct' if mode=='I' else 'Thinking')
            repo=base/('models--Qwen--'+name);revision=(repo/'refs/main').read_text().strip();checkpoint=repo/'snapshots'/revision
            files=list(required)
            if (checkpoint/'model.safetensors.index.json').exists():
                files+=['model.safetensors.index.json']+sorted(set(load(checkpoint/'model.safetensors.index.json')['weight_map'].values()))
            else:files+=['model.safetensors']
            # All tokenizer/processor support files are pinned too.
            files+=sorted(p.name for p in checkpoint.iterdir() if p.suffix in ['.json','.txt','.jinja'] and p.name not in files)
            files=sorted(set(files));assert all((checkpoint/f).is_file() for f in files)
            hashes={f:sha(checkpoint/f) for f in files}
            cfg=load(checkpoint/'config.json')
            assert cfg['model_type']=='qwen3_vl' and cfg['text_config']['max_position_embeddings']>=128000
            models[scale+'_'+mode]=dict(model=dict(identifier='Qwen/'+name,revision=revision,checkpoint=str(checkpoint),files_sha256=hashes),
                                      recipe=old['models'][mode]['recipe'],cap=32768 if mode=='I' else 81920)
            print('CHECKPOINT_PINNED',name,revision,flush=True)
    assert models['4B_I']['model']['revision']==old['models']['I']['model']['revision']
    assert models['4B_T']['model']['revision']==old['models']['T']['model']['revision']
    save(ROOT/'stage13b_checkpoint_manifest.json',dict(at=now(),models=models,downloads=False,selection='current local refs/main; frozen before Stage13B calls'))
    technical=[task(byid[f],s,m,c,0,'technical') for f in selection['technical'] for s in ['2B','4B','8B'] for m in ['I','T'] for c in ['img','EQ']]
    science=[task(byid[f],s,m,c,k,'equal' if c=='EQ' else 'image') for f in selection['scientific'] for s in ['2B','4B','8B'] for m in ['I','T'] for c in ['img','EQ'] if s!='4B' or c!='EQ' for k in range(3)]
    assert len(science)==1440 and len(technical)==48 and len({t['seed'] for t in science+technical})==1488
    save(ROOT/'stage13b_seed_manifest.json',dict(at=now(),new_scientific=science,technical=technical))
    # No historical correctness is read here: only frozen task metadata.
    old_tasks=load('outputs/stage13a/v1/audit/phaseP_execution.json')['tasks']
    reuse=[t for t in old_tasks if t['family_id'] in selection['scientific']];assert len(reuse)==288
    save(ROOT/'stage13b_4b_equal_evidence_reuse.json',dict(at=now(),stage13a_root='outputs/stage13a/v1',tasks=reuse,
        source_manifest_sha256=sha('outputs/stage13a/v1/audit/phaseP_execution.json'),regenerate=False,
        selection_seal_sha256=sha(ROOT/'stage13b_frozen48_manifest.json')))
    audit={}
    for s in ['2B','4B','8B']:
        for arm in CAPS:
            selected=[t for t in (reuse if s=='4B' and arm.endswith('EQ') else science) if t.get('scale',s)==s and t['arm']==arm]
            assert len(selected)==144,(s,arm,len(selected))
            audit[s+'_'+arm]=sorted([t['task_id'] for t in selected],key=lambda tid:digest('stage13b-v1|score-audit|'+tid))[:29]
    save(ROOT/'audit/random_review_manifest.json',dict(at=now(),tasks=audit,selection='29/144 per arm plus every ambiguity; same-agent QC'))
    # CPU input rendering/tokenization only, no model loading or GPU operation.
    from transformers import AutoProcessor
    sys.path.insert(0,str(Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision').resolve()))
    from run_mathv import build_mathv_prompt,prepare_inputs_for_vllm
    compatibility=[];pixels={}
    for key,model in models.items():
        processor=AutoProcessor.from_pretrained(model['model']['checkpoint'])
        for t in [t for t in technical if t['model_key']==key]:
            if t['image']:
                assert sha(t['image'])==t['image_sha256']
                messages=build_mathv_prompt(dict(question=t['prompt']),lambda row:t['image'],'MathVision')
                inp=prepare_inputs_for_vllm(messages,processor)
                im=inp['multi_modal_data']['image'][0];ph=hashlib.sha256(im.tobytes()).hexdigest()
                pixels.setdefault(t['family_id'],set()).add(ph)
            else:
                messages=[dict(role='user',content=[dict(type='text',text=t['prompt'])])]
                inp=dict(prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True));ph=None
            assert [c['text'] for msg in messages for c in msg['content'] if c['type']=='text']==[t['prompt']]
            assert inp['prompt'].endswith('<|im_start|>assistant\n'+('<think>\n' if t['mode']=='T' else ''))
            ids=processor.tokenizer.encode(inp['prompt']);assert len(ids)+t['cap']<128000
            assert (151655 in ids)==bool(t['image'])
            compatibility.append(dict(task_id=t['task_id'],chat_sha256=hashlib.sha256(inp['prompt'].encode()).hexdigest(),
                                      unexpanded_prompt_tokens=len(ids),prepared_pixel_sha256=ph,passed=True))
    assert all(len(x)==1 for x in pixels.values())
    save(ROOT/'audit/input_compatibility.json',dict(at=now(),checks=compatibility,passed=True,cpu_only=True))
    preserved={str(p):sha(p) for directory in sorted(Path('outputs').glob('stage12*'))+[Path('outputs/stage13a')]
        for p in directory.rglob('*') if p.is_file() and not any(x in p.parts for x in ['cache','__pycache__','.pytest_cache'])}
    save(ROOT/'audit/historical_preservation.json',dict(at=now(),files=preserved))
    inputs=list(ROOT.glob('stage13b_*'))+[ROOT/'audit/input_compatibility.json',ROOT/'audit/random_review_manifest.json']
    hashes={str(p):sha(p) for p in inputs if p.is_file()};hashes.update(seal['files'])
    save(ROOT/'stage13b_input_hashes.json',dict(at=now(),files=hashes,generation_started=False))
    code=list(Path('scripts/stage13b').glob('*.py'))+[Path('scripts/stage13b/run.sh'),Path('scripts/stage12xs/common.py'),Path('code/visual_reasoning/stage8b/v2_scoring.py'),Path('code/visual_reasoning/stage8b/scoring.py')]+list(Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision').glob('*.py'))
    save(ROOT/'config.json',dict(at=now(),models=models,runtime=old['runtime'],environment=old['environment'],caps=CAPS,
        resource=dict(target_gpu_hours=24,hard_gpu_hours=32,max_concurrent_gpus=8),source_sha256={str(p):sha(p) for p in code},
        plan_sha256=sha('plan/stage13b_cross_scale_thinking_role_vlm_plan.md')))
    paths=shards('technical',technical)
    save(ROOT/'audit/preflight.json',dict(at=now(),passed=True,scientific48=selection['scientific'],technical4=selection['technical'],
        new_scientific_calls=1440,technical_calls=48,reused4b_calls=288,manifests=paths,historical_files=len(preserved),estimated_gpu_hours=[20,30]))
    print('PREFLIGHT_PASS',len(preserved),'historical files;',len(paths),'technical shards',flush=True)


if __name__=='__main__':main()
