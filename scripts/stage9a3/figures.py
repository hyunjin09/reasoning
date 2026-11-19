"""Standalone PNG/PDF figures for the bounded calibration."""
import argparse,os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scripts.stage9a3.prepare import ROOT,load

DEST=ROOT/'figures'


def export(fig,name):
    DEST.mkdir(exist_ok=True)
    for ext in ['png','pdf']:
        p=DEST/(name+'.'+ext);assert not p.exists();fig.savefig(p,dpi=180,bbox_inches='tight')
    plt.close(fig)


def design():
    fig,ax=plt.subplots(figsize=(8,4.5))
    ax.add_patch(Rectangle((-20,0),20,1,color='#c9d5e2'))
    ax.add_patch(Rectangle((0,0),80,1,color='#ead9d9'))
    ax.add_patch(Rectangle((0,0),16,.5,color='#75b99b'))
    ax.axvline(0,color='black',lw=1);ax.axvline(16,color='#27624b',ls='--');ax.plot([0,80],[.5,.5],color='#27624b',ls='--')
    ax.text(-10,.5,'Prefill\nunchanged',ha='center',va='center',fontsize=11)
    ax.text(8,.24,'Direct\naccess',ha='center',va='center',fontsize=10)
    ax.text(48,.65,'Generated query → image keys blocked\noutside the allowed rectangle',ha='center',fontsize=11)
    ax.set(xlim=(-20,80),ylim=(1,0),yticks=[0,.5,.75,1],yticklabels=['0','0.5L','0.75L','L'],
           xticks=[0,16,64,80],xticklabels=['0','16','64','…'],xlabel='Generated-token query time',ylabel='Decoder depth')
    ax.set_title('Model-wide visual-access mask: example (0.5L, 16)',pad=14)
    fig.subplots_adjust(bottom=.29)
    fig.text(.12,.03,'Token 0 is predicted by unchanged prefill. For generated query t, block image keys\nwhen layer ≥ cutoff or t > cutoff. Image K/V and previously propagated\nimage information remain cached.',fontsize=9)
    export(fig,'figure1_intervention_rectangle')


def surface(key,split='primary'):
    r=load(ROOT/f'audit/{key}_{split}_calibration_result.json')
    m=load(ROOT/f'audit/{key}_grid_primary_manifest.json')
    meta={row['policy_id']:(row['fraction'],row['token_cutoff']) for row in m['rows']};times=m['token_grid'];fractions=m['fractions']
    from scripts.stage9a3.grid import canonical,policy_id
    acc=np.array([[r['surface'][policy_id(*canonical(f,t))]['accuracy']*100 for t in times] for f in fractions])
    dmg=np.array([[r['surface'][policy_id(*canonical(f,t))]['damage']*100 for t in times] for f in fractions])
    fig,axs=plt.subplots(1,2,figsize=(10,4),constrained_layout=True)
    for ax,arr,title,cmap,vmin,vmax in zip(axs,[acc,dmg],['Accuracy (%)','Damage vs FULL (pp)'],['viridis','RdBu_r'],[0,-50],[100,50]):
        im=ax.imshow(arr,cmap=cmap,vmin=vmin,vmax=vmax)
        for i in range(4):
            for j in range(4):ax.text(j,i,f'{arr[i,j]:.1f}',ha='center',va='center',fontsize=10,
                                     color='white' if title.startswith('Accuracy') and arr[i,j]<55 else 'black')
        ax.set(xticks=range(4),xticklabels=[str(t) if t is not None else 'FULL' for t in times],yticks=range(4),
               yticklabels=['0','0.5L','0.75L','L'],xlabel='Token cutoff',ylabel='Layer cutoff',title=title)
        ax.add_patch(Rectangle((2.53,2.53),.94,.94,fill=False,ec='black',lw=2))
        ax.add_patch(Rectangle((-.47,-.47),.94,.94,fill=False,ec='#a50026',lw=2))
        if r['selected_policy']:
            f,t=meta[r['selected_policy']];i=fractions.index(f);j=times.index(t)
            ax.add_patch(Rectangle((j-.4,i-.4),.8,.8,fill=False,ec='#f3ca40',lw=2))
        fig.colorbar(im,ax=ax,shrink=.8)
    title='Qwen2.5-VL-3B CoT' if key=='qwen25' else 'Qwen3-VL-2B CoT'
    n=r['n_images']
    fig.suptitle(title+f' · {n} images / {2*n} queries\nBlack: FULL · red: zero access · gold: point-preserving candidate',fontsize=12)
    name='figure2_qwen25_surface' if key=='qwen25' else 'figure3_qwen3_surface'
    if split=='combined':name='figure2b_qwen25_extended_surface'
    export(fig,name)


def comparison():
    r=load(ROOT/'stage9a3_generation_comparison.json');fig,ax=plt.subplots(figsize=(5.5,4))
    for i,key in enumerate(['qwen25','qwen3']):
        row=r['same_cutoff'][key];y=row['damage']*100;lo,hi=np.array(row['ci95'])*100
        ax.errorbar(i,y,yerr=[[y-lo],[hi-y]],fmt='o',capsize=5,color=['#356f9f','#b0604e'][i],ms=8)
    ax.axhline(5,color='gray',ls='--',label='5 pp preservation tolerance');ax.axhline(0,color='black',lw=.6)
    ax.set(xticks=[0,1],xticklabels=['Qwen2.5 3B CoT','Qwen3 2B CoT'],ylabel='Damage vs FULL (pp)',
           title='Same frozen Qwen2.5 cutoff\n'+r['selected_policy']);ax.legend(fontsize=9)
    export(fig,'figure4_same_cutoff_comparison')


if __name__=='__main__':
    assert os.environ.get('SLURM_JOB_ID')
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['design','qwen25','qwen25_extended','qwen3','comparison']);a=ap.parse_args().action
    if a=='design':design()
    elif a=='comparison':comparison()
    elif a=='qwen25_extended':surface('qwen25','combined')
    else:surface(a)
