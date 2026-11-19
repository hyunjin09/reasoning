"""Native geometry and secondary controlled/natural validation figures."""
from collections import defaultdict
from PIL import Image
from scripts.stage6b.common import OUT,read_json,read_jsonl
from scripts.stage6b.figure_support import plt,np,save,empty,index,BLUE,ORANGE,GREEN,GRAY,RED


def geometry():
    model=read_json(OUT/'trajectory/pca_discovery.json')
    points=read_jsonl(OUT/'trajectory/pca_all_projections.jsonl')
    fig,axes=plt.subplots(1,2,figsize=(10,4.5))
    for ax,split,color in zip(axes,['discovery','confirmation'],[BLUE,ORANGE]):
        rows=[r for r in points if r['split']==split and r['review_scope']=='manual_semantic_prefix' and r['condition']=='intact']
        ax.scatter([r['PC1'] for r in rows],[r['PC2'] for r in rows],s=8,alpha=.35,color=color)
        ax.set_title(split+' ('+str(len(rows))+' reviewed states)');ax.set_xlabel('PC1');ax.set_ylabel('PC2')
    limits=[min(ax.get_xlim()[0] for ax in axes),max(ax.get_xlim()[1] for ax in axes)]
    vertical=[min(ax.get_ylim()[0] for ax in axes),max(ax.get_ylim()[1] for ax in axes)]
    for ax in axes:ax.set_xlim(limits);ax.set_ylim(vertical)
    save(fig,19,'passive_pca','Discovery fit and unchanged confirmation projection',
        f"Manual intact endpoints; equal discovery-base weights. PC1/PC2 explain{model['explained_variance_ratio'][0]:.1%}/{model['explained_variance_ratio'][1]:.1%}of discovery variance. PCA defines no causal state.",
        ['trajectory/pca_discovery.json','trajectory/pca_all_projections.jsonl'])
    rows=read_json(OUT/'trajectory/demand_aligned_comparison.json')['paired_movement_and_coupling']
    fig,axes=plt.subplots(2,2,figsize=(9,7))
    for ax,(space,metric) in zip(axes.flat,[(s,m) for s in ['original_space','pca_space'] for m in ['path_length','tortuosity']]):
        for split,color in [('discovery',BLUE),('confirmation',ORANGE)]:
            chosen=[r for r in rows if r['split']==split and r[space][metric] is not None]
            ax.scatter([r[space][metric] for r in chosen],[r['exact_selected_anchor_coupling']['mean_DCM'] for r in chosen],color=color,label=split,s=25)
        ax.set_xlabel(space.replace('_',' ')+' '+metric.replace('_',' '));ax.set_ylabel('Mean exact selected-anchor DCM');ax.legend(fontsize=7)
    save(fig,20,'path_vs_coupling','Passive movement and selected-anchor demand coupling',
        'Each point is a base. Sparse exact anchors and absent matched holds prevent a cohort-level test of unnecessary switching. No fitted trend or PCA-based failure label.',
        ['trajectory/trajectory_metrics.jsonl','trajectory/demand_aligned_comparison.json'])


