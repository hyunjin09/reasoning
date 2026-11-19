"""Measure frozen passive traces, then join sealed semantics and final outcomes."""
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import binomtest

from visual_reasoning.stage8b.block1_data import digest, save
from visual_reasoning.stage8b.block3b import post_read, pre_post, aligned_refresh
from visual_reasoning.stage8b.block3b_stats import contrast, missing_bounds

ROOT=Path('outputs/stage8b_block3b/v1')
B0=Path('outputs/stage8b_block0/v1')
PREFIX='stage8b_block3b_'
PRIMARY=['mutation','refresh_compliance128','reretrieval128','delta_tortuosity256']


def load(path):
    return json.loads(Path(path).read_text())


def output(name, value):
    save(ROOT/(PREFIX+name+'.json'),value)


def main():
    started=time.monotonic()
    seal=load(ROOT/'annotations/semantic_seal.json')
    for path, expected in seal['review_sha256'].items():
        assert digest(path)==expected,path
    assert digest(ROOT/'annotations/anchors.json')==seal['anchors_sha256']
    assert digest('plan/stage8b_block3b_execution_protocol_v1.md')==seal['protocol_sha256']
    anchors=load(ROOT/'annotations/anchors.json')['rows']
    reviews={r['event_id']:r for r in seal['records']}
    adjacency=load(ROOT/'annotations/adjacency_audit_v1.json')
    # Explicitly select nuisance columns, without final outcome values.
    cols=['item_id','reasoning_tokens','generated_tokens','post_think_tokens','subject_group','completion','log_question_length']
    meta=pd.read_csv('outputs/stage8b_block1/v1/stage8b_block1_trajectory_metrics.csv',usecols=cols,dtype={'item_id':str}).set_index('item_id')
    local=pd.read_parquet('outputs/stage8b_block2/v1/stage8b_block2_local_read_table.parquet',columns=['event_id','roi_type']).set_index('event_id')
    episode_cols=['item_id','event_id','start_token','end_token','episode_index']
    episodes=pd.read_parquet(B0/'stage8b_block0_retrieval_episode_table.parquet',columns=episode_cols)
    episodes.item_id=episodes.item_id.astype(str)
    features_path=B0/'stage8b_block0_token_retrieval_features.parquet'
    reader=pq.ParquetFile(features_path)
    standard=['standardized_R','standardized_qk_visual_nonvisual','standardized_visual_mass','standardized_visual_concentration']
    by_item={str(a['item_id']):[] for a in anchors}
    for i,a in enumerate(anchors):
        by_item[str(a['item_id'])].append((i,a))
    rows=[]; passive=[]; opportunities=[]; source_alignment=[]
    for group in range(reader.num_row_groups):
        item=str(reader.read_row_group(group,columns=['item_id']).column(0)[0].as_py())
        if item not in by_item:
            continue
        tokens=reader.read_row_group(group,columns=['item_id','token_index','R']+standard).to_pandas()
        tokens=tokens.sort_values('token_index')
        length=int(meta.loc[item,'reasoning_tokens'])
        tokens=tokens.loc[tokens.token_index<length]
        assert np.array_equal(tokens.token_index.to_numpy(),np.arange(length)),item
        z=tokens[standard].to_numpy(float)
        es=episodes.loc[episodes.item_id==item].sort_values('start_token').to_dict('records')
        starts=[int(e['start_token']) for e in es]
        for index,a in by_item[item]:
            t0=a['t0']; assert length==a['reasoning_tokens']
            review=reviews[a['event_id']]
            retrieval=post_read(t0,length,starts); geo=pre_post(t0,z)
            start_retrieval=post_read(a['claim_start_token'],length,starts)
            start_geo=pre_post(a['claim_start_token'],z)
            row=dict(anchor_index=index,event_id=a['event_id'],item_id=item,
                family_id=a['family_id'],analysis_family_id=a['analysis_family_id'],local=a['local'],
                t0=t0,tR=a['tR'],tF=None,tF_status='exact committed final-answer token not identified; use native think boundary and generation end separately',
                claim_start_token=a['claim_start_token'],native_reasoning_end=length-1,
                source_identity=a['source_identity'],local_quote=a['quote'],
                reasoning_tokens=length,normalized_t0=t0/max(1,length-1),log_reasoning_length=np.log(length),
                R_at_tR=float(tokens.R.iloc[a['tR']]),roi_type=local.loc[a['event_id'],'roi_type'],
                mutation=review['mutation'],recovery=review['recovery'],downstream=review['downstream'],
                full_remainder_reviewed=review['full_remainder_reviewed'],
                states_reviewed=''.join(review['states']),semantic_refresh_candidate='R' in review['states'],
                observations_json=json.dumps(review['observations'],ensure_ascii=False),
                coverage_note=review['coverage_note'],lineage_rationale=review['rationale'],
                retrieval_use_latency=t0-a['tR'],remaining_episodes=retrieval['remaining_episodes'],
                next_retrieval_latency=retrieval['time_to_next'],next_retrieval_censored=retrieval['next_retrieval_censored'],
                followup_tokens=retrieval['followup_tokens'],burstiness=retrieval['burstiness'],
                source_switch_count=None,source_entropy=None)
            for key in cols[2:]:
                row[key]=meta.loc[item,key]
            row['generation_end_token']=int(row['generated_tokens'])-1
            for width,info in retrieval['windows'].items():
                row['reretrieval'+width]=info['within_window']
                row['retrieval_count'+width]=info['episodes']
                row['retrieval_exposure'+width]=info['exposure']
            row['reretrieval128_start_anchor']=start_retrieval['windows']['128']['within_window']
            for width,info in geo.items():
                for key in ['delta_tortuosity','delta_movement']:
                    row[key+width]=info[key]
                for side in ['pre','post']:
                    for key in ['tortuosity','movement','displacement','path_length','valid_transitions']:
                        row[f'{side}_{key}{width}']=info[side][key] if info['complete'] else None
            row['delta_tortuosity256_start_anchor']=start_geo['256']['delta_tortuosity']
            for kind in ['correction','mutation']:
                observed=[o for o in review['observations'] if o['kind']==kind]
                first=min((o['start_token'] for o in observed),default=None)
                row[kind+'_witness_token']=first
                row[kind+'_latency_upper_bound']=first-t0 if first is not None else None
                row[kind+'_retrievals_before_witness']=sum(t0<s<=first for s in starts) if first is not None else None
            for o in review['observations']:
                if o['kind']=='refresh':
                    source_alignment.append(dict(event_id=a['event_id'],source_identity=a['source_identity'],
                        semantic_span=o,aligned_episodes=aligned_refresh(o,es),
                        status='semantic engagement plus temporal detector alignment; source routing/causality not certified'))
            own=[]
            for op in adjacency['opportunities']:
                if op['anchor_index']!=index:
                    continue
                use=review['observations'][op['reuse_observation']]
                previous=t0 if op.get('previous')=='anchor' else review['observations'][op['previous_observation']]['end_token']-1
                engagement=review['observations'][op['refresh_observation']] if op['refresh_observation'] is not None else None
                intervening=[e for e in es if e['end_token']>previous and e['start_token']<=use['end_token']-1]
                alignment=aligned_refresh(engagement,intervening) if engagement else []
                refreshed=None if op['semantic_refresh'] is None else int(op['semantic_refresh'] and bool(alignment))
                own.append(dict(**op,event_id=a['event_id'],previous_token=previous,reuse_token=use['start_token'],
                    gap=use['start_token']-previous,refreshed=refreshed,aligned_episodes=alignment,
                    stale_reuse=None if refreshed is None or (op['semantic_refresh'] and not alignment) else bool(op['refresh_expected'] and not refreshed)))
            opportunities.extend(own)
            for gap in [64,128,256]:
                eligible=[o for o in own if o['gap']>=gap]
                row[f'refresh_opportunities{gap}']=len(eligible) if index in adjacency['anchor_opportunity_census_complete'] else None
                row[f'refresh_compliance{gap}']=float(np.mean([o['refreshed'] for o in eligible])) if eligible and all(o['refreshed'] is not None for o in eligible) else None
            if review['next_subgoal_token'] is not None:
                row['next_subgoal_token']=review['next_subgoal_token']
                row['retrievals_until_subgoal']=sum(t0<s<=review['next_subgoal_token'] for s in starts)
            else:
                row['next_subgoal_token']=None;row['retrievals_until_subgoal']=None
            rows.append(row)
            passive.append(dict(event_id=a['event_id'],retrieval=retrieval,geometry=geo,
                start_anchor_retrieval=start_retrieval,start_anchor_geometry=start_geo))
        print('extracted',item,'anchors',len(rows),flush=True)
    frame=pd.DataFrame(rows).sort_values('anchor_index')
    assert len(frame)==148 and frame.event_id.is_unique
    lp=frame.loc[frame.local=='L+']
    roi=lp.roi_type.fillna('MISSING').astype(str).value_counts()
    kept=roi.loc[roi>=10].index.tolist()
    frame['roi_group']=frame.roi_type.fillna('MISSING').astype(str).map(lambda x:x if x=='MISSING' or x in kept else 'OTHER')
    lp=frame.loc[frame.local=='L+']
    continuous=['normalized_t0','log_reasoning_length','R_at_tR','log_question_length']
    freeze=dict(at=datetime.now(timezone.utc).isoformat(),semantic_seal_sha256=digest(ROOT/'annotations/semantic_seal.json'),
        outcome_values_opened=False,continuous={k:dict(mean=float(lp[k].mean()),scale=float(lp[k].std(ddof=0)) or 1) for k in continuous},
        categorical={k:sorted(lp[k].astype(str).unique().tolist()) for k in ['subject_group','completion','roi_group']},
        roi_counts=roi.to_dict(),roi_kept=kept,low_displacement_threshold={})
    for width in [128,256,512]:
        pool=frame[[f'pre_displacement{width}',f'post_displacement{width}']].to_numpy(float).ravel()
        pool=pool[np.isfinite(pool)]
        freeze['low_displacement_threshold'][str(width)]=float(np.quantile(pool,.05)) if len(pool) else None
    original=load(ROOT/'audit/initial_analysis_before_mechanical_repairs/nuisance_freeze.json')
    assert {k:v for k,v in freeze.items() if k!='at'}=={k:v for k,v in original.items() if k!='at'}
    freeze=original  # Preserve the actual pre-outcome freeze, including its timestamp.
    save(ROOT/'audit/nuisance_freeze.json',freeze)
    save(ROOT/'audit/passive_measurements.json',dict(records=passive,source_sha256=digest(features_path)))
    # The final outcomes are first read only after semantic and nuisance seals exist.
    outcome=pd.read_csv('outputs/stage8b_block1/v1/stage8b_block1_trajectory_metrics.csv',usecols=['item_id','benchmark_label'],dtype={'item_id':str})
    frame=frame.merge(outcome,on='item_id',how='left',validate='many_to_one').sort_values('anchor_index')
    assert frame.benchmark_label.notna().all()
    final_spans=pd.read_csv(B0/'stage8b_block0_outcome_table.csv',dtype={'item_id':str}).set_index('item_id')
    cohort={str(r['item_id']):r for r in load(B0/'stage8b_block0_cohort_manifest.json')['rows']}
    for item in frame.item_id.unique():
        source=final_spans.loc[item]
        if not np.isfinite(source.source_span_start) or not np.isfinite(source.source_span_end):
            continue
        packet=load(ROOT/f'annotations/packets/{item}.json')
        assert digest(packet['token_file'])==packet['token_sha256']
        pieces=[json.loads(line)['decoded_token'] for line in Path(packet['token_file']).read_text().splitlines()]
        text=''.join(pieces);endpoints=np.cumsum([len(piece) for piece in pieces])
        generation=Path(cohort[item]['receipt']).parent/'generation.json'
        assert digest(generation)==source.generation_sha256
        assert text==load(generation)['raw_decoded_response']
        lo,hi=int(source.source_span_start),int(source.source_span_end)
        assert 0<=lo<hi<=len(text)
        match=frame.item_id==item
        frame.loc[match,'tF']=int(np.searchsorted(endpoints,lo,side='right'))
        frame.loc[match,'tF_end_token']=int(np.searchsorted(endpoints,hi-1,side='right'))+1
        frame.loc[match,'tF_char_start']=lo;frame.loc[match,'tF_char_end']=hi
        frame.loc[match,'tF_status']='frozen Block0 answer-extraction span; not necessarily first final-answer commitment'

    path=ROOT/(PREFIX+'evidence_lineage.parquet');assert not path.exists()
    frame.to_parquet(path,index=False)
    lp=frame.loc[frame.local=='L+'];lm=frame.loc[frame.local=='L-']
    primary={}; sensitivities={}
    for metric in PRIMARY:
        primary[metric]=contrast(lp,metric,freeze)
        sensitivities[metric]={
            'first_event_per_family':contrast(lp.loc[lp[metric].notna()].sort_values('anchor_index').drop_duplicates('analysis_family_id'),metric,freeze),
            'normal_completion':contrast(lp.loc[lp.completion=='normal completed'],metric,freeze)}
        print('primary',metric,primary[metric]['status'],flush=True)
    for metric in ['reretrieval64','reretrieval256','delta_tortuosity128','delta_tortuosity512','delta_movement256','retrieval_use_latency','reretrieval128_start_anchor','delta_tortuosity256_start_anchor']:
        sensitivities[metric]=contrast(lp,metric,freeze)
    threshold=freeze['low_displacement_threshold']['256']
    sensitivities['delta_tortuosity256_low_displacement_excluded']=contrast(lp.loc[(lp.pre_displacement256>=threshold)&(lp.post_displacement256>=threshold)],'delta_tortuosity256',freeze)
    exploratory={metric:contrast(frame.loc[frame.local.isin(['L+','L-'])],metric,freeze,group='local',labels=('L+','L-')) for metric in ['reretrieval128','pre_tortuosity256','post_tortuosity256','delta_tortuosity256','retrieval_use_latency']}
    save(ROOT/'audit/statistical_results.json',dict(primary=primary,sensitivities=sensitivities,exploratory_local=exploratory))
    flattened=[]
    for metric,result in primary.items():
        for mode in ['raw','adjusted']:
            entry=result.get(mode) or {}
            ci=entry.get('ci95') or [None,None];mc=entry.get('ci9875') or [None,None]
            flattened.append(dict(metric=metric,mode=mode,events=result['events'],families=result['families'],
                correct_events=result['group_events'].get('correct',0),wrong_events=result['group_events'].get('wrong',0),
                estimate=entry.get('estimate'),ci95_low=ci[0],ci95_high=ci[1],ci9875_low=mc[0],ci9875_high=mc[1],
                valid_bootstrap=entry.get('valid_bootstrap',0),status=result['status']))
    p=ROOT/(PREFIX+'primary_effects.csv');assert not p.exists();pd.DataFrame(flattened).to_csv(p,index=False)
    output('retrieval_after_read',dict(records=[dict(event_id=r['event_id'],**r['retrieval']) for r in passive],primary=primary['reretrieval128'],local_exploratory=exploratory['reretrieval128'],secondary={k:v for k,v in sensitivities.items() if k.startswith('reretrieval')},source_alignment=source_alignment,
        caution='An episode already active at t0 is not new retrieval; source engagement is semantic and detector alignment does not certify causal grounding.'))
    known=lm.loc[lm.recovery.notna()].sort_values('anchor_index').drop_duplicates('analysis_family_id')
    positives=int(known.recovery.sum());n=len(known)
    interval=binomtest(positives,n).proportion_ci(method='exact') if n else None
    output('recovery_Lminus',dict(events=len(lm),families=lm.analysis_family_id.nunique(),known_first_eligible_family_events=n,
        observed_corrected=int(lm.recovery.eq(1).sum()),known_uncorrected=int(lm.recovery.eq(0).sum()),unknown=int(lm.recovery.isna().sum()),
        exact_interval_complete_cases=[interval.low,interval.high] if interval else None,
        interpretation='Descriptive conditional-on-review interval; strong ascertainment and missingness prevent population recovery inference. Latencies are witness upper bounds. No final-correctness proxy for recovery.',
        records=lm.to_dict('records'),missing_bounds=missing_bounds(lm,'recovery')))
    output('mutation_Lplus',dict(primary=primary['mutation'],sensitivities=sensitivities['mutation'],
        observed_mutations=int(lp.mutation.eq(1).sum()),verified_no_mutation=int(lp.mutation.eq(0).sum()),unknown=int(lp.mutation.isna().sum()),
        missing_bounds=missing_bounds(lp,'mutation'),cases=lp.loc[lp.mutation.eq(1)].to_dict('records'),
        caution='Partial-reference positives and full-remainder negatives have unequal ascertainment; complete-case rates are not cohort incidence. Witness time is not necessarily first mutation.'))
    output('refresh_compliance',dict(primary=primary['refresh_compliance128'],sensitivities=sensitivities['refresh_compliance128'],
        opportunities=opportunities,missing_bounds=missing_bounds(lp,'refresh_compliance128'),
        threshold_counts={str(g):sum(o['gap']>=g for o in opportunities) for g in [64,128,256]},
        caution='Only certified adjacent reuse opportunities enter; absent complete inventories remain unknown. Insufficient coverage for a refresh/staleness mechanism comparison.'))
    output('retrieval_use_latency',dict(records=frame[['event_id','local','benchmark_label','t0','tR','retrieval_use_latency']].to_dict('records'),
        negative_count=int(frame.retrieval_use_latency.lt(0).sum()),outcome_contrast=sensitivities['retrieval_use_latency'],local_exploratory=exploratory['retrieval_use_latency'],
        caution='Negative latencies retained; detector onset can follow the annotated read. Secondary timing association.'))
    output('pre_post_wandering',dict(primary=primary['delta_tortuosity256'],sensitivities={k:v for k,v in sensitivities.items() if 'tortuosity' in k or 'movement' in k},
        exposure={str(w):dict(all=int(frame[f'delta_tortuosity{w}'].notna().sum()),Lplus=int(lp[f'delta_tortuosity{w}'].notna().sum()),Lminus=int(lm[f'delta_tortuosity{w}'].notna().sum())) for w in [128,256,512]},
        local_exploratory={k:v for k,v in exploratory.items() if 'tortuosity' in k},nuisance_freeze=freeze,
        caution='Four standardized retrieval features, not hidden-state vSTREAM. Early anchors limit symmetric windows; temporal associations do not establish precursor or consequence.'))
    output('source_switching',dict(status='continuous post-read source switches and entropy not identifiable',semantic_refresh_alignment=source_alignment,
        original_source_anchor_counts=frame.groupby('item_id').size().value_counts().to_dict(),
        replay_decision='No new replay: original Block2/3A source replays measure isolated prefixes, not a continuous post-read source inventory; bounded replay would not repair primary lineage coverage.',
        unknown_switch_event_count=len(frame),target_confuser_transitions=None,source_entropy=None))
    wrong=lp.loc[lp.benchmark_label=='wrong']
    output('downstream_failure_taxonomy',dict(events=len(wrong),families=wrong.analysis_family_id.nunique(),
        counts={key:int(wrong.downstream.eq(key).sum()) for key in ['D1','D2','D3','D4','D5','DU']},
        observed_mutation_witnesses_in_final_wrong=wrong.loc[wrong.mutation.eq(1),'event_id'].tolist(),
        caution='A later mutation witness does not establish the first downstream failure. DU includes incomplete coverage and different-fact errors, not absence of downstream failure.'))
    save(ROOT/'audit/analysis_complete.json',dict(at=datetime.now(timezone.utc).isoformat(),seconds=time.monotonic()-started,
        slurm_job_id=os.environ.get('SLURM_JOB_ID'),gpu_count=0,anchors=len(frame),families=frame.analysis_family_id.nunique(),
        code_sha256={p:digest(p) for p in [__file__,'code/visual_reasoning/stage8b/block3b.py','code/visual_reasoning/stage8b/block3b_stats.py']},
        semantic_seal_sha256=digest(ROOT/'annotations/semantic_seal.json'),all_upstream_data_preserved=True))
    print('analysis_complete',flush=True)


if __name__=='__main__':
    main()
