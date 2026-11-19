"""Five standalone figures from sealed Stage9A main/secondary estimates."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scripts.stage9a_dynamics.prepare_answers import MAIN
from scripts.stage9a_dynamics.analyze_main import load
from visual_reasoning.stage9a.protocol import ARMS

LABELS = {'instruct_direct':'Direct', 'instruct_cot':'CoT', 'thinking':'Thinking'}
COLORS = {'instruct_direct':'#2471A3', 'instruct_cot':'#B9770E', 'thinking':'#B03A48'}
DEST = MAIN/'figures'


def save(fig, name):
    DEST.mkdir(exist_ok=True)
    for ext in ('png','pdf'):
        path=DEST/f'{name}.{ext}'
        assert not path.exists(), path
        fig.savefig(path, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)


def estimate(ax, x, values, arm, *, scale=100, line=True, label=None):
    y=np.array([v['mean']*scale for v in values])
    ci=np.array([v['ci'] if v['ci'] is not None else [v['mean'],v['mean']] for v in values])*scale
    ax.errorbar(x, y, yerr=np.maximum(0,np.vstack([y-ci[:,0],ci[:,1]-y])), color=COLORS[arm],
                fmt='o-' if line else 'o', capsize=3, linewidth=1.6, markersize=5,
                label=label or LABELS[arm])


def axes(ax, ylabel):
    ax.axhline(0,color='#999999',linewidth=.8)
    ax.set_ylabel(ylabel);ax.grid(axis='y',alpha=.18)
    ax.spines[['top','right']].set_visible(False)


def main():
    plt.rcParams.update({'font.size':10,'axes.titlesize':12,'pdf.fonttype':42})
    profiles=load(MAIN/'stage9a_temporal_necessity_profiles.json')['arms']
    inference=load(MAIN/'stage9a_primary_inference.json')
    native=load(MAIN/'audit/native_usage_secondary.json')['summaries']['main64_subset']

    fig,ax=plt.subplots(figsize=(10,4.8))
    for y,name,blocks in [(3,'FULL',[]),(2,'Cumulative cutoff',[(.3,1)]),
                           (1,'Local window',[(.6,.8)]),(0,'Demand / shifted control',[(.45,.51)])]:
        ax.add_patch(Rectangle((0,y),1,.42,facecolor='#B6D7A8',edgecolor='none'))
        for lo,hi in blocks:ax.add_patch(Rectangle((lo,y),hi-lo,.42,facecolor='#C85A61',edgecolor='none'))
        ax.text(-.02,y+.21,name,ha='right',va='center')
    ax.add_patch(Rectangle((.68,0),.06,.42,facecolor='none',edgecolor='#555555',linestyle='--',linewidth=1.5))
    ax.annotate('cutoff',xy=(.3,2.43),xytext=(.3,2.85),ha='center',arrowprops={'arrowstyle':'->'})
    ax.annotate('separate matched control',xy=(.71,-.02),xytext=(.72,-.48),ha='center',arrowprops={'arrowstyle':'->'})
    ax.set_xlim(-.31,1.05);ax.set_ylim(-.8,4.05);ax.axis('off')
    ax.text(.5,3.9,'Scheduled removal of direct image-key access',ha='center',weight='bold',fontsize=13)
    ax.text(0,3.57,'Native reasoning start',fontsize=9);ax.text(1,3.57,'Native reasoning end',ha='right',fontsize=9)
    fig.text(.12,.055,'Green: access allowed    Red: image access removed    Dashed: separate equal-width control',fontsize=10)
    fig.text(.12,.012,'Decoder indices 19–22; prefill and prior KV preserved; later cache evolves. Cumulative axis uses token count.',fontsize=9)
    save(fig,'figure1_intervention_schematic')

    fig,ax=plt.subplots(figsize=(8.5,4.8));x=np.arange(5)
    for i,arm in enumerate(ARMS):
        vals=[profiles[arm][f'cutoff{c}_damage'] for c in (0,128,512,2048)]+[dict(mean=0,ci=[0,0])]
        estimate(ax,x+(i-1)*.05,vals,arm)
    axes(ax,'Accuracy damage (percentage points)');ax.set_xticks(x,['0','128','512','2048','FULL'])
    ax.set_xlabel('Access allowed through generated token cutoff (categorical spacing)')
    ax.set_title('Cumulative direct visual-access cutoff');ax.legend(ncol=3,loc='best')
    fig.subplots_adjust(bottom=.20)
    fig.text(.12,.01,'64 paired families per arm. Error bars: descriptive 95% family bootstrap intervals. Positive = harmful removal.',fontsize=9)
    save(fig,'figure2_cumulative_necessity')

    fig,ax=plt.subplots(figsize=(9,5));x=np.arange(5)
    ax.axvspan(2.5,4.5,color='#ece9e2',zorder=0)
    for i,arm in enumerate(ARMS):estimate(ax,x+(i-1)*.05,[profiles[arm][f'local{k}_damage'] for k in range(5)],arm)
    axes(ax,'Accuracy damage (percentage points)');ax.set_xticks(x,['0–20%','20–40%','40–60%','60–80%','80–100%'])
    ax.set_xlabel('Fixed native reasoning window');ax.set_title('Temporal necessity profiles — primary local assay')
    fig.subplots_adjust(bottom=.23)
    ax.legend(ncol=3,loc='best');p=inference['primary']['P2']['simultaneous']
    fig.text(.12,.045,f"P2, shaded final 40%: Thinking − CoT = {100*p['mean']:+.2f} pp; 98.75% CI [{100*p['ci'][0]:+.2f}, {100*p['ci'][1]:+.2f}]",fontsize=10)
    fig.text(.12,.004,'Profile error bars: descriptive 95% family bootstrap intervals; n=64 per arm. No post-intervention time normalization.',fontsize=9)
    save(fig,'figure3_temporal_necessity')

    fig,(ax,bx)=plt.subplots(1,2,figsize=(11,4.8),gridspec_kw={'width_ratios':[1.2,1]})
    for i,arm in enumerate(ARMS):
        vals=[profiles[arm][k] for k in ('demand_damage','control_damage')]
        estimate(ax,np.arange(2)+(i-1)*.12,vals,arm,label=f"{LABELS[arm]} (n={vals[0]['n_families']})")
        estimate(bx,[i],[profiles[arm]['demand_minus_control']],arm,line=False)
    axes(ax,'Accuracy damage (percentage points)');axes(bx,'Demand − control damage (pp)')
    ax.set_xticks([0,1],['Demand knockout','Shifted control']);bx.set_xticks(range(3),[LABELS[a] for a in ARMS])
    ax.set_title('Eligible families within each arm');bx.set_title('Specific demand-aligned damage');ax.legend(fontsize=9)
    p=inference['primary']['P3']['simultaneous']
    fig.text(.1,.035,f"Paired P3: Thinking − CoT = {100*p['mean']:+.2f} pp; 98.75% CI [{100*p['ci'][0]:+.2f}, {100*p['ci'][1]:+.2f}], n={p['n_families']}",fontsize=10)
    fig.text(.1,.002,'Arm profiles use their own eligible families; primary cross-arm contrast uses their intersection. Error bars: descriptive 95% CI.',fontsize=9)
    save(fig,'figure4_demand_aligned_necessity')

    fig,aa=plt.subplots(1,3,figsize=(12,4.7))
    for i,arm in enumerate(ARMS):
        estimate(aa[0],[i],[native[arm]['episodes_per_1k']],arm,scale=1,line=False)
        estimate(aa[1],[i],[native[arm]['P2']],arm,scale=100,line=False)
        estimate(aa[2],[i],[profiles[arm]['late_damage']],arm,line=False)
    for ax,y,title in zip(aa,['Episodes / 1,000 tokens','Late episode fraction (%)','Final-40% accuracy damage (pp)'],
                         ['Native retrieval frequency','Native retrieval timing','Causal late necessity']):
        axes(ax,y);ax.set_title(title);ax.set_xticks(range(3),[LABELS[a] for a in ARMS],rotation=20)
    fig.text(.1,.015,'Same 64-family cohort; usage timing excludes families with no retrieval episodes. Distinct estimands, not an equivalence test.',fontsize=9)
    fig.text(.1,-.023,'Original 128-family native-use study found 0/4 supported positive primary contrasts. Error bars are descriptive 95% intervals.',fontsize=9)
    fig.subplots_adjust(wspace=.45,bottom=.22)
    save(fig,'figure5_native_usage_vs_necessity')
    print(DEST)


if __name__=='__main__': main()
