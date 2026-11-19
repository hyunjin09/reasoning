"""Publication-export figures with explicit denominators and measured claim limits."""
import textwrap
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.patches import Patch,Rectangle
from scripts.stage10ar.common import ROOT,load


def main():
    r=load(ROOT/'stage10ar_primary_inference.json');states=load(ROOT/'stage10ar_item_transition_states.json')
    events={e['query_id']:e for e in load(ROOT/'stage10ar_anchor_annotations.json')['rows']}
    cohort=load(ROOT/'stage10ar_primary_cohort.json');dest=ROOT/'figures';dest.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
    def finish(fig,name):
        for suffix in ('png','pdf'):
            p=dest/f'{name}.{suffix}';assert not p.exists();fig.savefig(p,bbox_inches='tight')
        plt.close(fig)
    e=events[cohort['primary_ids'][0]];fig,ax=plt.subplots(figsize=(13,4));ax.axis('off');ax.set(xlim=(0,1),ylim=(0,1))
    titles=['A0\nNo generated facts','A1\nFirst observation','A2\nPartial evidence','A3\nComplete evidence','A4\nExplicit count']
    for i,title in enumerate(titles):
        x=.10+i*.20;a=e['anchors'][f'A{i}'];snippet='No generated reasoning.' if i==0 else ('… '+a['prefix_text'][-110:].split(' ',1)[-1]) if a else 'Unavailable.'
        ax.text(x,.75,title,ha='center',va='center',bbox=dict(boxstyle='round,pad=.5',fc='#eaf1f8',ec='#64788c'))
        ax.text(x,.38,textwrap.fill(snippet,24),ha='center',va='center',fontsize=9)
        if i<4:ax.annotate('',(x+.12,.75),(x+.08,.75),arrowprops=dict(arrowstyle='->',color='#64788c'))
    ax.set_title(f'Frozen semantic progression — {e["query_id"]} (first by predeclared hash order)')
    ax.text(.5,-.03,'Text excerpts only. A0 retains image prefill in image-off; fresh text A0 has question only.\nA3 may equal A4. Missing A2 is retained. Anchors were sealed before Stage10AR outcomes.',ha='center',fontsize=10)
    finish(fig,'figure1_semantic_progression')
    fig,ax=plt.subplots(figsize=(9,5));x=np.arange(5)
    for assay,field,ci_key,label,color in [('image_off','necessity','necessity_ci95','Future visual necessity Nᵥ','#326ca4'),
                                         ('text_only','accuracy','accuracy_ci95','Fresh text sufficiency Sₜ','#bc6936')]:
        values=[r['curves'][assay][f'A{i}'] for i in range(5)];y=np.array([v[field] for v in values])*100;ci=np.array([v[ci_key] for v in values])*100
        ax.errorbar(x,y,yerr=np.array([y-ci[:,0],ci[:,1]-y]),fmt='o-',lw=2,capsize=4,label=label,color=color)
    ax.set_xticks(x,[f'A{i}\nn={r["curves"]["text_only"][f"A{i}"]["n"]}' for i in range(5)])
    ax.set_ylim(-5,105);ax.set_ylabel('Percentage points / accuracy (%)');ax.set_title('Visual necessity and text sufficiency across frozen anchors')
    ax.legend(frameon=False);ax.grid(axis='y',alpha=.2)
    fig.text(.5,-.04,'Pointwise 95% image-bootstrap intervals; primary contrasts use multiplicity-adjusted intervals.\nA0 image-off retains multimodal prefill; fresh text replay carries no image state.',ha='center',fontsize=10)
    finish(fig,'figure2_phase_transition')
    sr=states['rows'];mat=[]
    for row in sr:
        values=[]
        for i in range(5):
            pair=row['assay_correct_by_anchor'][f'A{i}'];values.append(-1 if pair is None else int(pair[0])+2*int(pair[1]))
        mat.append(values)
    cmap=ListedColormap(['#ededed','#e6aaa4','#a6bddb','#f3c58c','#5d9c83']);norm=BoundaryNorm(np.arange(-1.5,4.5),cmap.N)
    fig,ax=plt.subplots(figsize=(7,9));ax.imshow(mat,aspect='auto',cmap=cmap,norm=norm,interpolation='none')
    ax.set_xticks(range(5),[f'A{i}' for i in range(5)]);ax.set_yticks(range(len(sr)),[s['image_id'] for s in sr],fontsize=9)
    for j,s in enumerate(sr):
        if s['H'] is not None:ax.add_patch(Rectangle((int(s['H'][1])-.48,j-.48),.96,.96,fill=False,lw=2,ec='black'))
    labels=['A2 unavailable','Neither correct','Image-off only','Text-only only','Both correct']
    ax.legend(handles=[Patch(facecolor=c,label=l) for c,l in zip(cmap.colors,labels)],loc='upper center',bbox_to_anchor=(.5,-.04),ncol=2,frameon=False,fontsize=9)
    ax.set_title(f'Earliest joint-success anchor H (black outline)\n{states["identifiable_H"]}/{len(sr)} identifiable; {states["nonmonotonic_images"]} image(s) with later reversals')
    finish(fig,'figure3_item_transition_states')
    fig,ax=plt.subplots(figsize=(12,4));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    names=['V_A','T₁','V_B','T₂','V_A'];colors=['#cbdced','#f4dcc8','#cbdced','#f4dcc8','#cbdced']
    for i,(label,color) in enumerate(zip(names,colors)):
        x=.1+i*.2;ax.text(x,.68,label,ha='center',va='center',fontsize=18,bbox=dict(boxstyle='round,pad=.6',fc=color,ec='#64788c'))
        if i<4:ax.annotate('',(x+.14,.68),(x+.06,.68),arrowprops=dict(arrowstyle='->',lw=1.5,linestyle='--'))
    status='Joint localization gate passed in successful controlled counting.' if r['main_gate_pass'] else 'Joint localization gate did not pass; the full phase cycle remains a hypothesis.'
    ax.text(.5,.31,status,ha='center',fontsize=12)
    ax.text(.5,.12,'Stage4A: demand-aligned source A→B→A dependence/re-engagement (36/48 bases).\nStage10A: emitted text can be a causal carrier. Full trigger/Q-mediated chain remains unestablished.',ha='center',fontsize=10)
    ax.set_title('Integration with dynamic re-access — conceptual links, not a newly measured cycle')
    finish(fig,'figure4_dynamic_reaccess_integration')


if __name__=='__main__':main()
