"""Twenty standalone scientific figures, including explicit low-yield panels."""
import os,textwrap
os.environ.setdefault('MPLCONFIGDIR','workspace/matplotlib')
from collections import Counter,defaultdict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json
from scripts.stage5a.analyze_taxonomy import base_values


FIG=OUT/'analysis/figures'
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130,'savefig.bbox':'tight','pdf.fonttype':42})
TEAL='#187e80';ORANGE='#bf642f';GRAY='#858b94'


def empty(ax,message):
    ax.axis('off');ax.text(.5,.5,textwrap.fill(message,40 if len(ax.figure.axes)>1 else 68),ha='center',va='center',transform=ax.transAxes,fontsize=13,color='#4c5563')


def bars(ax,names,values,title,ylabel='Unique bases',color=TEAL):
    ax.bar(range(len(names)),values,color=color);ax.set_xticks(range(len(names)),names,rotation=25,ha='right');ax.set_title(title);ax.set_ylabel(ylabel)
    for i,v in enumerate(values):ax.text(i,v,str(v),ha='center',va='bottom',fontsize=9)
    ax.margins(y=.18)


def grouped_values(ax,groups,key,title,ylabel=None):
    data=[];names=[]
    for name,rows in groups:
        v=list(base_values(rows,key).values())
        if v:data.append(v);names.append(name+'\nN='+str(len(v)))
    if not data:empty(ax,'No eligible measured bases for this panel.');return
    ax.boxplot(data,tick_labels=names,showfliers=False,patch_artist=True,boxprops={'facecolor':'#cee5e5'})
    rng=np.random.default_rng(1234)
    for i,v in enumerate(data):ax.scatter(i+1+rng.uniform(-.12,.12,len(v)),v,s=13,c=TEAL,alpha=.65)
    ax.axhline(0,color=GRAY,lw=.8);ax.set_title(title);ax.set_ylabel(ylabel or key);ax.tick_params(axis='x',labelrotation=20)


