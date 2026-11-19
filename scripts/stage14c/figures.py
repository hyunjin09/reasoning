"""Standalone descriptive figures from sealed primary results; no model calls."""
import os
os.environ.setdefault('MPLCONFIGDIR','runs/stage14c/mpl_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scripts.stage14c.common import *

LABELS={'math':'MATH-Vision\n(existing anchor)','MMStar':'MMStar\n(mixed VQA)','BlindTest':'BlindTest\n(E*: line intersections)'}
COLORS={'math':'#3b6d96','MMStar':'#c27f30','BlindTest':'#327a52'}

def savefig(fig,name):
    p=ROOT/'figures'/name;assert not p.exists();fig.savefig(p,dpi=190,bbox_inches='tight');plt.close(fig)

def point(ax,y,value,ci,bounds,color):
    if value is None:ax.text(0,y,'Not estimable',va='center');return
    if bounds:ax.plot(bounds,[y,y],color='0.75',lw=5,zorder=1)
    if ci:ax.plot(ci,[y,y],color=color,lw=2,zorder=2)
    ax.scatter([value],[y],color=color,s=40,zorder=3)

def main():
    seal=load(ROOT/'audit/primary_analysis_seal.json')
    for p,h in seal['files'].items():assert sha(p)==h,p
    data=load(ROOT/'analysis/primary_results.json')['tasks'];names=list(LABELS);ys=np.arange(3)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(12,4),sharey=True)
    for y,b in enumerate(names):
        s=data[b]['I_supply'];r=s['rescue']
        point(axes[0],y,r['estimate_pp'],r['ci95_pp'],r['bounds_pp'],COLORS[b])
        axes[0].annotate(f"{r['numerator']}/{r['scored_denominator']}; unresolved {r['unresolved_followups']}",(r['estimate_pp'] or 0,y),xytext=(0,12),textcoords='offset points',ha='center',fontsize=8)
        point(axes[1],y,s['difference_pp'],s['ci95_pp'],s['difference_bounds_pp'],COLORS[b])
    axes[0].set_yticks(ys,[LABELS[b] for b in names]);axes[0].set_xlim(-3,103)
    axes[0].set_xlabel('Instruct rescue among scored native-wrong follow-ups (%)');axes[0].set_title('Conditional evidence-supply rescue')
    axes[1].axvline(0,color='0.7',lw=1);axes[1].set_xlabel('Paired E* minus native correctness (pp)');axes[1].set_title('Net supply benefit, including regressions')
    fig.suptitle('Eligible-stratum evidence supply: distinct denominators')
    fig.text(.02,-.04,'Colored intervals: 95% family bootstrap. Gray spans: conservative missingness bounds. No full-benchmark bottleneck interpretation.',fontsize=8)
    fig.tight_layout();savefig(fig,'figure2_rescue_profile.png')
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for y,b in enumerate(names):
        p=data[b]['post']
        for offset,side,label,color in [(-.16,'left','I','#92adc3'),(.16,'right','T','#355b7a')]:
            value=p['marginal_'+side]['accuracy_pp'];c=p['counts_'+side];n=c['CORRECT']+c['WRONG']
            if value is not None:
                axes[0].barh(y+offset,value,height=.28,color=color,label=label if y==0 else None)
                axes[0].text(value+1,y+offset,f'n={n}',va='center',fontsize=8)
        point(axes[1],y,p['difference_pp'],p['ci95_pp'],p['difference_bounds_pp'],COLORS[b])
    axes[0].set_yticks(ys,[LABELS[b] for b in names]);axes[1].set_yticks(ys,[LABELS[b] for b in names]);axes[0].set_xlim(0,115);axes[0].legend(frameon=False)
    axes[0].set_xlabel('Marginal scored-answer accuracy under E* (%)');axes[1].set_xlabel('Paired Thinking − Instruct under E* (pp)');axes[1].axvline(0,color='0.7',lw=1)
    axes[0].set_title('Separate scored denominators');axes[1].set_title('Common scored pairs; no marginal subtraction')
    fig.tight_layout();savefig(fig,'figure3_post_evidence_profile.png')
    fig,ax=plt.subplots(figsize=(8,4))
    for y,b in enumerate(names):
        p=data[b]['native_all'];point(ax,y,p['difference_pp'],p['ci95_pp'],p['difference_bounds_pp'],COLORS[b])
        ax.annotate(f"{p['paired_n']}/{p['n']} scored pairs",(p['difference_pp'] or 0,y),xytext=(0,13),textcoords='offset points',ha='center',fontsize=8)
    native_labels=dict(LABELS,BlindTest='BlindTest\n(all nine task types)')
    ax.set_yticks(ys,[native_labels[b] for b in names]);ax.axvline(0,color='0.7',lw=1);ax.set_xlabel('Paired native Thinking − Instruct correctness (pp)');ax.set_title('Native task selectivity on full selected source populations')
    fig.tight_layout();savefig(fig,'figure4_native_selectivity.png')
    fig,ax=plt.subplots(figsize=(7,5))
    for b in names:
        r=data[b]['I_supply']['rescue'];p=data[b]['post'];x=r['estimate_pp'];y=p['difference_pp']
        if x is None or y is None:continue
        if r['ci95_pp']:ax.plot(r['ci95_pp'],[y,y],color=COLORS[b])
        if p['ci95_pp']:ax.plot([x,x],p['ci95_pp'],color=COLORS[b])
        ax.scatter([x],[y],s=50,color=COLORS[b]);ax.annotate(f"{b} (E* n={p['n']})",(x,y),xytext=(6,8),textcoords='offset points',fontsize=9)
    ax.axhline(0,color='0.8',lw=1);ax.set_xlabel('Instruct rescue among scored native-wrong follow-ups (%)');ax.set_ylabel('Paired equal-evidence Thinking − Instruct (pp)')
    ax.set_title('Descriptive task map: different eligible strata and estimands')
    fig.text(.02,-.01,'Axes do not measure comparable amounts of upstream vs downstream failure. Cross-task differences are observational.',fontsize=8)
    fig.tight_layout();savefig(fig,'figure5_task_map.png')
if __name__=='__main__':main()
