"""Reconcile this stage's records and compact research state after verification."""
import subprocess
from infra.harness_state import mutate_run_state,append_run_history
from scripts.stage13d.common import *
def main():
    final=load(ROOT/'audit/final_verification.json');ledger=load(ROOT/'stage13d_resource_accounting.json');decision=load(ROOT/'stage13d_decision.json');inf=load(ROOT/'stage13d_primary_inference.json')
    assert final['all_gpus_released'] and not ledger['active_jobs']
    index=Path('reports/index.md');original=index.read_text();updates=[]
    try:
        for r in ledger['jobs']:
            job=load(ROOT/'audit/launches'/f"{r['slurm_job_id']}.json")['jobs'][0];assert job['id'].startswith(PREFIX)
            status={'COMPLETED':'succeeded','CANCELLED':'cancelled','FAILED':'failed','TIMEOUT':'failed'}[r['state']]
            note='Stage13D complete: '+decision['decision']+'. '+r['state']+'.'
            p=subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','update','--project','.', '--id',job['id'],'--status',status,'--note',note],capture_output=True,text=True,check=True)
            def close(data):
                data.update(status=status,current_step=note,display_summary=note,finished_at=now());append_run_history(data,'stage13d_close',note)
            mutate_run_state(Path.cwd(),job['exp_id'],close);updates.append(dict(id=job['id'],slurm_job_id=r['slurm_job_id'],status=status,stdout=p.stdout))
    finally:index.write_text(f"[Stage13D — {decision['decision']}](stage13d/v1/index.md)\n\n"+original)
    at=now();s=inf['semantic'];b=inf['buffer'];d=s['contrasts']['dummy']
    head=f"**CURRENT — {at}: Stage13D COMPLETE / STOP — {decision['decision']}.** Safe semantic23, complete{s['n_complete']}; derived−dummy={d['mean']},95%CI{d['ci']}. Immediate-buffer n={b['n']},meanmarginΔ={b['mean']},95%CI{b['ci']}. All GPUs released,{ledger['allocated_gpu_hours_upper']:.6f}GPUh;{final['prior_files']}historical files unchanged. Exactly one recommendation,notlaunched. [Report](../reports/stage13d/v1/index.md) · [Phase](phase_memory/phase_13d_derived_state_immediate_buffer.md).\n\nOlder entries below are historical.\n\n"
    for name in ['workflow_state.md','research_plan.md']:
        p=Path('workspace')/name;p.write_text(head+p.read_text())
    with Path('workspace/decision_log.md').open('a') as f:f.write(f"\n\n## D163 — {at}: Stage13D bounded mechanism study complete\n{decision['decision']}. Semantic23eligible/{s['n_complete']}complete families, five fresh seeds per arm; derived−dummy={d['mean']},95%CI{d['ci']}; source errors and missingness explicit. Buffer{b['n']}MCpairs,meanmarginΔ={b['mean']},95%CI{b['ci']},positivefraction={b['positive_fraction']}. No free tokens after close; all12technical checks pass and four short repeats match exactly. Stage13Aunchanged; not a hybrid ThinkingON/OFF decomposition. Exactly one recommendation: {decision['recommendation']} NOT_LAUNCHED. Evidence:outputs/stage13d/v1/stage13d_summary.md and audit/final_verification.json. All GPUsreleased,{ledger['allocated_gpu_hours_upper']:.6f}GPUh.\n")
    p=Path('workspace/env_state.md');p.write_text(f"## Stage13D closure — {at}\nAll{len(ledger['jobs'])}stage Slurm allocations released;{ledger['allocated_gpu_hours_upper']:.6f}GPUh. Existing BF16/vLLM/project-local environments and pinned4B models unchanged. No downloads, installs, tmux or keepalive.\n\n"+p.read_text())
    Path('workspace/phase_memory/phase_13d_derived_state_immediate_buffer.md').write_text(f"""# Phase13D: derived-state priming and immediate buffer

## Current Objective

Complete; {decision['decision']}. Authorized stage stopped after one recommendation.

## Active Constraints

All original24/technical4, source traces,23safe deductions/controls/seeds, model
recipes and outputs remain sealed. No follow-on or interpretation beyond the plan.

## Current State

- Done: source QC;460scheduled semantic calls subject to initial8 gate; technical
  buffer12;11MC short/long pairs; scoring/QC, inference,20artifacts/five figure pairs,
  full raw-response pages, historical/resource verification.
- Complete semantic families:{s['n_complete']}; safe families:23; one no-safe936.
- Result: derived−dummy={d['mean']},95%CI{d['ci']}; buffer marginΔ={b['mean']},95%CI{b['ci']}.
- GPUs: all released;{ledger['allocated_gpu_hours_upper']:.6f}allocatedGPUh.

## Evidence That Matters

- `outputs/stage13d/v1/stage13d_primary_inference.json`: frozen family effects/gates.
- `stage13d_buffer_technical_validation.json`: zero free tokens and exact repeatability.
- `stage13d_derived_state_audit.json`: pre-outcome leakage/source correctness labels.
- `audit/final_verification.json`:{final['prior_files']}prior files unchanged.

## Failed Attempts and Lessons

Stage13C free-reasoning reopening was avoided through immediate raw option scoring.
Portability in Instruct and within-Thinking forced computation remain distinct from
the deployed-variant comparison. Same-agent QC is not independent reliability.

## Open Candidates

No automatically authorized further research action.

## Next-Step Decision

- Chosen action: STOP; the approved bounded study is complete.
- Exactly one recommendation: {decision['recommendation']}
- Follow-on: NOT_LAUNCHED; requires a new instruction.

### Step Result

All required artifacts and figures saved, original seals/history preserved,
resource records reconciled. See Stage13D summary for technical missingness,
effect sizes, uncertainty and interpretation limits.
""")
    p=Path('plan/stage13d_execution_checklist.md');s=p.read_text().replace('- [ ]','- [x]');p.write_text(s+f'\nCompleted {at}. {decision["decision"]}; all required artifacts/figures and resources verified; exactly one recommendation, no follow-on.\n')
    save(ROOT/'audit/publication_receipt.json',dict(at=at,queue_updates=updates,report_files={str(p):sha(p) for p in Path('reports/stage13d/v1').rglob('*') if p.is_file()},follow_on_launched=False))
    print('PUBLISHED',decision['decision'],len(updates),'jobs closed')
if __name__=='__main__':main()
