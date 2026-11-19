"""Five required comparison figures, with image-cluster uncertainty."""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage9a5.common import ROOT, COT, load

COLORS={'cot':'#416B9D','thinking':'#C96738'}
LABELS={'cot':'Instruct + CoT','thinking':'Native Thinking'}


def save(fig,name):
    path=ROOT/'figures';path.mkdir(exist_ok=True)
    fig.tight_layout()
    for ext in ('png','pdf'):
        dest=path/f'{name}.{ext}';assert not dest.exists()
        fig.savefig(dest,dpi=180,bbox_inches='tight')
    plt.close(fig)


def main():
    assert os.environ.get('SLURM_JOB_ID')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    baselines={'cot':load(COT/'stage9a4_qwen3_4b_full_baseline.json'),
               'thinking':load(ROOT/'stage9a5_thinking_full_baseline.json')}
    fig,axs=plt.subplots(1,2,figsize=(12,4),gridspec_kw={'width_ratios':[2,1]})
    metrics=['correct','cot','valid_final','normal_eos','capped'];x=np.arange(len(metrics))
    for arm,offset in [('cot',-.18),('thinking',.18)]:
        b=baselines[arm];ys=[100*b['rates'][k] for k in metrics]
        bars=axs[0].bar(x+offset,ys,.36,color=COLORS[arm],label=LABELS[arm]);axs[0].bar_label(bars,fmt='%.1f',padding=2,fontsize=8)
    axs[0].set(xticks=x,xticklabels=['Accuracy','Reasoning','Valid final','Normal EOS','Cap'],ylim=(0,114),ylabel='Percent')
    axs[0].legend(loc='upper right',fontsize=8)
    for i,arm in enumerate(('cot','thinking')):
        values=[r['tokens'] for r in baselines[arm]['rows']]
        axs[1].boxplot([values],positions=[i],widths=.45,patch_artist=True,boxprops={'facecolor':COLORS[arm],'alpha':.6})
    axs[1].set(xticks=[0,1],xticklabels=['CoT','Thinking'],ylabel='Observed generated tokens',ylim=(0,540))
    axs[1].axhline(512,color='gray',ls=':',label='512 cap');axs[1].legend(fontsize=8)
    fig.suptitle('Qwen3-VL-4B FULL validity: same 32 images / 64 queries')
    save(fig,'figure1_full_validity')
    c=load(ROOT/'stage9a5_absolute_access_comparison.json')
    policies=['full','t0','t64','t128']+(['t256'] if 't256' in c['thinking']['surface'] else [])
    fig,axs=plt.subplots(1,2,figsize=(11,4));x=np.arange(len(policies))
    for arm,offset in [('cot',-.08),('thinking',.08)]:
        s=c[arm]['surface'];ids=[i for i,p in enumerate(policies) if p in s];positions=np.array(ids)+offset
        for ax,metric in zip(axs,('accuracy','damage')):
            ax.plot(positions,[100*s[policies[i]][metric] for i in ids],'o-',color=COLORS[arm],label=LABELS[arm])
            if metric=='damage':
                ax.vlines(positions,[100*s[policies[i]]['ci95'][0] for i in ids],[100*s[policies[i]]['ci95'][1] for i in ids],color=COLORS[arm])
    for ax in axs:ax.set(xticks=x,xticklabels=['FULL','ZERO','64','128']+(['256'] if len(x)==5 else []),xlabel='All-layer token cutoff')
    axs[0].set(ylabel='Accuracy (%)');axs[0].legend()
    axs[1].set(ylabel='Damage (pp)');axs[1].axhline(5,color='gray',ls='--');axs[1].axhline(0,color='gray',lw=.5)
    fig.suptitle('Finite-access panel: 95% paired image-bootstrap intervals')
    save(fig,'figure2_absolute_access')
    fig,ax=plt.subplots(figsize=(7,4));contrast=c['contrasts']['t128']
    for i,arm in enumerate(('cot','thinking')):
        r=c[arm]['surface']['t128'];ax.bar(i,r['damage']*100,width=.5,color=COLORS[arm])
        ax.vlines(i,*[v*100 for v in r['ci95']],color='black')
    ax.axhline(0,color='gray',lw=.5);ax.axhline(5,color='gray',ls='--')
    ax.set(xticks=[0,1],xticklabels=['CoT','Thinking'],ylabel='Damage at token128 (pp)',title='Same cutoff, paired 32-image comparison')
    fig.text(.5,-.03,f"Thinking − CoT: {100*contrast['difference']:.2f} pp; 95% CI [{100*contrast['ci95'][0]:.2f}, {100*contrast['ci95'][1]:.2f}]",ha='center')
    save(fig,'figure3_token128_contrast')
    rel=load(ROOT/'stage9a5_relative_time_analysis.json');fig,axs=plt.subplots(1,3,figsize=(13,4))
    for arm in ('cot','thinking'):
        vals=sorted(r['tokens'] for r in rel['rows'] if r['arm']==arm)
        axs[0].step(vals,np.arange(1,len(vals)+1)/len(vals),where='post',color=COLORS[arm],label=LABELS[arm])
        cut=rel['arms'][arm]['cutoffs'];ts=[64,128,256]
        axs[1].plot(ts,[cut[str(t)]['median_item_fraction'] for t in ts],'o-',color=COLORS[arm],label=LABELS[arm])
        axs[2].plot(ts,[100*cut[str(t)]['fraction_observed_reaching_mask'] for t in ts],'o-',color=COLORS[arm])
    axs[0].set(xlabel='Observed FULL tokens (cap512)',ylabel='Empirical cumulative fraction');axs[0].legend(fontsize=8)
    axs[1].set(xlabel='Token cutoff',ylabel='Median cutoff / FULL length',xticks=[64,128,256]);axs[1].axhline(1,color='gray',ls=':')
    axs[2].set(xlabel='Token cutoff',ylabel='Observed trajectories reaching mask (%)',xticks=[64,128,256],ylim=(-3,103))
    fig.suptitle('Relative exposure is descriptive; capped lengths are right-censored')
    save(fig,'figure4_relative_exposure')
    inference=load(ROOT/'stage9a5_cot_vs_thinking_inference.json')
    fig,ax=plt.subplots(figsize=(11,5));ax.axis('off')
    ax.text(.02,.94,'Native causal use',fontsize=17,weight='bold',color=COLORS['cot'])
    ax.text(.02,.81,'Stage4A · Qwen3-VL-4B-Thinking · MathVerse\nDemand A → B → A; source dependence follows\n36/48 bases meet the frozen dynamic definition\nLocal source suppression + semantic retargeting',fontsize=11,va='top',linespacing=1.6)
    ax.text(.54,.94,'Access-removal necessity',fontsize=17,weight='bold',color=COLORS['thinking'])
    ax.text(.54,.81,inference['figure_conclusion'],fontsize=11,va='top',linespacing=1.6)
    ax.text(.5,.30,'Native visual use ≠ prolonged direct-access necessity',ha='center',fontsize=16,weight='bold')
    ax.text(.5,.16,'Distinct tasks and interventions; native prefill and image-derived cache remain available.\nCheckpoint comparison does not identify a training objective or architectural cause.',ha='center',fontsize=10,linespacing=1.5)
    save(fig,'figure5_native_use_vs_necessity')


if __name__=='__main__':main()
