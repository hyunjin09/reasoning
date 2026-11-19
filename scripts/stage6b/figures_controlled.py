"""C2 factorial and C1 fixed-prefix figures, including valid mixed outcomes."""
from collections import defaultdict
import numpy as np
from PIL import Image
from scripts.stage6b.common import OUT,read_json,read_jsonl
from scripts.stage6b.figure_support import plt,save,strip,empty,BLUE,ORANGE,GREEN,GRAY,RED,index


def main():
    c2=read_jsonl(OUT/'c2_alignment_retrieval/passive_features.jsonl');conf=[r for r in c2 if r['split']=='confirmation'];cells=['AR','A_only','R_only','Neither']
    fig,axs=plt.subplots(2,2,figsize=(8,4))
    for ax,cell in zip(axs.flat,cells):
        r=next(r for r in c2 if r['condition']==cell);ax.axis('off')
        ax.text(.5,.65,cell,ha='center',fontsize=15,color=BLUE)
        ax.text(.5,.36,f"Focal alignment: {r['roles']['alignment']}\nDemanded source: {r['roles']['demanded']}",ha='center',va='center')
    save(fig,1,'c2_design','C2: focal alignment × focal retrieval demand',
        'All31families retain all4cells. A_only and Neither still demand image source X; this is not a global image-needed/unneeded design.',['c2_alignment_retrieval/source_roles.jsonl'])
    fig,axs=plt.subplots(1,2,figsize=(9,3.6))
    for ax,k in zip(axs,['attention_density','qk_cosine']):strip(ax,[[r['focal_features'][k] for r in conf if r['condition']==c] for c in cells],cells,k)
    save(fig,2,'c2_routing','C2 focal routing by factorial cell',
        'Held-out19families; layers28–29, all32heads. Alignment effects do not pass the full frozen robustness rule.',['c2_alignment_retrieval/factorial_statistics.json'])
    fig,axs=plt.subplots(1,2,figsize=(9,3.6))
    strip(axs[0],[[r['vsd']['T']['2'] for r in conf if r['condition']==c] for c in cells],cells,'Focal T VSD (W2)')
    strip(axs[1],[[r['vsd'][r['roles']['demanded']]['2'] for r in conf if r['condition']==c] for c in cells],cells,'Currently demanded source VSD (W2)')
    save(fig,3,'c2_source_dependence','C2: focal and currently demanded source dependence',
        'VSD is native minus suppressed correct-versus-foil margin, in nats/candidate token. Focal-demand effects are robust; the two estimands remain separate.',['c2_alignment_retrieval/w2_scores.jsonl'])
    matched=read_json(OUT/'c2_alignment_retrieval/matched_high_attention.json')['confirmation']
    fig,axs=plt.subplots(1,2,figsize=(8,3.5))
    if matched['pairs']:
        pair=matched['pairs'][0];selected=[next(r for r in c2 if r['id']==eid) for eid in [pair['alignment_event'],pair['retrieval_event']]]
        axs[0].bar(['A_only','AR'],[r['focal_features']['attention_density'] for r in selected],color=[ORANGE,BLUE]);axs[0].set_ylabel('Focal attention density')
        axs[1].bar(['A_only','AR'],[r['vsd']['T']['2'] for r in selected],color=[ORANGE,BLUE]);axs[1].set_ylabel('Focal VSD (W2)');axs[1].axhline(0,color=GRAY)
    save(fig,4,'c2_matched_example','C2 matched high-attention example: insufficient yield',
        'Only1held-out matched pair qualifies (minimum8). The example is descriptive and has overlapping merged ROI tokens; it does not establish the stronger dissociation.',['c2_alignment_retrieval/matched_high_attention.json','config/c2_overlap_sensitivity.json'])
    rows=read_jsonl(OUT/'c1_mirage/fixed_prefix_scores.jsonl');bases=defaultdict(dict)
    for r in rows:bases[r['base_id']][r['condition']]=r
    c1=[c for c in bases.values() if c['intact']['split']=='confirmation'];levels=['intact','mild','strong','mask']
    labels=read_json(OUT/'c1_mirage/mirage_confirmation.json')['classification_rows'];strict=[r for r in labels if r['strict_mirage']]
    manifest=read_jsonl(OUT/'c1_mirage/fixed_prefix_manifest.jsonl');entry={r['id']:r for r in manifest}
    example=sorted({r['base_id'] for r in strict})[0] if strict else c1[0]['intact']['base_id']
    fig,axs=plt.subplots(1,4,figsize=(10,3.4))
    for ax,condition in zip(axs,levels):
        e=entry[example+'__'+condition];ax.imshow(Image.open(e['row']['image_path']));x0,y0,x1,y1=e['row']['target']['roi'];pad=max(x1-x0,y1-y0)
        ax.set_xlim(max(0,x0-pad),x1+pad);ax.set_ylim(y1+pad,max(0,y0-pad));ax.set_title(condition);ax.axis('off')
    save(fig,5,'c1_evidence_ladder','C1 target evidence ladder',
        'Saved source pixels around the reviewed target; identical intact text prefix across conditions. Example: '+example+'. No generated or retouched image content.',['c1_mirage/fixed_prefix_manifest.jsonl','audit/stress_condition_audit.json'])
    fig,axs=plt.subplots(1,2,figsize=(9,3.8))
    for ax,k,label in zip(axs,['vsd','margin'],['Target VSD (W2)','Intact-x versus x′ margin']):
        strip(ax,[[c[level][k] for c in c1] for level in levels],levels,label+' (nats/token)')
    save(fig,6,'c1_grounding_curve','C1 grounding under evidence degradation',
        'All62confirmationbases. Strong and mask reduce target VSD and semantic margin beyond their matched shams. Absolute cross-condition values use the same fixed textual prefix.',['c1_mirage/fixed_prefix_scores.jsonl','c1_mirage/sham_did.json'])
    fig,axs=plt.subplots(1,3,figsize=(12,3.6))
    for ax,k in zip(axs,['attention_density','qk_cosine','alpha_v_norm']):strip(ax,[[c[level][k] for c in c1] for level in levels],levels,k)
    save(fig,7,'c1_engagement_curve','C1 apparent engagement under evidence degradation',
        'Held-out fixed-prefix queries; mean over all32heads in layers28–29. These routing features do not define causal source use.',['c1_mirage/fixed_prefix_scores.jsonl'])
    stats=read_json(OUT/'c1_mirage/sham_did.json')['statistics']['confirmation'];rule=read_json(OUT/'config/mirage_discovery_rule.json')
    fig,ax=plt.subplots(figsize=(9,4));keys=['vsd','margin','attention_density','qk_cosine','alpha_v_norm'];x=np.arange(len(keys))
    for j,level in enumerate(['mild','strong','mask']):
        values=[stats[f'sham_minus_{level}__{k}'] for k in keys];scales=[rule['feature_scales'][k] for k in keys]
        means=np.asarray([r['mean']/s for r,s in zip(values,scales)]);lo=np.asarray([r['bootstrap_mean_ci95'][0]/s for r,s in zip(values,scales)]);hi=np.asarray([r['bootstrap_mean_ci95'][1]/s for r,s in zip(values,scales)])
        ax.errorbar(x+(j-1)*.18,means,yerr=[means-lo,hi-means],fmt='o',capsize=3,label=level)
    ax.set_xticks(x,keys,rotation=15);ax.set_ylabel('Sham − target stress / discovery SD');ax.axhline(0,color=GRAY);ax.legend()
    save(fig,8,'c1_sham_did','C1 target-specific degradation beyond sham',
        'Equal-base means and10,000source-group bootstrap95%CIs. Positive values indicate a larger loss under target degradation; opposite sign to the plan’s algebraic DiD.',['c1_mirage/sham_did.json'])
    contrasts=read_json(OUT/'c1_mirage/sham_did.json')['contrasts'];fig,axs=plt.subplots(1,3,figsize=(12,3.6))
    for ax,k in zip(axs,['attention_density','qk_cosine','alpha_v_norm']):
        key='grounding_minus_'+k+'_degradation_slope';values=[v for b,v in contrasts[key].items() if bases[b]['intact']['split']=='confirmation']
        ax.scatter(range(len(values)),values,c=[GREEN if v>0 else RED for v in values],s=14);ax.axhline(0,color=GRAY)
        ax.set_title(k+f"\n{100*stats[key]['positive_fraction']:.1f}% positive");ax.set_ylabel('Grounding − engagement loss slope');ax.set_xlabel('Confirmation base')
    save(fig,9,'c1_continuous_divergence','C1 continuous divergence: limited cross-base consistency',
        'None passes the full frozen rule, including≥75%positive bases. Attention divergence has a significant mean but only61.3%positive bases; the stronger cohort claim remains unestablished.',['c1_mirage/sham_did.json','c1_mirage/claim_assessment.json'])
    examples=sorted({r['base_id'] for r in strict})[:2];fig,axs=plt.subplots(2,max(1,len(examples)),figsize=(9,6),squeeze=False)
    if not examples:
        for ax in axs.flat:empty(ax,'No strict held-out mirage example qualified.')
    for column,base in enumerate(examples):
        ax=axs[0,column];engax=axs[1,column]
        c=bases[base];intact=c['intact'];axis_levels=['intact','strong','mask']
        ax.plot(axis_levels,[c[l]['vsd']/intact['vsd'] for l in axis_levels],'o-',label='W2 VSD / intact',color=BLUE)
        ax.plot(axis_levels,[c[l]['vsd_w8']/intact['vsd_w8'] for l in axis_levels],'s--',label='W8 VSD / intact',color=GRAY)
        chosen=next(r for r in strict if r['base_id']==base);eng=next(k for k,v in chosen['engagement_retained'].items() if v)
        engax.plot(axis_levels,[c[l][eng]/intact[eng] for l in axis_levels],'o-',color=ORANGE)
        engax.set_ylabel(eng.replace('_',' ')+' / intact');engax.axhline(1,color=GRAY,lw=.6)
        ax.axhline(0,color=GRAY,lw=.6);ax.set_title(base);ax.legend(fontsize=7);ax.set_ylabel('VSD / intact')
    save(fig,10,'c1_mirage_examples','C1 strict held-out mirage examples',
        '9events across8of62bases; all9also show W8collapse. Examples are the first two qualifying base IDs. Outcomes are fixed-prefix candidate preferences, not newly generated native hallucinations.',['c1_mirage/mirage_confirmation.json','c1_mirage/w8_sensitivity.json'])
    similarity=read_json(OUT/'c1_mirage/no_image_similarity.json')['comparisons'];fig,axs=plt.subplots(1,2,figsize=(9,3.5))
    for ax,reference in zip(axs,['no_image','unrelated']):
        conditions=['intact','strong','mask'];strip(ax,[[r['js_divergence'] for r in similarity if r['split']=='confirmation' and r['condition']==c and r['reference']==reference] for c in conditions],conditions,'JS divergence to '+reference)
    save(fig,11,'c1_prior_similarity','C1 distribution similarity to no-image and unrelated baselines',
        'Full raw next-token distributions; same textual history, fresh legal interfaces. Similarity supports a prior-like description and does not prove zero visual influence.',['c1_mirage/no_image_similarity.json'])
    cf=read_json(OUT/'c1_mirage/counterfactual_followability.json')['bases'];fig,ax=plt.subplots(figsize=(6,4))
    for split,color in [('discovery',GRAY),('confirmation',BLUE)]:
        selected=[r for r in cf if r['split']==split];ax.scatter([abs(r['render_sham_effect']) for r in selected],[r['CF'] for r in selected],s=22,c=color,label=split,alpha=.7)
    limit=max(abs(r['render_sham_effect']) for r in cf);ax.plot([0,limit],[.05,limit+.05],'--',color=RED,label='CF gate');ax.legend()
    ax.set_xlabel('|Intact − render-sham margin|');ax.set_ylabel('Intact − counterfactual margin (CF)')
    save(fig,12,'c1_counterfactual_followability','C1 source-semantic followability',
        'All62confirmationbases pass the frozen positive-CF-beyond-render-sham gate. Candidate margins are mean log-probabilities per divergent candidate token.',['c1_mirage/counterfactual_followability.json'])
    index();print('Saved controlled figures1–12.')


if __name__=='__main__':main()
