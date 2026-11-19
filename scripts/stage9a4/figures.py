"""Bounded assay figures; explicitly separate primary and extended cohorts."""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage9a4.common import ROOT,OLD,load


def save(fig,name):
    path=ROOT/'figures';path.mkdir(exist_ok=True)
    fig.tight_layout()
    for ext in ['png','pdf']:fig.savefig(path/f'{name}.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)


def main():
    assert os.environ.get('SLURM_JOB_ID')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    a=load(OLD/'stage9a3_qwen25_full_access.json');b=load(ROOT/'stage9a4_qwen3_4b_full_baseline.json')
    labels=['Accuracy','Intermediate\nreasoning','Valid final\noption','Capped']
    av=[a['counts']['correct']/64,a['counts']['cot']/64,a['counts']['valid_option']/64,
        sum(not r['normal_eos'] and r['tokens']>=a['scientific_cap'] for r in a['rows'])/64]
    bv=[b['rates'][k] for k in ['correct','cot','valid_final','capped']]
    fig,ax=plt.subplots(figsize=(8,4));x=np.arange(4)
    for values,offset,color,name in [(av,-.18,'#416B9D','Qwen2.5-3B (256 cap)'),(bv,.18,'#D07D37','Qwen3-4B (512 cap)')]:
        bars=ax.bar(x+offset,np.array(values)*100,.36,color=color,label=name);ax.bar_label(bars,fmt='%.1f',padding=2)
    ax.set(xticks=x,xticklabels=labels,ylim=(0,113),ylabel='Percent',title='FULL validity: same 32 images / 64 queries');ax.legend(loc='upper right',fontsize=8)
    save(fig,'figure1_baseline_validity')
    primary=None
    for stage in ['r1','t128','t256']:
        p=ROOT/f'audit/{stage}_decision.json'
        if p.exists():primary=load(p)
    q25=load(OLD/'audit/qwen25_primary_calibration_result.json')['surface']
    conditions=['full','t0','t64']+[p for p in ['t128','t256'] if p in primary['surface']]
    q25map={'full':'l100_tFULL','t0':'l000_t0','t64':'l100_t64'}
    fig,axs=plt.subplots(1,2,figsize=(10,4));x=np.arange(len(conditions));display=['FULL','ZERO','64','128','256'][:len(conditions)]
    for ax,metric in zip(axs,['accuracy','damage']):
        for data,mapping,offset,color,label in [(q25,q25map,-.12,'#416B9D','Qwen2.5-3B'),(primary['surface'],{p:p for p in conditions},.12,'#D07D37','Qwen3-4B')]:
            ids=[i for i,p in enumerate(conditions) if p in mapping]
            y=[100*data[mapping[conditions[i]]][metric] for i in ids]
            ax.plot(np.array(ids)+offset,y,'o-',color=color,label=label)
            if metric=='damage':
                ci=np.array([data[mapping[conditions[i]]]['ci95'] for i in ids]).T*100
                ax.vlines(np.array(ids)+offset,ci[0],ci[1],colors=color,alpha=.7)
        ax.set(xticks=x,xticklabels=display,xlabel='All-layer access cutoff (tokens)',ylabel='Accuracy (%)' if metric=='accuracy' else 'Damage (percentage points)')
        if metric=='damage':ax.axhline(5,color='gray',ls='--',lw=1,label='5 pp tolerance');ax.axhline(0,color='gray',lw=.5)
    axs[0].legend();fig.suptitle('Temporal access: primary 32-image cohorts (95% image-bootstrap intervals)')
    save(fig,'figure2_temporal_finite_access')
    comparison=load(ROOT/'stage9a4_qwen25_qwen3_comparison.json');c=comparison['paired_primary32']
    fig,ax=plt.subplots(figsize=(7,4))
    vals=[c['qwen25_damage64'],c['qwen3_damage64']];ci=[q25['l100_t64']['ci95'],primary['surface']['t64']['ci95']]
    ax.bar([0,1],np.array(vals)*100,color=['#416B9D','#D07D37'],width=.5)
    ax.vlines([0,1],np.array(ci)[:,0]*100,np.array(ci)[:,1]*100,color='black');ax.axhline(5,color='gray',ls='--');ax.axhline(0,color='gray',lw=.5)
    ax.set(xticks=[0,1],xticklabels=['Qwen2.5-3B','Qwen3-4B'],ylabel='Damage at token64 (pp)',title='Same cutoff, paired primary 32 images')
    fig.text(.5,-.02,f"Paired shift {c['gamma64']*100:.2f} pp; 95% CI [{c['ci95'][0]*100:.2f}, {c['ci95'][1]*100:.2f}]",ha='center')
    save(fig,'figure3_same_token64')
    control=ROOT/'stage9a4_qwen3_4b_null_sink_control.json'
    if control.exists():
        s=load(control)['surface'];selected=load(ROOT/'audit/selected_cutoff.json')['cutoff'];ps=['full','t0',f't{selected}']
        fig,ax=plt.subplots(figsize=(7,4));x=np.arange(3)
        for data,offset,color,label in [(primary['surface'],-.1,'#D07D37','Standard image-key mask'),(s,.1,'#558B6E','Null-sink (no redistribution)')]:
            ax.plot(x+offset,[data[p]['damage']*100 for p in ps],'o-',color=color,label=label)
            ax.vlines(x+offset,[data[p]['ci95'][0]*100 for p in ps],[data[p]['ci95'][1]*100 for p in ps],color=color)
        ax.axhline(5,color='gray',ls='--');ax.axhline(0,color='gray',lw=.5)
        ax.set(xticks=x,xticklabels=['FULL','ZERO',str(selected)],ylabel='Damage (pp)',xlabel='All-layer token cutoff',title='Redistribution control: primary 32 images');ax.legend()
        save(fig,'figure4_null_sink_robustness')


if __name__=='__main__':main()
