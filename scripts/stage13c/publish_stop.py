"""Close only Stage13C's queue entries and publish the preserved technical evidence."""
import os,subprocess
from pathlib import Path
from infra.harness_state import mutate_run_state,append_run_history
from scripts.stage13c.common import *

def main():
    final=load(ROOT/'audit/final_verification.json');ledger=load(ROOT/'stage13c_resource_accounting.json')
    assert final['all_gpus_released'] and not ledger['active_jobs']
    report=Path('reports/stage13c/v1');index=Path('reports/index.md');original=index.read_text();updates=[]
    try:
        for r in ledger['jobs']:
            job=load(ROOT/'audit/launches'/f"{r['slurm_job_id']}.json")['jobs'][0]
            assert job['id'].startswith(PREFIX) and r['state'] in ['COMPLETED','CANCELLED','FAILED']
            status={'COMPLETED':'succeeded','CANCELLED':'cancelled','FAILED':'failed'}[r['state']]
            note='Stage13C closed at forced-trace contract gate; no scientific generation. '+r['state']+'.'
            proc=subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','update','--project','.',
                '--id',job['id'],'--status',status,'--note',note],capture_output=True,text=True,check=True)
            def close(data):
                data.update(status=status,current_step=note,display_summary=note,finished_at=now())
                append_run_history(data,'stage13c_contract_stop',note)
            mutate_run_state(Path.cwd(),job['exp_id'],close)
            updates.append(dict(job=r['slurm_job_id'],id=job['id'],status=status,stdout=proc.stdout))
    finally:
        index.write_text('[Stage13C — forced-trace contract blocked; no scientific calls](stage13c/v1/index.md)\n\n'+original)
    os.environ['MPLCONFIGDIR']=str(Path('runs/stage13c/v1/cache/matplotlib').resolve())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows=[r for r in load(ROOT/'stage13c_forced_trace_technical_validation.json')['rows'] if r['complete']]
    fig,ax=plt.subplots(figsize=(10,4.8),constrained_layout=True)
    labels=[r['item_id']+' / '+r['condition'].replace('T_','') for r in rows]
    y=list(range(len(rows)));forced=[r['forced_reasoning_tokens']+1 for r in rows];free=[r['generated_tokens_after_forced_close'] for r in rows]
    ax.barh(y,forced,color='#396ca8',label='Prescribed reasoning + closing token')
    ax.barh(y,free,left=forced,color='#e49b65',label='Free continuation (includes final answer)')
    for i,r in enumerate(rows):
        if r['extra_native_close']:ax.plot(r['close_positions'][1]+1,i,'kx',ms=8,label='Second closing marker' if not any(x.get('extra_native_close') for x in rows[:i]) else None)
    ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlabel('Generated-token positions');ax.set_title('Stage13C technical check: free continuation persists after forced close')
    ax.legend(loc='lower right',fontsize=8);ax.spines[['top','right']].set_visible(False)
    figures=ROOT/'figures';figures.mkdir(exist_ok=True)
    for extension in ['png','pdf']:fig.savefig(figures/('stage13c_technical_forced_contract.'+extension),dpi=180)
    plt.close(fig)
    with (report/'index.md').open('a') as f:f.write('\n[Technical token diagnostic](../../../outputs/stage13c/v1/figures/stage13c_technical_forced_contract.png). This is a technical display, not one of the unexecuted scientific-effect figures.\n')
    at=now();summary=f'**CURRENT — {at}: Stage13C STOP / FORCED_TRACE_CONTRACT_BLOCKED.** Exact token forcing8/8; seven complete technical responses, one interrupted. Five completed responses emit a second native close after free deliberation; no scientific calls or mechanism estimates. All GPUs released after{ledger["allocated_gpu_hours_upper"]:.6f}GPUh;20,520historical files unchanged. [Report](../reports/stage13c/v1/index.md) · [Phase](phase_memory/phase_13c_buffer_vs_derived_state.md).\n\nOlder entries below are historical.\n\n'
    for name in ['workspace/workflow_state.md','workspace/research_plan.md']:
        p=Path(name);p.write_text(summary+p.read_text())
    with Path('workspace/decision_log.md').open('a') as f:
        f.write(f'\n\n## D161 — {at}: Native closing-token enforcement does not establish zero further reasoning\n\nStage13C technical check passes exact token-by-token dummy forcing and firstclose in8/8 receipts, yet5/7 complete outputs emit a second </think> after2,016–7,751free tokens; another shows explicit reconsideration. This violates the approved no-additional-free-reasoning contract. No scientific calls, correctness inference or prompt/grammar/cap tuning. The mechanism question is not evaluated, not null. Decision FORCED_TRACE_CONTRACT_BLOCKED; sole recommendation: retain Stage13A confirmed post-evidence advantage and do not expand the mechanism story. Original+repaired loader versions,28source traces/drafts and completed outputs preserved; all4jobs closed at{ledger["allocated_gpu_hours_upper"]:.6f}GPUh. Evidence: outputs/stage13c/v1/stage13c_forced_trace_technical_validation.json and stage13c_summary.md.\n')
    with Path('workspace/env_state.md').open('a') as f:f.write(f'\n\nStage13C closed {at}: Slurm134926/134927 failed at processor class-loader parsing before calls;134932cancelled after mandatory contract stop,134933completed. All allocations released;0scientific calls,8technical attempted/7complete/1interrupted. Exact allocated{ledger["allocated_gpu_hours_upper"]:.6f}GPUh. No installs/downloads or global environment changes.\n')
    phase=Path('workspace/phase_memory/phase_13c_buffer_vs_derived_state.md')
    phase.write_text('''# Phase13C: computational buffer versus derived-state priming

## Current Objective

Closed at the approved forced-trace technical stop. Scientific mechanism study not run.

## Active Constraints

Preserve source-only24, disjointtechnical4, frozen source traces, exact Q+E*, models,
recipes/caps and every completed output. No prompt/grammar/cap tuning, scientific
rerun or follow-on. Exactly one recommendation has been delivered, not launched.

## Current State

- Done: selection/source trace seals, real token-step forcing, technical review,
  all19 required artifacts with explicit not-run entries, raw-response report,
  technical figure, historical verification and resource closure.
- Blocked: FORCED_TRACE_CONTRACT_BLOCKED. Closing the native channel does not
  stop new free deliberation under the frozen normal answer-generation recipe.
- Not run: final sourceD audit/seal, remaining technical checks, all scientific
  conditions, correctness/QC, paired effects, bootstrap and scientific figures.

## Evidence That Matters

- `outputs/stage13c/v1/stage13c_forced_trace_technical_validation.json`: all8exact
  forced-token receipts pass;5of7complete responses emit another </think> after
  thousands of free tokens. A sixth visibly reconsiders its derivation. The
  remaining response is not certified by absence of a second marker alone.
- `outputs/stage13c/v1/audit/loader_repair_v1.json`: startup FQCN delimiter error
  reproduced with the actual vLLM loader; one-character repair passes regression.
  This earlier wiring issue is separate from the observed contract failure.
- `outputs/stage13c/v1/audit/final_verification.json`:20,520historical files intact;
  original and repaired generation-code seals both verified.
- `reports/stage13c/v1/responses.md`: all7complete technical continuations; the
  eighth retains input/forced receipt, but its interrupted free suffix was not flushed.

## Failed Attempts and Lessons

Observed: a native closing token plus banning reopening tokens does not enforce
absence of additional reasoning. Cause of model behavior unresolved. Do not mask
the second close and call that a repair: doing so would hide a witness without
controlling computation. Do not repeat the same experiment with an altered prompt
or answer grammar without authorization. No mechanism-null interpretation.

## Open Candidates

Both scientific hypotheses remain unevaluated by Stage13C. SourceD annotations
for28families are preserved as unsealed drafts, not final eligible interventions.

## Next-Step Decision

- Chosen action: mandatory STOP and closure; no further GPU work needed.
- Evidence: repeated extra native close and explicit free deliberation in the
  disjoint technical outputs, despite exact prescribed token-step receipts.
- Exactly one recommendation: Retain Stage13A's confirmed post-evidence advantage
  as the strongest claim and do not expand the mechanism story.
- Follow-on: NOT_LAUNCHED. Await a new user instruction.

### Step Result

Seven completed/eight attempted technical calls; zero scientific calls. All four
Slurm jobs released;0.307778allocatedGPUh. Runtime/source artifacts and required
not-run inference outputs are complete. Authorized stage terminated at its gate;
the scientific study itself is incomplete.
''')
    checklist=Path('plan/stage13c_execution_checklist.md')
    with checklist.open('a') as f:f.write('\n## Final disposition\n\nFORCED_TRACE_CONTRACT_BLOCKED. GPU validation failed the no-further-free-reasoning requirement. All unchecked scientific/semantic steps are NOT_RUN_AT_REQUIRED_STOP, not pending automatic execution. Required19artifacts, technical figure,20,520-file history check, queue/resource closure and exactly one recommendation are complete. No GPUs remain allocated.\n')
    save(ROOT/'audit/publication_receipt.json',dict(at=at,queue_updates=updates,
        report_files={str(p):sha(p) for p in report.rglob('*') if p.is_file()},
        figures={str(p):sha(p) for p in figures.iterdir()},follow_on_launched=False))
    print('PUBLISHED',len(updates),'closed jobs')

if __name__=='__main__':main()
