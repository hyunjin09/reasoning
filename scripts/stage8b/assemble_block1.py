"""Assemble frozen contrasts and five publication-exportable descriptive figures."""
import json
from datetime import datetime,timezone
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from visual_reasoning.stage8b.block1_data import ROOT,PREFIX,PRIMARY,FAMILIES,PHASE_METRICS,digest,save,load_frame,b0_path
from visual_reasoning.stage8b.block1_statistics import joint_intervals

LABELS={
 'retrieval_episode_count':'Episode count','retrieval_density':'Episodes / 1,000 tokens',
 'active_token_fraction':'Active-token fraction','first_retrieval_token':'First retrieval: token',
 'first_retrieval_normalized':'First retrieval: fraction','median_gap':'Median inter-episode gap',
 'episodes_after_first':'Recurrence count','late_episode_fraction_gt_0.5':'Late episode fraction > 50%',
 'late_episode_fraction_gt_0.75':'Late episode fraction > 75%',
 'standardized_transition_normalized_path_length':'Mean feature movement',
 'standardized_tortuosity':'Tortuosity'}
COLORS={'correct':'#2467a0','wrong':'#d16a35'}


def figures(frame,primary,curves):
    dest=ROOT/'figures';dest.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    def finish(fig,name):
        fig.tight_layout();fig.savefig(dest/(name+'.png'),bbox_inches='tight');fig.savefig(dest/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
    for number,key,title,ylabel in [(1,'density','Retrieval density through reasoning','Episodes / 1,000 tokens'),
                                    (2,'cumulative','Cumulative retrieval episodes','Mean cumulative episode count')]:
        fig,ax=plt.subplots(figsize=(7,4.4));rows=curves[key];x=[r['position'] for r in rows]
        for g,outcome in [('group0','correct'),('group1','wrong')]:
            mean=[r[g]['mean'] for r in rows]
            ci=np.array([r[g]['mean_ci']['ci95'] if r[g]['mean_ci']['ci95'] is not None else [np.nan,np.nan] for r in rows])
            ax.plot(x,mean,label=f'{outcome} (items n={rows[0][g]["n"]})',color=COLORS[outcome],lw=2)
            ax.fill_between(x,ci[:,0],ci[:,1],color=COLORS[outcome],alpha=.16)
        ax.set(xlabel='Normalized reasoning position',ylabel=ylabel,title=title,xlim=(0,1));ax.legend(frameon=False)
        fig.text(.02,.005,'Shading: pointwise 95% item-bootstrap intervals (4,000 resamples); unadjusted.',fontsize=8)
        finish(fig,f'figure{number}_{key}')
    def distributions(ax,metric):
        data=[frame.loc[frame.benchmark_label==g,metric].dropna().to_numpy() for g in ['correct','wrong']]
        artists=ax.boxplot(data,tick_labels=[f'{g}\nn={len(v)}' for g,v in zip(['correct','wrong'],data)],showfliers=False,patch_artist=True)
        for patch,color in zip(artists['boxes'],COLORS.values()):patch.set_facecolor(color);patch.set_alpha(.25)
        rng=np.random.default_rng(1234)
        for i,(values,color) in enumerate(zip(data,COLORS.values()),1):
            ax.scatter(i+rng.uniform(-.1,.1,len(values)),values,s=9,alpha=.45,color=color)
        ax.set_title(LABELS.get(metric,metric.replace('_',' ')));ax.set_ylabel('Per-item value')
        ax.set_yscale('symlog',linthresh=1 if 'fraction' not in metric else .01)
    fig,axes=plt.subplots(1,2,figsize=(9,4.6))
    for ax,metric in zip(axes,['median_gap','episodes_after_first']):distributions(ax,metric)
    fig.suptitle('Intervals and recurrence: one observation per trajectory')
    finish(fig,'figure3_intervals_recurrence')
    fig,axes=plt.subplots(1,3,figsize=(12,4.6))
    for ax,metric in zip(axes,['standardized_path_length','standardized_transition_normalized_path_length','standardized_tortuosity']):distributions(ax,metric)
    fig.suptitle('Geometry in the frozen standardized feature space')
    finish(fig,'figure4_geometry')
    fig,ax=plt.subplots(figsize=(10,7));ys=np.arange(len(PRIMARY))
    specs=[('Raw',None,-.24,'#777777'),('Length','length',-.08,'#4c9f70'),
           ('Length + completion','joint',.08,'#407fb3'),('All controls','full',.24,'#af5270')]
    for label,key,offset,color in specs:
        for i,metric in enumerate(PRIMARY):
            row=primary[metric]
            value=row['raw']['hedges_g'] if key is None else row['adjusted'][key]['standardized_coefficient']
            ci=row['raw']['hedges_g_ci']['ci95'] if key is None else row['adjusted'][key]['standardized_ci']['ci95']
            if value is not None:
                ax.plot(value,i+offset,'o',color=color,ms=4,label=label if i==0 else None)
                if ci is not None:ax.plot(ci,[i+offset]*2,color=color,lw=1)
    ax.axvline(0,color='black',lw=.8);ax.set_yticks(ys,[LABELS[m] for m in PRIMARY]);ax.invert_yaxis()
    ax.set(xlabel='Wrong − correct (pooled within-group SD units)',title='Effects before and after descriptive adjustment')
    ax.legend(frameon=False,loc='best',fontsize=8)
    fig.text(.02,.005,'Pointwise 95% item-bootstrap intervals. Family-wise simultaneous intervals are in the JSON report.',fontsize=8)
    finish(fig,'figure5_adjusted_effects')


def main():
    states=[json.loads((ROOT/'workers'/f'rank{i}'/'complete.json').read_text()) for i in range(2)]
    assert all(s['completed'] for s in states) and states[0]['all_tasks']==states[1]['all_tasks']
    tasks=states[0]['all_tasks'];assert sorted(sum([s['tasks'] for s in states],[]))==list(range(len(tasks)))
    primary={};secondary={};sensitivity={'gap0':{},'gap8':{},'low_displacement':{}};phase={};samples={}
    for t in tasks:
        name=f"{t['index']:03d}_{t['kind']}_{t['metric']}";row=json.loads((ROOT/'tasks'/(name+'.json')).read_text())
        kind=t['kind'];metric=t['metric']
        if kind=='primary':
            primary[metric]=row
            with np.load(ROOT/'tasks'/(name+'_bootstrap.npz')) as archive:samples[metric]={k:archive[k] for k in archive.files}
        elif kind=='secondary':secondary[metric]=row
        elif kind=='phase':phase[metric]=row
        elif kind=='curves':curves=row
        else:sensitivity[kind][metric]=row
    assert set(primary)==set(PRIMARY)
    family_ci={'raw':{},'full':{},'normal_full':{}}
    for mode in family_ci:
        for family,metrics in FAMILIES.items():
            entries={m:dict(point=primary[m]['raw']['mean_difference'] if mode=='raw' else primary[m]['adjusted'][mode]['coefficient'],
                            samples=samples[m][mode]) for m in metrics}
            # Unidentified coefficients are serialized as null; retain missingness.
            for e in entries.values():
                if e['point'] is None:e['point']=np.nan
            family_ci[mode][family]=joint_intervals(entries)
    raw=dict(direction='wrong minus correct',unit='item/image family',resamples=4000,seed=1234,
        primary={m:dict(all_scorable=r['raw'],normal_completion=r['normal_raw']) for m,r in primary.items()},
        secondary={m:dict(all_scorable=r['raw'],normal_completion=r['normal_raw']) for m,r in secondary.items()},
        simultaneous_families=family_ci['raw'],curves=curves)
    adjusted=dict(direction='wrong minus correct',unit='item/image family',resamples=4000,seed=1234,
        primary={m:r['adjusted'] for m,r in primary.items()},secondary={m:r['adjusted'] for m,r in secondary.items()},
        matched={m:r['matched'] for m,r in primary.items()},matching=json.loads((ROOT/'audit'/'matching_freeze.json').read_text()),
        simultaneous_families=family_ci['full'],normal_simultaneous_families=family_ci['normal_full'],
        robustness=sensitivity,limitations=['Cross-sectional descriptive adjustment, not causal identification.',
        'First timing and interval quantities condition on sufficient detected episodes; missingness is not imputed.',
        'Matching bootstrap conditions on the fixed matched pairs; sparse matches limit robustness.'])
    completion=dict(direction='capped minus normal',includes_unresolved=True,
        census=json.loads((ROOT/(PREFIX+'outcome_census.json')).read_text())['outcome_by_completion'],
        metrics={m:r['completion'] for m,r in primary.items()},
        interpretation_limit='Small capped cohort and length imbalance; not correctness evidence.')
    phase_data=dict(status='secondary descriptive',unit='item',metrics=phase,
        phases=['0–25%','25–50%','50–75%','75–100%'],
        warning='Pointwise intervals across phases; no causal-onset inference or promotion to primary status.')
    for filename,data in [('correct_wrong_raw.json',raw),('correct_wrong_adjusted.json',adjusted),('completion_analysis.json',completion),('phase_analysis.json',phase_data)]:save(ROOT/(PREFIX+filename),data)
    figures(load_frame(),primary,curves)
    expected=['outcome_census.json','retrieval_episode_table.parquet','trajectory_metrics.csv','correct_wrong_raw.json',
              'correct_wrong_adjusted.json','completion_analysis.json','phase_analysis.json']
    paths=[ROOT/(PREFIX+n) for n in expected]+sorted((ROOT/'figures').glob('*'))
    assert len(list((ROOT/'figures').glob('*.png')))==len(list((ROOT/'figures').glob('*.pdf')))==5
    base=json.loads(b0_path('freeze.json').read_text())
    for path,sha in {**base['artifacts_sha256'],**base['supporting_sha256']}.items():assert digest(path)==sha,path
    save(ROOT/'audit'/'analysis_result_freeze.json',dict(at=datetime.now(timezone.utc).isoformat(),analysis_complete=True,
        tasks=len(tasks),artifacts_sha256={str(p):digest(p) for p in paths},
        definition_sha256=digest(ROOT/'audit'/'analysis_definition_freeze.json'),
        execution_sha256=digest(ROOT/'audit'/'execution_freeze.json'),
        block0_unchanged=True,local_L_labels_not_inspected=True,scientific_summary_pending=True))
    print(json.dumps(dict(event='analysis_assembled',tasks=len(tasks),figures=5,summary_pending=True)),flush=True)


if __name__=='__main__':main()
