"""Publish compact Stage11C state only after closure validation and GPU release."""
from pathlib import Path
from scripts.stage11c.common import ROOT, load, save, now
from scripts.stage11c.close_early_stop import RECOMMENDATION
from harness_state import mutate_run_state, append_run_history
from workflow_hooks import refresh_report_index


def main():
    assert load(ROOT/'audit/closure_validation.json')['status']=='PASS'
    resource=load(ROOT/'stage11c_resource_accounting.json')
    assert resource['all_stage_allocations_released']
    gate=load(ROOT/'stage11c_native_gate.json')
    assert gate['status']=='STOP_COMPLETION'
    at=now();hours=resource['allocated_gpu_hours_observed'];hits={k:v['cap_hits'] for k,v in gate['technical_diagnostics'].items()}
    status=f'Stage11C COMPLETE / prescribed technical STOP ({at}).250 sources reviewed twice,120 eligible;80 primary/40 reserve sealed before outcomes.48 calibration calls and32 native completion-gate calls preserved. Native cap hits Thinking{hits["thinking"]}/16,Direct{hits["instruct_direct"]}/16 at8192; remaining128 native calls, oracle and conditional blocks NOT_RUN. P1–P3 NOT_ESTIMATED; Claim3 unresolved. All GPUs released;{hours:.6f} allocatedGPUh. No follow-on launched.'
    archived={}
    for name in ['workspace/workflow_state.md','workspace/research_plan.md']:
        p=Path(name);text=p.read_text();marker='Earlier entries are historical.\n'
        assert marker in text
        prefix,prior=text.split(marker,1)
        assert 'Stage11C ACTIVE' in prefix and 'Stage11B COMPLETE' in prior
        archived[name]=prefix
        p.write_text(status+'\n\n[Report](../outputs/stage11c/v1/stage11c_summary.md) · [Phase](phase_memory/phase_11c_thinking_instruct_lifecycle.md).\n\nEarlier entries are historical.\n'+prior)
    save(ROOT/'audit/dashboard_prefixes_before_closure.json',dict(at=at,removed_active_prefixes=archived))
    phase=Path('workspace/phase_memory/phase_11c_thinking_instruct_lifecycle.md')
    archive=ROOT/'audit/phase_memory_at_closure.md';assert not archive.exists();archive.write_text(phase.read_text())
    phase.write_text(f'''# Phase11C: Thinking versus Instruct lifecycle localization

## Current Objective
Approved Stage11C execution complete with its prescribed early technical STOP. Claim3 remains unresolved.

## Active Constraints
Plan:plan/stage11c_thinking_vs_instruct_lifecycle_localization_plan.md. No new research action, cap/decoding rescue, reserve rescue, benchmark search or manuscript changes are authorized by completion. Preserve all negative/partial evidence. Distinct checkpoints; no same-weights or formal-mediation claim.

## Current State
{status}

## Evidence That Matters
- outputs/stage11c/v1/stage11c_summary.md: full bounded result and exactly one recommendation.
- stage11c_e_star_sufficiency_review.json / primary_split.json:250 reviewed,120 eligible,80/40 split; raw disagreements and low candidate-only kappa retained. No outcome selection or E* repairs.
- stage11c_cap_validation.json:Thinking12/12,Direct11/12 cap hits at both4096/8192. Prescribed8192 completion-limited fallback.
- stage11c_native_gate.json:fixed16 matched families fail completion (>4 cap hits in either mode); performance gate not evaluated.
- stage11c_native_td_results.parquet:32 completed and128 NOT_RUN entries, no unknown-as-wrong imputation.
- stage11c_primary_inference.json:P1/P2/P3 unknown, not null effects; no oracle localization.
- stage11c_resource_accounting.json / audit/closure_validation.json:all allocations released,{hours:.6f}GPUh, provenance/chronology/count checks passed.

## Failed Attempts and Lessons
Batch1 under the frozen greedy protocol did not produce completion-valid new native trajectories. A fixed technical-case check confirmed image inputs/templates, but noncompletion cause remains unknown. Do not attribute this to difficulty, missing evidence, batch behavior or a mechanism without new evidence. Prior Stage11A/11B outcomes remain valid for their frozen regimes.

## Open Candidates
None authorized. Reserve40 remains unopened, conditional controls unrun.

## Next-Step Decision — {at}
The authorized plan reached its explicit completion stop. Close artifacts, release all resources and STOP. Exactly one recommendation: {RECOMMENDATION}

## Step Result
COMPLETE_WITH_TECHNICAL_STOP. The recommendation has not been executed as a new research action. Earlier boundary history is preserved in audit/phase_memory_before_primary.md and audit/phase_memory_at_closure.md.
''')
    decision=Path('workspace/decision_log.md')
    with decision.open('a') as stream:
        stream.write(f'\n## D121 — Stage11C completion gate stops Claim3 localization ({at})\n'+status+'\nThe batch1/common-cap protocol still exhibits severe noncompletion; cause is unknown. A failed technical gate is not a null mechanism effect. Preserve raw annotations, completed traces and unknown outcomes; no selective rescue. '+RECOMMENDATION+' Recommendation not executed. Evidence:outputs/stage11c/v1/stage11c_summary.md;stage11c_native_gate.json;audit/closure_validation.json.\n')
    checklist=Path('plan/stage11c_execution_checklist.md');text=checklist.read_text()
    text=text.replace('- [ ] Run first16 matched primary native families and completion gate before further native work.','- [x] Run32 native calls on first16 matched families; completion gate fails, prescribed STOP.')
    text=text.replace('- [ ] Complete native T/D and freeze performance gate, or prescribed STOP.','- [x] Prescribed early STOP. Remaining128 native calls NOT_RUN; full performance gate NOT_EVALUATED.')
    text=text.replace('- [ ] Conditional oracle validity, paired oracle and24-family neutral control.','- [x] Conditional oracle/neutral explicitly NOT_RUN because completion gate fails.')
    text=text.replace('- [ ] Freeze P1–P3 inference; conditional48-family CoT and predeclared reserve, no automatic expansion.','- [x] P1–P3 NOT_ESTIMATED. CoT/native-state/reserve blocks NOT_RUN; no expansion.')
    text=text.replace('- [ ] Required artifacts/figures, resources, provenance/closure audit, research state and exactly one recommendation; STOP.','- [x] Required artifacts and four figure pairs, final resource accounting, provenance/chronology audit and state complete. Exactly one recommendation; STOP.')
    checklist.write_text(text)
    env=Path('workspace/env_state.md');env.write_text(f'## Stage11C complete — {at}\nAll{len(resource["jobs"])} Slurm allocations terminal/released, total{hours:.6f}GPUh. No Stage11C GPU job remains or next-phase launch is authorized. Runtime stays project.venv/BF16/batch1/TF32off.\n\nEarlier entries are historical.\n\n'+env.read_text())
    for job in resource['jobs']:
        def mutate(data, job=job):
            partial=job['queue_id']=='stage11c_cap_thinking'
            data.update(status='completed',current_step='Safe partial calibration shard; remaining9 calls completed separately' if partial else 'Finite generation shard complete; Stage11C closed',
                node=job['node'],finished_at=at,updated_at=at,
                display_summary='Stage11C terminal; GPU released. '+('Planned safe partial shard preserved.' if partial else 'All assigned calls completed.'))
            append_run_history(data,'stage11c_closure','Terminal receipt verified; stage technical STOP, no next action.')
        mutate_run_state(Path.cwd(),job['queue_id'],mutate)
    refresh_report_index(Path.cwd())
    index=Path('reports/index.md')
    index.write_text('# Latest research outcome\n\n'+status+'\n\n[Stage11C summary](../outputs/stage11c/v1/stage11c_summary.md) · [Stage11B summary](../outputs/stage11b/v1/stage11b_summary.md) · [Stage11A summary](../outputs/stage11a/v1/stage11a_summary.md).\n\n'+index.read_text())
    save(ROOT/'audit/state_publication.json',dict(at=now(),status='COMPLETE',recommendation=RECOMMENDATION,no_next_action=True))
    print('STAGE11C_STATE_PUBLISHED_STOP')


if __name__=='__main__':
    main()
