"""Five descriptive figures; family-level points, explicit inferential limits."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from visual_reasoning.stage9a.protocol import ARMS

ROOT=Path('outputs/stage9a/v1')
COLORS=['#6b7280','#007a9e','#bb4b25']
LABELS=['Direct','Prompted CoT','Thinking']
KEYS=['P1','P2','P3','P4']
TITLES=['Demand alignment ±16','Late episode fraction','Episodes / 1k tokens','Long-gap re-engagement']


def export(fig,name):
    dest=ROOT/'figures';dest.mkdir(exist_ok=True)
    for suffix in ('png','pdf'):fig.savefig(dest/(name+'.'+suffix),dpi=180,bbox_inches='tight')
    plt.close(fig)


def plot_ci(ax,estimate,ci,y,color,label):
    if estimate is None:return
    ax.plot(estimate,y,'o',color=color,label=label)
    if ci is not None:ax.plot(ci,[y,y],color=color,lw=2)


def main():
    rows=json.loads((ROOT/'audit/trajectory_metrics.json').read_text())['rows']
    effects=json.loads((ROOT/'stage9a_primary_effects.json').read_text())
    causal_path=ROOT/'stage9a_causal_validation.json'
    causal=json.loads(causal_path.read_text()) if causal_path.exists() else None
    matched=json.loads((ROOT/'stage9a_length_matched_pairs.json').read_text())
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    families=sorted({r['family_id'] for r in rows});order={f:i for i,f in enumerate(families)}
    fig,axes=plt.subplots(3,1,figsize=(12,10),sharex=True)
    for arm,label,ax in zip(ARMS,LABELS,axes):
        matrix=np.zeros((len(families),200))
        for r in (r for r in rows if r['arm']==arm):
            m=r['primary'];length=m['reasoning_tokens'];width=length/200
            if not length:matrix[order[r['family_id']]]=np.nan;continue
            for ep in m['episodes']:
                a,b=ep['start']/width,ep['end']/width
                for j in range(max(0,int(a)),min(200,int(np.ceil(b)))):matrix[order[r['family_id']],j]+=max(0,min(b,j+1)-max(a,j))
        im=ax.imshow(matrix,aspect='auto',interpolation='nearest',extent=(0,1,len(families),0),vmin=0,vmax=1,cmap='magma')
        ax.set_title(label,loc='left');ax.set_ylabel('Family (fixed order)')
    axes[-1].set_xlabel('Normalized primary reasoning position')
    fig.suptitle('Frozen retrieval proxy activity across all 128 paired families')
    fig.colorbar(im,ax=axes,label='Active fraction in normalized-time bin',pad=.015,shrink=.7)
    export(fig,'figure1_visual_access_trajectories')

    fig,axes=plt.subplots(1,3,figsize=(13,4));rng=np.random.default_rng(920260924)
    for ax,key,title in zip(axes,['P3','P2','P4'],[TITLES[2],TITLES[1],TITLES[3]]):
        for i,arm in enumerate(ARMS):
            values=[r['primary'][key] for r in rows if r['arm']==arm and r['primary'][key] is not None]
            ax.scatter(i+rng.uniform(-.15,.15,len(values)),values,s=9,color=COLORS[i],alpha=.35)
            d=effects['descriptive'][arm]['metrics'][key];ax.plot(i,d['mean'],'_',ms=24,color='black',mew=2)
            if d['ci']:ax.plot([i,i],d['ci'],color='black',lw=2)
            ax.text(i,.98,f'n={len(values)}',ha='center',va='top',transform=ax.get_xaxis_transform(),fontsize=8)
        ax.set_xticks(range(3),LABELS);ax.set_title(title);ax.grid(axis='y',alpha=.2)
    fig.suptitle('One point per family; means and exploratory 95% family-bootstrap CIs')
    fig.tight_layout();export(fig,'figure2_recurrence_and_late_access')

    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for i,arm in enumerate(ARMS):
        rr=[r for r in rows if r['arm']==arm and r['primary']['reviewed_demands']]
        offsets=np.arange(-64,65)
        matrix=np.array([[r['primary']['peri_demand'][str(t)]['mean'] for t in offsets] for r in rr],dtype=float)
        axes[0].plot(offsets,np.nanmean(matrix,axis=0),color=COLORS[i],label=f'{LABELS[i]} (n={len(rr)} families)')
        for j,key in enumerate(['P1','shift_control_alignment16','nondemand_alignment16']):
            d=effects['demand_specificity'][arm][key];x=j+(i-1)*.23
            axes[1].bar(x,d['mean'] or 0,width=.21,color=COLORS[i],label=LABELS[i] if j==0 else None)
            if d['ci']:axes[1].plot([x,x],d['ci'],color='black',lw=1)
    axes[0].axvspan(-16,16,color='grey',alpha=.1);axes[0].axvline(0,color='black',lw=.6)
    axes[0].set(xlabel='Generated tokens from reviewed demand',ylabel='Family-mean probability of active retrieval',ylim=(0,1));axes[0].legend(fontsize=8)
    axes[1].set_xticks(range(3),['Demand ±16','Circular-shift control','Reviewed non-demand']);axes[1].set(ylim=(0,1.05),ylabel='Trajectory-mean alignment probability')
    axes[1].legend(fontsize=8);fig.suptitle('Bounded explicit-demand annotations; no-candidate trajectories are unobserved')
    fig.tight_layout();export(fig,'figure3_demand_alignment')

    fig,axes=plt.subplots(1,5,figsize=(17,4),gridspec_kw={'width_ratios':[1.5,1,1,1,1]})
    for matched_flag,c,label in [(False,'#cccccc','Outside caliper'),(True,COLORS[2],'Within |Δ log L| ≤ .15')]:
        rr=[r for r in matched['rows'] if r['included']==matched_flag]
        axes[0].scatter([r['cot_length'] for r in rr],[r['thinking_length'] for r in rr],s=15,c=c,label=label)
    lim=np.geomspace(10,50000);axes[0].plot(lim,lim,'k--',lw=.7)
    axes[0].set(xscale='log',yscale='log',xlabel='CoT reasoning tokens',ylabel='Thinking reasoning tokens',title=f"Matched {matched['matched_families']}/128 families")
    axes[0].legend(fontsize=7)
    for ax,key,title in zip(axes[1:],KEYS,TITLES):
        for y,(scope,label,c) in enumerate([('primary','Raw',COLORS[0]),('matched','Matched',COLORS[1]),('adjusted','Adjusted',COLORS[2])]):
            d=effects[scope][key];plot_ci(ax,d.get('mean',d.get('coefficient')),d['ci'],y,c,label)
            ax.text(.98,y+.18,f"n={d['n_families']}",transform=ax.get_yaxis_transform(),ha='right',fontsize=7)
        ax.axvline(0,color='black',lw=.7);ax.set_yticks(range(3),['Raw','Matched','Adjusted']);ax.set_title(title,fontsize=9);ax.set_xlabel('Thinking − CoT');ax.set_ylim(-.35,2.55)
    fig.suptitle('Length controls; 98.75% CIs when ≥20 families; missing CI means insufficient support')
    fig.tight_layout();export(fig,'figure4_length_controls')

    if causal is None:
        print('Four observational figures saved; causal figure awaits the complete frozen subset')
        return
    fig,axes=plt.subplots(1,2,figsize=(13,4))
    for i,arm in enumerate(ARMS):
        rr=[r for r in causal['rows'] if r['arm']==arm]
        for j,condition in enumerate(['target','irrelevant','sham']):
            x=j+(i-1)*.23;v=[r['effects'][condition] for r in rr]
            axes[0].scatter(x+rng.uniform(-.065,.065,len(v)),v,s=15,color=COLORS[i],alpha=.55,label=LABELS[i] if j==0 else None)
            axes[0].plot(x,np.mean(v),'_',color='black',ms=14,mew=2)
        v=[r['target_minus_irrelevant'] for r in rr]
        axes[1].scatter(i+rng.uniform(-.12,.12,len(v)),v,s=18,color=COLORS[i],alpha=.6)
        axes[1].plot(i,np.mean(v),'_',color='black',ms=20,mew=2)
        axes[1].text(i-.4,.98,f'n={len(rr)}',transform=axes[1].get_xaxis_transform(),ha='left',va='top')
    axes[0].set_xticks(range(3),['Target substitution','Irrelevant substitution','Self/sham']);axes[0].set_ylabel('Donor-semantic preference shift (nats/token)');axes[0].legend(fontsize=8)
    axes[1].set_xticks(range(3),LABELS);axes[1].set_ylabel('Target − irrelevant preference shift')
    for ax in axes:ax.axhline(0,color='black',lw=.7);ax.grid(axis='y',alpha=.15)
    fig.suptitle('Frozen local Value assays: descriptive only per arm (fewer than 20 families); sham exactly zero')
    fig.tight_layout();export(fig,'figure5_causal_source_validation')


if __name__=='__main__':main()
