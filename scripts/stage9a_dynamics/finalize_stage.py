"""Verify completed control evidence, release unused reservations, close Stage9A."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from scripts.stage9a_dynamics.prepare_answers import MAIN, save, sha
from scripts.stage9a_dynamics.analyze_main import load
from scripts.stage9a_dynamics.finish_report import main as report, REQUIRED


def main():
    root=MAIN/'controls_v1';comparison=load(MAIN/'stage9a_attention_redistribution_control.json')
    assert comparison['complete'] and comparison['n_continuations']==87
    manifest=load(root/'audit/interventions.json')['rows']
    assert manifest==load(MAIN/'audit/interventions.json')['deferred_control_rows']
    expected={r['result_key'] for r in manifest}
    actual={p.parent.name for p in (root/'rollouts/results').glob('*/result.json')}
    assert actual==expected and len(actual)==87
    assert sha(root/'annotations/answer_extraction_review_frozen.json')==comparison['review_sha256']
    receipts={}
    for key in sorted(expected):
        path=root/'rollouts/results'/key/'result.json';r=load(path)
        assert r['generation_sha256']==sha(path.parent/'generation.json')
        assert r['prefix_identity_verified'] and r['config_sha256']==sha(root/'config.json')
        assert r['representative_condition']['mode']=='null_sink'
        receipts[key]=sha(path)
    tasks=load(root/'audit/tasks.json')['rows']
    assert len(tasks)==24
    for task in tasks:
        r=load(root/'rollouts/tasks'/task['task_id']/'complete.json')
        assert all(receipts[k]==v for k,v in r['result_sha256'].items())
    assert not list((root/'rollouts/workers').glob('*/failure.json'))
    cfg=load(root/'config.json')
    assert all(sha(p)==v for p,v in cfg['source_sha256'].items())
    # Cancel only this control queue's remaining pending reservations, after all work is durable.
    jobs=[j for j in load(Path('state/gpu_experiment_queue.json'))['jobs'] if j['id'].startswith('stage9a_controls_v1_worker')]
    owned={str(j['slurm_job_id']) for j in jobs}
    def live():
        output=subprocess.run(['squeue','--me','-h','-o','%i %T'],check=True,text=True,capture_output=True).stdout
        return {parts[0]:parts[1] for line in output.splitlines() if (parts:=line.split()) and parts[0] in owned}
    release_record=root/'audit/released_pending_reservations.json'
    current=live();cancelled=load(release_record)['slurm_job_ids'] if release_record.exists() else []
    for job,state in current.items():
        assert state=='PENDING',f'Wait for completed control worker to exit: {job} {state}'
        subprocess.run(['scancel',job],check=True);cancelled.append(job)
        release_record.write_text(json.dumps(dict(slurm_job_ids=cancelled,reason='All87 control receipts and24 task receipts verified complete'),indent=2)+'\n')
    current=live()
    assert not current,f'Wait for Slurm release: {current}'
    for j in jobs:
        job=str(j['slurm_job_id']);done=root/'rollouts/workers'/('slurm_'+job)/'completed.json'
        state='cancelled' if job in cancelled else 'succeeded'
        if state=='succeeded':assert done.exists(),job
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','update','--project','.',
                        '--id',j['id'],'--status',state,'--note',
                        'All87 frozen controls durable; worker completed or unused pending reservation released.'],check=True)
    report()
    assert all((MAIN/name).exists() for name in REQUIRED)
    now=datetime.now(timezone.utc).isoformat()
    result=dict(at=now,pass_all=True,main_postprocess_sha256=sha(MAIN/'audit/main_postprocess_validation.json'),
        control_results=87,control_tasks=24,control_receipt_sha256=receipts,control_review_sha256=comparison['review_sha256'],
        required_artifacts=12,figure_files=10,active_control_jobs=0,cancelled_unused_pending=cancelled,
        all_primary_contrasts_unsupported=True,reserve_families_used=0,query_text_triggered=False,next_experiment_launched=False,
        recommendation=load(MAIN/'audit/gates.json')['recommendation'],
        files_sha256={name:sha(MAIN/name) for name in REQUIRED})
    save(MAIN/'audit/final_validation.json',result)
    message=('Stage9A causal visual-access dynamics COMPLETE / STOP.1904 main continuations,87 null-sink controls,'
        '50 local readouts,sealed extraction reviews,12 artifacts and five PNG/PDF figures verified. '
        'No primary Thinking-over-CoT late necessity contrast is supported; demand+10.71pp is uncertain and loses direction without algebra. '
        'No reserve/query-text/Stage9B run. Exactly one recommendation: close the Thinking-specific visual-access scheduling branch. '
        'All control allocations and unused reservations released.')
    for name in ('workflow_state.md','research_plan.md','env_state.md'):
        p=Path('workspace')/name
        p.write_text(f'**CURRENT — {now}.** {message} [Report](../outputs/stage9a_dynamics/amendment_v1/stage9a_summary.md).\n\nEarlier checkpoints below are historical.\n\n'+p.read_text())
    phase=Path('workspace/phase_memory/phase_9a_access_dynamics.md');text=phase.read_text()
    start=text.index('## Current State');end=text.index('\n## Evidence That Matters',start)
    text=text[:start]+'## Current State\n\n'+message+'\n\nEvidence: outputs/stage9a_dynamics/amendment_v1/audit/final_validation.json.\n'+text[end:]
    start=text.index('## Next-Step Decision');end=text.index('\n### Step Result',start)
    text=text[:start]+'## Next-Step Decision\n\nAuthorized action complete. STOP; await a separately authorized user action. No strategic pivot, reserve or Stage9B.\n'+text[end:]
    phase.write_text(text+'\n### Final closure — '+now+'\n\n'+message+'\n')
    p=Path('workspace/decision_log.md');p.write_text(p.read_text()+'\n\n## D-101 — Stage9A dynamics closed after bounded controls ('+now+')\n\n'+message+'\nEvidence: outputs/stage9a_dynamics/amendment_v1/stage9a_summary.md and audit/final_validation.json.\n')
    p=Path('reports/index.md');p.write_text(p.read_text()+'\n\n## Stage9A causal visual-access dynamics completed\n\n'+message+'\n[Report](../outputs/stage9a_dynamics/amendment_v1/stage9a_summary.md) · [Validation](../outputs/stage9a_dynamics/amendment_v1/audit/final_validation.json).\n')
    print(message)


if __name__=='__main__':main()
