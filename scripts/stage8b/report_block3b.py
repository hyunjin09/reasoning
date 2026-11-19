"""Render the prescribed Block3B figures and bounded interpretation."""
import json
import os
from pathlib import Path

_scratch=Path(__file__).resolve().parents[2]/'runs/stage8b_block3b_v1/render_cache'
_scratch.mkdir(parents=True,exist_ok=True)
os.environ['MPLCONFIGDIR']=str(_scratch/'matplotlib')
os.environ['TMPDIR']=str(_scratch)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from visual_reasoning.stage8b.block1_data import save

ROOT=Path('outputs/stage8b_block3b/v1');PREFIX='stage8b_block3b_'
COLORS={'correct':'#237d78','wrong':'#bb573e','unresolved':'#898989'}


def load(name):
    return json.loads((ROOT/name).read_text())


def finish(fig,name):
    path=ROOT/'figures';path.mkdir(exist_ok=True)
    fig.tight_layout()
    for extension in ['png','pdf']:
        output=path/f'{name}.{extension}';assert not output.exists()
        fig.savefig(output,dpi=180,bbox_inches='tight')
    plt.close(fig)


def paired_summary(frame):
    result=[];rng=np.random.default_rng(820260922)
    for width in [128,256,512]:
        for metric in ['tortuosity','movement']:
            name=f'delta_{metric}{width}'
            for local in ['L+','L-']:
                for outcome in ['all','correct','wrong']:
                    data=frame.loc[(frame.local==local)&frame[name].notna()]
                    if outcome!='all':data=data.loc[data.benchmark_label==outcome]
                    family=data.groupby('analysis_family_id')[name].mean().to_numpy()
                    samples=family[rng.integers(len(family),size=(4000,len(family)))].mean(axis=1) if len(family)>1 else None
                    result.append(dict(window=width,metric=metric,local=local,outcome=outcome,events=len(data),families=len(family),
                        paired_mean_delta=float(family.mean()) if len(family) else None,
                        ci95=np.quantile(samples,[.025,.975]).tolist() if samples is not None else None))
    save(ROOT/'audit/paired_changes.json',dict(records=result,status='secondary paired changes; no new primary hypothesis'))