def c3():
    rows=read_jsonl(OUT/'c3_object_stress/present_object_scores.jsonl')
    assessment=read_json(OUT/'c3_object_stress/replication_assessment.json')
    conditions=['intact','strong','mask','sham_strong','sham','unrelated','no_image']
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for split,color in [('discovery',BLUE),('confirmation',ORANGE)]:
        selected=[[r for r in rows if r['split']==split and r['condition']==c] for c in conditions]
        axes[0].plot(range(len(conditions)),[np.mean([r['native_answer']=='yes' for r in group]) for group in selected],'o-',color=color,label=split)
        values=[[r['vsd'] for r in group if r['vsd'] is not None] for group in selected[:5]]
        axes[1].plot(range(5),[np.mean(v) for v in values],'o-',color=color,label=split)
    axes[0].set_xticks(range(7),conditions,rotation=25);axes[0].set_ylabel('Fraction native final answers = yes');axes[0].set_ylim(-.03,1.03)
    axes[1].set_xticks(range(5),conditions[:5],rotation=25);axes[1].set_ylabel('Mean target VSD at native final readout, W2');axes[1].axhline(0,color=GRAY,lw=.7)
    for ax in axes:ax.legend()
    save(fig,21,'c3_object_response','C3 native object responses and local source dependence',
        '63present-object families. Each condition uses its own native prefix. Late final-readout W2 cannot measure earlier acquisition; mask+yes is not automatically hallucination.',
        ['c3_object_stress/present_object_scores.jsonl','c3_object_stress/replication_assessment.json'])
    labels=assessment['condition_labels'];byid={r['id']:r for r in rows};fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,state,title in zip(axes,['residual_target_source_support','apparent_engagement_weak_grounding_candidate'],['Residual target support','Mirage-like candidate']):
        candidates=[r for r in labels if r['split']=='confirmation' and r['state']==state]
        if not candidates:empty(ax,title+': no qualifying confirmation example');continue
        item=sorted(candidates,key=lambda r:r['id'])[0];base=item['base_id'];cond=item['condition'];sham='sham_strong' if cond=='strong' else 'sham'
        choices=[byid[base+'__'+c] for c in ['intact',cond,sham]]
        ax.bar(range(3),[r['vsd'] for r in choices],color=[BLUE,RED,GREEN]);ax.set_xticks(range(3),['intact',cond,sham]);ax.set_ylabel('Target VSD, W2')
        ax.set_title(title+'\n'+base,fontsize=9);ax.axhline(.05,color=GRAY,ls=':')
        ax.text(.02,.95,'Native answers: '+', '.join(r['native_answer'] for r in choices),transform=ax.transAxes,va='top',fontsize=7)
    save(fig,22,'c3_residual_vs_mirage','C3 residual evidence and mirage-like screening',
        'First eligible held-out examples after frozen labels; empty panels preserve zero yield. C3 lacks the semantic counterfactual gate needed for strict C1 mirage.',
        ['c3_object_stress/replication_assessment.json','c3_object_stress/present_object_scores.jsonl'])


def c4():
    rows={r['base_id']:r for r in read_jsonl(OUT/'c4_natural_validation/controlled_signature_projection.jsonl')}
    effects=read_json(OUT/'c4_natural_validation/exploratory_effects.json');wrong=read_jsonl(OUT/'c4_natural_validation/wrong_claim_passive_readouts.jsonl')
    examples=sorted([r for r in effects['matched_pairs'] if r['split']=='confirmation'],key=lambda r:r['pair_id'])[:2]
    fig,axes=plt.subplots(2,3,figsize=(11,7))
    for axs,pair in zip(axes,examples):
        for ax,key in zip(axs[:2],['case','control']):
            record=rows[pair[key]]
            with Image.open(record['source_image']) as im:ax.imshow(im)
            ax.axis('off');ax.set_title(key+': '+pair[key],fontsize=8)
        categories=sorted({r['claim']['category'] for r in wrong if r['base_id']==pair['case']})
        delta=pair['case_minus_control'];ax=axs[2]
        ax.axis('off');ax.set_title('Unsupported: '+', '.join(categories),fontsize=8)
        for y,key,label,unit in [(0.75,'visual_attention_mass','Visual mass','fraction'),(0.5,'sink_attention_mass','Sink mass','fraction'),(0.25,'predictive_entropy','Entropy','nats')]:
            ax.text(.05,y,f'{label}: {delta[key]:+.4f} {unit}',transform=ax.transAxes,fontsize=9)
        ax.text(.05,.02,'Case − matched control',transform=ax.transAxes,fontsize=8)
    save(fig,23,'c4_natural_cases','Exploratory frozen natural cases and controls',
        'Illustrative2of10matched pairs; unsupported COCO80categories follow frozen review. Global passive directions are not strict causal replication or a prevalence claim.',
        ['c4_natural_validation/exploratory_effects.json','c4_natural_validation/wrong_claim_passive_readouts.jsonl'])


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['geometry','c3','c4','all']);a=p.parse_args()
    for name,fn in [('geometry',geometry),('c3',c3),('c4',c4)]:
        if a.phase in [name,'all']:fn()
    index()
