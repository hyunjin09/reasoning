"""Close a failed technical gate without opening scientific correctness."""
import os
import re
from pathlib import Path

from scripts.stage12a.common import ROOT, load, save, sha, now
from scripts.stage12a.resources import account


def main():
    gate = load(ROOT / 'stage12a_technical_prompt_validation.json')
    assert gate['pass'] is False and gate['repair_rounds'] == 1
    assert gate['correctness_opened'] is False
    source = load(ROOT / 'stage12a_frozen_e_star_manifest.json')
    active = load(ROOT / 'audit/primary_v2.json')
    active_ids = {t['task_id'] for t in active['rows']}
    decisions = {}
    for label in ['technical_v1', 'technical_v2']:
        for r in load(ROOT / 'audit' / f'{label}_review.json')['rows']:
            decisions[r['task_id']] = r
    resources = account('closure', final=True)

    import pandas as pd
    by_arm = {a: [] for a in 'EDC'}
    for folder in sorted((ROOT / 'generations').iterdir()):
        g = load(folder / 'generation.json')
        receipt = load(folder / 'result.json')
        assert receipt['generation_sha256'] == sha(folder / 'generation.json')
        assert receipt['input_sha256'] == sha(folder / 'input.json')
        d = decisions[g['task_id']]
        by_arm[g['arm']].append(dict(
            task_id=g['task_id'], item_id=g['item_id'], family_id=g['family_id'],
            arm=g['arm'], prompt_version=g['prompt_version'],
            active_version=g['task_id'] in active_ids, phase='TECHNICAL_ONLY',
            raw_decoded_response=g['raw_decoded_response'], tokens=g['tokens'],
            cap_hit=g['cap_hit'], normal_stop=g['normal_stop'],
            format_valid=d['format_valid'], committed_final=d['committed_final'],
            intermediate_reasoning=d['intermediate_reasoning'],
            repetition_pathology=d['repetition_pathology'],
            technical_reason=d['reason'], technical_quote=d['quote'],
            correctness=None, correctness_status='NOT_SCORED_TECHNICAL_STOP',
            request_latency_seconds=g['request_latency_seconds'],
            slurm_job=g['job'], node=g['node'],
            generation_path=str(folder / 'generation.json'),
            generation_sha256=sha(folder / 'generation.json')))
    expected = {'E': 12, 'D': 24, 'C': 24}
    assert {a: len(rr) for a, rr in by_arm.items()} == expected
    for a, name in [('E', 'evidence_probe'), ('D', 'answer_only'), ('C', 'reasoning')]:
        p = ROOT / f'stage12a_{name}_results.parquet'
        assert not p.exists()
        pd.DataFrame(by_arm[a]).to_parquet(p, index=False)

    comparison = Path('reports/stage12a/v1/technical_outputs')
    comparison.mkdir(parents=True, exist_ok=True)
    index = ['# Stage12A technical responses', '',
             'Full model responses, with initial and repaired D/C versions shown together. '
             'E was not rerun. No gold answers or correctness scores are shown.', '',
             '| Case | Native answer type | Responses |', '|---|---|---|']
    source_by_id = {r['item_id']: r for r in source['rows']}
    for item in source['technical_selection']['ids']:
        r = source_by_id[item]
        content = [f'# Case {item}', '', r['question'], '',
                   f"[Original image]({r['image']})", '']
        for task_id in [f'E_{item}_v1', f'D_{item}_v1', f'C_{item}_v1', f'D_{item}_v2', f'C_{item}_v2']:
            folder = ROOT / 'generations' / task_id
            g = load(folder / 'generation.json')
            prompt = load(folder / 'input.json')['task']['prompt']
            s = g['raw_decoded_response']
            fence = '`' * max(3, 1 + max([len(x) for x in re.findall(r'`+', s + prompt)] or [0]))
            content += [f'## {task_id}', '',
                        f"{g['tokens']} generated tokens; stop={g['finish_reason']}; correctness unscored.", '',
                        'Exact user text:', '', fence + 'text', prompt, fence, '',
                        'Full model response:', '', fence + 'text', s, fence, '',
                        f"[Raw generation JSON]({(folder / 'generation.json').resolve()})", '']
        with (comparison / f'{item}.md').open('x') as f:
            f.write('\n'.join(content))
        index.append(f"| {item} | {r['answer_type']} | [All five responses](technical_outputs/{item}.md) |")
    with (comparison.parent / 'index.md').open('x') as f:
        f.write('\n'.join(index) + '\n')

    profiles = []
    for row in source['rows']:
        tasks = {t['arm']: t for t in active['rows'] if t['item_id'] == row['item_id']}
        profiles.append(dict(item_id=row['item_id'], family_id=row['family_id'],
            answer_type=row['answer_type'], status='NOT_ESTIMATED_TECHNICAL_STOP',
            technical_case=row['item_id'] in source['technical_selection']['ids'],
            E=None, D=None, C=None, L=None, F1=None, F2=None, F3=None, F4=None,
            **{f'{a}_generation_available': (ROOT / 'generations' / tasks[a]['task_id'] / 'result.json').exists() for a in 'EDC'}))
    pd.DataFrame(profiles).to_parquet(ROOT / 'stage12a_failure_profiles.parquet', index=False)
    save(ROOT / 'stage12a_primary_inference.json', dict(at=now(),
        status='NOT_ESTIMATED_TECHNICAL_STOP', independent_unit='problem/image family',
        frozen_families=61, scientific_families_scored=0,
        P1=None, P2=None, P3=None, P4=None, R_unavail=None,
        wilson_intervals=None, bootstrap_intervals=None,
        bootstrap_draws_executed=0, frozen_bootstrap_draws=4000,
        frozen_analysis_seed=1120260928,
        reason='Technical gate fails after the single permitted wording repair. No correctness opened; absent and format-invalid outputs are not scientific zeroes.'))
    recommendation = ('Do not expand or interpret the Lost-Keys pilot until a separately approved '
                      'technical repair establishes compliant Answer-Only and completion-valid reasoning '
                      'on the frozen validation cases.')
    save(ROOT / 'stage12a_go_nogo_decision.json', dict(at=now(),
        status='TECHNICAL_STOP', scientific_go_nogo='NOT_EVALUABLE',
        technical_pass=False, scientific_thresholds_unchanged=True,
        not_a_scientific_no_go=True, recommendation=recommendation,
        recommendation_executed=False, further_generation_authorized_by_this_result=False))

    # The three required scientific panels explicitly display unavailable estimates.
    os.environ['MPLCONFIGDIR'] = str(Path('runs/stage12a/v1/matplotlib').resolve())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figures = ROOT / 'figures'
    figures.mkdir(exist_ok=True)
    panels = [
        ('figure1_visual_evidence_profiling', 'Visual Evidence Profiling',
         '61 frozen families / 157 frozen facts\n12 technical cases / 60 saved responses across versions\n'
         'E / D / C technical gate did not pass\nEvidence recovery and task-success counts: NOT ESTIMATED'),
        ('figure2_failure_state_composition', 'Answer-Only failure-state composition',
         'NOT ESTIMATED\nTechnical format failures are not scored task errors.\n'
         'No E− / E+ / rescued / persistent partition is available.'),
        ('figure3_selective_reasoning_rescue', 'Selective reasoning rescue',
         'NOT ESTIMATED\nR_available, R_unavailable, and their difference remain undefined.\n'
         'No accuracy scoring or bootstrap inference was performed.')]
    for name, title, message in panels:
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.axis('off')
        ax.set_title(title, fontsize=17, pad=20)
        ax.text(.5, .5, message, ha='center', va='center', fontsize=12, linespacing=1.7)
        fig.text(.5, .02, 'Stage12A: technical stop; not a negative scientific result', ha='center', fontsize=10)
        fig.tight_layout()
        for ext in ['png', 'pdf']:
            fig.savefig(figures / f'{name}.{ext}', dpi=160)
        plt.close(fig)

    first = load(ROOT / 'audit/technical_v1_review.json')
    lines = ['# Stage12A — technical validation stopped', '',
        'The fixed12-case technical gate failed after the plan’s one bounded wording repair. '
        'The61-family Lost-Keys question remains unresolved; this is not a scientific NO-GO.', '',
        '## Preserved design and specification versions', '',
        'All61 original families (24 multiple-choice /37 open-ended),157 E* facts, images/questions, '
        'E requests, seeds, model/runtime,128/16/8192 caps and numerical gates remain unchanged. '
        'The original plan/spec is archived in `audit/spec_versions/`. '
        '`output_contract_v2.json` records the user-approved native-answer clarification before any generation. '
        '`output_contract_v3_bounded_repair.json` records the later, explicitly plan-permitted, output-only '
        'D/C wording repair. It was based on technical failures, with correctness unopened. '
        'These are distinct changes; the later repair is not described as pre-outcome.', '',
        'Initial exact templates remain in `stage12a_prompt_templates.md`; appended repair wording is in '
        '`audit/spec_versions/output_contract_v3_bounded_repair.json`. '
        '`audit/technical_v1.json` and `audit/technical_v2.json` preserve every exact executed request.', '',
        '## Technical results', '',
        '| Version | Arm | Format valid | Committed finals | Cap hits | Severe repetitive cycles | Gate |',
        '|---|---|---:|---:|---:|---:|---|']
    for version, result in [('Initial', first), ('After one repair', gate)]:
        for a in 'EDC':
            s = result['summaries'][a]
            finals = 'n/a' if a == 'E' else f"{s['committed_finals']}/12"
            lines.append(f"| {version} | {a} | {s['format_valid']}/12 | {finals} | {s['caps']}/12 | {s['repetitions']}/12 | {'PASS' if result['pass_by_arm'][a] else 'FAIL'} |")
    lines += ['', 'E was reused unchanged in the second gate. D requires a single native answer, without '
        'reasoning; an MCQ letter plus explanatory text/value is invalid. C commitment is distinguished '
        'from strict terminal formatting. A literal template placeholder `X` is not a committed answer. '
        'Severe repetition was reviewed semantically from actual output cycles; the exact32-gram metric '
        'is supporting evidence and can miss differently tokenized loops. Normal stopping does not erase repetition.', '',
        '## Scope of the result', '',
        '60 outputs were preserved:36 initial E/D/C calls and24 repaired D/C calls. '
        'All12 technical families were retained; the other49 families were not generated. '
        'No task correctness or E* recovery was scored, no E+/D− phenotype was assigned, and '
        'P1–P4, GO/NO-GO scientific thresholds and bootstrap intervals are NOT ESTIMATED. '
        'Parquets preserve both versions and mark the active prompt version; null outcomes mean unscored, not incorrect. '
        'The three required figure panels explicitly mark scientific estimates unavailable.', '',
        'The observed issue is instruction/completion noncompliance under these fixed conditions. '
        'Its cause remains unresolved; neither missing visual encoding nor a Lost-Keys mechanism follows from this result.', '',
        '## Resources and evidence', '',
        f"Allocated GPU time: **{resources['allocated_gpu_hours']:.6f} GPU-hours** including startup/shutdown. "
        'All Stage12A allocations released. Slurm127229 saved all36 valid receipts before timing out during '
        'shutdown; no completed response was retried. The repair used a longer finite wall allowance. '
        'Exact terminal receipts and commands are in `stage12a_resource_accounting.json`.', '',
        'Raw responses, token IDs and actual input prompts: `generations/<task_id>/`. '
        'Readable side-by-side versions: [technical response index](../../../reports/stage12a/v1/index.md). '
        'Output-only manual decisions and integrity evidence: `audit/technical_v1_review.json`, '
        '`audit/technical_v2_review.json`, and `audit/technical_v1_integrity.json`. '
        'No native Thinking, oracle, new benchmark, full-cohort correctness, further wording search or follow-on launched.', '',
        '## Exactly one recommendation', '', recommendation, '', '**TECHNICAL_STOP — scientific gate not evaluable**', '']
    summary = ROOT / 'stage12a_summary.md'
    with summary.open('x') as f:
        f.write('\n'.join(lines))
    print('CLOSED_TECHNICAL_STOP', resources['allocated_gpu_hours'])


if __name__ == '__main__':
    main()
