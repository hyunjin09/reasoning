"""Freeze the user amendment using only pre-intervention metadata/annotations.

This module does not open any masked generation or receipt. Reuse/resource
accounting is a separate pass after this immutable selection is written.
"""
import json
from collections import Counter,defaultdict
from pathlib import Path
from scripts.stage8c.prepare import save,sha
from scripts.stage9a.run_native import now
from visual_reasoning.stage9a_dynamics.amendment import SEED,CUTOFFS,rank,stratified_select,choose_demand,matched_control
import hashlib

OLD=Path('outputs/stage9a_dynamics/v1')
BASE=Path('outputs/stage9a/v1')
ROOT=Path('outputs/stage9a_dynamics/amendment_v1')


def merged(intervals):
    result=[]
    for lo,hi in sorted(intervals):
        if result and result[-1][1]==lo:result[-1][1]=hi
        else:result.append([lo,hi])
    return result


def classify(rows,tasks):
    seen=set()
    for r in rows:
        n=tasks[r['task_id']]['native_tokens']
        effective=[(max(1,lo),hi) for lo,hi in r['intervals'] if max(1,lo)<n and (hi is None or hi>max(1,lo))]
        if not r.get('eligible',True):r.update(execution='missing_window',result_key=None)
        elif not effective:r.update(execution='identity_native',result_key=None)
        else:
            key=hashlib.sha256(json.dumps([r['task_id'],r['mode'],effective]).encode()).hexdigest()[:24]
            r.update(result_key=key,execution='alias' if key in seen else 'run');seen.add(key)


def distribution(rows):
    return {k:dict(sorted(Counter(str(r[k]) for r in rows).items())) for k in ['subject','difficulty','answer_format']}


