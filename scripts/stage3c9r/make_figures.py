#!/usr/bin/env python3
"""Render the 15 required scientific figures from frozen repair analyses."""

import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[2] / 'workspace/matplotlib_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from scripts.stage3c9r.freeze_inputs import OUT, read_json, write_json


def main():
    output = OUT / 'analysis/figures'
    output.mkdir(parents=True, exist_ok=True)
    profile = read_json(OUT / 'analysis/source_vs_rescue_2d.json')['rows']
    classified = read_json(OUT / 'analysis/checkpoint_classification.json')
    bases = classified['bases']
    sensitivity = read_json(OUT / 'analysis/threshold_sensitivity.json')['rows']
    lifetime = read_json(OUT / 'analysis/lifetime_analysis.json')
    comparison = read_json(OUT / 'analysis/stage3c9_phase_comparison.json')
    reference = read_json(OUT / 'analysis/base38_reference.json')
    outcome = read_json(OUT / 'analysis/scientific_outcome.json')
    plt.rcParams.update({'figure.dpi':130,'axes.spines.top':False,'axes.spines.right':False,
                         'font.size':10,'axes.titleweight':'bold'})
    inventory = []

    def save(fig, name, description):
        fig.tight_layout()
        for suffix in ('png','pdf'):
            fig.savefig(output / f'{name}.{suffix}', bbox_inches='tight')
        plt.close(fig)
        inventory.append({'name':name,'description':description,'png':f'analysis/figures/{name}.png','pdf':f'analysis/figures/{name}.pdf'})

    fig, axes = plt.subplots(1,3,figsize=(13,4))
    for ax,left,right,title in zip(axes,['phase_a_source_loss','phase_b_source_loss','phase_a_source_loss'],
        ['repair_source_loss','repair_source_loss','phase_b_source_loss'],['Phase A → repair','Phase B → repair','Original A → B']):
        rows = [r for r in comparison['condition_rows'] if r[left] is not None and r[right] is not None]
        x,y = [r[left] for r in rows],[r[right] for r in rows]
        ax.scatter(x,y,s=13,alpha=.5,color='#286a91')
        limits = min(x+y),max(x+y)
        ax.plot(limits,limits,color='gray',ls='--',lw=1)
        ax.set(title=f'{title} (n={len(rows)} O/C cells)',xlabel=left.replace('_',' '),ylabel=right.replace('_',' '))
    save(fig,'01_source_path_comparison','Descriptive legacy vs repair source losses; no legacy scores enter repair classification.')

    for i,w in enumerate(('W8','W16'),2):
        fig,ax = plt.subplots(figsize=(7,4))
        ax.hist([r['source_loss_mean'] for r in profile if r['window']==w],bins=30,color='#397b9b',edgecolor='white')
        ax.axvline(.05,color='#be523c',ls='--',label='Primary floor 0.05')
        ax.set(title=f'{w}: same-path source loss',xlabel='Mean sign-aligned source loss (nats / candidate token)',ylabel='Event windows (descriptive)')
        ax.legend()
        save(fig,f'{i:02d}_{w.lower()}_source_loss',f'{w} source loss across all frozen events.')

    for i,metric,title in [(4,'rescue_gain_mean','Event-span rescue'),(5,'neighbor_gain_mean','Matched-neighbor rescue')]:
        fig,ax=plt.subplots(figsize=(7,5))
        for w,color in [('W8','#2a789e'),('W16','#b66e3c')]:
            rows=[r for r in profile if r['window']==w]
            ax.scatter([r['source_loss_mean'] for r in rows],[r[metric] for r in rows],s=23,alpha=.65,label=w,color=color)
        ax.axvline(.05,color='gray',ls='--',lw=1);ax.axhline(.05,color='gray',ls='--',lw=1)
        ax.axhline(0,color='gray',lw=.5)
        ax.set(title=f'Same-path source loss vs {title.lower()}',xlabel='Source loss L',ylabel=f'{title} G (nats / candidate token)')
        ax.legend()
        save(fig,f'{i:02d}_source_vs_{"event" if i==4 else "neighbor"}', 'All event-window pairs; events are repeated observations within bases.')

    fig,ax=plt.subplots(figsize=(7,4))
    ax.hist([r['event_minus_neighbor'] for r in profile],bins=35,color='#568774',edgecolor='white')
    ax.axvline(0,color='gray',lw=1)
    ax.set(title='Event rescue minus matched-neighbor rescue',xlabel='Gain difference (nats / candidate token)',ylabel='Event windows (descriptive)')
    save(fig,'06_event_minus_neighbor','Frozen equal-width neighbors; all event windows included.')

    fig,ax=plt.subplots(figsize=(13,4))
    ax.bar(range(len(bases)),[b['checkpoint_count'] for b in bases],color='#397b9b')
    ax.set_xticks(range(len(bases)),[b['base_problem_id'] for b in bases],rotation=90,fontsize=7)
    ax.set(title='Confirmed C2/C3 checkpoints per frozen base',xlabel='Base problem ID (frozen order)',ylabel='Distinct checkpoints',ylim=(0,3.3),yticks=[0,1,2,3])
    save(fig,'07_checkpoints_per_base','A span qualifying at both W8/W16 is counted once.')

    fig,ax=plt.subplots(figsize=(6,4))
    n=classified['repeated_checkpoint_bases']
    bars=ax.bar(['No repeated pair','Repeated pair'],[48-n,n],color=['#9baab1','#397b9b'])
    ax.bar_label(bars); ax.set(title='Repeated-checkpoint bases at 0.05',ylabel='Independent bases',ylim=(0,53))
    save(fig,'08_repeated_primary','Two nonoverlapping checkpoints with start separation at least 24 tokens.')

    for i,metric,title in [(9,'checkpoint_events','Distinct C2/C3 checkpoints'),(10,'repeated_checkpoint_bases','Repeated-checkpoint bases')]:
        fig,ax=plt.subplots(figsize=(7,4))
        bars=ax.bar([str(r['effect_floor']) for r in sensitivity],[r[metric] for r in sensitivity],
                    color=['#9baab1','#397b9b','#9baab1','#9baab1'])
        ax.bar_label(bars);ax.set(title=f'Threshold sensitivity: {title.lower()}',xlabel='Effect floor (0.05 primary)',ylabel=title)
        ax.set_ylim(0,max(1,max(r[metric] for r in sensitivity))*1.25)
        save(fig,f'{i:02d}_threshold_{"checkpoints" if i==9 else "repeated"}','Only effect floor changes, after the primary freeze.')

    fig,ax=plt.subplots(figsize=(7,5))
    observed=[]
    for row in lifetime['rows']:
        for w,r in row['per_window'].items():
            if r['final_rescue_gain_mean'] is not None:
                observed.append(r)
                ax.scatter(r['local_rescue_gain_mean'],r['final_rescue_gain_mean'],s=40)
                ax.annotate(f"{row['base_problem_id']}/{row['event_id']} {w}",(r['local_rescue_gain_mean'],r['final_rescue_gain_mean']),fontsize=8,xytext=(4,4),textcoords='offset points')
    if not observed:
        ax.text(.5,.5,'No confirmed checkpoint with a distinct final probe',ha='center',transform=ax.transAxes,wrap=True)
    ax.axhline(.05,color='gray',ls='--');ax.axvline(.05,color='gray',ls='--')
    ax.set(title='Checkpoint rescue: local vs distinct final use',xlabel='Local rescue gain',ylabel='Final rescue gain')
    save(fig,'11_local_vs_final','Coincident local/final probes are right-censored and excluded from this comparison.')

    fig,axes=plt.subplots(1,2,figsize=(11,4))
    early=reference['repair']['events'][0]
    x=np.arange(2)
    axes[0].bar(x-.17,[early['windows'][w]['source_loss_mean'] for w in ('W8','W16')],.34,label='Source L')
    axes[0].bar(x+.17,[early['windows'][w]['rescue_gain_mean'] for w in ('W8','W16')],.34,label='Event G')
    axes[0].axhline(.05,color='gray',ls='--')
    axes[0].set_xticks(x,[f"{w} ({early['windows'][w]['classification']})" for w in ('W8','W16')])
    axes[0].set(title='Base 38, frozen first event',ylabel='Nats / candidate token');axes[0].legend()
    life=next((r for r in reference['lifetime'] if r['event_id']==early['event_id']),None)
    if life:
        for w,r in life['per_window'].items():
            axes[1].plot([0]+[v['distance_from_span_end'] for v in r['readouts']],
                         [r['local_rescue_gain_mean']]+[v['rescue_gain_mean'] for v in r['readouts']],
                         marker='o',linestyle='none',label=f'Repair {w}')
        axes[1].legend()
    else:
        axes[1].text(.5,.5,'First event did not remain C2/C3;\nlifetime follow-up not eligible',ha='center',transform=axes[1].transAxes)
    axes[1].axhline(.05,color='gray',ls='--');axes[1].set(title='Observed semantic readouts',xlabel='Distance from span end (local shown at 0)',ylabel='Rescue gain')
    save(fig,'12_base38_replication','Observed probes only; intervening intervals are unresolved. Labels show full frozen checkpoint classes; the reference does not tune the repair.')

    fig,ax=plt.subplots(figsize=(7,4))
    labels=['RIGHT-CENSORED','L-Short','L-Medium','L-Persistent']
    bars=ax.bar(labels,[lifetime['phenotype_counts'].get(x,0) for x in labels],color=['#bb8155','#397b9b','#568774','#816d9f'])
    ax.bar_label(bars);ax.set(title='Checkpoint lifetime and explicit censoring',ylabel='Distinct checkpoints')
    ax.set_ylim(0,max(1,max(lifetime['phenotype_counts'].values(),default=0))*1.3)
    ax.tick_params(axis='x',labelsize=8)
    save(fig,'13_lifetime_censoring','Distant readouts do not resolve the decay time inside unobserved intervals.')

    examples=[r for r in profile if r['source_sensitive'] and not r['functional_span_rescue']][:6]
    fig,ax=plt.subplots(figsize=(10,4))
    x=np.arange(len(examples))
    for offset,metric,label in [(-.25,'source_loss_mean','Source L'),(0,'rescue_gain_mean','Event G'),(.25,'neighbor_gain_mean','Neighbor G')]:
        ax.bar(x+offset,[r[metric] for r in examples],width=.25,label=label)
    ax.axhline(.05,color='gray',ls='--');ax.set_xticks(x,[f"{r['base_problem_id']}/{r['event_id']} {r['window']}" for r in examples],fontsize=8)
    ax.set(title='Source-sensitive windows without qualifying span rescue',ylabel='Nats / candidate token',xlabel='First eligible examples in frozen order (descriptive)');ax.legend()
    save(fig,'14_source_sensitive_nonrescued','Illustrative controls, with no new event or span selection for inference.')

    fig,ax=plt.subplots(figsize=(12,4));ax.axis('off')
    cells=[['R1','Repeated checkpoints absent at all floors','Retrieval Trigger, review only'],
           ['R2','Source sensitivity with rare sparse rescue','Local state / renewed retrieval interpretation'],
           ['R3','Robust repeated checkpoints emerge','Original route gate must pass before execution'],
           ['R4','Repeated conclusion changes with floor','Continuous window-level measure, review only']]
    table=ax.table(cellText=cells,colLabels=['Branch','Evidence criterion','Plan implication'],loc='center',cellLoc='left',colWidths=[.09,.45,.46])
    table.auto_set_font_size(False);table.set_fontsize(10);table.scale(1,2.3)
    selected=int(outcome['outcome'][1])
    for column in range(3):table[selected,column].set_facecolor('#d5e8df')
    ax.set_title(f"Selected {outcome['outcome']}: {outcome['recommendation']}\nNo next-stage experiment starts in Stage 3C.9R",pad=12)
    save(fig,'15_scientific_decision','Exactly one recommendation from the approved outcome branches.')
    write_json(output / 'index.json',{'figures':inventory,'count':len(inventory)})
    print(f'{len(inventory)} figures saved as PNG and PDF')


if __name__=='__main__':
    main()
