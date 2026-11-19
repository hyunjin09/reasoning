"""Freeze the approved Thinking science before new generation/correctness."""
import copy,shutil
from pathlib import Path
from scripts.stage12ts.common import ROOT,OLD,load,save,sha,now
from scripts.stage12ts.protocol import authorize_manifest

def main():
    assert not ROOT.exists()
    assert load(OLD/'stage12tr_fresh12_decision.json')['decision']=='THINKING_REGIME_VALIDATED'
    assert load(OLD/'audit/final_verification.json')['pass_all']
    ROOT.mkdir(parents=True);(ROOT/'audit').mkdir()
    plan=Path('plan/stage12ts_thinking_scientific_rescue_visual_evidence_recovery_plan.md')
    shutil.copyfile(plan,ROOT/'audit/approved_plan.md')
    shutil.copyfile('reports/index.md',ROOT/'audit/report_index_before_launch.md')
    preserved=load(OLD/'audit/preserved_history_hashes.json')['files']
    for p,h in preserved.items():assert sha(p)==h,p
    for folder in [OLD,Path('reports/stage12cr/v1'),Path('scripts/stage12cr')]:
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in str(p):preserved[str(p)]=sha(p)
    save(ROOT/'audit/preserved_history_hashes.json',dict(at=now(),files=preserved))
    full=load('outputs/stage12c/v1/stage12c_frozen_bottleneck_manifest.json')
    tasks=[dict(t,cap=81920) for t in full['tasks'] if t['arm']=='T']
    reuse=[t for phase in ['same12','fresh12'] for t in load(OLD/f'stage12tr_{phase}_manifest.json')['rows']]
    reuse_ids={t['task_id'] for t in reuse};remaining=[t for t in tasks if t['task_id'] not in reuse_ids]
    assert len(tasks)==61 and len(reuse)==24 and len(remaining)==37
    assert all(t in tasks for t in reuse)
    cfg=copy.deepcopy(load(OLD/'config.json'));cfg.update(at=now(),parent_config_sha256=sha(OLD/'config.json'))
    cfg['resource']=dict(target_gpu_hours=4.5,hard_gpu_hours=6.5,max_concurrent_gpus=8)
    cfg['source_sha256'].update({str(p):sha(p) for p in Path('scripts/stage12ts').glob('*') if p.suffix in ['.py','.sh']})
    save(ROOT/'config.json',cfg)
    for t in tasks:assert sha(t['image'])==t['image_sha256']
    for name,rows in [('reused24',reuse),('remaining37',remaining)]:
        m=dict(at=now(),frozen=True,arm='T',phase='remaining' if name=='remaining37' else 'reuse',
               config_sha256=sha(ROOT/'config.json'),rows=rows)
        if name=='reused24':
            m['origins']={t['task_id']:dict(path=str(OLD/'generations'/t['task_id']),
                 files={p.name:sha(p) for p in (OLD/'generations'/t['task_id']).glob('*.json')}) for t in rows}
        save(ROOT/f'stage12ts_{name}_manifest.json',m)
    manifest=dict(at=now(),frozen=True,n_families=61,n_facts=157,tasks=tasks,rows=full['rows'],
         source='outputs/stage12c/v1/stage12c_frozen_bottleneck_manifest.json',
         source_sha256=sha('outputs/stage12c/v1/stage12c_frozen_bottleneck_manifest.json'),
         reuse_ids=sorted(reuse_ids),new_ids=[t['task_id'] for t in remaining],config_sha256=sha(ROOT/'config.json'))
    save(ROOT/'stage12ts_thinking_manifest.json',manifest)
    for rank in range(3):
        m=dict(frozen=True,phase='remaining',arm='T',config_sha256=sha(ROOT/'config.json'),rows=remaining[rank::3])
        authorize_manifest(m);save(ROOT/f'audit/remaining_{rank}.json',m)
    for t in reuse:
        p=OLD/'audit/technical_annotations'/f"{t['task_id']}.json"
        a=load(p);assert a['generation_sha256']==sha(OLD/'generations'/t['task_id']/'generation.json')
        save(ROOT/'audit/technical_annotations'/p.name,dict(a,reused_annotation_path=str(p),reused_annotation_sha256=sha(p)))
    bs=load('outputs/stage12bs/v1/stage12bs_full_manifest.json');cohort={r['item_id'] for r in full['rows']}
    sources={
      'Stage12B development (also Stage12A/AR executed development)':bs['development_ids'],
      'Stage12BR validation':bs['validation_ids'],
      'Stage12C/12TR original':full['sanity_ids'],
      'Stage12TR fresh':[t['item_id'] for t in reuse],
      'Stage11C/11CR nonprimary and official-protocol sanity':[r['item_id'] for r in load('outputs/qwen3vl_official_eval/v1/qwen3vl_official_sanity_manifest.json')['cases']],
      'Stage11CR known-good technical reproduction':[r['item_id'] for r in load('outputs/stage11cr/v1/stage11cr_known_good_manifest.json')['rows']]}
    s2=sorted(cohort.intersection(set().union(*(set(v) for v in sources.values()))))
    rules=copy.deepcopy(load(OLD/'audit/analysis_rules.json'));rules.update(at=now(),generation_started=False,correctness_opened=False)
    rules['trace_evidence']['arms']=['T'];rules['random_audit']['rule']='T-only: every ambiguity plus ceil20% unambiguous families in inherited deterministic order.'
    rules['decision']='Frozen approved plan section23; visual >=5B1,>=3T-only B1,>=3T-only FULL B1; downstream>=5B4; states can coexist.'
    rules['stopping']='16 artifacts,5 figures,exactly one recommendation; no next experiment.'
    rules['full_gate_rationale']='Inherit the prospectively frozen full61 gate from Stage12C/CR (61 valid,51 scoreable,<=5 pre-outcome caps); no repetition exclusion.'
    rules['sensitivities']=dict(S1_exclude=bs['development_ids'],S2_exclude=s2,technical_sources=sources,
        rule='Union of actual prior technical development/validation in this cohort lineage, including official audit and Stage11CR; never-run Stage12AR validation is excluded from exposure accounting. Historical scientific generation alone is not technical development.')
    save(ROOT/'audit/analysis_rules.json',rules)
    (ROOT/'stage12ts_thinking_scientific_spec.md').write_text(f'''# Stage12T-S scientific specification

Frozen {now()} before new generation and before Thinking correctness. Approved user plan: audit/approved_plan.md; this plan supersedes the earlier draft, which is preserved.

Exact61 families/157 facts and prior E/N/O/C labels preserved. Reuse24 Thinking81920 outputs including the pre-outcome cap; generate37 missing calls once in deterministic13/12/12 shards, original task order round-robin. Qwen3-VL-4B-Thinking1de27d8c51f12e819435303b9e84c4e25ba8401e; original image/question, no suffix;temperature1/top-p.95/top-k20/repetition1/presence0/cap81920. Same BF16/vLLM environment, preprocessing, batch limit18/max context128000 and family seeds. No changes selected from outcomes.

Inherited full technical gate61 input-valid,>=51 scoreable,<=5 pre-outcome caps prospectively operationalizes material breakdown. R1–R4 never exclude. A unique surviving committed outcome after a cap may count; provisional scratchpad candidates alone do not. Missingness never wrong. All61 technical labels sealed before correctness. All26 E* trace annotations also sealed before correctness; packets omit outcomes and strata. WRONG/CONFLICTING takes precedence over FULL; FULL requires every frozen fact before final commitment, not inferred from a correct answer. Review coverage is recorded.

T-only scoring then ambiguity-triggered/ceil20% deterministic second review under unchanged MathVision equivalence. Single-agent separate-pass QC is not independent reliability. Correctness and trace seals precede paired joins. Primary T-P1/B1,T-P2/B4,T-P3 difference,T-P4 paired C/T and T-only evidence-linked B1; Wilson95%,4000 family-stratified bootstrap,seed{cfg['bootstrap_seed']}, equal family weights. Missingness bounds and frozen denominators retained. B2/B3/subtypes descriptive. Overall N/C/T accuracy uses a common jointly scoreable denominator, with pairwise transitions separately reported.

S1 excludes{len(bs['development_ids'])} original Stage12B development families. S2 excludes{len(s2)} actual prior technical families in the documented lineage; IDs/sources frozen in analysis_rules.json. Undefined tiny sensitivity denominators remain undefined. Five figures; if no qualifying evidence-linked example exists, T5 explicitly shows zero eligible cases, with no substituted favorable examples. Deterministic examples use smallest family IDs after label seals.

Decision thresholds exactly plan section23. T-vs-C is a checkpoint/recipe/budget comparison, not causal Thinking on/off. Visible traces do not establish hidden-state retrieval. Exactly one section34 recommendation, not executed. New compute target<4.5/hard6.5GPUh; three one-GPU120minute finite jobs have a6GPUh ceiling including startup, max8authorized concurrent GPUs. No new E/N/C/oracle/intervention or decoding search.
''')
    frozen=[ROOT/'config.json',ROOT/'stage12ts_thinking_scientific_spec.md']+list(ROOT.glob('*manifest.json'))+[ROOT/'audit/analysis_rules.json']+list((ROOT/'audit').glob('remaining_*.json'))
    save(ROOT/'audit/prospective_freeze.json',dict(at=now(),new_generation_started=False,thinking_correctness_opened=False,
           files={str(p):sha(p) for p in frozen},approved_plan_sha256=sha(plan)))
    print('Frozen61 tasks,24reuse,37new; S1',len(bs['development_ids']),'S2',len(s2),'history',len(preserved))

if __name__=='__main__':main()
