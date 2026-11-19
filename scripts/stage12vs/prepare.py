"""Seal source-derived structure before any localization replay."""
import math
from pathlib import Path
from scripts.stage12vs.common import ROOT,load,save,sha,now
from scripts.stage12vs.protocol import segment,anchors,seed
from scripts.stage12vs.annotation import annotate


def main():
    assert not ROOT.exists(),'Do not replace a frozen study'
    prior=Path('outputs/stage12us/v1');inference=load(prior/'stage12us_primary_inference.json')
    primary=[r for r in inference['primary'] if r['PRODUCTION_SUPPORT'] is True]
    negative=[r for r in inference['primary'] if r['PRODUCTION_SUPPORT'] is not True]
    assert {r['item_id'] for r in primary}=={'2975','798','750','2908'} and len(negative)==1
    history={}
    for parent in ['outputs','reports','scripts']:
        for folder in sorted(Path(parent).glob('stage12*')):
            if folder.name=='stage12vs':continue
            for p in sorted(folder.rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts:history[str(p)]=sha(p)
    save(ROOT/'audit/preserved_history.json',dict(at=now(),files=history))
    (ROOT/'audit/reports_index_before.md').write_text(Path('reports/index.md').read_text())
    manifest=dict(at=now(),primary=primary,descriptive_negative=negative,
        source_inference_sha256=sha(prior/'stage12us_primary_inference.json'),negative_new_calls=0)
    save(ROOT/'stage12vs_primary_manifest.json',manifest)
    old=load(prior/'config.json');cfg=dict(old,at=now(),
        seed_rule='int(SHA256(stage12vs-v1|family_id|phase|step_index|replicate),16) modulo2**31',
        runtime_source_sha256={str(p):sha(p) for p in [Path('scripts/stage12vs')/n for n in ['common.py','protocol.py','worker.py','run.sh','launch.py']]})
    cfg['runtime_source_sha256']['scripts/stage12us/protocol.py']=sha('scripts/stage12us/protocol.py')
    save(ROOT/'config.json',cfg)
    sources={r['item_id']:r for r in load(prior/'stage12us_source_prefixes.json')['rows'] if r['source']=='T'}
    all_steps=[];all_annotations=[];tasks=[];coarse=[];fine_upper=0
    for row in primary:
        item=row['item_id'];source=sources[item];text=Path(source['prefix_path']).read_text()
        assert text==source['canonical_text'];parts=segment(text);offset=0;ss=[]
        for k,part in enumerate(parts,1):
            ss.append(dict(item_id=item,family_id=row['family_id'],step_index=k,start=offset,end=offset+len(part),text=part))
            offset+=len(part)
        all_steps+=ss;all_annotations+=annotate(parts,item)
        aa=anchors(len(parts));fine_upper+=3*max(math.ceil(math.log2(b-a)) for a,b in zip(aa,aa[1:]))
        coarse.append(dict(item_id=item,family_id=row['family_id'],m=len(parts),anchors=aa,
            source_prefix_path=source['prefix_path'],source_prefix_sha256=sha(source['prefix_path']),
            question=source['question'],inherited_answer_audit=dict(EXPLICIT_FINAL_PRESENT=False,ANSWER_CANDIDATE_PRESENT=False)))
        for k in aa:
            prefix=''.join(parts[:k]);p=ROOT/'prefixes'/f'{item}_P{k}.txt';p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('x') as f:f.write(prefix)
            for rep in range(3):
                tasks.append(dict(task_id=f'A_{item}_k{k}_r{rep}',phase='phaseA',cohort='primary',item_id=item,
                    family_id=row['family_id'],question=source['question'],target='I',condition='A',step_index=k,
                    replicate=rep,seed=seed(row['family_id'],'phaseA',k,rep),prefix_path=str(p),prefix_sha256=sha(p)))
    save(ROOT/'stage12vs_semantic_steps.json',dict(at=now(),rows=all_steps,
         boundary_rule='Blank-line paragraph boundaries outside display math/code; paragraphs>600 characters additionally split at sentence punctuation followed by uppercase. Whitespace assigned to preceding span; exact partition, no wording edits.'))
    save(ROOT/'stage12vs_step_annotations.json',dict(at=now(),rows=all_annotations,source_only=True,
         review_limit='Source-cue annotation for every step with explicit uncertain properties, complete short-source primary-role review; long-source semantic roles are not independently exhaustively certified. Do not force a common mechanism from unvalidated tags.'))
    save(ROOT/'stage12vs_coarse_prefix_manifest.json',dict(at=now(),families=coarse,tasks=tasks))
    save(ROOT/'audit/phaseA_execution.json',dict(at=now(),tasks=tasks))
    # Two finite queues, balanced by source size, both containing independent families.
    ordered=sorted(tasks,key=lambda r:(-Path(r['prefix_path']).stat().st_size,r['task_id']))
    for i in range(2):save(ROOT/'queues'/f'phaseA_I{i}.json',dict(frozen=True,phase='phaseA',target='I',config_sha256=sha(ROOT/'config.json'),rows=ordered[i::2]))
    spec='''# Stage12V-S frozen execution specification

Execute only plan/stage12vs_portable_thinking_state_localization_plan.md. Its malformed LaTeX control characters are preserved in the original plan; prose and numerical gates govern.

Four primary families2975/798/750/2908 from Stage12U-S PRODUCTION_SUPPORT;991 is preserved descriptively, no new calls. Exact original questions and successful Thinking source prefixes; no source generation or added image. Reuse verified Stage12U-S native assistant-prefill rendering, BF16 vLLM, pinned4B checkpoints, model-specific recipes/caps and128000 context. No new technical cohort; prior12-call prefix-input validation and new per-call token/receipt checks apply.

Semantic segmentation/roles freeze before new generation. Paragraph boundaries are preferred, with long prose paragraphs split at sentence boundaries; display equations/code stay intact. Exact source text including whitespace is conserved. Primary roles are source-cue annotations, with source-only manual review for the complete short trace; uncertain semantic properties remain null. No post-outcome relabeling, and no claim of exhaustive independent source annotation. Approximate anchors round half up at0/20/40/60/80/100 percent of step count.

Three seeds per boundary. PhaseA seed uses exact stage12vs-v1|family_id|phaseA|step_index|replicate string, full SHA256 modulo2**31. PhaseB uses phaseB in the same rule; adjacent Thinking uses adjacentT; content uses C1_DROP/C2_CF/C3_PARA/C4_CTRL_DROP/C5_ESTAR; optional uses E_PLUS_STEP. Choices/hashes frozen before corresponding generation. Reuse already tested boundaries, never seed-search.

Replication: each eligible family needs P0 majority failure and Pm majority success. More than one resolved full-prefix failure triggers PORTABILITY_UNSTABLE and stops content ablation. Missing majorities do not count as failure; endpoint-invalid families stay frozen/ineligible. Fine search uses earliest observed failure→success interval and floor midpoint, three seeds once per new boundary. Missing midpoint stops that family unresolved. Nonmonotonicity is a tested success followed by failure and subsequent success (the replicated full endpoint provides the latter); no sharp transition claim. Stable adjacent transition needs a later tested successful prefix. No later boundary beyond Pm is invented. Unspecified/missingness-limited decision cases remain UNRESOLVED rather than forcing a named signal.

The plan gives approximate call estimates: fine-search maximum is computed from frozen actual step counts rather than coarsening semantic units to meet the nominal48 calls. All launches enforce cumulative allocated-plus-pending upper bound<=7GPUh; target<5. No model/hyperparameter/cap/seed retries. Optional evidence-plus-step only after mandatory phases complete within budget.

C1 removal of final critical step exactly equals P(k−1), with fresh C1 seeds as a prospective replication. Counterfactual changes one semantic conclusion; paraphrase preserves it; all intervention texts and expected counterfactual direction freeze before replay. Matched earlier noncritical deletion: eligible source-tagged META_REASONING or exact restatement with no new proposition/value, nearest token length, earliest index tie. No eligible control or interpretable proposition means intervention not identifiable; do not fabricate one. E*-only uses exact prior Stage12B-S oracle user text without image and no assistant prefix, with fresh seeds. Optional E*+step retains that user text and prefills the critical step.

Only new continuation terminal answers count under frozen MathVision equivalence. Unfinished pre-outcome caps/input failures are missing, not incorrect; normal-stop no-answer is unsuccessful. Three-valued >=2/3 majority with missingness bounds. Separate own-response extraction before family aggregation; all caps/ambiguities plus deterministic20% ordinary outcomes receive same-agent separate-pass QC. Numeric CF-following readout must be prospectively determined and not inferred from outcome correctness; otherwise report CF correctness only.

Report exact family counts and descriptive Clopper-Pearson intervals. No independent-rater or population-prevalence claim. Four figures, all required artifacts, history hashes, allocated GPU accounting, exactly one recommendation and STOP. No next-stage launch.
'''
    (ROOT/'stage12vs_portable_state_localization_spec.md').write_text(spec)
    sealed=['stage12vs_primary_manifest.json','stage12vs_semantic_steps.json','stage12vs_step_annotations.json',
            'stage12vs_coarse_prefix_manifest.json','stage12vs_portable_state_localization_spec.md','config.json']
    save(ROOT/'audit/source_seal.json',dict(at=now(),hashes={str(ROOT/n):sha(ROOT/n) for n in sealed},no_new_generation=True))
    save(ROOT/'audit/resource_estimate.json',dict(at=now(),coarse_calls=len(tasks),fine_max_calls=fine_upper,
         adjacent_T_max=24,mandatory_content_max=60,optional_max=12,target_gpu_hours=5,hard_gpu_hours=7,
         expected_gpu_hours_range=[2.5,4.8],basis='Stage12U-S observed4.261GPUh for156 scientific calls including78 Thinking; current study primarily Instruct, up to24 Thinking. Adaptive phase counts not additive independent-family samples.'))
    save(ROOT/'audit/initial_freeze.json',dict(at=now(),plan_sha256=sha('plan/stage12vs_portable_thinking_state_localization_plan.md'),prior_files=len(history),no_replay_outcome_exists=True,tests_passed=7))
    print('Frozen',len(tasks),'coarse calls;',len(all_steps),'steps; fine upper',fine_upper,'preserved',len(history),'files')


if __name__=='__main__':main()
