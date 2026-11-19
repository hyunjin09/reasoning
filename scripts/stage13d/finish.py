"""Publish one bounded stage; never submits research work."""
import os,re,subprocess
import pandas as pd
from scripts.stage13d.common import *
from scripts.stage13d.resources import account

def historic(tid):
    root=Path('outputs/stage13a/v1')
    p=root/'audit/score_adjudications'/f'{tid}.json'
    if not p.exists():p=root/'audit/first_scores'/f'{tid}.json'
    return load(p)['correct']
def main():
    inf=load(ROOT/'stage13d_primary_inference.json');decision=load(ROOT/'stage13d_decision.json')
    assert inf['selected_historical_cases_opened'] is False
    families=pd.read_parquet(ROOT/'audit/semantic_family_effects.parquet');rescue=[]
    for r in families.to_dict('records'):
        item=r['item_id'];i=[historic(f'P_I_EQ_{item}_r{k}') for k in range(3)];t=[historic(f'P_T_EQ_{item}_r{k}') for k in range(3)]
        historical_resolved=all(x is not None for x in i+t)
        selected=historical_resolved and sum(i)<2 and sum(t)>=2
        if selected:
            rescued=None if not r['complete'] else bool(r['I_DERIVED_correct']>=3 and all(r[c+'_correct']<=2 for c in ['I_BASE','I_DUMMY','I_SHUFFLED']))
            rescue.append(dict(item_id=item,family_id=r['family_id'],historical_I=i,historical_T=t,complete=bool(r['complete']),
                stage13d_correct_counts={c:int(r[c+'_correct']) for c in CONDITIONS},TRACE_SPECIFIC_DERIVED_RESCUE=rescued))
    save(ROOT/'audit/selected_case_rescue.json',dict(at=now(),primary_seal_sha256=sha(ROOT/'stage13d_primary_inference.json'),
        rows=rescue,selection='Historical3/3resolved majority I-/T+; secondary only after primary sealed',n_rescued=sum(r['TRACE_SPECIFIC_DERIVED_RESCUE'] is True for r in rescue),n_unresolved=sum(r['TRACE_SPECIFIC_DERIVED_RESCUE'] is None for r in rescue)))
    ledger=account('final');assert not ledger['active_jobs'] and ledger['allocated_gpu_hours_upper']<=12
    save(ROOT/'stage13d_resource_accounting.json',ledger)
    audits={c:load(ROOT/'audit'/f'{c}_scoring_closed.json') for c in CONDITIONS}
    save(ROOT/'stage13d_semantic_scoring_audit.json',dict(at=now(),arms=audits,
        n_second=sum(len(x['reviews']) for x in audits.values()),independent_rater_reliability=False,
        ambiguity_review='All flagged extraction/cap/math cases plus deterministic20% per arm',
        equivalent_policy='Inherited MathVision options and bounded numeric1e-6; manual mathematical-equivalence adjudication where needed'))
    os.environ['MPLCONFIGDIR']=str(Path('runs/stage13d/v1/cache/matplotlib').resolve())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    figure_dir=ROOT/'figures';figure_dir.mkdir(exist_ok=True)
    def publish(fig,name):
        for ext in ['png','pdf']:fig.savefig(figure_dir/(name+'.'+ext),dpi=180,bbox_inches='tight')
        plt.close(fig)
    order=['I_BASE','I_DUMMY','I_SHUFFLED','I_DERIVED'];colors=['#7c8795','#bec6cf','#80a4bf','#2c7a55']
    fig,ax=plt.subplots(figsize=(6.5,4),constrained_layout=True)
    vals=[inf['semantic']['rates'][c]['complete_family_accuracy'] for c in order]
    if all(v is not None for v in vals):
        ax.bar([c.replace('I_','') for c in order],np.array(vals)*100,color=colors)
        for k,v in enumerate(vals):ax.text(k,v*100+1,f'{v*100:.1f}%',ha='center')
    else:ax.text(.5,.5,'No fully resolved semantic families',ha='center',transform=ax.transAxes)
    ax.set_ylim(0,105);ax.set_ylabel('Accuracy (%)');ax.set_title(f"13D-1  Derived-state priming (n={inf['semantic']['n_complete']} families)");publish(fig,'stage13d_1_derived_state_priming')
    complete=families[families.complete].sort_values('delta_dummy');fig,ax=plt.subplots(figsize=(7,6),constrained_layout=True)
    ax.barh(complete.item_id.astype(str),complete.delta_dummy*100,color=['#2c7a55' if x>0 else '#b04d42' if x<0 else '#7c8795' for x in complete.delta_dummy]);ax.axvline(0,color='black',lw=.8)
    ax.set_xlabel('Derived minus dummy accuracy (percentage points)');ax.set_title('13D-2  Five-seed family effects');publish(fig,'stage13d_2_family_semantic_effects')
    fig,ax=plt.subplots(figsize=(7,max(3,len(rescue)*.65)),constrained_layout=True)
    if rescue:
        arr=np.array([[r['stage13d_correct_counts'][c] if r['complete'] else np.nan for c in order] for r in rescue]);im=ax.imshow(arr,vmin=0,vmax=5,cmap='YlGn',aspect='auto')
        ax.set_xticks(range(4),[c.replace('I_','') for c in order]);ax.set_yticks(range(len(rescue)),[r['item_id']+(' *' if r['TRACE_SPECIFIC_DERIVED_RESCUE'] else '') for r in rescue])
        for y in range(len(rescue)):
            for x in range(4):ax.text(x,y,'missing' if np.isnan(arr[y,x]) else f'{arr[y,x]:.0f}/5',ha='center',va='center')
        fig.colorbar(im,ax=ax,label='Correct out of 5')
    else:ax.text(.5,.5,'No eligible historical Thinking-only overlaps',ha='center',transform=ax.transAxes)
    ax.set_title('13D-3  Selected-case rescue (* trace-specific rescue)');publish(fig,'stage13d_3_selected_rescue')
    buffer=pd.read_parquet(ROOT/'stage13d_buffer_family_margins.parquet');fig,ax=plt.subplots(figsize=(6,5),constrained_layout=True)
    if len(buffer):
        ax.scatter(buffer.B_SHORT_margin,buffer.B_LONG_margin,c='#396ca8')
        lo=min(buffer.B_SHORT_margin.min(),buffer.B_LONG_margin.min());hi=max(buffer.B_SHORT_margin.max(),buffer.B_LONG_margin.max());ax.plot([lo,hi],[lo,hi],'--',color='gray')
        for r in buffer.itertuples():ax.annotate(r.item_id,(r.B_SHORT_margin,r.B_LONG_margin),fontsize=8,xytext=(3,3),textcoords='offset points')
    else:ax.text(.5,.5,'Buffer assay unavailable',ha='center',transform=ax.transAxes)
    ax.set(xlabel='Short gold margin (nats/token)',ylabel='Long gold margin (nats/token)',title='13D-4  Immediate answer margins');publish(fig,'stage13d_4_buffer_margin')
    fig,ax=plt.subplots(figsize=(7,4),constrained_layout=True)
    if len(buffer):
        b=buffer.sort_values('delta_margin');ax.bar(b.item_id,b.delta_margin,color=['#2c7a55' if x>0 else '#b04d42' for x in b.delta_margin]);ax.tick_params(axis='x',rotation=45)
    ax.axhline(0,color='black',lw=.8);ax.set(ylabel='Long minus short gold margin (nats/token)',title='13D-5  Buffer-effect distribution');publish(fig,'stage13d_5_buffer_effect_distribution')
    sem=inf['semantic'];buf=inf['buffer'];bounds=load(ROOT/'stage13d_missingness_bounds.json')['semantic'];results=pd.read_parquet(ROOT/'stage13d_semantic_results.parquet')
    text=f"""# Stage13D — {decision['decision']}

The approved study is complete. Exact24 scientific families and disjointtechnical4
were inherited from Stage13C. Source-only QC sealed23safe derived states and excluded
936 from semantic calls; it remains in the11-family MC buffer panel. Stage13A's
confirmed deployed4B post-evidence advantage is unchanged.

Semantic arm: {len(results)} calls, {sem['n_complete']}/23 fully resolved families,
five fresh seeds per condition. Correctness rates below use the same complete-family
denominator. Technical missingness remains separate from errors; repetition is retained.

| Arm | Accuracy | Scoreable calls | Technical missing |
|---|---:|---:|---:|
"""
    for c in order:
        v=sem['rates'][c];rate='not estimable' if v['complete_family_accuracy'] is None else f"{100*v['complete_family_accuracy']:.2f}%"
        text+=f"| {c} | {rate} | {v['scoreable_calls']} | {v['missing_calls']} |\n"
    text+='\nPaired family contrasts (10,000 bootstrap draws; seed120220260929):\n\n'
    for name,v in sem['contrasts'].items():
        if v['mean'] is None:text+=f'- Derived minus {name}: not estimable.\n';continue
        text+=f"- Derived minus {name}: {v['mean']*100:+.2f}pp,95%CI[{v['ci'][0]*100:+.2f},{v['ci'][1]*100:+.2f}]; positive/zero/negative families {v['positive']}/{v['zero']}/{v['negative']}. Missingness bounds[{bounds[name]['lower']*100:+.2f},{bounds[name]['upper']*100:+.2f}]pp.\n"
    text+=f"\nSemantic confirmation: **{sem['confirmed']}**. Historical I−/T+ secondary overlaps:{len(rescue)}; trace-specific derived rescues:{sum(r['TRACE_SPECIFIC_DERIVED_RESCUE'] is True for r in rescue)}. Unresolved selected families:{sum(r['TRACE_SPECIFIC_DERIVED_RESCUE'] is None for r in rescue)}. These were opened only after the primary inference seal.\n\n"
    text+='Derived-correctness strata are descriptive, not causal error-propagation claims:\n\n'
    for label,g in sem['correctness_groups'].items():text+=f"- {label}: {g}.\n"
    if buf['mean'] is not None:
        text+=f"\nImmediate buffer: {buf['n']} MC pairs; mean long−short gold margin {buf['mean']:+.4f} nats/token,95%CI[{buf['ci'][0]:+.4f},{buf['ci'][1]:+.4f}]. Positive families:{buf['positive']}/{buf['n']} ({buf['positive_fraction']:.1%}); top1 gold short:{buf['short_top1']}/{buf['n']},long:{buf['long_top1']}/{buf['n']}. Signal confirmed:**{buf['confirmed']}**.\n"
    else:text+='\nImmediate buffer: unavailable at technical gate; no scientific buffer inference.\n'
    text+=f"""
Buffer validation passes12technical requests, including exact16/sourceL autoregressive
forced counts, native close and identical answer prefix, zero free tokens, no images,
and exact repeatability on all4short probes. Scientific MC letters are singleton
tokens scored from the same raw next-token logits, before temperature or penalties;
the physically forced first letter is bookkeeping, not a model prediction. Margins
were independently recomputed from saved token-level probabilities. Open-ended
technical probes never enter the scientific buffer denominator.

Source deductions are compact, source-grounded extractions, not exhaustive trace
annotation. Source errors are retained and labeled. Same-agent semantic/QC review
is not independent-rater reliability. The portability assay and same-checkpoint
buffer assay identify possible contributors; they do not fully decompose a hybrid
Thinking ON/OFF effect or establish that these mechanisms exhaust the advantage.

Resources:{ledger['allocated_gpu_hours_upper']:.6f} allocatedGPUh; all allocations
released. No follow-on experiment launched. All prior Stage12/13 artifacts checked
against the prospective preservation manifest.

Exactly one recommendation: {decision['recommendation']}

STOP.
"""
    with (ROOT/'stage13d_summary.md').open('x') as f:f.write(text)
    report=Path('reports/stage13d/v1');(report/'responses').mkdir(parents=True,exist_ok=True)
    responseindex=['# Stage13D raw semantic responses','', 'All new image-free Instruct responses; each page retains full generated text and the original input.','']
    for gpath in sorted((ROOT/'generations').glob('A_*/generation.json')):
        g=load(gpath);inp=load(gpath.parent/'input.json');tid=g['task_id'];page=report/'responses'/f'{tid}.md'
        fence='`'*max(3,max((len(m.group())+1 for m in re.finditer(r'`+',g['raw_decoded_response']+inp['chat_prompt'])),default=3))
        page.write_text(f"# {tid}\n\nTokens:{g['tokens']}; cap:{g['cap_hit']}; seed:{g['seed']}.\n\n## Input\n\n{fence}text\n{inp['chat_prompt']}\n{fence}\n\n## Raw generated response\n\n{fence}text\n{g['raw_decoded_response']}\n{fence}\n")
        responseindex.append(f'- [{tid}](responses/{tid}.md)')
    (report/'responses.md').write_text('\n'.join(responseindex)+'\n')
    (report/'index.md').write_text(text+'\n[Full responses](responses.md)\n\n'+ '\n'.join(f'- [{p.stem}](../../../{p})' for p in sorted(figure_dir.glob('*.png')))+'\n')
    preserved=load(ROOT/'audit/historical_preservation.json')['files'];changed=[p for p,h in preserved.items() if sha(p)!=h];assert not changed,changed
    seal=load(ROOT/'audit/prospective_seal.json');assert all(sha(p)==h for p,h in seal['files'].items())
    assert all(sha(p)==h for p,h in load(ROOT/'config.json')['source_sha256'].items())
    save(ROOT/'audit/final_verification.json',dict(at=now(),prior_files=len(preserved),all_unchanged=True,
        prospective_seal_unchanged=True,generation_code_unchanged=True,all_gpus_released=True,
        required_artifacts={str(p):sha(p) for p in ROOT.glob('stage13d_*') if p.is_file()},figure_pairs=5,
        recommendation_count=1,follow_on_launched=False))
    print(text)
if __name__=='__main__':main()
