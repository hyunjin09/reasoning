"""Required descriptive figures; missing/not-run panels are explicit."""
from pathlib import Path
import os
os.environ['MPLCONFIGDIR']=str(Path('runs/stage12xs/v2/cache/matplotlib').resolve())
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage12xs.execution_v2 import ROOT,load


def savefig(fig,name):
    dest=ROOT/'figures';dest.mkdir(exist_ok=True)
    for ext in ['png','pdf']:
        p=dest/f'{name}.{ext}';assert not p.exists();fig.savefig(p,dpi=180,bbox_inches='tight')
    plt.close(fig)

def make():
    a=load(ROOT/'audit/phaseA_inference.json');b=load(ROOT/'stage12xs_transfer_candidate_manifest.json');inf=load(ROOT/'stage12xs_primary_inference.json')
    counts=a['B_counts'];fig,ax=plt.subplots(1,2,figsize=(9,3.5));labels=list(counts)
    ax[0].bar(labels,[counts[k] for k in labels],color=['#4991bb','#80b9a3','#d2ad62','#ba6e6e'])
    for k,v in enumerate(counts.values()):ax[0].text(k,v+.2,str(v),ha='center')
    ax[0].set(ylabel='Independent families',title='Complete scoreable native failures')
    r=a['oracle_rescue_complete'];p=r['estimate'];ci=r['wilson95']
    if p is not None:ax[1].errorbar([0],[p],yerr=[[p-ci[0]],[ci[1]-p]],fmt='o',capsize=5,color='#266080')
    ax[1].set(xlim=(-.6,.6),ylim=(0,1),xticks=[0],xticklabels=[f"O+ among complete N−: {r['numerator']}/{r['denominator']}"],title='Oracle rescue (Wilson 95%)')
    fig.suptitle('X1 · Fresh held-out failure map');fig.tight_layout();savefig(fig,'X1_fresh_failure_map')
    groups=['BOTH_FAIL','C_ONLY','T_ONLY','BOTH_SUCCESS','UNSCOREABLE_TECHNICAL'];vals=[sum(x['transition']==k for x in b.get('transitions',[])) for k in groups]
    fig,ax=plt.subplots(figsize=(8,3.5));ax.bar(range(5),vals,color=['#9c7777','#ddaa55','#558bab','#72a887','#bbbbbb'])
    for k,v in enumerate(vals):ax.text(k,v+.1,str(v),ha='center')
    ax.set(xticks=range(5),xticklabels=['Both fail','C only','T only','Both succeed','Technical missing'],ylabel='Independent families',title='X2 · Fresh B4 C/T transitions');savefig(fig,'X2_ct_transitions')
    c=inf.get('transfer');fig,ax=plt.subplots(figsize=(8,max(3,0.45*b.get('n_selected',0)+1.5)))
    if c and c.get('families'):
        arms=['RT_T','RT_I','Q_I','Q_T','SH_I'];matrix=np.array([[r['panels'][a].count(True)/5 for a in arms] for r in c['families']])
        im=ax.imshow(matrix,vmin=0,vmax=1,cmap='Blues',aspect='auto')
        ax.set(xticks=range(5),xticklabels=['RT → T','RT → I','Q → I','Q → T','Shuffled RT → I'],yticks=range(len(matrix)),yticklabels=[r['item_id'] for r in c['families']])
        for i,r in enumerate(c['families']):
            for j,a_ in enumerate(arms):
                values=r['panels'][a_];missing=values.count(None);txt=f"{values.count(True)}/5"+(f"\n{missing} missing" if missing else '')
                ax.text(j,i,txt,ha='center',va='center',color='white' if matrix[i,j]>.6 else 'black',fontsize=9)
        fig.colorbar(im,ax=ax,label='Correct continuations / five frozen seeds')
    else:ax.text(.5,.5,'Phase C not run: candidate gate not met',ha='center',transform=ax.transAxes);ax.set_axis_off()
    ax.set_title('X3 · Held-out portability panel');savefig(fig,'X3_portability_matrix')
    ds=load('outputs/stage12us/v1/stage12us_primary_inference.json')
    refs=[ds['endpoints']['U_P1_S_TT'],ds['endpoints']['U_P2_S_TI_given_TT'],ds['supports']['PRODUCTION_SUPPORT']]
    dev=[r['successes']/r['frozen'] for r in refs]
    fig,ax=plt.subplots(figsize=(7,4))
    x=np.arange(3);ax.bar(x-.17,dev,width=.34,color='#8096a5',label='U-S development (n=5; 3 seeds)')
    for k,r in enumerate(refs):ax.text(k-.17,dev[k]+.015,f"{r['successes']}/{r['frozen']}",ha='center',fontsize=9)
    if c and c.get('families'):
        keys=['RT_T','RT_I','production_support'];vals=[c['endpoints'][k]['missingness_bounds'][0] for k in keys]
        ax.bar(x+.17,vals,width=.34,color='#367ba8',label=f"X-S held out (n={c['n_selected']}; 5 seeds)")
        for k,key in enumerate(keys):
            panel=c['endpoints'][key];e=panel['exact'];label=f"{e['numerator']}/{panel['frozen_denominator']}"+(f" ({panel['unknown']} missing)" if panel['unknown'] else '')
            ax.text(k+.17,vals[k]+.015,label,ha='center',fontsize=9)
    else:ax.text(.5,.15,'Held-out transfer not tested; no portability null inferred.',ha='center',transform=ax.transAxes,fontsize=9)
    ax.set(xticks=x,xticklabels=['Same-model sufficiency','Cross-checkpoint portability','Production support'],ylim=(0,1.18),ylabel='Confirmed family successes / frozen families',title='X4 · Development versus held-out signature');ax.legend(fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.13));savefig(fig,'X4_development_heldout')
