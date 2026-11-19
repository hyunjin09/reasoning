"""Reporting-only refinements: full denominators and eligible/native profiles."""
from scripts.stage14c.figures import *
from scripts.stage14c.figures import savefig as original_savefig

def savefig(fig,name):
    original_savefig(fig,name.replace('.png','_v3.png'))

def main():
    for p,h in load(ROOT/'audit/primary_analysis_seal.json')['files'].items():assert sha(p)==h
    data=load(ROOT/'analysis/primary_results.json')['tasks'];names=list(LABELS);ys=np.arange(3)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(13,5),gridspec_kw={'width_ratios':[1.3,1]})
    for y,b in enumerate(names):
        p=data[b]['post']
        for off,side,lab,col in [(-.16,'left','Instruct','#92adc3'),(.16,'right','Thinking','#355b7a')]:
            value=p['marginal_'+side]['accuracy_pp'];c=p['counts_'+side]
            axes[0].barh(y+off,value,height=.28,color=col,label=lab if y==0 else None)
            axes[0].text(value+1,y+off,f"{c['CORRECT']}/{c['WRONG']}/{c['UNSCORABLE']}/{c['TECHNICAL_MISSING']}",va='center',fontsize=8)
        point(axes[1],y,p['difference_pp'],p['ci95_pp'],p['difference_bounds_pp'],COLORS[b])
        axes[1].annotate(f"{p['paired_n']}/{p['n']} scored pairs",(p['difference_pp'],y),xytext=(0,12),textcoords='offset points',ha='center',fontsize=8)
    axes[0].set_yticks(ys,[LABELS[b] for b in names]);axes[0].set_xlim(0,135);axes[0].set_xticks([0,25,50,75,100]);axes[0].legend(frameon=False,loc='lower right')
    axes[1].set_yticks(ys,['']*3);axes[1].axvline(0,color='0.7',lw=1)
    for ax in axes:ax.set_ylim(-.5,2.4)
    axes[0].set_title('Marginal accuracy; counts: correct/wrong/unscorable/missing')
    axes[0].set_xlabel('Scored-answer accuracy under E* (%)')
    axes[1].set_title('Paired post-evidence variant gap')
    axes[1].set_xlabel('Thinking − Instruct under E* (pp)')
    fig.text(.02,-.01,'Different scored marginal denominators; paired effect is not their subtraction. Colored: 95% family bootstrap; gray: missingness bounds.',fontsize=8)
    fig.tight_layout();savefig(fig,'figure3_post_evidence_profile.png')

    fig,axes=plt.subplots(1,2,figsize=(13,5),gridspec_kw={'width_ratios':[1.2,1]})
    for y,b in enumerate(names):
        p=data[b]['native_all']
        for off,side,lab,col in [(-.16,'left','Instruct','#92adc3'),(.16,'right','Thinking','#355b7a')]:
            value=p['marginal_'+side]['accuracy_pp'];c=p['counts_'+side];n=c['CORRECT']+c['WRONG']
            axes[0].barh(y+off,value,height=.28,color=col,label=lab if y==0 else None)
            axes[0].text(value+1,y+off,f"{value:.1f}%; n={n}",va='center',fontsize=8)
        for off,key,marker in [(-.15,'native_all','o'),(.15,'native_eligible','D')]:
            q=data[b][key];v=q['difference_pp'];ci=q['ci95_pp']
            axes[1].plot(ci,[y+off]*2,color=COLORS[b],lw=2)
            if q['difference_bounds_pp']:axes[1].plot(q['difference_bounds_pp'],[y+off]*2,color='0.8',lw=5,zorder=0)
            axes[1].scatter([v],[y+off],marker=marker,facecolor=COLORS[b] if key=='native_all' else 'white',edgecolor=COLORS[b],zorder=3)
            axes[1].annotate(f"{q['paired_n']}/{q['n']}",(v,y+off),xytext=(0,9),textcoords='offset points',ha='center',fontsize=7)
    labs=dict(LABELS,BlindTest='BlindTest\n(native: nine task labels)')
    axes[0].set_yticks(ys,[labs[b] for b in names]);axes[0].set_xlim(0,115);axes[0].set_xticks([0,25,50,75,100]);axes[0].legend(frameon=False,loc='lower right')
    axes[1].set_yticks(ys,['']*3);axes[1].axvline(0,color='0.7',lw=1)
    for ax in axes:ax.set_ylim(-.5,2.55)
    axes[0].set_title('Native accuracy on each variant’s scored population');axes[0].set_xlabel('Family-equal scored-answer accuracy (%)')
    axes[1].set_title('Native paired gaps: full vs E*-eligible source sets');axes[1].set_xlabel('Thinking − Instruct (pp)')
    fig.text(.02,-.01,'Filled circles: full native set. Open diamonds: E*-eligible subset (BlindTest: line intersections). Labels: scored pairs/items; 95% family bootstrap.',fontsize=8)
    fig.tight_layout();savefig(fig,'figure4_native_selectivity.png')

    fig,ax=plt.subplots(figsize=(8,5))
    for b in names:
        r=data[b]['I_supply']['rescue'];p=data[b]['post'];x=r['estimate_pp'];y=p['difference_pp']
        ax.plot(r['ci95_pp'],[y,y],color=COLORS[b]);ax.plot([x,x],p['ci95_pp'],color=COLORS[b]);ax.scatter([x],[y],s=50,color=COLORS[b])
        ax.annotate(f"{b}\nE*: {p['n']}/{data[b]['native_all']['n']} native items",(x,y),xytext=(6,6),textcoords='offset points',fontsize=9)
    ax.axhline(0,color='0.8',lw=1);ax.set_xlabel('Instruct rescue among scored native-wrong follow-ups (%)');ax.set_ylabel('Paired equal-evidence Thinking − Instruct (pp)');ax.set_xlim(48,107)
    ax.set_title('Descriptive task map: differing eligible strata and estimands')
    fig.text(.02,-.01,'Axes are not comparable amounts of upstream/downstream failure. Cross-task differences are observational; intervals: 95% family bootstrap.',fontsize=8)
    fig.tight_layout();savefig(fig,'figure5_task_map.png')
if __name__=='__main__':main()
