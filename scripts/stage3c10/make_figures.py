#!/usr/bin/env python3
"""Standalone scientific plots, using saved measurements only."""
import os
os.environ.setdefault('MPLCONFIGDIR','workspace/matplotlib_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scripts.stage3c10.freeze_inputs import OUT,ROOT,read_json,read_jsonl,write_json
from scripts.stage3c10.analyze import load_phase,TARGETS
from visual_reasoning.stage3c10.protocol import vsd

COLORS=['#176b9c','#bb5734']
NAMES=['Target A','Target B']

def main():
    folder=OUT/'analysis/figures';folder.mkdir(parents=True,exist_ok=True)
    p=read_json(OUT/'phase_b_primary/primary_statistics.json');e=read_json(OUT/'phase_e_mediation/mediation_statistics.json')
    temporal=read_json(OUT/'phase_c_temporal/temporal_profile.json');layers=read_json(OUT/'phase_d_layers/layer_profile.json')
    summary=read_json(OUT/'analysis/retrieval_trigger_summary.json')
    primary=load_phase('primary');med=load_phase('mediation');index=[]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130,'savefig.bbox':'tight'})
    def save(fig,num,name,title):
        fig.suptitle(title,fontsize=13);fig.tight_layout(rect=(0,0,1,.94))
        stem=f'{num:02d}_{name}';png=folder/f'{stem}.png';pdf=folder/f'{stem}.pdf'
        fig.savefig(png);fig.savefig(pdf);plt.close(fig)
        index.append({'number':num,'title':title,'png':str(png.relative_to(ROOT)),'pdf':str(pdf.relative_to(ROOT))})
    def panels():return plt.subplots(1,2,figsize=(10,3.8))
    def paired(ax,columns,labels,color,ylabel):
        matrix=np.asarray(columns).T
        for row in matrix:ax.plot(range(len(labels)),row,color=color,alpha=.18,lw=.7)
        ax.plot(range(len(labels)),np.median(matrix,axis=0),'o-',color=color,lw=2,label='median')
        ax.set_xticks(range(len(labels)),labels);ax.axhline(0,color='.6',lw=.7);ax.set_ylabel(ylabel);ax.legend(frameon=False)
    def scalar(ax,stats,labels,color):
        for x,s in enumerate(stats):
            if s.get('mean') is None:continue
            low,high=s['bootstrap_mean_ci95'];ax.errorbar(x,s['mean'],yerr=[[s['mean']-low],[high-s['mean']]],fmt='o',color=color,capsize=4)
        ax.set_xticks(range(len(labels)),labels);ax.axhline(0,color='.6',lw=.7)
    by={(r['base_problem_id'],r['target_id'],r['state']):r['arms'] for r in primary}
    ids=read_json(OUT/'config/stage3c10_config.json')['cohort_ids']['primary']
    fig,axs=panels()
    for ax,t,name,c in zip(axs,TARGETS,NAMES,COLORS):
        paired(ax,[[by[(b,t,s)]['N']['none']['rds'] for b in ids] for s in ['M','T']],['M','T'],c,'RDS (scaled-logit gap)');ax.set_title(name)
    save(fig,1,'native_mt','Native mention versus retrieval routing')
    for num,kind in [(2,'rds'),(3,'VSD')]:
        fig,axs=panels()
        for ax,t,name,c in zip(axs,TARGETS,NAMES,COLORS):
            cols=[[by[(b,t,'T')][a]['none']['rds'] if kind=='rds' else vsd(by[(b,t,'T')],a) for b in ids] for a in ['N','R16']]
            paired(ax,cols,['Native','R16-KD'],c,'RDS' if kind=='rds' else 'VSD (nats/candidate token)');ax.set_title(name)
        save(fig,num,'r16_'+kind.lower(),'R16 knockdown: T-state '+kind)
    fig,axs=panels()
    for ax,t,name,c in zip(axs,TARGETS,NAMES,COLORS):
        vals=p['paired_effects_by_base'][t];paired(ax,[[vals[b][k] for b in ids] for k in ['vsd_M','vsd_T']],['M trigger effect','T trigger effect'],c,'TE_VSD');ax.set_title(name+f"; median DiD={p['statistics'][t]['did']['median']:.3f}")
    save(fig,4,'did','Retrieval-specific trigger difference-in-differences')
    for num,control,label in [(5,'irrelevant_vsd_T','Irrelevant ROI'),(6,'e16_vsd_T','E16'),(7,'q_vsd_T','Question')]:
        fig,axs=panels()
        for ax,t,name,c in zip(axs,TARGETS,NAMES,COLORS):
            vals=p['paired_effects_by_base'][t];bs=[b for b in ids if vals[b][control] is not None]
            paired(ax,[[vals[b][k] for b in bs] for k in ['vsd_T',control]],['R16 target',label],c,'TE_VSD');ax.set_title(f'{name}; n={len(bs)} paired bases')
        save(fig,num,'control_'+str(num),'Target retrieval trigger versus '+label+' control')
    for num,profile,title in [(8,temporal,'Cumulative recent-window trigger profile'),(9,layers,'Upstream layer-bin trigger profile')]:
        fig,axs=panels()
        for ax,t,name,c in zip(axs,TARGETS,NAMES,COLORS):
            keys=[k for k,v in profile[t].items() if isinstance(v,dict) and 'mean' in v]
            if keys:scalar(ax,[profile[t][k] for k in keys],keys,c)
            else:ax.text(.5,.5,'Not run: gate closed',ha='center',transform=ax.transAxes)
            ax.set_title(name);ax.set_ylabel('Mean TE_VSD ± bootstrap 95% CI')
        save(fig,num,'localization_'+str(num),title)
    fig,ax=plt.subplots(figsize=(6,4))
    for t,name,c in zip(TARGETS,NAMES,COLORS):
        vals=list(p['paired_effects_by_base'][t].values());ax.scatter([v['rds_T'] for v in vals],[v['vsd_T'] for v in vals],color=c,label=name,alpha=.8)
    ax.axhline(0,color='.6');ax.axvline(0,color='.6');ax.set_xlabel('RDS drop');ax.set_ylabel('TE_VSD');ax.legend(frameon=False)
    save(fig,10,'routing_behavior','Routing and behavioral dependence: each dot is one base')
    for num,kind in [(11,'rds'),(12,'VSD')]:
        fig,axs=panels()
        for ax,t,name,c in zip(axs,TARGETS,NAMES,COLORS):
            rr=sorted([r for r in med if r['target_id']==t],key=lambda r:int(r['base_problem_id']))
            cols=[[r['arms'][a]['none']['rds'] if kind=='rds' else vsd(r['arms'],a) for r in rr] for a in ['N','R16','Q_all']]
            paired(ax,cols,['Native','R16-KD','Native-Q rescue'],c,kind);ax.set_title(name)
        save(fig,num,'q_rescue_'+kind.lower(),'All-head same-state Q rescue: '+kind)
    fig,axs=panels()
    for ax,t,name,c in zip(axs,TARGETS,NAMES,COLORS):
        rr=[r for r in med if r['target_id']==t]
        paired(ax,[[vsd(r['arms'],a)-vsd(r['arms'],'R16') for r in rr] for a in ['Q_selected','Q_all']],['Historical four heads','All 32 heads'],c,'Q mediation VSD gain');ax.set_title(name)
    save(fig,13,'q_head_scope','Selected-head versus all-head behavioral mediation')
    fig,ax=plt.subplots(figsize=(10,3.3));ax.axis('off')
    body=[]
    for t,name in zip(TARGETS,NAMES):
        s=summary[t];body.append([name,'PASS' if s['primary_trigger_gate']['passed'] else 'FAIL',f"{s['statistics']['vsd_T']['median']:.3f}",str(s['k80']['k80']),f"{s['statistics']['q_rescue_vsd']['median']:.3f}",s['mediation'].split(' — ')[0]])
    tab=ax.table(cellText=body,colLabels=['Target','Trigger gate','Median TE_VSD','k80','Median Q VSD gain','Mediation'],loc='center',cellLoc='center');tab.auto_set_font_size(False);tab.set_fontsize(10);tab.scale(1,2)
    save(fig,14,'target_mechanism','Target A and Target B remain separately assessed')
    fig,axs=panels();positions=read_jsonl(OUT/'phase_f_secondary/recent_position_scan.jsonl')
    for ax,t,name in zip(axs,TARGETS,NAMES):
        for state,c in [('M','#777777'),('T','#176b9c')]:
            vals=[[r['TE_VSD'] for r in positions if r['target_id']==t and r['state']==state and r['distance']==d] for d in range(1,9)]
            ax.plot(range(1,9),[np.mean(v) for v in vals],'o-',color=c,label=state)
        ax.axhline(0,color='.6');ax.set_title(name);ax.set_xlabel('Distance before current query');ax.set_ylabel('Mean single-position TE_VSD');ax.legend(frameon=False)
    save(fig,15,'position_scan','Last-eight-position effects (descriptive; no earlier search)')
    fig,ax=plt.subplots(figsize=(12,4));ax.axis('off')
    labels=['Recent reasoning\nsource contribution','Current-query Q\nat frozen late layer','Target-specific\nvisual routing','Behavioral visual\nsource dependence']
    for x,label in zip([.08,.35,.62,.89],labels):ax.text(x,.62,label,ha='center',va='center',transform=ax.transAxes,bbox={'boxstyle':'round,pad=.6','facecolor':'#eef3f5','edgecolor':'#426477'})
    allq=all(summary[t]['statistics']['q_rescue_vsd']['robust_positive'] for t in TARGETS)
    for i,(a,b) in enumerate([(.18,.25),(.45,.52),(.72,.79)]):
        supported=i<2 or allq
        ax.annotate('',xy=(b,.62),xytext=(a,.62),xycoords='axes fraction',arrowprops={'arrowstyle':'->','lw':2,'color':'#237650' if supported else '#b64646','linestyle':'-' if supported else '--'})
    if not allq:
        ax.text(.765,.79,'Behavioral Q mediation\nnot established',ha='center',transform=ax.transAxes,color='#b64646',fontsize=9)
        ax.annotate('',xy=(.88,.36),xytext=(.08,.36),xycoords='axes fraction',arrowprops={'arrowstyle':'->','lw':2,'color':'#237650'})
    ax.text(.5,.25,'Solid chain supported at both frozen targets' if allq else 'Recent-state → visual dependence supported; behavioral mediator unresolved',ha='center',transform=ax.transAxes,fontsize=12)
    ax.text(.5,.07,'Untested: natural-generation sufficiency, multi-evidence generality, and sink causality',ha='center',transform=ax.transAxes,color='.35')
    save(fig,16,'causal_chain','Stage 3C.10 causal-chain assessment')
    write_json(folder/'index.json',index);print({'figures':len(index),'formats':['PNG','PDF']})

if __name__=='__main__':main()
