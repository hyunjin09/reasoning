"""Publish only after audited STOP and release; preserve all earlier stage history."""
from pathlib import Path
from scripts.stage11cr.common import ROOT,load,save,now
from harness_state import mutate_run_state,append_run_history
from workflow_hooks import refresh_report_index


def main():
    assert load(ROOT/'audit/closure_validation.json')['status']=='PASS'
    resource=load(ROOT/'stage11cr_resource_accounting.json');assert resource['all_stage_allocations_released']
    gate=load(ROOT/'stage11cr_nonprimary_validation.json')['gate'];assert gate['status']=='STOP'
    at=now();hours=resource['allocated_gpu_hours_observed'];t=gate['arms']['thinking'];d=gate['arms']['instruct_direct']
    status=f'Stage11C-R COMPLETE / prescribed nonprimary technical STOP ({at}). Historical12/12 replay exact; bounded sampling-only diagnostic resolves2/2 greedy loop/cap cases. Original12 nonprimary families×T/D at recovered40960cap yield Thinking{t["caps"]}/12 and Direct{d["caps"]}/12 cap hits; completion gate fails. Frozen80 primary/40 reserve/E*/subsets unchanged,160 primary calls and oracle/controls NOT_RUN. P1–P3 NOT_ESTIMATED. All GPUs released;{hours:.6f} allocatedGPUh. No follow-on launched.'
    archives={}
    for n in ['workflow_state.md','research_plan.md']:
        p=Path('workspace')/n;text=p.read_text();prefix,prior=text.split('Earlier entries are historical.\n',1)
        assert 'Stage11C-R ACTIVE' in prefix;archives[str(p)]=prefix
        p.write_text(status+'\n\n[Report](../outputs/stage11cr/v1/stage11cr_summary.md) · [Phase](phase_memory/phase_11cr_technical_repair_frozen_rerun.md).\n\nEarlier entries are historical.\n'+prior)
    save(ROOT/'audit/dashboard_prefixes_before_closure.json',dict(at=at,prefixes=archives))
    p=Path('workspace/phase_memory/phase_11cr_technical_repair_frozen_rerun.md')
    (ROOT/'audit/phase_memory_before_closure.md').write_text(p.read_text())
    p.write_text(f'''# Phase11C-R: technical repair and frozen rerun

## Current Objective
Approved action complete with prescribed R3 technical STOP. No mechanism localization.

## Active Constraints
Plan:plan/stage11cr_technical_repair_and_frozen_rerun_plan.md. Old Stage11C evidence preserved separately; cohort/E*/subsets/endpoints unchanged. No additional cap/protocol/model/benchmark search or scientific continuation authorized after STOP.

## Current State
{status}

## Evidence That Matters
- outputs/stage11cr/v1/stage11cr_summary.md: final result, transparent cap-protocol correction, exactly one recommendation.
- historical_runtime_comparison / discrepancy_audit: sampled historical eager recipe versus greedySDPA Stage11C; input tensors identical.
- known_good_reproduction.parquet:12/12 full token identities, normal EOS/finals, no cap hits.
- audit/diagnostic_completion_review.json: two fixed greedySDPA failures recover EOS/finals after sampling only; no correctness evaluated.
- nonprimary_validation.json: unchanged12 cases×2 arms fail the prospective completion gate at historical40960 common cap.
- resource_accounting.json / audit/closure_validation.json: all resources released, historical/source provenance preserved, unknowns not imputed.

## Failed Attempts and Lessons
Exact reproduction of selected historical completed cases does not ensure a completion-valid frozen assay. Greedy decoding is a supported contributor in the two bounded diagnostic cases, not a universal explanation. Historical long generation costs invalidate the optimistic resource target; hard budget remained binding.

## Open Candidates
None authorized. Reserve40 remains unopened; no new protocol search.

## Next-Step Decision — {at}
The prescribed nonprimary gate failed. Preserve the technical repair evidence and unchanged scientific cohort, close reporting/accounting and STOP. Recommendation: Close the Thinking-performance mechanism branch and finalize the paper around Claims 1 and 2. Recommendation not executed.

### Step Result
COMPLETE_WITH_NONPRIMARY_TECHNICAL_STOP. Claim3 remains unresolved; no scientific null.
''')
    with Path('workspace/decision_log.md').open('a') as f:
        f.write(f'\n## D123 — Stage11C-R historical repair reproduces but assay validation stops ({at})\n'+status+'\nInput tensors match exactly; sampled eager historical recipe restores all12 selected traces token-for-token. Sampling-only SDPA diagnostic resolves both fixed greedy loops, without correctness selection. The original nonprimary pool still fails completion at the recovered historical budget; selected known-good reproduction cannot substitute for assay validity. No scientific performance/oracle result or new mechanism claim. Recommendation: Close the Thinking-performance mechanism branch and finalize the paper around Claims 1 and 2. Not executed. Evidence:outputs/stage11cr/v1/stage11cr_summary.md;stage11cr_nonprimary_validation.json;audit/closure_validation.json.\n')
    p=Path('plan/stage11cr_execution_checklist.md');lines=[]
    for line in p.read_text().splitlines():
        if line.startswith('- [ ] S'):
            line='- **NOT_RUN — R3 STOP:** '+line[len('- [ ] '):]
        elif line.startswith('- [ ]'):
            line=line.replace('- [ ]','- [x]',1)
        lines.append(line)
    p.write_text('\n'.join(lines)+'\n\nR1 exact12/12; R2 historical repair selected; R3 STOP. Conditional scientific branches were not executed.\n')
    p=Path('workspace/env_state.md');p.write_text(f'## Stage11C-R complete — {at}\nAll{len(resource["jobs"])} finite Slurm allocations terminal/released, total{hours:.6f}GPUh. Existing .venv/local models,BF16/batch1/TF32off. Historical sampling/eager language protocol recorded separately from old11C greedySDPA. No next-stage execution, tmux, keepalive, download or install.\n\nEarlier entries are historical.\n\n'+p.read_text())
    for job in resource['jobs']:
        def mutate(data,job=job):
            data.update(status='completed',current_step='Finite technical shard terminal; Stage11C-R closed',
                node=job['node'],finished_at=at,updated_at=at,display_summary='Stage11C-R terminal; GPU released; R3 technical STOP.')
            append_run_history(data,'stage11cr_closure','Terminal receipt verified; no next action.')
        mutate_run_state(Path.cwd(),job['queue_id'],mutate)
    refresh_report_index(Path.cwd())
    p=Path('reports/index.md');p.write_text('# Latest research outcome\n\n'+status+'\n\n[Stage11C-R summary](../outputs/stage11cr/v1/stage11cr_summary.md) · [Stage11C summary](../outputs/stage11c/v1/stage11c_summary.md) · [Stage11B summary](../outputs/stage11b/v1/stage11b_summary.md).\n\n'+p.read_text())
    save(ROOT/'audit/state_publication.json',dict(at=now(),status='COMPLETE',no_next_action=True))
    print('STAGE11CR_STATE_PUBLISHED_STOP')


if __name__=='__main__':main()
