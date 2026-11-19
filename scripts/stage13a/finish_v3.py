"""Close only the authorized Stage13A study; never launch its recommendation."""
from pathlib import Path
import os
import pandas as pd
from scripts.stage13a.execution import ROOT,load,save,sha,now
from scripts.stage13a.resources import account

RECOMMENDATIONS={
'EQUAL_EVIDENCE_THINKING_ADVANTAGE_CONFIRMED':'Run a cross-scale image-vs-equal-evidence study at 2B/4B/8B to test whether the functional role of Thinking changes with model size.',
'EQUAL_EVIDENCE_SIGNAL_PARTIAL':'Treat the post-evidence advantage as suggestive rather than central, and let the next cross-scale study determine whether it strengthens or disappears with scale.',
'EQUAL_EVIDENCE_NO_ADVANTAGE':'Restrict Claim 1 to the robust visual-evidence bottleneck and selected-case portability findings; do not claim a broad post-evidence Thinking advantage.',
'EQUAL_EVIDENCE_TECHNICALLY_UNRESOLVED':'Repair only the technical missingness needed to reach the frozen paired-coverage gate, without changing prompts, checkpoints, or the cohort.'}

def figures(primary,comparable,old,optional):
    os.environ.setdefault('MPLCONFIGDIR',str(Path('runs/stage13a/v1/cache/matplotlib').resolve()))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from collections import Counter
    out=ROOT/'figures';out.mkdir(exist_ok=True)
    def keep(fig,name):
        fig.tight_layout()
        for ext in ['png','pdf']:fig.savefig(out/f'{name}.{ext}',dpi=180,bbox_inches='tight')
        plt.close(fig)
    rows=pd.read_parquet(ROOT/'stage13a_family_level_results.parquet').to_dict('records')
    counts=Counter((r['I_mean'],r['T_mean']) for r in rows if r['complete'])
    fig,ax=plt.subplots(figsize=(5.5,5))
    for (i,t),n in counts.items():
        ax.scatter(i,t,s=100+35*n,color='#39729a',alpha=.75);ax.annotate(str(n),(i,t),ha='center',va='center',color='white')
    ax.plot([0,1],[0,1],'--',color='gray');ax.set(xlim=(-.07,1.07),ylim=(-.07,1.07),xlabel='Instruct: mean of three replicates',ylabel='Thinking: mean of three replicates',title=f'Equal evidence: {primary["primary"]["n"]} complete families')
    ax.text(.5,-.22,'Numbers show families at each paired outcome; no seed independence.',transform=ax.transAxes,ha='center',fontsize=8);keep(fig,'13A_1_paired_equal_evidence')
    import numpy as np
    c=primary['majority_transitions']['counts']
    matrix=np.array([[c['BOTH_WRONG'],c['THINKING_ONLY']],[c['INSTRUCT_ONLY'],c['BOTH_CORRECT']]])
    fig,ax=plt.subplots(figsize=(6,5));ax.imshow(matrix,cmap='Blues',vmin=0,vmax=max(1,matrix.max()))
    for y in range(2):
        for x in range(2):ax.text(x,y,str(matrix[y,x]),ha='center',va='center',fontsize=18,color='white' if matrix[y,x]>matrix.max()/2 else 'black')
    ax.set_xticks([0,1],['Thinking wrong','Thinking correct']);ax.set_yticks([0,1],['Instruct wrong','Instruct correct'])
    ax.set_title('Three-replicate majority transitions')
    ax.text(.5,-.15,f'All 96 families; unresolved: {c["UNRESOLVED"]}. Cells count independent families.',transform=ax.transAxes,ha='center',fontsize=9)
    keep(fig,'13A_2_majority_transitions')
    def effects(labels,estimates,title,name):
        fig,ax=plt.subplots(figsize=(7,4))
        for j,e in enumerate(estimates):
            if e['effect_pp'] is None:ax.text(j,0,'Not estimable',ha='center');continue
            point=e['effect_pp'];lo,hi=e['ci95_pp'];ax.errorbar(j,point,yerr=[[max(0,point-lo)],[max(0,hi-point)]],fmt='o',capsize=5,color='#39729a')
            ax.annotate(f'n={e["n"]}',(j,point),xytext=(8,5),textcoords='offset points')
        ax.axhline(0,color='gray');ax.axhline(5,color='gray',ls=':',label='Prospective5pp threshold');ax.set_xticks(range(len(labels)),labels);ax.set_xlim(-.5,len(labels)-.5)
        ax.set_ylabel('Thinking − Instruct, percentage points');ax.set_title(title);ax.legend(loc='best',fontsize=8);keep(fig,name)
    old_est=dict(n=old['n'],effect_pp=old['estimate']*100,ci95_pp=[x*100 for x in old['bootstrap95']])
    effects(['Stage12Y\nsingle-run screen','Stage13A\nfresh three-seed confirmation'],[old_est,primary['primary']],'Same frozen cohort; estimates are not independent','13A_3_stage12y_vs_stage13a')
    labels=['Primary','32k-comparable'];est=[primary['primary'],comparable]
    if optional['executed']:labels.append('Optional24\ncap-matched');est.append(optional['estimate'])
    effects(labels,est,'Output-budget sensitivity; not decoding matched','13A_4_budget_sensitivity')