def main():
    assert (ROOT/'audit/analysis_complete.json').exists()
    f=pd.read_parquet(ROOT/(PREFIX+'evidence_lineage.parquet'))
    stats=load('audit/statistical_results.json')
    recovery=load(PREFIX+'recovery_Lminus.json')
    mutation=load(PREFIX+'mutation_Lplus.json')
    wandering=load(PREFIX+'pre_post_wandering.json')
    refresh=load(PREFIX+'refresh_compliance.json')
    source=load(PREFIX+'source_switching.json')
    taxonomy=load(PREFIX+'downstream_failure_taxonomy.json')
    paired_summary(f)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    lp=f.loc[f.local=='L+'];lm=f.loc[f.local=='L-']
    fig,ax=plt.subplots(figsize=(8,4.2))
    categories=['Mutation witnessed','No mutation\n(full remainder)','Incidence unknown']
    for offset,outcome in [(-.19,'correct'),(.19,'wrong')]:
        d=lp.loc[lp.benchmark_label==outcome]
        counts=[d.mutation.eq(1).sum(),d.mutation.eq(0).sum(),d.mutation.isna().sum()]
        bars=ax.bar(np.arange(3)+offset,counts,.36,label=f'Final {outcome}',color=COLORS[outcome])
        ax.bar_label(bars)
    ax.set_xticks(range(3),categories);ax.set_ylabel('Anchor events (nested in families)')
    ax.set_title('L+ evidence fate: observed changes versus incomplete lineage')
    ax.legend();fig.text(.5,-.015,'Preserved references are not proof of full-trajectory stability; refresh coverage is insufficient.',ha='center',fontsize=9)
    finish(fig,'figure1_evidence_lifecycle')

    fig,axes=plt.subplots(2,2,figsize=(10,7))
    labels=['Mutation incidence','Refresh compliance (128-token gap)','New retrieval within 128 tokens','Post-minus-pre tortuosity (256)']
    for ax,(metric,result),label in zip(axes.flat,stats['primary'].items(),labels):
        ax.axvline(0,color='#999',lw=1)
        for y,mode in [(1,'raw'),(0,'adjusted')]:
            value=result.get(mode) or {};estimate=value.get('estimate');interval=value.get('ci9875')
            if estimate is not None:
                ax.plot(estimate,y,'o',color='#333' if mode=='adjusted' else '#777')
                if interval:ax.plot(interval,[y,y],color='#333' if mode=='adjusted' else '#777',lw=2)
                else:ax.annotate('CI unavailable',(estimate,y),xytext=(4,8),textcoords='offset points',fontsize=8)
        if not result.get('raw'):ax.text(.5,.5,'Insufficient outcome groups',transform=ax.transAxes,ha='center')
        ax.set_yticks([0,1],['Adjusted','Raw']);ax.set_ylim(-.6,1.6)
        ax.set_title(f'{label}\n{result["events"]} events / {result["families"]} families')
        ax.set_xlabel('Final wrong minus correct; 98.75% bootstrap CI')
    finish(fig,'figure2_primary_contrasts')

    fig,ax=plt.subplots(figsize=(10,7))
    for y,(_,row) in enumerate(lm.iterrows()):
        end=row.followup_tokens;color=COLORS[row.benchmark_label]
        ax.plot([0,end],[y,y],color=color,alpha=.55)
        ax.plot(0,y,'s',color='#333',ms=4)
        if pd.notna(row.next_retrieval_latency):ax.plot(row.next_retrieval_latency,y,'|',color='#334bb4',ms=10)
        if pd.notna(row.correction_latency_upper_bound):ax.plot(row.correction_latency_upper_bound,y,'^',color='#237d78',ms=7)
        status='correction witnessed' if row.recovery==1 else 'no correction (full review)' if row.recovery==0 else 'recovery unknown'
        ax.text(end+350,y,status,va='center',fontsize=8,color=color)
    ax.set_yticks(range(len(lm)),[f'{r.item_id} / {r.anchor_index}' for r in lm.itertuples()])
    ax.set_xlim(-400,lm.followup_tokens.max()*1.65);ax.set_xlabel('Reasoning tokens after committed local read')
    ax.set_title('L− recovery census: next retrieval | ; correction witness ▲\nTeal: final correct; rust: final wrong; gray: unresolved')
    finish(fig,'figure3_Lminus_recovery')

    fig,axes=plt.subplots(1,2,figsize=(10,4.8))
    for ax,local in zip(axes,['L+','L-']):
        d=f.loc[(f.local==local)&f.delta_tortuosity256.notna()]
        for row in d.itertuples():
            ax.plot([0,1],[row.pre_tortuosity256,row.post_tortuosity256],color=COLORS[row.benchmark_label],alpha=.45,marker='o',ms=3)
        ax.set_xticks([0,1],['Pre256','Post256']);ax.set_yscale('log');ax.set_ylabel('Standardized retrieval-feature tortuosity')
        ax.set_title(f'{local}: {len(d)} paired events\n{d.analysis_family_id.nunique()} families')
    fig.suptitle('Fixed symmetric exposure only; individual lines are descriptive',y=1.02)
    finish(fig,'figure4_pre_post_wandering')

    categories=[('L+ stable / final correct',(f.local=='L+')&(f.mutation==0)&(f.benchmark_label=='correct')),
        ('L+ stable / final wrong',(f.local=='L+')&(f.mutation==0)&(f.benchmark_label=='wrong')),
        ('L− correction witnessed',(f.local=='L-')&(f.recovery==1)),
        ('L− no correction / full review',(f.local=='L-')&(f.recovery==0))]
    fig,axes=plt.subplots(1,4,figsize=(13,4),sharey=True)
    for ax,(label,mask) in zip(axes,categories):
        allrows=f.loc[mask];d=allrows.loc[allrows.delta_tortuosity256.notna()]
        for row in d.itertuples():ax.plot([0,1],[row.pre_tortuosity256,row.post_tortuosity256],color=COLORS[row.benchmark_label],marker='o',alpha=.6)
        if not len(d):ax.text(.5,.5,'No full symmetric\n256-token pair',transform=ax.transAxes,ha='center')
        ax.set_xticks([0,1],['Pre','Post']);ax.set_yscale('log');ax.set_title(label.replace(' / ',' /\n'),fontsize=9)
        ax.set_xlabel(f'{len(d)} eligible / {len(allrows)} cases')
    axes[0].set_ylabel('Retrieval-feature tortuosity')
    fig.suptitle('vSTREAM bridge: coverage limits temporal interpretation\nThese features are not hidden-state vSTREAM measurements',fontsize=11,y=1.06)
    finish(fig,'figure5_vstream_bridge')

    fig,ax=plt.subplots(figsize=(8,4.3))
    labels=['D1\nArithmetic','D2\nBinding','D3\nFirst mutation','D4\nStale reuse','D5\nIntegration','DU\nUnresolved']
    bars=ax.bar(range(6),list(taxonomy['counts'].values()),color=['#777']*5+['#bb573e']);ax.bar_label(bars)
    ax.set_xticks(range(6),labels);ax.set_ylabel('L+ / final-wrong events');ax.set_title('First downstream failure remains unresolved\nLater error witnesses do not identify the first failure')
    finish(fig,'figure6_downstream_taxonomy')

    recommendation='Emphasize the dissociation between local evidence fate and final-answer correctness, using the observed correction, mutation and persistent-error cases as illustrations and reporting the controlled post-read comparisons as inconclusive.'
    primary=stats['primary'];ret=primary['reretrieval128'];ri=ret['adjusted']['ci9875']
    exposure=wandering['exposure'];align=sum(bool(r['aligned_episodes']) for r in source['semantic_refresh_alignment'])
    row_lines=[]
    for metric,result in primary.items():
        point=(result.get('adjusted') or {}).get('estimate');ci=(result.get('adjusted') or {}).get('ci9875')
        point_text=f'{point:.4g}' if point is not None else 'not identifiable'
        ci_text=f'[{ci[0]:.4g}, {ci[1]:.4g}]' if ci else 'unavailable'
        row_lines.append(f'| {metric} | {result["events"]} / {result["families"]} | {point_text} | {ci_text} |')
    summary=f'''# Stage8B Block3B — post-read lifecycle analysis

Status: **completed at the prescribed sparse-coverage / inconclusive-result stop boundary**.
No robust post-read mechanism was established. This is not evidence that mutation,
refresh, or recovery has no effect: semantic coverage and symmetric exposure are
too limited for that conclusion. No new research action was launched.

## Scope and validity

The frozen 256 MathVision items, 456 Block2 reviews and 148 T anchors remain unchanged:
120 L+, 17 L−, 11 L?, spanning 127 items and 126 conservative analysis families.
The 1707/1245 image alias is clustered together. All 148 anchors received masked
lineage review and quote validation before outcomes/passive values were joined.
There was one annotator, not an independent blinded panel.

Only 16 anchors had complete remainder review; 132 used source-reference windows
and concluding text. Thus witnessed reuse is not a full persistence certificate,
and failure to find a mutation/correction is not coded 0. This is a limitation of
the performed annotation coverage, not proof that the remaining text is inherently
unannotatable. The two mutation witnesses are 2 different families; the three
correction witnesses are 3 different families. All original evidence is preserved.

## Main comparison: L+ / final wrong minus L+ / final correct

| Endpoint | Eligible events / families | Adjusted difference | Multiplicity-adjusted 98.75% CI |
|---|---:|---:|---|
{chr(10).join(row_lines)}

New retrieval within 128 tokens was observed at family-weighted rates
{100*ret['means']['correct']:.1f}% in final-correct and {100*ret['means']['wrong']:.1f}% in final-wrong traces.
The adjusted difference was {100*ret['adjusted']['estimate']:.2f} percentage points
(98.75% CI {100*ri[0]:.2f} to {100*ri[1]:.2f}). This does not distinguish the groups reliably.
The first-eligible-event and normal-completion sensitivities also include zero.

Mutation: 2 observed positives, 14 full-review negatives, 104 unknown among 120 L+.
One mutation occurred in a final-correct item 1833 (die top-face 1→2), one in
final-wrong item 1017 (notch bottom→top). Unequal ascertainment prevents treating
complete-case rates as population incidence. The adjusted mutation bootstrap had
only {primary['mutation']['adjusted']['valid_bootstrap']}/4000 valid replicates, below the frozen 95% rule.

Refresh: three certified reuse gaps across two anchors were recorded, including
one semantically ambiguous refresh interval. Only one anchor had an identifiable
128-token compliance denominator with resolved refresh status; no outcome contrast
is possible. Explicit verbal reinspection without detector support is kept apart
from a stale-reuse certificate. {align}/{len(source['semantic_refresh_alignment'])} reviewed source-engagement spans have nearby
frozen detector episodes; these are sparse temporal alignments, not causal grounding.

## Pre/post wandering and vSTREAM bridge

Full symmetric 256-token exposure covers 27 L+ events /24 families (12 correct, 15 wrong)
and 7 L− events. The 128/512 sensitivities contain {exposure['128']['Lplus']}/{exposure['512']['Lplus']} L+ events.
The primary raw wrong-minus-correct delta was 19.46 tortuosity units, with a wide
interval crossing zero; adjustment reversed the point estimate and only
{primary['delta_tortuosity256']['adjusted']['valid_bootstrap']}/4000 bootstrap draws supported a nonsaturated identifiable fit.
Its interval is therefore withheld. No controls, anchors or windows were loosened.

The exploratory L− minus L+ post-minus-pre contrast is negative in the raw data,
not the hypothesized increase after local error. Its fully adjusted interval
includes zero and is very wide. With only seven exposed L− events, it establishes
neither a precursor nor a consequence of local failure. Secondary paired changes,
alternate windows, claim-start anchors and low-displacement exclusion are saved.
The representation is the frozen four standardized retrieval features, not a
hidden-state vSTREAM replication.

## Recovery and downstream evidence

L−: 3 observed corrections, 2 full-review persistent errors, 12 unknown.
The corrections occur in final-correct items 243 (circle count 3→4), 1715
(bottom-edge endpoints), 1642 (box count 4→5). Positive witness times are upper
bounds on first correction, not necessarily exact first-adoption latency.
The complete-case exact recovery interval is conditional on review coverage and
cannot support a population rate or a targeted-refresh mechanism.

Item 2634 re-inspects the chart and retains E-bar 1 instead of the source value 5;
it finishes wrong. Item 1707 retains the wrong edge binding yet finishes correct.
Together with the final-correct mutation case, these show why final correctness
cannot substitute for recovery or evidence preservation.

Continuous source switching, target/confuser transitions and source entropy are
unidentified: existing source replay covers isolated prefixes. No new replay was
needed, since it would not repair the primary annotation/exposure limitations.
All 62 L+ / final-wrong events (57 families) retain DU for the **first** downstream failure;
observing a later mutation does not identify the first error. This is unresolved
coverage, not evidence that arithmetic/integration errors are absent.

## Inference, resources and completion

Four frozen primary endpoints; 4000 complete-family bootstrap draws, seed 820260922;
family-equal event weighting; controls for t0 position, log trajectory length,
subject group, completion, R at the original T episode, ROI group and question
length. Pointwise 95% and four-endpoint 98.75% intervals are included only when
≥95% of replicates are valid. Missingness bounds accompany semantic endpoints.
Seven focused tests passed (boundaries, censoring, frozen geometry parity,
family weighting, confound identifiability and unknown semantics).

Both analysis executions were CPU-only Slurm jobs on node02, 2 CPUs / 8 GB, 0 GPUs.
The original execution and its mechanical correction are retained separately.
Frozen final-answer extraction spans map to tokens for 147 of 148 anchors; these
need not be the first answer commitment. Semantic subgoal boundaries remain
unidentified; full remaining retrieval is measured through native reasoning end.
Repairs select the first metric-eligible family event, separate semantic refresh
from unsupported staleness, and retain frozen final-answer extraction spans.
Labels, controls and primary windows were unchanged. No model/dataset download,
generation, detector refit or causal intervention occurred. GPU-hours: 0.
Detailed job receipts, timing and provenance are in `audit/` and `runs/`.

The 11 required artifacts and six figures are saved here. Figures explicitly show
missing coverage; empty categories are not evidence of mechanism absence.

## Exactly one recommendation

{recommendation}
'''
    path=ROOT/(PREFIX+'summary.md');assert not path.exists();path.write_text(summary)
    save(ROOT/'audit/paper_recommendation.json',dict(recommendation=recommendation,number_of_recommendations=1,
        decision='stop; no next experiment authorized by this completed action',robust_primary_support=False))
    print('report_and_six_figures_complete')


if __name__=='__main__':
    main()
