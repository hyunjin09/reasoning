"""Render the16 plan-required scientific figures from saved base-level evidence."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage4a.prepare_config import OUT, read_json, read_jsonl, write_json
from visual_reasoning.stage4a.analysis import EVENTS

FIG=OUT/'analysis/figures'
COLORS={'A':'#2768a5','B':'#d47b21'}
UNIT='nats / candidate token'


def save(fig, number, name, caption, index):
    stem=f'{number:02d}_{name}'
    fig.savefig(FIG/f'{stem}.png',dpi=180,bbox_inches='tight')
    fig.savefig(FIG/f'{stem}.pdf',bbox_inches='tight')
    plt.close(fig)
    index.append({'number':number,'stem':stem,'caption':caption})


def trajectory(ax, values, label, color):
    a=np.asarray(values)
    ax.plot(range(3),np.median(a,axis=0),'-o',color=color,label=label)
    ax.fill_between(range(3),np.quantile(a,.25,axis=0),np.quantile(a,.75,axis=0),color=color,alpha=.12)
    ax.set_xticks(range(3),EVENTS);ax.axhline(0,color='gray',lw=.7)


def identity(ax, x, y, xlabel, ylabel):
    ax.scatter(x,y,s=23,alpha=.75,color='#2768a5')
    lo=min(0,min(x),min(y));hi=max(x+y)
    ax.plot([lo,hi],[lo,hi],'--',lw=.8,color='gray')
    ax.axvline(0,color='gray',lw=.5);ax.axhline(0,color='gray',lw=.5)
    ax.set(xlabel=xlabel,ylabel=ylabel)


def main():
    FIG.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.constrained_layout.use':True})
    data=read_json(OUT/'phase_b_source_switch/dynamic_selectivity.json');w=data['W2'];wide=data['W8'];bases=list(w)
    summary=read_json(OUT/'analysis/selection_switch_refresh.json')
    trigger=read_json(OUT/'phase_c_trigger/trigger_selectivity.json')['bases']
    semantic=read_json(OUT/'phase_d_counterfactual_refresh/counterfactual_refresh_statistics.json')['bases']
    phenotype=read_json(OUT/'analysis/native_failure_phenotypes.json')['bases']
    index=[]
    fig,ax=plt.subplots(figsize=(6.4,4))
    for x in ('A','B'):trajectory(ax,[[r['VSD'][e][x] for e in EVENTS] for r in w.values()],f'ROI {x}',COLORS[x])
    ax.set(title='Causal visual dependence follows A → B → A demand',ylabel=f'W2 VSD ({UNIT})');ax.legend()
    save(fig,1,'causal_vsd','48 independent bases; median lines and interquartile bands. W2 source deletion is primary.',index)
    fig,ax=plt.subplots(figsize=(6.4,4))
    trajectory(ax,[[r['S_'+e] for e in EVENTS] for r in w.values()],'Demanded minus other','#397655')
    ax.set(title='Demand-aligned causal selectivity',ylabel=f'S ({UNIT})');ax.legend()
    save(fig,2,'selectivity','Medians and interquartile ranges, not confidence intervals. Positive values favor the demanded ROI.',index)
    for num,first,last,title in [(3,'A1','B','A → B switch'),(4,'B','A2','B → A refresh')]:
        fig,ax=plt.subplots(figsize=(5.4,4.6))
        # A-minus-B on both axes makes an actual dominance crossover visible.
        x=[w[b]['VSD'][first]['A']-w[b]['VSD'][first]['B'] for b in bases]
        y=[w[b]['VSD'][last]['A']-w[b]['VSD'][last]['B'] for b in bases]
        identity(ax,x,y,f'{first}: VSD A − B',f'{last}: VSD A − B');ax.set_title(title)
        save(fig,num,'switch_scatter' if num==3 else 'refresh_scatter','Each dot is one base. Axes use the same A-minus-B orientation; opposite-sign quadrants show crossover.',index)
    fig,axs=plt.subplots(1,3,figsize=(12,3.7))
    for ax,e in zip(axs,EVENTS):
        demanded,other=('B','A') if e=='B' else ('A','B')
        identity(ax,[r['VSD'][e][other] for r in w.values()],[r['VSD'][e][demanded] for r in w.values()],'Other ROI VSD','Demanded ROI VSD');ax.set_title(e)
    save(fig,5,'demanded_vs_other','48 paired bases per event. Above the diagonal favors the demanded source.',index)
    fig,axs=plt.subplots(1,3,figsize=(12,3.7))
    for ax,e in zip(axs,EVENTS):
        identity(ax,[w[b]['S_'+e] for b in bases],[wide[b]['S_'+e] for b in bases],'W2 selectivity','W8 selectivity');ax.set_title(e)
    save(fig,6,'window_sensitivity','W8 was predeclared sensitivity; no per-base window selection. Full dynamic counts: W2=36/48, W8=30/48.',index)
    fig,axs=plt.subplots(1,3,figsize=(12,3.7))
    for ax,e in zip(axs,EVENTS):
        x='B' if e=='B' else 'A'
        identity(ax,[r['VSD'][e][x] for r in w.values()],[r['joint_AB'][e] for r in w.values()],'Demanded-only W2 VSD','Joint A+B W2 VSD');ax.set_title(e)
    save(fig,7,'joint_suppression','Joint suppression uses an explicit union reduction. Joint-minus-single is not a unique information fraction.',index)
    fig,ax=plt.subplots(figsize=(8,4.5))
    keys=['dynamic_full','successful_switch','successful_refresh','failed_switch_A_dominant','failed_refresh_stale_B','tied_retrieval_events','mixed_retrieval_events','local_insensitive_events']
    labels=['Full A→B→A','Successful switch','Successful refresh','A-dominant at B','Stale B at A2','Tied at ≥1 event','Mixed at ≥1 event','Insensitive at ≥1 event']
    counts=[sum(bool(r[k]) for r in phenotype.values()) for k in keys]
    ax.barh(labels,counts,color='#597c94');ax.invert_yaxis();ax.set(xlim=(0,52),xlabel='Bases / 48',title='Native causal phenotypes (overlapping)')
    for i,n in enumerate(counts):ax.text(n+.5,i,str(n),va='center')
    save(fig,8,'dynamic_classes','These descriptive classes overlap. Threshold=0.05 nats/candidate token; weak demanded effects and stale dominance are distinct.',index)
    fig,ax=plt.subplots(figsize=(6.8,4))
    if trigger:
        trajectory(ax,[[r['TS_'+e] for e in EVENTS] for r in trigger.values()],'Trigger selectivity','#795895')
        ax.set(ylabel=f'TS ({UNIT})',title='R16 trigger retargeting fails the full robust criterion');ax.legend()
    else:ax.text(.5,.5,'Phase C gate closed; no confirmatory trigger run',ha='center');ax.axis('off')
    save(fig,9,'trigger_selectivity','Frozen layers16–23, current query. Median/IQR; all three TS tests fail the full robustness rule.',index)
    fig,axs=plt.subplots(1,2,figsize=(9.5,4))
    if trigger:
        for ax,k,ends in zip(axs,('Switch_AB','Refresh_BA'),(('A1','B'),('B','A2'))):
            ax.scatter([w[b][k] for b in bases],[sum(trigger[b]['TS_'+e] for e in ends) for b in bases],s=23,alpha=.75)
            ax.axhline(0,color='gray',lw=.7);ax.set(xlabel=f'Native {k}',ylabel='Demand-aligned trigger contrast sum')
    else:
        for ax in axs:ax.text(.5,.5,'Gate closed',ha='center');ax.axis('off')
    save(fig,10,'trigger_vs_switch','Descriptive paired scatter only; no correlation-selected examples or mediation inference.',index)
    fig,ax=plt.subplots(figsize=(6.8,4))
    for x in ('A','B'):trajectory(ax,[[r[e][x+'_effect'] for e in EVENTS] for r in semantic.values()],f'{x} semantic edit',COLORS[x])
    ax.set(title='Fixed-history factorial semantic control',ylabel=f'Native preference loss ({UNIT})');ax.legend()
    save(fig,11,'semantic_trajectory','First24 frozen primary bases; each effect averages both contexts of the other fact. Median/IQR.',index)
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    x=np.arange(len(semantic));rows=list(semantic.values())
    axs[0].scatter(x,[r['A2']['A_effect'] for r in rows],label='A semantic',color=COLORS['A'])
    axs[0].scatter(x,[r['A2']['B_effect'] for r in rows],label='B semantic',color=COLORS['B'])
    axs[0].scatter(x,[r['A2']['demanded_sham_magnitude'] for r in rows],label='|A sham|',marker='x',color='gray')
    axs[0].set(xlabel='Frozen subset order',ylabel=UNIT,title='A2 semantic effects and rendering control');axs[0].legend()
    identity(axs[1],[r['A2']['A_factorial_contexts'][0] for r in rows],[r['A2']['A_factorial_contexts'][1] for r in rows],'OO − AO (native B)','OB − AB (changed B)')
    save(fig,12,'fixed_history_refresh','Image varies throughout fixed-history replay. This is not a cache splice or a natural free rollout; both factorial contexts are shown.',index)
    for num,success,failure,name in [(13,'successful_switch','failed_switch_A_dominant','switch_examples'),(14,'successful_refresh','failed_refresh_stale_B','refresh_examples')]:
        fig,axs=plt.subplots(1,2,figsize=(10,4))
        for ax,key,label in zip(axs,(success,failure),('Successful','Native stale-source signature')):
            selected=next((b for b in bases if phenotype[b][key]),None)
            if selected is None and key=='failed_switch_A_dominant':
                selected=next((b for b in bases if 'B' in phenotype[b]['tied_retrieval_events']),None)
                label='Tied at B (no A-dominant case)'
            if selected is None:ax.text(.5,.5,'No qualifying base',ha='center');continue
            for source in ('A','B'):ax.plot(range(3),[w[selected]['VSD'][e][source] for e in EVENTS],'-o',label=source,color=COLORS[source])
            ax.set_xticks(range(3),EVENTS);ax.axhline(.05,color='gray',ls=':',lw=.8)
            ax.set(title=f'{label}\nbase {selected}',ylabel=f'W2 VSD ({UNIT})');ax.legend()
        save(fig,num,name,'First qualifying base in frozen cohort order for each predeclared causal phenotype. Illustrative only; not selected by attention or magnitude.',index)
    tel=read_jsonl(OUT/'telemetry/attention_qk_alphav.jsonl')
    lookup={(r['base_problem_id'],r['event']):r for r in tel}
    fig,axs=plt.subplots(2,2,figsize=(10,7))
    for row,layer in enumerate(('28','29')):
        for col,metric in enumerate(('mean_attention_density','mean_qk_cosine')):
            ax=axs[row,col]
            for role,style in [('selected','-'),('all','--')]:
                for x,g in [('A','T'),('B','M')]:
                    v=[[lookup[b,e]['layers'][layer][role]['groups'][g][metric] for e in EVENTS] for b in bases]
                    ax.plot(range(3),np.median(v,axis=0),style+'o',color=COLORS[x],label=f'{x} {role}')
            ax.set_xticks(range(3),EVENTS);ax.set(title=f'Layer {layer}',ylabel=metric.replace('mean_','').replace('_',' '));ax.legend(fontsize=8)
    save(fig,15,'passive_support','Passive medians for frozen selected heads and all32 heads. No causal interpretation from attention/QK alone.',index)
    fig,ax=plt.subplots(figsize=(10,4.8));ax.axis('off')
    ax.text(.5,.95,'Observed: demand-aligned causal visual dependence',ha='center',fontsize=15,weight='bold')
    for i,(e,source) in enumerate(zip(EVENTS,('A','B','A'))):
        xpos=.15+.35*i
        ax.text(xpos,.68,f'{e}: demand {source}\n\nROI {source} > other\nmedian S={summary["primary_family"]["S_"+e]["median"]:.3f}',ha='center',va='center',bbox={'boxstyle':'round,pad=.8','facecolor':'#edf2f6','edgecolor':COLORS[source]})
        if i<2:ax.annotate('',xy=(xpos+.245,.68),xytext=(xpos+.115,.68),arrowprops={'arrowstyle':'->','lw':1.8})
    ax.text(.5,.32,'36/48 bases meet the full W2 dynamic definition; native refresh is supported.',ha='center')
    ax.text(.5,.17,'R16 trigger retargeting: not robust across events.\nFixed-history semantic challenge remains secondary; Q mediation is unresolved.',ha='center',color='#654b42')
    save(fig,16,'conceptual_result','Diagram reflects the observed causal result and its mechanistic limits; it does not assert the unsupported trigger or Q-mediated chain.',index)
    write_json(FIG/'figure_index.json',{'figures':index,'count':len(index),'units':UNIT})
    text=['# Stage4A figures','','All inferential units are independent base IDs. Bands show interquartile ranges.','']
    for r in index:text += [f'## {r["number"]}. {r["stem"]}', '',r['caption'],'',f'![{r["stem"]}]({r["stem"]}.png)', '',f'[PDF]({r["stem"]}.pdf)','']
    (FIG/'README.md').write_text('\n'.join(text))
    print({'figures':len(index),'png_pdf_pairs':len(index)})


if __name__=='__main__':main()