def main():
    primary=load(ROOT/'stage13a_primary_inference.json');comparable=load(ROOT/'stage13a_32k_comparable_sensitivity.json')
    for p,h in load(ROOT/'audit/primary_inference_seal.json')['files'].items():assert sha(p)==h,p
    optional=load(ROOT/'audit/capmatched_status.json')
    assert primary['optional_capmatched_triggered']==optional['executed'] or optional.get('budget_blocked')
    if optional.get('budget_blocked'):raise RuntimeError('Conditional assay required but resource boundary reached: report blocker, do not claim complete.')
    ledger=account('final');assert not ledger['active_jobs'] and ledger['allocated_gpu_hours_upper']<=14
    from collections import defaultdict
    receipts=defaultdict(list)
    for p in (ROOT/'generations').glob('*/result.json'):
        receipt=load(p)
        assert receipt['generation_sha256']==sha(p.parent/'generation.json')
        receipts[str(receipt['job'])].append(receipt['task_id'])
    jobs={j['slurm_job_id']:j for j in ledger['jobs']}
    workers=[]
    for p in (ROOT/'workers').glob('*/environment.json'):
        r=load(p);job=str(r['job']);exit_path=p.parent/'exit.json'
        manifest=load(r['manifest_path']);authorized={t['task_id'] for t in manifest['rows']}
        complete=receipts[job];assert len(set(complete))==len(complete) and set(complete)<=authorized
        batches=[load(x) for x in p.parent.glob('batch_*_started.json')]
        submitted=[tid for batch in batches for tid in batch['tasks']]
        assert len(set(submitted))==len(submitted) and set(complete)<=set(submitted)<=authorized
        if exit_path.exists():
            ex=load(exit_path);assert ex['complete'] and ex['calls']==len(complete)==len(submitted)
            seconds=ex['seconds'];interrupted=False
        else:
            assert job=='133782' and jobs[job]['state']=='TIMEOUT'
            assert len(complete)==59 and len(submitted)==72
            seconds=None;interrupted=True
        workers.append(dict(job=job,node=r['node'],gpu=r['gpu'],calls=len(complete),
            submitted_attempts=len(submitted),interrupted=interrupted,seconds=seconds,
            environment_path=str(p),exit_path=str(exit_path) if exit_path.exists() else None,
            terminal_state=jobs[job]['state']))
    expected=576+72*optional['executed']
    assert sum(w['calls'] for w in workers)==expected
    assert len({tid for ids in receipts.values() for tid in ids})==expected
    preservation=load(ROOT/'audit/recovery_preservation.json')
    for p,h in preservation['completed_files'].items():assert sha(p)==h,p
    for entry in preservation['archived']:
        for name,h in entry['files'].items():assert sha(Path(entry['archive'])/name)==h
    assert sum(w['submitted_attempts'] for w in workers)==expected+13
    ledger.update(workers=workers,new_calls=expected,submitted_generation_attempts=expected+13,interrupted_attempts=13,completed_rows_recomputed=0,target_gpu_hours=10,all_allocations_released=True,
        annotation_counts={name:len(list((ROOT/'audit'/name).glob('*.json'))) for name in ['technical_decisions','technical_adjudications','first_scores','second_scores','score_adjudications']},
        memory_note='Parent allocator peaks do not measure vLLM child allocations; engine logs preserve model/KV memory.')
    save(ROOT/'stage13a_resource_accounting.json',ledger)
    old=load('outputs/stage12ys/v1/audit/phaseA_inference.json')['G_E']
    save(ROOT/'audit/historical_comparison.json',dict(at=now(),primary_seal_sha256=sha(ROOT/'audit/primary_inference_seal.json'),stage12y=old,stage13a=primary['primary'],pooled=False,same_cohort=True))
    state=primary['decision'];rec=RECOMMENDATIONS[state]
    save(ROOT/'stage13a_decision.json',dict(at=now(),decision=state,recommendation=rec,optional=optional,follow_on_launched=False))
    historical=load(ROOT/'audit/historical_preservation.json')['files']
    for p,h in historical.items():assert sha(p)==h,p
    for p,h in load(ROOT/'stage13a_input_hashes.json')['files'].items():assert sha(p)==h,p
    save(ROOT/'audit/final_preservation.json',dict(at=now(),passed=True,historical_files=len(historical)))
    figures(primary,comparable,old,optional)
    e=primary['primary'];b=primary['missingness_bounds'];s=primary['scoreability'];tr=primary['majority_transitions']
    lines=['# Stage13A: confirmatory equal-evidence Thinking advantage','',f'Decision: **{state}**.','',
        f'Exact96 source-frozen MathVision families;576 fresh primary calls,three per checkpoint/family. Both variants received identical Q+E* without images or added reasoning instructions.','',
        f'Primary complete paired families: **{e["n"]}/96**. Thinking minus Instruct: **{e["effect_pp"]} percentage points**,95% family-bootstrap interval **{e["ci95_pp"]}**. Median family difference {e["median_pp"]}pp; positive/zero/negative families {e["positive"]}/{e["zero"]}/{e["negative"]}.',
        '10,000 family resamples; seeds are repeated measurements within families. Frozen confirmation requires at least80 complete families,+5pp,CI lower>0,and the scoreability safeguard.','',
        f'Scoreability: Instruct {s["I"]*100:.2f}%,Thinking {s["T"]*100:.2f}%; difference {primary["scoreability_difference_pp"]:.2f}pp. Full96 missingness bounds: [{b["lower_pp"]:.3f},{b["upper_pp"]:.3f}]pp. Technical missingness is never scored as incorrect.',
        '',f'Majority transitions: {tr["counts"]}. Net Thinking-only families: {tr["net_thinking_only"]}; descriptive exact discordant-family p={tr["exact_two_sided_p"]}.','',
        f'32k-comparable: n={comparable["n"]},effect={comparable["effect_pp"]}pp,95% interval={comparable["ci95_pp"]}. Optional cap-matched panel executed: {optional["executed"]}.',
        '',f'Stage12Y descriptive estimate: {old["estimate"]*100:.2f}pp,95% interval={[x*100 for x in old["bootstrap95"]]}. The same96 families are reused; these estimates are not independent and were not pooled. Stage13A supersedes Stage12Y for the cohort-level Claim1C estimate.','',
        'Interpretation is limited to deployed4B variants under their intended recipes. Checkpoints,sampling settings and output budgets differ. A positive result does not isolate a pure Thinking switch or establish state construction as universal. Negative/partial evidence does not erase selected-case portability; insufficient coverage is a technical limitation.','',
        'All Instruct scoring/QC closed before Thinking outputs were reviewed. All ambiguous cases and a frozen20% random sample were second-reviewed by the same agent; this is not independent-rater reliability. Cap-after-unretracted-final remains scoreable; pre-outcome caps remain missing; normal-stop refusal/no-answer is scientific failure.',
        '',f'Resources: {ledger["new_calls"]} completed logical calls;{ledger["submitted_generation_attempts"]} submitted attempts including13 interrupted by the Slurm wall-time limit,{ledger["allocated_gpu_hours_upper"]:.3f} allocatedGPUh,target<10/hard14. All allocations released. {len(historical)} historical artifacts and source/input seals unchanged. Four PNG/PDF figure pairs saved.',
        '','Exactly one recommendation: '+rec,'','STOP. Recommendation not launched.']
    if optional['executed']:
        e32=optional['estimate']
        lines.insert(lines.index('Exactly one recommendation: '+rec),f'Optional 24-family cap-matched sensitivity: n={e32["n"]} complete families, effect={e32["effect_pp"]}pp, 95% interval={e32["ci95_pp"]}; primary decision unchanged.')
    with (ROOT/'stage13a_summary.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    required=['equal_evidence_confirmation_spec.md','frozen96_manifest.json','input_hashes.json','seed_manifest.json','instruct_equal_evidence_results.parquet','thinking_equal_evidence_results.parquet','scoring_audit.json','family_level_results.parquet','missingness_bounds.json','32k_comparable_sensitivity.json','primary_inference.json','decision.json','resource_accounting.json','summary.md','capmatched24_manifest.json']
    if optional['executed']:required.append('capmatched24_results.parquet')
    save(ROOT/'audit/final_verification.json',dict(at=now(),complete=True,artifacts={str(ROOT/('stage13a_'+name)):sha(ROOT/('stage13a_'+name)) for name in required},figures={str(p):sha(p) for p in (ROOT/'figures').glob('*')},all_gpus_released=True,historical_unchanged=True))
    print(state,rec)

if __name__=='__main__':main()