def main():
    assert not (ROOT/'stage9a_amended_family_selection.json').exists()
    raw=json.loads((BASE/'stage9a_cohort_manifest.json').read_text())['rows']
    metadata=[dict(family_id=r['family_id'],item_id=r['item_id'],subject=r['subject'],difficulty=r['level'],answer_format=r['answer_format']) for r in raw]
    del raw
    assert len(metadata)==len({r['family_id'] for r in metadata})==128
    main=stratified_select(metadata,64);main_ids={r['family_id'] for r in main}
    reserve=[r for r in metadata if r['family_id'] not in main_ids]
    extension=stratified_select(reserve,32);extension_ids={r['family_id'] for r in extension}
    final=sorted([r for r in reserve if r['family_id'] not in extension_ids],key=lambda r:rank(r['family_id']))
    selection=dict(at=now(),frozen=True,seed=SEED,rule='Hamilton largest-remainder quotas recursively by subject, difficulty(level), answer format; SHA256 seed-prefixed ties and within-cell family order. Apply the identical rule to the complementary64 to freeze a possible32-family extension.',
        scientific_outcomes_accessed=False,metadata_columns=['family_id','item_id','subject','difficulty','answer_format'],
        main=main,reserve=extension+final,extension32=extension,final32=final,
        distribution=dict(full=distribution(metadata),main=distribution(main),reserve=distribution(reserve)),
        source_sha256={str(BASE/'stage9a_cohort_manifest.json'):sha(BASE/'stage9a_cohort_manifest.json')})
    save(ROOT/'stage9a_amended_family_selection.json',selection)
    old_tasks=json.loads((OLD/'audit/tasks.json').read_text())['rows'];tasks={r['task_id']:r for r in old_tasks if r['family_id'] in main_ids}
    old=json.loads((OLD/'audit/interventions.json').read_text());by_task=defaultdict(list)
    for r in old['rows']:by_task[r['task_id']].append(r)
    selected_events=[];main_rows=[]
    for task,row in tasks.items():
        prior={r['condition_id']:r for r in by_task[task]}
        def add(name,assay,intervals,**meta):
            main_rows.append(dict(task_id=task,condition_id=name,assay=assay,mode='standard',intervals=intervals,**meta))
        for cutoff in CUTOFFS:
            key='cutoff_'+str(cutoff if cutoff is not None else 'full')
            add(key,'cumulative',prior[key]['intervals'],cutoff=cutoff)
        for k in range(5):
            intervals=merged(prior[f'local_{2*k}']['intervals']+prior[f'local_{2*k+1}']['intervals'])
            add(f'local20_{k}','local',intervals,window=k,normalized_window=[k/5,(k+1)/5],native_exposure=sum(hi-lo for lo,hi in intervals))
        accepted=[r for r in by_task[task] if r['assay']=='demand' and r['role']=='demand' and r['radius']==16]
        candidates=[dict(r,valid_full_radius16=r['intervals']==[[r['demand_token']-16,r['demand_token']+17]]) for r in accepted]
        selected=choose_demand(candidates)
        if selected is None:
            selected_events.append(dict(task_id=task,event_id=None,reason='No accepted demand with full valid radius16 window.'));continue
        d=selected['demand_token'];eid=selected['event_id'];span=row['reasoning_span']
        old_control=prior[f'{eid}_r16_control']['intervals']
        control,rule=matched_control(d,span['start'],span['end'],[r['demand_token'] for r in accepted],old_control[0] if old_control else None)
        selected_events.append(dict(task_id=task,event_id=eid,demand_token=d,normalized_position=selected['normalized_position'],
            rule='Earliest fully eligible accepted event after25% if any, otherwise earliest fully eligible accepted event.',control_rule=rule,
            control_interval=control,paired=control is not None))
        for role,interval in [('demand',(d-16,d+17)),('control',control)]:
            add(f'{eid}_r16_{role}','demand',[] if interval is None else [list(interval)],
                event_id=eid,radius=16,role=role,demand_token=d,normalized_position=selected['normalized_position'],
                paired=control is not None,eligible=interval is not None,
                control_label='shifted_time_without_annotated_demand',control_rule=rule)
    classify(main_rows,tasks)
    sink_families=sorted(main_ids,key=lambda f:rank('sink:'+f))[:8]
    controls=[]
    for row in main_rows:
        if tasks[row['task_id']]['family_id'] not in sink_families:continue
        if row['condition_id'] in ['local20_0','local20_4','cutoff_128'] or (row['assay']=='demand' and row['role']=='demand' and row['paired']):
            controls.append(dict(row,condition_id='sink_'+row['condition_id'],assay='redistribution',mode='null_sink',standard_condition=row['condition_id']))
    classify(controls,tasks)
    all_unique=sum(r['execution']=='run' for r in main_rows+controls);assert all_unique<=3000
    inventory=dict(at=now(),frozen=True,scientific_outcomes_accessed=False,rows=main_rows,
        deferred_control_rows=controls,control_gate='Only after main64 results exist; no automatic control launch.',
        sink_families=sink_families,selected_demand_events=selected_events,
        main_counts=dict(Counter(r['execution'] for r in main_rows)),control_counts=dict(Counter(r['execution'] for r in controls)),
        main_assays=dict(Counter(r['assay'] for r in main_rows)),distinct_continuations_main_plus_deferred_controls=all_unique,
        extension_gate='No automatic reserve execution. At most frozen next32 after P2/P3 positive direction, uncertainty/underpower, subject robustness, valid controls and precision-limited assessment. Final32 requires new user authorization.',
        primary_inference=dict(groups=['P1: Thinking-CoT cumulative damage at512 and2048','P2: Thinking-CoT average local damage in [.6,.8] and [.8,1]','P3: Thinking-CoT demand-minus-control damage'],
            elementary_components=4,confidence_unadjusted=.95,simultaneous_confidence=1-.05/4,multiplicity='Bonferroni over the two specified P1 components and single P2/P3 components, within three scientific groups; other windows descriptive.',
            bootstrap_draws=4000,seed=920260924,min_paired_families=20,min_valid_fraction=.95,unit='conservative visual family; equal weights'))
    save(ROOT/'stage9a_amended_condition_manifest.json',inventory)
    save(ROOT/'audit/interventions.json',inventory)
    save(ROOT/'audit/tasks.json',dict(rows=list(tasks.values())))
    save(ROOT/'audit/freeze_receipt.json',dict(at=now(),no_masked_output_or_receipt_opened_by_this_builder=True,
        family_selection_sha256=sha(ROOT/'stage9a_amended_family_selection.json'),manifest_sha256=sha(ROOT/'stage9a_amended_condition_manifest.json'),
        source_sha256={str(p):sha(p) for p in [Path(__file__),Path('code/visual_reasoning/stage9a_dynamics/amendment.py'),OLD/'audit/tasks.json',OLD/'audit/interventions.json']}))
    print(json.dumps(dict(main=inventory['main_counts'],controls=inventory['control_counts'],main_assays=inventory['main_assays'],unique_main_plus_controls=all_unique,selected_demand_events=sum(e['event_id'] is not None for e in selected_events),distributions=selection['distribution']),indent=2))


if __name__=='__main__':main()
