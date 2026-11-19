"""Exact-anchor figures with explicit limits of the frozen sparse panel."""
from collections import Counter
from scripts.stage6b.common import OUT,read_json,read_jsonl
from scripts.stage6b.figure_support import plt,np,save,empty,index,BLUE,ORANGE,GREEN,GRAY,RED
from matplotlib.patches import FancyBboxPatch


def source_lines(ax,pair,states):
    for source in pair['sources']:
        values=[states[pair[key]]['source_scores'][source] for key in ['pre_id','post_id']]
        role='previous' if source==pair['pre_source'] else 'new demand' if source==pair['post_source'] else 'alternative'
        ax.plot([0,1],values,'o-',label=f'{source}: {role}')
    ax.set_xticks([0,1],['Before transition','After transition'])
    ax.set_ylabel('Exact source VSD, W2');ax.axhline(.05,color=GRAY,ls=':',lw=1)
    ax.set_title(pair['base_id']);ax.legend(fontsize=7)


def main():
    pairs=read_jsonl(OUT/'c1_dynamics/wandering_fixation_classes.jsonl')
    states={r['id']:r for r in read_jsonl(OUT/'c1_dynamics/exact_source_scores.jsonl')}
    latency=read_json(OUT/'c1_dynamics/transition_latency.json')['rows']
    sources=['c1_dynamics/exact_source_scores.jsonl','c1_dynamics/wandering_fixation_classes.jsonl']
    ordered=sorted(pairs,key=lambda p:(p['split']=='confirmation',p['base_id'],p['transition_span_index']))
    labels=['Previous source','New demanded source','Other source','MIXED','NONE / unresolved','ROI overlap']
    def role(pair,which):
        d=pair[which+'_dominant']
        if not pair['strict_source_identity_valid']:return 5
        if d==pair['pre_source']:return 0
        if d==pair['post_source']:return 1
        if d=='MIXED':return 3
        if d in ['NONE','UNRESOLVED']:return 4
        return 2
    fig,ax=plt.subplots(figsize=(7.5,8))
    from matplotlib.colors import ListedColormap,BoundaryNorm
    colors=[ORANGE,GREEN,BLUE,'#b59ac6',GRAY,'#d8d8d8']
    cmap=ListedColormap(colors);norm=BoundaryNorm(np.arange(-.5,6),6)
    im=ax.imshow([[role(p,'pre'),role(p,'post')] for p in ordered],cmap=cmap,norm=norm,aspect='auto')
    ax.set_xticks([0,1],['Before demand change','After demand change'])
    ax.set_yticks(range(len(ordered)),[p['base_id']+' / '+str(p['transition_span_index'])+' / '+p['split'][:1].upper() for p in ordered],fontsize=6)
    fig.colorbar(im,ax=ax,ticks=range(6),fraction=.04,pad=.03).ax.set_yticklabels(labels)
    save(fig,13,'causal_transition_states','Causal source states at selected demand transitions',
        '35 unique transition/refresh comparisons in20bases;34primary transitions. D=discovery, C=confirmation. Panel below minimum; these are selected anchors, not cohort rates.',sources)
    healthy=[p for p in ordered if p['split']=='confirmation' and p['causal_state_class']=='DEMAND_ALIGNED_SWITCH'][:2]
    fig,axes=plt.subplots(1,2,figsize=(9,4))
    for ax,pair in zip(axes,healthy):source_lines(ax,pair,states)
    save(fig,14,'healthy_switch_examples','Held-out demand-aligned source switches',
        'Illustrative first two eligible confirmation pairs after frozen labels. Numeric source dependence follows the new demand; this does not establish when the evidence was acquired.',sources)
    diag=read_json(OUT/'audit/dynamic_readout_coverage_diagnostic.json')
    fig,axes=plt.subplots(1,2,figsize=(9,4))
    axes[0].bar(['Candidate\nno-change','Matched exact\nno-change'],[diag['total_eligible_no_change_before_matching'],0],color=[GRAY,BLUE])
    axes[0].set_ylabel('Pairs with valid numeric readouts')
    empty(axes[1],'Wandering examples: not estimable\n\nNo matched no-change pair survived\nthe frozen semantic/readout rules.')
    save(fig,15,'wandering_unidentified','Wandering is not identified in this panel',
        'Four numeric-readout no-change intervals exist before matching; zero qualify as the frozen matched controls. Do not label passive movement or missing observations as wandering.',
        ['audit/dynamic_readout_coverage_diagnostic.json','c1_dynamics/no_change_pairs.jsonl'])
    mixed=next(p for p in ordered if p['split']=='confirmation' and p['causal_state_class']=='NO_SWITCH_OR_MIXED')
    fig,axes=plt.subplots(1,2,figsize=(9,4));source_lines(axes[0],mixed,states)
    empty(axes[1],'Strict fixation: zero identified\n\n7of16 selected confirmation comparisons\nare MIXED, not proven fixation.\n\nNo cohort fixation-rate estimate.')
    save(fig,16,'fixation_unresolved','Mixed source dependence does not establish fixation',
        'Example is the first confirmation MIXED comparison, not a fixation case. Frozen dominance margin=.3125 and positive-effect floor=.05; ambiguous sources remain ambiguous.',sources)
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    offsets=sorted({r['latency_reviewed_spans'] for r in latency if r['latency_reviewed_spans'] is not None})
    cats=offsets+['censored']
    for j,split in enumerate(['discovery','confirmation']):
        rows=[r for r in latency if r['split']==split]
        counts=[sum(r['latency_reviewed_spans']==v for r in rows) for v in offsets]+[sum(r['right_censored'] for r in rows)]
        axes[0].bar(np.arange(len(cats))+(j-.5)*.35,counts,width=.35,label=split,color=[BLUE,ORANGE][j])
    axes[0].set_xticks(range(len(cats)),[str(x) for x in cats]);axes[0].set_xlabel('First observed new-source dominance: span offset')
    axes[0].set_ylabel('Selected comparisons');axes[0].legend()
    counts=Counter(r['refresh_class'] for r in latency if r['refresh'])
    names=list(counts);axes[1].barh(range(len(names)),[counts[n] for n in names],color=GREEN)
    axes[1].set_yticks(range(len(names)),[n.replace('_','\n') for n in names],fontsize=7);axes[1].set_xlabel('Selected refresh comparisons')
    save(fig,17,'transition_latency','Observed transition and refresh timing',
        'First observed dominance is not acquisition time. Unobserved earlier spans leave delay unresolved; right censoring is not a proven failure. Sparse anchors only.',
        ['c1_dynamics/transition_latency.json'])
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    classes=sorted({p['causal_state_class'] for p in pairs})
    for ax,key,title in zip(axes,['local_correctness_after','final_correctness'],['Local geometric correctness','Final answer correctness']):
        bottom=np.zeros(len(classes))
        for status,color in [('CORRECT',GREEN),('INCORRECT',RED),('UNRESOLVED',GRAY)]:
            vals=np.array([sum(p['causal_state_class']==c and p[key]==status for p in pairs) for c in classes])
            ax.barh(range(len(classes)),vals,left=bottom,label=status,color=color);bottom+=vals
        ax.set_yticks(range(len(classes)),[c.replace('UNRESOLVED_OVERLAPPING_SOURCE_TOKENS','ROI overlap').replace('NO_SWITCH_OR_','').replace('_',' ') for c in classes],fontsize=6)
        ax.set_title(title);ax.set_xlabel('Selected comparisons');ax.legend(fontsize=6)
    save(fig,18,'correctness_by_state','Correctness stratification after causal state assignment',
        'All selected numeric claims are numerically correct; some geometric roles or final answers are wrong. Numeric contrasts do not establish causation of those errors.',sources)
    fig,ax=plt.subplots(figsize=(10,7));ax.set_xlim(0,10);ax.set_ylim(0,7);ax.axis('off')
    def box(x,y,w,h,text,color):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',fc=color,ec='white'))
        ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10)
    box(3.2,5.9,3.6,.65,'Reasoning demand','#dae6ee')
    box(.6,4.5,3.9,.7,'Demand changes','#e9eff5');box(5.5,4.5,3.9,.7,'Demand stays stable','#e9eff5')
    box(.6,3.15,3.9,.8,'Causal source follows new demand\n→ demand-aligned switch','#dceee7')
    box(5.5,3.15,3.9,.8,'Causal source stays appropriate\n→ demand-aligned hold','#dceee7')
    for x in [2.55,7.45]:
        ax.annotate('',(x,5.25),(5,5.9),arrowprops={'arrowstyle':'->','color':GRAY})
        ax.annotate('',(x,4),(x,4.5),arrowprops={'arrowstyle':'->','color':GRAY})
    box(.6,1.8,3.9,.8,'Demand changes; old source persists\n→ fixation / staleness','#f2e2df')
    box(5.5,1.8,3.9,.8,'Demand stays; source changes\n→ wandering','#f2e2df')
    box(1.45,.35,7.1,.85,'Visual engagement persists after causal grounding collapses\n→ mirage (requires sham and counterfactual validation)','#eee3f2')
    save(fig,24,'conceptual_framework','Demand, causal source use, and failure definitions',
        'Definitions, not prevalence claims. Stage6B finds selected switches and strict mirage candidates; matched holds/wandering and error-promoting fixation remain unidentified.',sources+['c1_mirage/claim_assessment.json'])
    index();print('Saved dynamics figures13–18 and24.')


if __name__=='__main__':main()
