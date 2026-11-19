"""Close the approved research cycle after validated, fully analyzed execution."""
from pathlib import Path
from scripts.stage14e.common import P, load, save, sha, now


def main():
    stamp = now()
    acc = load(P / 'analysis/final_accuracy_v1.json')
    res = load(P / 'audit/resource_accounting_final_v1.json')
    verify = load(P / 'audit/final_execution_verification_v1.json')
    assert verify['all_cycle_allocations_terminal'] and verify['physical_solver_generations'] == 77
    assert (P / 'reports/final_research_report_v1.md').exists()
    hours = res['new_actual_gpu_hours']
    answers = ', '.join(f"{a} {acc['arms'][a]['correct']}/32" for a in ['N', 'S', 'M'])
    status = (f'Completed the authorized bounded research cycle: all72 SAVA postmortem,24-family diagnostic, '
        f'one24-family revision and one32-family evaluation;96logical/77physical solvers,19native aliases. '
        f'Acquisition M0/32 versus S1/32; M−S−3.125pp,95%CI[−9.375,0]. Final answers: {answers}; '
        f"unscorable " + ', '.join(f"{a}={acc['arms'][a]['unscorable']}" for a in ['N', 'S', 'M']) + '. '
        f'All allocations released; new{hours:.6f}/24GPUh, historical21.365278GPUh separate. '
        'No demonstrated acquisition improvement. No further tuning or follow-on launch. '
        'OldStage14D375GPUh remains HOLD; Stage14C-V remains unfinished.')
    head = f'# Stage14E — COMPLETE / STOP ({stamp})\n\n{status}\n\n'
    for name in ['workspace/workflow_state.md', 'workspace/research_plan.md']:
        p = Path(name)
        p.write_text(head + '[Final report](../outputs/stage14e_acquisition_development/v1/reports/final_research_report_v1.md) · '
            '[Phase](phase_memory/phase_14e_acquisition_development.md). Earlier entries below are history.\n\n' + p.read_text())
    phase = Path('workspace/phase_memory/phase_14e_acquisition_development.md')
    text = phase.read_text(); a = text.index('## Current State\n'); b = text.index('\n## Evidence That Matters', a)
    text = text[:a] + '## Current State\n' + status + '\n' + text[b:]
    a = text.index('## Next-Step Decision\n'); b = text.index('\n### Diagnostic release', a)
    text = text[:a] + '''## Next-Step Decision
STOP: the authorized bounded cycle is complete. Do not launch a larger ledger evaluation or tune on the32observed cases. The single recommendation is a separately scoped source-reading development study centered on reliable entity–relation binding and independent evidence-level validation. This recommendation is not executed. Preserve all negative evidence, aliases, source judgments and original artifacts.
''' + text[b:]
    text += '\n### Final closure — ' + stamp + '\n' + status + '\n'
    phase.write_text(text)
    decision = Path('workspace/decision_log.md')
    with decision.open('a') as out:
        out.write(f'\n## Stage14E final source-evidence result — {stamp}\n\n'
            'The obligation-first ledger selected on3/24partial development reinspections produced0/32useful '
            'new/reinspected facts in the one-shot evaluation, versus1/32original SAVA-style reader. '
            'Seventeen targets were accepted,12ledgers rejected,3NONElegitimate; accepted targets were0fully '
            'relevant/9partial/8unhelpful. Technical provenance and exact-prefix/replay validity do not certify '
            'task relevance or evidence fidelity. Seven invalid ledgers had a valid first eligible entry but '
            'another invalid entry; no alternative execution was tested, so no claim that relaxation solves this. '
            'Keep helper evidence, later solver image use and final answers distinct. '
            f'Final answers {answers}; no accuracy result is relabeled as fresh helper acquisition. '
            'Recommendation: do not scale this implementation; establish reliable source binding before another '
            'efficacy study. No follow-on launched. '
            '[Evidence](../outputs/stage14e_acquisition_development/v1/reports/final_research_report_v1.md).\n')
    index = Path('reports/index.md')
    index.write_text(f'# Stage14E — completed bounded acquisition cycle ({stamp})\n\n'
        '[Final report](../outputs/stage14e_acquisition_development/v1/reports/final_research_report_v1.md) · '
        '[All32 casebook](../outputs/stage14e_acquisition_development/v1/reports/final32_casebook_v1.md). '
        + status + '\n\nEarlier entries are historical.\n\n' + index.read_text())
    with Path('workspace/env_state.md').open('a') as out:
        out.write(f'\n## Stage14E closure — {stamp}\n\nAll cycle allocations are terminal. New{hours:.6f}GPUh '
            'within24additional;48hSlurmlimits/finitequeues. Pinned project-local environments unchanged; no '
            'package install or global-environment modification during closure. Final runtime: Qwen3-VL-4B-Thinking '
            '1de27d8c51f12e819435303b9e84c4e25ba8401e, vLLM0.11.0, BF16,MP0,cacheoff. '
            'Resource receipts: outputs/stage14e_acquisition_development/v1/audit/resource_accounting_final_v1.json.\n')
    with Path('workspace/dataset_inventory.md').open('a') as out:
        out.write(f'\n## Stage14E closure — {stamp}\n\nReused local MathVision source images and pinned4BThinking checkpoint. '
            'No new dataset/model download. Frozen32family/32uniqueimage evaluation is disjoint from old72and '
            'excluded300audit image hashes; prior benchmark exposure retained. Selection and source paths: '
            'outputs/stage14e_acquisition_development/v1/manifests/evaluation_family_selection_v1.json.\n')
    readme = Path('scripts/stage14e/README.md')
    readme.write_text(head + 'This is the terminal state; execution notes below document the earlier recovery and reproduction steps. '
        'Saved artifacts are write-once. Do not rerun generators into existing roots.\n\n' + readme.read_text())
    with (P / 'README.md').open('x') as out:
        out.write(head + '[Final research report](reports/final_research_report_v1.md)\n\n'
            '[All32 source/output casebook](reports/final32_casebook_v1.md) · '
            '[Every final-answer change](reports/final_answer_change_casebook_v1.md) · '
            '[Case index](analysis/final_case_index_v1.csv)\n\n'
            '[Acquisition results](analysis/evaluation_acquisition_results_v1.json) · '
            '[Final accuracy](analysis/final_accuracy_v1.json) · '
            '[Resource accounting](audit/resource_accounting_final_v1.json)\n\n'
            '[SAVA postmortem](reports/sava_failure_postmortem_v1.md) · '
            '[Prior art and hypotheses](reports/prior_art_and_hypotheses_v1.md) · '
            '[Implementation/reproduction guide](../../../scripts/stage14e/README.md)\n\n'
            'All source judgments precede final-score inspection. Raw generations, inputs, token IDs, seeds, '
            'source images, hashes and failed attempts remain preserved. No new experiment follows this closure.\n')
    files = ['workspace/workflow_state.md', 'workspace/research_plan.md', str(phase), 'workspace/decision_log.md',
             'workspace/env_state.md', 'workspace/dataset_inventory.md', 'reports/index.md']
    save(P / 'audit/closure_state_snapshot_v1.json', dict(at=stamp,
        files={f: dict(sha256=sha(f), text=Path(f).read_text()) for f in files}))
    save(P / 'audit/execution_checklist_final_v1.json', dict(at=stamp,
        postmortem_families=72, diagnostic_families=24, revision_families=24,
        evaluation_families=32, logical_solvers=96, physical_solvers=77,
        acquisitions_reviewed=96, physical_finals_reviewed=77, follow_on_launched=False,
        all_cycle_allocations_released=True, additional_gpu_hours=hours,
        prior375_gpu_hour_experiment='HOLD', stage14c_v='UNFINISHED'))
    print('Closed compact state; no follow-on experiment')


if __name__ == '__main__':
    main()
