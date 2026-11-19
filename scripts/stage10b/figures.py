"""Four standalone census figures with explicit candidate-only interpretation."""
import os,textwrap
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from scripts.stage10b.common import ROOT,load,save,sha,now


def store(fig,name):
    root=ROOT/'figures';root.mkdir(exist_ok=True)
    for suffix in ('png','pdf'):fig.savefig(root/f'{name}.{suffix}',dpi=180,bbox_inches='tight')
    plt.close(fig)


def wrapped(s,width=68,max_chars=420):
    s=s[:max_chars]+('…' if len(s)>max_chars else '')
    return '\n'.join(textwrap.wrap(s,width=width))


def main():
    assert os.environ.get('SLURM_JOB_ID')
    result=load(ROOT/'stage10b_yield_inference.json');events=load(ROOT/'audit/analyzed_events.json')['rows']
    # Deterministic illustration choice, unrelated to strength of the routing effect.
    choices=sorted([e for e in events if e['primary_for_trajectory']],key=lambda e:e['event_id'])
    if not choices:choices=sorted([e for e in events if e['semantic_clean']],key=lambda e:e['event_id'])
    fig=plt.figure(figsize=(12,7));axes=fig.subplots(2,2)
    if choices:
        e=choices[0];a,b,c,d=axes.ravel()
        a.axis('off');a.set_title('A → intervening text reasoning',loc='left')
        a.text(0,.92,'Resolved: '+wrapped(e['A_fact'])+'\n\nQuote: '+wrapped(e['A_resolution_quote'])+'\n\n'+wrapped(e['text_interval_reason']),va='top',fontsize=10,transform=a.transAxes)
        b.axis('off');b.set_title('New B demand → candidate re-access',loc='left')
        b.text(0,.92,wrapped(e['B_onset_quote'])+'\n\nRequired: '+wrapped(e['B_fact_required'])+
               '\n\nObservation: '+wrapped(e.get('B_observation_quote') or 'No explicit observation',max_chars=180)+f"\n\nPrior availability: {e['prior_availability']}\nC5: {e['C5']} | lag: {e['lag']}",va='top',fontsize=10,transform=b.transAxes)
        rr=e['rows'];x=[r['offset'] for r in rr]
        if rr:
            c.plot(x,[r['target_control_mean_ratio'] for r in rr],label='Target/control mean attention',color='#117a7a')
            c.axhline(1.5,color='grey',ls='--',label='Frozen ratio threshold')
            d.plot(x,[r['retrieval_score'] if r['retrieval_score'] is not None else np.nan for r in rr],label='Frozen retrieval score',color='#634a99')
            d.plot(x,[r['target_image_mass'] for r in rr],label='Target within-image mass',color='#b9672a')
            d.axhline(.5478025980771918,color='#634a99',ls='--',alpha=.5)
            d.axhline(.05,color='#b9672a',ls=':',alpha=.7)
        else:
            for ax in (c,d):ax.text(.5,.5,'Routing unavailable',ha='center',transform=ax.transAxes)
        for ax in (c,d):ax.set(xlabel='Generated-token offset from B onset',xlim=(0,31));ax.legend(fontsize=8,loc='best') if rr else None
        c.set_ylabel('Patch-mean ratio');d.set_ylabel('Score / mass')
        fig.suptitle(f"Candidate anatomy: {e['trajectory_id']} · association, not causal reopening")
        chosen=e['event_id']
    else:
        for ax in axes.ravel():ax.axis('off')
        axes[0,0].text(0,.8,'No C1–C4 candidate was identified.\nA clean anatomy cannot be illustrated.',fontsize=14)
        chosen=None
    fig.tight_layout();store(fig,'stage10b_figure1_candidate_anatomy')
    flow=result['flow'];fig,ax=plt.subplots(figsize=(10,4));ax.axis('off')
    labels=[('Eligible traces',flow['eligible']),('New B demand\n(C3)',flow['any_C3']),
            ('B absent\n(C3+C4)',flow['any_C3_C4']),('Resolved A\n+ text interval\n(C1–C4)',flow['C1_C4']),
            ('Target-specific\nre-access\n(C1–C5)',flow['C1_C5'])]
    for i,(label,count) in enumerate(labels):
        x=.005+i*.202;w=.175
        ax.add_patch(FancyBboxPatch((x,.34),w,.42,boxstyle='round,pad=.005',
                                   facecolor='#e9f3f3',edgecolor='#117a7a',transform=ax.transAxes))
        ax.text(x+w/2,.55,f'{label}\n\n{count}',ha='center',va='center',fontsize=9.5,transform=ax.transAxes)
        if i<4:ax.annotate('',xy=(x+.196,.55),xytext=(x+w+.004,.55),xycoords='axes fraction',arrowprops=dict(arrowstyle='->',lw=1.4))
    ax.text(.5,.13,'One count per independent problem/image trajectory; observed prefixes retained.',ha='center',transform=ax.transAxes)
    ax.set_title('Stage10B census flow');store(fig,'stage10b_figure2_census_flow')
    fig,ax=plt.subplots(figsize=(9,4))
    for d,color in [('MathVision','#117a7a'),('MathVerse','#b9672a')]:
        x=result['datasets'][d]['timing']['offsets'];ax.hist(x,bins=np.arange(-.5,32.5,1),alpha=.65,label=f'{d} (n={len(x)})',color=color)
    ax.set(xlabel='Earliest qualifying re-access offset (generated tokens)',ylabel='Independent trajectories',xlim=(-.5,31.5),title='Candidate timing within the frozen32-token window')
    ax.legend();store(fig,'stage10b_figure3_timing')
    fig,(a,b)=plt.subplots(1,2,figsize=(12,5),gridspec_kw={'width_ratios':[1,2]})
    cats=result['pooled']['taxonomy'];a.bar(list(cats),list(cats.values()),color='#117a7a');a.set(title='Earliest clean event taxonomy',ylabel='Independent trajectories')
    neg=result['primary_negative_categories'];keys=list(neg);b.barh(keys,[neg[k] for k in keys],color='#8b949e');b.invert_yaxis();b.tick_params(axis='y',labelsize=8);b.set(title='Preserved primary negative categories',xlabel='Independent trajectories')
    fig.tight_layout();store(fig,'stage10b_figure4_taxonomy')
    save(ROOT/'audit/figure_receipt.json',dict(at=now(),anatomy_event_id=chosen,
        selection='Lexicographically first primary clean event; first semantic near-miss if none clean.',
        figures_sha256={str(p):sha(p) for p in (ROOT/'figures').glob('*') if p.suffix in ('.png','.pdf')}))


if __name__=='__main__':main()