def main():
    FIG.mkdir(parents=True,exist_ok=True);rows=read_jsonl(OUT/'phase_e_internal/features.jsonl');byid={r['event_id']:r for r in rows}
    ann={e['event_id']:e for e in read_jsonl(OUT/'annotations/events.jsonl')};summary=read_json(OUT/'analysis/taxonomy_summary.json')
    census=summary['natural'];subtypes=summary['subtypes'];classifier=read_json(OUT/'phase_i_separability/feature_ablation.json')
    manifest=[]
    def save(n,name,title,fig,caption):
        fig.suptitle(title,fontsize=15,y=1.03);fig.tight_layout();stem=f'{n:02d}_{name}'
        for ext in ('png','pdf'):fig.savefig(FIG/(stem+'.'+ext))
        plt.close(fig);manifest.append({'number':n,'title':title,'png':str((FIG/(stem+'.png')).relative_to(ROOT)),
            'pdf':str((FIG/(stem+'.pdf')).relative_to(ROOT)),'caption':caption})
    fig,ax=plt.subplots(figsize=(11,5));ax.axis('off')
    boxes=[(.02,.62,'A: semantic role\nreviewed before scores'),(.27,.62,'B: local correctness\nseparate from final answer'),(.52,.62,'C: causal source profile\nW2 / W8 / semantic control'),(.77,.62,'D: temporal evidence\nfull native history')]
    for x,y,label in boxes:ax.text(x,y,label,transform=ax.transAxes,va='center',bbox={'boxstyle':'round,pad=.7','fc':'#e4eeee','ec':TEAL})
    ax.text(.5,.23,'Freeze A–D  →  E: attention / QK / value / sink\n\nDerived diagnoses can overlap; unresolved cases remain unresolved.',ha='center',va='center',transform=ax.transAxes,fontsize=13)
    save(1,'taxonomy_overview','An attention-independent taxonomy',fig,'A–D labels were frozen before fresh passive extraction. Attention is a phenotype, not the causal label.')
    fig,axs=plt.subplots(1,3,figsize=(13,4))
    names=list(census['semantic_roles']);bars(axs[0],names,[census['semantic_roles'][n]['bases'] for n in names],'Selected semantic roles')
    names=list(census['local_correctness']);bars(axs[1],names,[census['local_correctness'][n]['bases'] for n in names],'Local claim correctness')
    bars(axs[2],['Correct','Wrong'],[census['final_correct_bases'],census['final_wrong_bases']],'Final correctness')
    save(2,'natural_prevalence','Natural cohort: 200 bases, 550 selected events',fig,'Semantic/local categories overlap at the base level; the census covers up to3 selected events per trajectory.')
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    data=[];names=[]
    for role in ('T','X','M','I'):
        values=list(base_values(rows,'VSD_'+role).values())
        if values:data.append(values);names.append(role+'\nN='+str(len(values)))
    axs[0].boxplot(data,tick_labels=names,showfliers=False);axs[0].axhline(0,color=GRAY);axs[0].set_ylabel('VSD (nats / candidate token)');axs[0].set_title('Mean within each base, by source')
    profiles=read_json(OUT/'phase_b_causal/causal_state_classification.json')['causal_profiles'];bars(axs[1],list(profiles),list(profiles.values()),'Overlapping causal profiles','Events')
    save(3,'source_profiles','Demanded, alternative and irrelevant source dependence',fig,'Signed unnormalized effects are primary. A large negative effect is not a null; overlapping profiles are not independent counts.')
    fig,ax=plt.subplots(figsize=(8,4));empty(ax,'No strict alignment-only confirmation events. No attention-matched alignment-versus-retrieval pairs; all six inferential slots remain unrun.')
    save(4,'alignment_matched','Alignment versus retrieval: confirmation feasibility',fig,'The strict independently mentioned M definition was retained; generic visual claims were not relabeled as alignment-only.')
    fig,ax=plt.subplots(figsize=(8,4));scored=classifier['grounded_correct_vs_hallucination'];names=list(scored)
    vals=[scored[n]['metrics']['balanced_accuracy'] for n in names];ax.bar(names,vals,color=[TEAL]*3+[ORANGE]*2);ax.set_ylim(0,1);ax.axhline(.5,color=GRAY,ls=':');ax.set_ylabel('Balanced accuracy');ax.set_title('Whole-template held-out classification')
    for i,v in enumerate(vals):ax.text(i,v+.015,f'{v:.3f}',ha='center')
    save(5,'attention_causal_separation','Grounded-correct versus locally wrong visual claims',fig,'Descriptive classification, aggregated within base/class. F4/F5 include causal features that partly define grounded labels; scores do not validate a mechanism.')
    states=['retrieval','verification','refresh','H-MR','H-SC','integration_failure','unresolved'];groups=[(s,[r for r in rows if r['primary_state']==s]) for s in states]
    fig,axs=plt.subplots(1,3,figsize=(15,4))
    for ax,key in zip(axs,('QK_T_minus_control','alphaV_T','VSD_T')):grouped_values(ax,groups,key,key)
    save(6,'state_signatures','QK, value transport and causal dependence by state',fig,'Base means within each descriptive display state. The underlying labels can overlap; the display uses an explicit priority order.')
    fig,axs=plt.subplots(1,2,figsize=(11,4));temporal=[('First use',[r for r in rows if r['temporal_role']=='FIRST_USE']),('Reuse',[r for r in rows if r['temporal_role']=='REUSE_WITHOUT_INTERVENING_SOURCE']),('Refresh',[r for r in rows if r['temporal_role']=='REFRESH_AFTER_OTHER_SOURCE'])]
    grouped_values(axs[0],temporal,'VSD_T','Source dependence by reviewed temporal role');bars(axs[1],['First','Reuse','Refresh','Unresolved'],[121,19,4,203],'Temporal review coverage','Events')
    save(7,'temporal_states','First retrieval, verification and refresh',fig,'Only full-native reviewed histories receive temporal roles. Four refresh opportunities do not support population inference about stale-source failures.')
    fig,axs=plt.subplots(1,2,figsize=(10,4));confirmation=[r for r in rows if r['split']=='confirmation'];p=[r for r in confirmation if r['T_density_percentile'] is not None]
    axs[0].scatter([r['T_density_percentile'] for r in p],[r['VSD_T'] for r in p],s=22,alpha=.65,c=TEAL);axs[0].axvline(.9,color=ORANGE,ls='--');axs[0].axhspan(-.05,.05,color=GRAY,alpha=.2);axs[0].set_xlabel('Discovery-matched density percentile');axs[0].set_ylabel('VSD_T');axs[0].set_title('139 matched confirmation events')
    empty(axs[1],'0 strict mirages; 0 high-attention missing-CE candidates. No eligible mirage–retrieval pairs. The other128 confirmation events have unresolved matching.')
    save(8,'mirage_confirmation','Mirage confirmation under the frozen rule',fig,'Zero confirmed cases does not establish absence: matching coverage and clean semantic-edit feasibility limit ascertainment.')
    fig,ax=plt.subplots(figsize=(10,5));ax.axis('off');lines=['Explicit, checkable wrong local claim?','  ↓ source evidence under frozen W2 / W8 / semantic assays','Weak T + measured semantic null → H-NR: 0','Alternative source dominates → H-MR: 10 events /9 bases','Correct ROI + semantic control, wrong extraction → H-SC: 1 /1','Verified refresh + actual prior-source dominance → H-ST: 0','Correct local retrieval + reviewed later error → H-INT: 13 /7 (separate)']
    for i,line in enumerate(lines):ax.text(.04,.93-i*.13,line,transform=ax.transAxes,fontsize=12,color=ORANGE if 'H-MR' in line or 'H-SC' in line else '#24323f')
    save(9,'failure_decision_tree','Causal failure decision tree',fig,'Wrong final answers do not enter the hallucination branch automatically. Missing semantic controls cannot establish a semantic null.')
    fig,ax=plt.subplots(figsize=(9,4));names=['H-NR','H-MR','H-SC','H-ST'];vals=[subtypes[n]['bases'] for n in names];bars(ax,names,vals,'Ascertained subtype bases within natural200','Ascertained bases')
    ax.text(.98,.95,'64 bases contain selected wrong claims\n1 such base is outside the atlas\nUnresolved mechanism ≠ absent subtype',ha='right',va='top',transform=ax.transAxes)
    save(10,'natural_subtype_ascertainment','Natural-cohort failure subtype ascertainment',fig,'Counts are ascertained lower bounds from the nested causal atlas, not a correctness-balanced atlas prevalence estimate. Categories can overlap; unclassified errors remain unresolved.')
    fig,axs=plt.subplots(1,3,figsize=(14,4));sg=[(name,[byid[e] for e in s['events_ids']]) for name,s in subtypes.items()]
    for ax,key in zip(axs,('VSD_T','VSD_X','CE_minus_sham')):grouped_values(ax,sg,key,key)
    save(11,'failure_causal_profiles','Causal profiles of failure subtypes',fig,'H-NR and H-ST have no diagnosed cases. H-MR is Tier2; its alternative-fact semantic readout is unavailable. H-SC108_E1 is Tier1.')
    fig,axs=plt.subplots(1,2,figsize=(12,4));ints=[r for r in rows if r['integration_failure']];grouped_values(axs[0],[('Reviewed integration failures',ints)],'VSD_T','Local source dependence survives a wrong final answer')
    axs[1].axis('off')
    for i,r in enumerate(ints[:4]):axs[1].text(0,.96-i*.24,textwrap.fill(r['event_id']+': '+(r['next_downstream_use'] or ''),62),va='top',transform=axs[1].transAxes,fontsize=9)
    save(12,'integration_failures','13 locally grounded integration-error events on7 bases',fig,'A reviewed error must occur after the selected event. These events are not visual hallucinations solely because the final answer is wrong.')
    fig,axs=plt.subplots(1,2,figsize=(13,4));grouped_values(axs[0],groups,'sink_mass','Sink mass');grouped_values(axs[1],groups,'sink_release','Release from t−8 prior')
    save(13,'sink_states','Sink behavior is descriptive',fig,'Only2 attention-matched confirmation pairs; all sink gate conditions are unestablished. No sink intervention was performed.')
    fig,ax=plt.subplots(figsize=(11,4));grouped_values(ax,groups,'TE_T','R16 effect on demanded-source dependence','TE_VSD_T (nats / candidate token)')
    save(14,'trigger_states','Fixed recent-reasoning trigger by state',fig,'256 events from the frozen96-base subset. Trigger dependence is secondary and is not required for retrieval labels.')
    utility=read_jsonl(OUT/'phase_j_alignment_utility/alignment_removal_results.jsonl');fig,axs=plt.subplots(1,2,figsize=(10,4))
    if utility:
        axs[0].bar([r['event_id'] for r in utility],[r['correct_local_NLL_change_removal_minus_native'] for r in utility],color=TEAL);axs[0].axhline(0,color=GRAY);axs[0].set_ylabel('Removal − native correct-token NLL');axs[0].tick_params(axis='x',labelrotation=25)
    else:empty(axs[0],'No independent mentioned-source arm available.')
    empty(axs[1],'0 strict alignment-only events (<32 minimum). Dedicated utility and final-candidate margin assays are unrun.')
    save(15,'alignment_utility','Existing mentioned-source arms: descriptive utility only',fig,f'The {len(utility)} independent M candidates were scored in the frozen causal run; they are not silently promoted to an alignment-only cohort. Other overlapping M maps are excluded from this contrast.')
    fig,ax=plt.subplots(figsize=(12,5));ax.axis('off')
    for i,r in enumerate(utility):
        quote=ann[r['event_id']]['claimed_visual_fact'];text=f"{r['event_id']} | conditional {r['label']} | ΔNLL={r['correct_local_NLL_change_removal_minus_native']:.3f}\n"+textwrap.fill(quote,110)
        ax.text(.02,.97-i*.19,text,transform=ax.transAxes,va='top',fontsize=10)
    save(16,'alignment_candidate_examples','Helpful, benign or interfering: qualification remains necessary',fig,'Labels describe the sign of the existing M-removal effect. None of these examples meets the strict alignment-only criterion.')
    fig,ax=plt.subplots(figsize=(11,4));comp=read_json(OUT/'analysis/template_robustness.json')['state_template_composition'];names=list(comp);values=[max(v.values())/sum(v.values()) for v in comp.values()]
    ax.bar(names,values,color=GRAY);ax.set_ylim(0,1);ax.set_ylabel('Largest template share of state events');ax.tick_params(axis='x',labelrotation=25)
    save(17,'template_robustness','Template concentration limits generality',fig,'All leave-one-template-out primary matched comparisons remain insufficient; concentration is descriptive, not a substitute for replication.')
    fig,axs=plt.subplots(1,2,figsize=(11,4));names=list(scored)
    for ax,metric in zip(axs,('macro_F1','AUROC')):
        ax.bar(names,[scored[n]['metrics'][metric] for n in names],color=[TEAL]*3+[ORANGE]*2);ax.set_ylim(0,1);ax.set_title(metric)
    save(18,'heldout_ablation','Held-out feature ablation: one adequately sized task',fig,'Alignment/retrieval, retrieval/mirage, and failure-subtype tasks are insufficient. Only grounded-correct versus wrong visual claims is scored, with whole-template folds.')
    fig,ax=plt.subplots(figsize=(12,5));ax.axis('off');selected=[]
    for state in ('retrieval','verification','refresh','H-MR','H-SC','integration_failure','unresolved'):
        candidates=[r for r in confirmation if r['primary_state']==state and r['high_attention'] is True]
        if candidates:selected.append(sorted(candidates,key=lambda r:r['event_id'])[0])
    fig.set_size_inches(12,max(2.6,min(6,len(selected))*1.2))
    for i,r in enumerate(selected[:6]):
        text=f"{r['event_id']} | {r['primary_state']} | percentile={r['T_density_percentile']:.2f}, VSD_T={r['VSD_T']:.3f}\n"+textwrap.fill(ann[r['event_id']]['claimed_visual_fact'],105)
        ax.text(.02,.96-i*.8/max(1,min(6,len(selected))),text,transform=ax.transAxes,va='top',fontsize=10)
    if not selected:empty(ax,'No high-attention confirmation case available under the frozen matching rule.')
    save(19,'high_attention_examples','Representative high-attention confirmation states',fig,'First event ID within each observed state; illustrative cases are not matched causal contrasts. No alignment/mirage exemplar is manufactured.')
    fig,ax=plt.subplots(figsize=(11,5));ax.axis('off');ax.text(.02,.52,'High visual\nattention',fontsize=19,va='center',bbox={'boxstyle':'round,pad=.7','fc':'#e1eeee','ec':TEAL})
    labels=[('Semantic alignment','strict confirmation absent',False),('Causal retrieval','source-dependent events observed',True),('Verification / refresh','reviewed histories; limited refresh yield',True),('Mirage','0 confirmed; incomplete matching coverage',False),('Hallucination / misretrieval','Tier2 H-MR; one Tier1 H-SC',True)]
    for i,(label,note,supported) in enumerate(labels):
        y=.9-i*.19;ax.annotate('',xy=(.4,y),xytext=(.24,.52),xycoords='axes fraction',arrowprops={'arrowstyle':'->','color':GRAY})
        ax.text(.43,y,label+'\n'+note,transform=ax.transAxes,va='center',fontsize=11,bbox={'boxstyle':'round,pad=.4','fc':'#e6efef' if supported else '#f1f1f2','ec':TEAL if supported else GRAY,'linestyle':'-' if supported else '--'})
    ax.text(.02,-.05,'Solid: diagnosis observed somewhere in the atlas; this does not establish occurrence at high attention.',transform=ax.transAxes,fontsize=9,color='#4c5563')
    save(20,'conceptual_conclusion','Attention requires semantic and causal qualification',fig,'Conceptual possibilities are distinguished from observed diagnoses. Stage5A does not confirm the stronger matched alignment/mirage headline.')
    write_json(FIG/'index.json',{'figures':manifest,'count':len(manifest),'standalone_formats':['png','pdf'],'inferential_unit':'base; nested events retained for descriptive panels'})
    print('Saved20 PNG/PDF figure pairs')


if __name__=='__main__':main()
