"""Frozen Stage12C figures and report; requires completed scientific analysis."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scripts.stage12c.common import ROOT,load,now
from scripts.stage12c.responses import main as response_archive

COLORS={'C':'#2377b4','T':'#d17720'}


def savefig(fig,name):
    dest=ROOT/'figures';dest.mkdir(exist_ok=True)
    for ext in ['png','pdf']:fig.savefig(dest/f'{name}.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)


def fmt(p):
    if p['estimate'] is None:return f"undefined (0/{p['denominator']})"
    lo,hi=p['wilson95']
    return f"{p['numerator']}/{p['denominator']} ({p['estimate']:.1%});95%CI[{lo:.1%},{hi:.1%}]"


def main():
    assert load(ROOT/'audit/denominator_seal.json')['pass']
    result=load(ROOT/'stage12c_primary_inference.json');decision=load(ROOT/'stage12c_rescue_decision.json')
    accounting=load(ROOT/'stage12c_resource_accounting.json');review=load(ROOT/'stage12c_scoring_review_log.json')
    rows=pd.read_parquet(ROOT/'stage12c_rescue_transitions.parquet')
    traces=pd.read_parquet(ROOT/'stage12c_trace_evidence_states.parquet')
    pathology=pd.read_parquet(ROOT/'stage12c_pathology_transitions.parquet')
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(9,4.7));x=np.arange(4)
    counts=[result['by_stratum'][b]['frozen_total'] for b in ['B1','B2','B3','B4']]
    ax.bar(x,counts,width=.8,color='#e0e4ea',label='Frozen native failures')
    for a,offset in [('C',-.18),('T',.18)]:
        kk=[result['by_stratum'][b][a.lower()]['numerator'] for b in ['B1','B2','B3','B4']]
        ax.bar(x+offset,kk,width=.3,color=COLORS[a],label=a+' rescues')
        for xx,k,b in zip(x+offset,kk,['B1','B2','B3','B4']):
            p=result['by_stratum'][b][a.lower()]
            ax.text(xx,k+.13,f"{k}/{p['denominator']}",ha='center',fontsize=9)
    ax.set_xticks(x,['B1\nPrimary','B2\nDescriptive','B3\nDescriptive','B4\nPrimary'])
    ax.set_ylabel('Independent families');ax.set_title('Frozen native failure map with C/T rescue overlay')
    ax.set_ylim(0,max(counts)+3);ax.legend(fontsize=9,ncol=3)
    fig.text(.12,-.03,'Labels show rescues/scoreable outcomes; gray bars retain all frozen families.',fontsize=9)
    savefig(fig,'figure1_failure_map_rescue')

    fig,ax=plt.subplots(figsize=(8,4.7))
    for j,key in enumerate(['P1','P2','P3','P4']):
        p=result['primary'][key];a=p['arm'];point=p['estimate']
        if point is not None:
            lo,hi=p['wilson95'];ax.errorbar(j,point,yerr=[[point-lo],[hi-point]],fmt='o',color=COLORS[a],capsize=6,markersize=8)
            ax.text(j,hi+.035,f"{p['numerator']}/{p['denominator']}\nmissing:{p['missing']}",ha='center',fontsize=9)
    ax.set_xticks(range(4),['C | B1','T | B1','C | B4','T | B4']);ax.set_ylim(-.04,1.2)
    ax.set_ylabel('Rescue fraction among scoreable outcomes');ax.set_title('Primary rescue estimates: Wilson95% intervals')
    savefig(fig,'figure2_primary_rescue')

    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    order=['BOTH_FAIL','C_ONLY','T_ONLY','BOTH_SUCCEED','UNSCOREABLE_TECHNICAL']
    for ax,b in zip(axes,['B1','B4']):
        sub=rows[rows.bottleneck==b];values=[int((sub.CT_transition==s).sum()) for s in order]
        bars=ax.bar(range(5),values,color=['#7f8792',COLORS['C'],COLORS['T'],'#248269','#c2c5c9'])
        for bar,n in zip(bars,values):ax.text(bar.get_x()+bar.get_width()/2,n+.12,str(n),ha='center')
        ax.set_xticks(range(5),['Both\nfail','C-only','T-only','Both\nsucceed','Missing\npair'],fontsize=9);ax.set_title(b);ax.set_ylim(0,12)
    axes[0].set_ylabel('Independent families');fig.suptitle('C/T paired transitions: variant comparison')
    savefig(fig,'figure3_paired_rescue')

    fig,axes=plt.subplots(1,2,figsize=(11,4.5),sharey=True)
    states=['TRACE_E_FULL','TRACE_E_PARTIAL','TRACE_E_WRONG_OR_CONFLICTING','TRACE_E_NOT_EXTERNALIZED']
    labels=['Full','Partial','Wrong/conflicting','Not externalized'];colors=['#19856c','#d8b64b','#b95b61','#939ba8']
    for ax,a in zip(axes,'CT'):
        bottom=np.zeros(3)
        for state,label,color in zip(states,labels,colors):
            v=[result['visible_evidence_B1'][a][name]['counts'].get(state,0) for name in ['rescued','not_rescued','unscoreable']]
            ax.bar(range(3),v,bottom=bottom,label=label,color=color);bottom+=v
        ax.set_xticks(range(3),['Rescued','Not rescued','Unscoreable'],fontsize=9);ax.set_title(a+' | B1');ax.set_ylim(0,12)
    axes[0].set_ylabel('Independent families');axes[1].legend(fontsize=8)
    fig.suptitle('B1 visible evidence externalization; no hidden-retrieval inference')
    savefig(fig,'figure4_B1_visible_evidence')

    fig,axes=plt.subplots(1,2,figsize=(12,4.5),sharey=True)
    categories=['RESOLVED','PRESERVED','CHANGED','NO_PRIOR_PATHOLOGY','NEW_PATHOLOGY','UNSCOREABLE_TECHNICAL']
    for ax,a in zip(axes,'CT'):
        d=result['pathology_B4'][a]['NO_union'];counts=[d[c]['count'] for c in categories];rescues=[d[c]['rescued'] for c in categories]
        ax.bar(range(6),counts,color='#d9dfe5',label='All B4');ax.bar(range(6),rescues,color=COLORS[a],label='Rescued')
        ax.set_xticks(range(6),['Resolved','Shared\nlabel','Changed','No prior\nR1–R3','New','Unscoreable'],fontsize=8)
        ax.set_title(a);ax.set_ylim(0,12);ax.legend(fontsize=8)
    axes[0].set_ylabel('Independent families');fig.suptitle('B4 behavior relative to the union of native/oracle R1–R3')
    fig.text(.12,-.03,'R4 advancing computation is descriptive, not a pathology; N and O transitions also reported separately.',fontsize=9)
    savefig(fig,'figure5_B4_pathology')

    response_archive()
    summary=['# Stage12C selective rescue','',f"**{decision['decision']}**. Completed {now()}.",'',decision['interpretation'],'',
        '61 frozen MathVision families and all prior E/N/O labels remain unchanged. Exactly122 new calls:24 sanity calls reused within the full cohort,then98 remaining calls. No repeat generation,oracle or mechanistic follow-on.','',
        'C used the original image/question plus ` Let\'s think step by step.` on pinned4B Instruct with temperature.7,top-p.8,top-k20,repetition1,presence1.5,cap32768. T used the original image/question on pinned4B Thinking with temperature1,top-p.95,top-k20,repetition1,presence0,cap40960. The user resolved T-recipe inheritance prospectively before generation; the synthetic-counting greedy512 recipe was not inherited. BF16/vLLM,original per-family seeds and image preprocessing were preserved.','',
        '## Technical validity','', '| Arm | Valid inputs | Scoreable | Pre-outcome caps |','|---|---:|---:|---:|']
    ds=load(ROOT/'audit/denominator_seal.json')
    for a,s in ds['summaries'].items():summary.append(f"| {a} | {s['INPUT_VALID']}/61 | {s['SCOREABLE']}/61 | {s['TRUNCATED_BEFORE_OUTCOME']}/61 |")
    summary.extend(['','Validity was sealed before correctness. Repetition alone never excluded a response. Missing outcomes are neither wrong answers nor paired failures.','',
        '## Primary rescue results','', '| Endpoint | Rescue estimate | Frozen total | Missing | Identification bounds |','|---|---|---:|---:|---|'])
    for key,p in result['primary'].items():summary.append(f"| {key}: {p['arm']} in {p['stratum']} | {fmt(p)} | {p['frozen_total']} | {p['missing']} | {p['missingness_identification_bounds']} |")
    summary.extend(['','Intervals are family-level Wilson95%; identification bounds range from observed rescues/11 to(rescues+missing)/11 and do not impute correctness. B1 means incomplete demonstrated evidence recovery: seven explicit-wrong and four unresolved-only E profiles.','',
        '## Selectivity and paired comparisons','', '| Contrast | Estimate | Bootstrap95% |','|---|---:|---|'])
    for name,v in result['contrasts'].items():summary.append(f"| {name} | {v['estimate']} | {v['percentile95']} |")
    summary.extend(['',f"4000 family-cluster draws,seed{result['bootstrap_seed']}; family-equal weighting and C/T pairing retained. B1/B4 are resampled separately for selectivity. B2/B3 are descriptive only.",'',
        'N versus C is a same-checkpoint prompt comparison. T versus C/N is a checkpoint-variant comparison; it does not isolate a causal Thinking-on effect. Overall performance is secondary.',''])
    for a,p in result['overall_accuracy'].items():summary.append(f'- {a} marginal accuracy: {fmt(p)}; missing{p["missing"]}.')
    summary.extend(['','Jointly scoreable paired counts (missing pairs separate):','', '```json',json.dumps(result['overall_paired'],indent=2),'```','',
        'B1 explicit-wrong versus unresolved-only transitions:','', '```json',json.dumps(result['b1_subtypes'],indent=2),'```','',
        '## Visible evidence and reasoning behavior','',
        'All52 traces from the26 complete native failures were annotated against frozen E* before new correctness was opened. Packets omitted old outcomes,bottleneck labels and paired traces. TRACE_E_FULL supports correct visible externalization; it does not prove hidden retrieval. NOT_EXTERNALIZED does not show internal absence.','',
        '```json',json.dumps(result['visible_evidence_B1'],indent=2),'```','',
        'B4 pathology transitions relative to N,O and their union are saved separately. R1–R3 can overlap; R4 is advancing computation and is never an exclusion. Figure5 shows the union for compact display.','',
        '## Review and resources','',
        f"All122 first scores sealed;{review['audit']['second_pass_calls']} second reviews,including every ambiguity and the deterministic20% clean-family audit. This is single-agent,separate-pass quality control,not independent inter-rater reliability. Review/adjudication records are immutable.",'',
        f"New allocated GPU-hours:{accounting['allocated_gpu_hours']:.6f},including startup. All allocations released. Target<6,hard8. Existing project-local environment,models and dataset reused without installs or downloads.",'',
        'This is the same developmental61-family cohort. Small B1/B4 cells and missingness limit precision; no benchmark-wide prevalence claim or causal checkpoint claim follows.','',
        '## Figures and full responses',''])
    for name,title in [('figure1_failure_map_rescue','Failure map and rescues'),('figure2_primary_rescue','Primary rescue intervals'),('figure3_paired_rescue','Paired transitions'),('figure4_B1_visible_evidence','B1 visible evidence'),('figure5_B4_pathology','B4 behavior transitions')]:
        summary.append(f'- [{title}](figures/{name}.png) · [PDF](figures/{name}.pdf)')
    summary.extend(['','[Full unabridged C/T responses](../../../reports/stage12c/v1/index.md).','',
        '## Exactly one recommendation','',decision['recommendation'],'','**STOP. Recommendation not executed.**'])
    dest=ROOT/'stage12c_summary.md';assert not dest.exists();dest.write_text('\n'.join(summary)+'\n')


if __name__=='__main__':main()
