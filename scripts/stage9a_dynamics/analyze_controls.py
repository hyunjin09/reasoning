"""Score the sealed87 frozen null-sink controls against the same main conditions."""
import os
from collections import defaultdict
from datetime import datetime, timezone
from scripts.stage9a_dynamics.prepare_answers import MAIN, save, sha
from scripts.stage9a_dynamics.analyze_main import load, score_panel
from visual_reasoning.stage9a.protocol import ARMS
from visual_reasoning.stage9a.statistics import mean_interval


def paired_control_rows(control_rows, main_rows):
    lookup={(r['task_id'],r['condition_id']):r for r in main_rows}
    rows=[]
    for r in control_rows:
        original=lookup[r['task_id'],r['standard_condition']]
        baseline=lookup[r['task_id'],'cutoff_full']
        assert r['intervals']==original['intervals']
        name=r['standard_condition']
        if original['assay']=='demand': name='demand'
        rows.append(dict(r, representative=name,
                         full_accuracy=baseline['accuracy_no_credit'],
                         standard_accuracy=original['accuracy_no_credit'],
                         standard_damage=baseline['accuracy_no_credit']-original['accuracy_no_credit'],
                         null_sink_damage=baseline['accuracy_no_credit']-r['accuracy_no_credit'],
                         null_minus_standard_damage=original['accuracy_no_credit']-r['accuracy_no_credit'],
                         standard_label=original['benchmark_label'],
                         standard_raw_damage=baseline['accuracy_raw']-original['accuracy_raw'],
                         null_raw_damage=baseline['accuracy_raw']-r['accuracy_raw']))
    return rows


def main():
    assert os.environ.get('SLURM_JOB_ID')
    root=MAIN/'controls_v1'
    control,scores,tasks,review=score_panel(root)
    assert len(control)==len(scores)==87 and len(tasks)==24
    rows=paired_control_rows(control,load(MAIN/'audit/scored_conditions.json')['rows'])
    summaries=[]
    for name in ('cutoff_128','local20_0','local20_4','demand'):
        for arm in ARMS:
            rr=[r for r in rows if r['representative']==name and r['arm']==arm]
            assert len(rr)==len({r['family_id'] for r in rr})
            summaries.append(dict(condition=name,arm=arm,n_families=len(rr),
                **{key:mean_interval([r[key] for r in rr]) for key in
                   ('standard_damage','null_sink_damage','null_minus_standard_damage','standard_raw_damage','null_raw_damage')},
                identical_credit=sum(r['standard_accuracy']==r['accuracy_no_credit'] for r in rr),
                identical_label=sum(r['standard_label']==r['benchmark_label'] for r in rr)))
    cross=[]
    for name in ('cutoff_128','local20_0','local20_4','demand'):
        by=defaultdict(dict)
        for r in rows:
            if r['representative']==name: by[r['family_id']][r['arm']]=r
        pairs=[arms for arms in by.values() if 'thinking' in arms and 'instruct_cot' in arms]
        cross.append(dict(condition=name,n_paired_families=len(pairs),
            standard_thinking_minus_cot=mean_interval([a['thinking']['standard_damage']-a['instruct_cot']['standard_damage'] for a in pairs]),
            null_sink_thinking_minus_cot=mean_interval([a['thinking']['null_sink_damage']-a['instruct_cot']['null_sink_damage'] for a in pairs])))
    save(root/'audit/scored_answers.json',dict(rows=scores,review_sha256=sha(root/'annotations/answer_extraction_review_frozen.json')))
    save(root/'audit/scored_conditions.json',dict(rows=control))
    result=dict(at=datetime.now(timezone.utc).isoformat(),complete=True,rows=rows,summaries=summaries,cross_arm=cross,
        n_continuations=87,n_families=8,selection='Exact original deferred control inventory; frozen before main outcomes',
        independent_unit='family',inference='Descriptive only:8 families below the predeclared20-family interval threshold',
        scope='cutoff128,first20%,last20%,selected demand. Last20% is not the P2 final40% aggregate; no matched non-demand null-sink was prescribed.',
        interpretation='This bounded set diagnoses gross redistribution sensitivity. It cannot certify population robustness or rescue an unsupported primary effect.',
        review_sha256=sha(root/'annotations/answer_extraction_review_frozen.json'),
        control_manifest_sha256=sha(root/'audit/interventions.json'),slurm_job_id=os.environ['SLURM_JOB_ID'])
    save(MAIN/'stage9a_attention_redistribution_control.json',result)
    print('87 frozen null-sink controls scored and exported')


if __name__=='__main__': main()
