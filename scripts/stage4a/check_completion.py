"""Check plan deliverables, report links and the final stopped state."""
import ast
import re
import json
from scripts.stage4a.prepare_config import ROOT,OUT,read_json,write_json,sha


def main():
    plan=(ROOT/'plan/stage4a_multi_evidence_switch_refresh_plan.md').read_text()
    block=plan.split('# 48. Output Structure',1)[1].split('```text',1)[1].split('```',1)[0]
    stack=[];required=[]
    for line in block.splitlines():
        if not line.strip():continue
        depth=(len(line)-len(line.lstrip()))//2;name=line.strip()
        if depth==0:continue
        stack=stack[:depth-1]
        if name.endswith('/'):stack.append(name.rstrip('/'))
        else:required.append(OUT.joinpath(*stack,name))
    missing=[str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    assert not missing,missing
    for p in required:
        if p.suffix=='.json':read_json(p)
        if p.suffix=='.jsonl':
            for line in p.read_text().splitlines():json.loads(line)
    links=[]
    for p in [OUT/'summaries/stage4a_summary.md',OUT/'summaries/next_stage_recommendation.md',OUT/'analysis/figures/README.md']:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if not target.startswith(('http','#')):
                path=p.parent/target.split('#')[0];assert path.exists(),(p,target);links.append(str(path))
    code=list((ROOT/'scripts/stage4a').glob('*.py'))+list((ROOT/'code/visual_reasoning/stage4a').glob('*.py'))
    for p in code:ast.parse(p.read_text())
    acceptance=read_json(OUT/'summaries/stage4a_acceptance.json')
    assert acceptance['passed'] and len(acceptance['criteria'])==20
    for row in acceptance['criteria']:assert (ROOT/row['evidence']).exists(),row
    assert not list((OUT/'raw').rglob('*.part'))
    secondary=read_json(OUT/'analysis/secondary_evidence_freeze.json')
    assert all(sha(ROOT/p)==h for p,h in secondary['analysis_code_sha256'].items())
    assert '11 passed' in (ROOT/'runs/stage4a_final_tests_02.log').read_text()
    assert 'Active phase: none; stopped after Stage4A' in (ROOT/'workspace/workflow_state.md').read_text()
    report=' '.join((OUT/'summaries/stage4a_summary.md').read_text().split())
    assert 'zero strict A-dominant' in report and 'frozen irrelevant-control subset is40' in report
    jobs=[r for r in read_json(ROOT/'state/gpu_experiment_queue.json')['jobs'] if r['id'].startswith('stage4a_')]
    assert len(jobs)==5 and all(r['status']=='succeeded' for r in jobs)
    result={'passed':True,'required_plan_files':len(required),'markdown_links_checked':len(links),
        'acceptance_criteria':20,'all_required_json_parsed':True,'all_stage4a_python_parsed':True,
        'no_partial_score_files':True,'analysis_code_matches_evidence_freeze':True,'state_stopped':True,
        'all_five_stage4a_scheduler_records_succeeded':True,
        'report_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (OUT/'summaries').glob('*')},
        'final_code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in code}}
    write_json(OUT/'audit/completion_check.json',result)
    print({k:v for k,v in result.items() if not k.endswith('sha256')})


if __name__=='__main__':main()
