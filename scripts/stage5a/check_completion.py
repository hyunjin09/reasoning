"""Verify every plan deliverable, final report link and completed job record."""
import ast,re
from pathlib import Path
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,sha


def main():
    plan=(ROOT/'plan/stage5a_failure_attention_state_taxonomy_plan.md').read_text()
    section=plan.split('# 60.',1)[1].split('# 61.',1)[0];block=section.split('```',2)[1].splitlines()
    directory='';expected=[]
    for line in block:
        token=line.strip()
        if not token or token in ('text','outputs/stage5a/'):continue
        indent=len(line)-len(line.lstrip())
        if token.endswith('/'):
            if indent==2:directory=token.rstrip('/')
            continue
        if indent==4 and token.endswith(('.json','.jsonl','.md')):expected.append(OUT/directory/token)
    assert len(expected)>=60,len(expected)
    missing=[str(p.relative_to(ROOT)) for p in expected if not p.is_file()];assert not missing,missing
    for p in expected:
        if p.suffix=='.json':read_json(p)
        elif p.suffix=='.jsonl':read_jsonl(p)
    for p in [*(ROOT/'scripts/stage5a').glob('*.py'),*(ROOT/'code/visual_reasoning/stage5a').glob('*.py')]:ast.parse(p.read_text())
    acceptance=read_json(OUT/'summaries/stage5a_acceptance.json');assert acceptance['status']=='PASS' and acceptance['passed']==20
    assert read_json(OUT/'analysis/next_intervention_target.json')['recommendation_count']==1
    for filename in ('stage5a_summary.md','next_stage_recommendation.md'):
        p=OUT/'summaries'/filename
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            assert not link.startswith(('http:','https:'))
            assert (p.parent/link).resolve().is_file(),link
    figures=read_json(OUT/'analysis/figures/index.json')['figures'];assert len(figures)==20
    figure_paths=[ROOT/r[k] for r in figures for k in ('png','pdf')]
    assert all(p.is_file() and p.stat().st_size>1000 for p in figure_paths)
    jobs=[r for r in read_json(ROOT/'state/gpu_experiment_queue.json')['jobs'] if r['id'].startswith('stage5a_')]
    assert len(jobs)==5 and all(r['status']=='succeeded' and r['slurm_job_id']=='108548' and r['gpus']==4 for r in jobs)
    assert {p.name for p in (OUT/'raw').iterdir()}=={'validation_01','causal_01','semantic_01','passive_01'}
    assert '31 passed' in (ROOT/'runs/stage5a_all_tests.log').read_text()
    source=[*(ROOT/'scripts/stage5a').glob('*.py'),*(ROOT/'code/visual_reasoning/stage5a').glob('*.py')]
    write_json(OUT/'audit/code_review.json',{'reviewer':'main agent','independent_subagent':False,'scope':'Stage5A implementation and final outputs',
        'checks':['immutable cohort and A–D gates','native token/readout orientation','ROI aliases and overlaps','current/prior replay identity',
                  'within-base aggregation and template folds','missing data and low-yield gates','Holm family separation','no unsupported rescue interpretation'],
        'resolved_findings':['large signed effects are not null','integration error must follow event','overlapping M excluded from strict source contrast',
                             'completed native shard is a valid stop','H-MR margin label is not error-token promotion'],
        'tests_passed':31,'remaining_scientific_limits':'Recorded in summaries/stage5a_acceptance.json; no technical blocker',
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in source}})
    result={'passed':True,'required_deliverable_files':len(expected),'figure_files':len(figure_paths),'completed_gpu_task_records':len(jobs),
        'technical_acceptance':'20/20','tests_passed':31,'all_report_links_resolve':True,'visual_review':'All20-panel contact sheet plus selected standalone figures inspected by main agent',
        'no_followon_experiment_started':True,'sha256':{str(p.relative_to(ROOT)):sha(p) for p in [*expected,*figure_paths]}}
    write_json(OUT/'audit/completion_check.json',result)
    print({k:v for k,v in result.items() if k!='sha256'})


if __name__=='__main__':main()
