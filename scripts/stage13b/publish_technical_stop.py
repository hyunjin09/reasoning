"""Publish the gated stop and close only this stage's scheduler/state records."""
from pathlib import Path
import re
import subprocess

from infra.harness_state import mutate_run_state, append_run_history
from scripts.stage13b.execution import ROOT, load, save, sha, now
from scripts.stage13b.review import tasks, checked, technical, technical_path


def main():
    final = load(ROOT / 'audit/final_verification.json')
    assert final['all_gpus_released'] and not final['full_scientific_study_completed']
    ledger = load(ROOT / 'stage13b_resource_accounting.json')
    assert not ledger['active_jobs']
    report = Path('reports/stage13b/v1')
    entries = []
    pages = {}
    for t in tasks():
        if not (ROOT / 'generations' / t['task_id'] / 'result.json').exists():
            continue
        g, _ = checked(t)
        a = technical(t['task_id'])
        p = report / 'responses' / (t['task_id'] + '.md')
        raw = g['raw_decoded_response']
        fence = '`' * max(4, 1 + max((len(x) for x in re.findall(r'`+', raw)), default=0))
        if not p.exists():
            p.write_text('\n'.join([
                '# ' + t['task_id'], '',
                f"Family: {t['family_id']}; replicate: {t['replicate']}; seed: {t['seed']}.", '',
                f"Tokens: {g['tokens']}; finish: {g['finish_reason']}; technical validity: {a['validity']['TECHNICALLY_VALID']}.",
                'Correctness was not graded after the mandatory technical stop.', '',
                f"[Raw generation](../../../../{ROOT}/generations/{t['task_id']}/generation.json) · "
                f"[Input](../../../../{ROOT}/generations/{t['task_id']}/input.json) · "
                f"[Validity receipt](../../../../{technical_path(t['task_id'])})", '',
                '## Frozen input text', '', fence + 'text', t['prompt'], fence, '',
                '## Full model response', '', fence + 'text', raw, fence, ''
            ]))
        pages[str(p)] = sha(p)
        entries.append((t, g, a, p))
    response_lines = ['# All saved Stage13B responses', '',
        'Verbatim answers and reasoning, grouped by phase. Technical validity is separate from correctness; no new accuracy comparison was opened.', '']
    for phase in ['technical', 'equal']:
        response_lines += ['## ' + ('Separate technical validation' if phase == 'technical' else 'Initial eight-family equal-evidence tranche'), '',
            '| Item | Checkpoint | Input | Replicate | Tokens | Finish | Technical validity |',
            '|---|---|---|---:|---:|---|---|']
        for t, g, a, p in sorted(entries, key=lambda x: (str(x[0]['item_id']), x[0]['model_key'], x[0]['arm'], x[0]['replicate'])):
            if t['phase'] == phase:
                response_lines.append(f"| [{t['item_id']}](responses/{p.name}) | {t['model_key']} | {t['arm']} | {t['replicate']} | {g['tokens']} | {g['finish_reason']} | {a['validity']['TECHNICALLY_VALID']} |")
        response_lines.append('')
    (report / 'responses.md').write_text('\n'.join(response_lines))
    summary = (ROOT / 'stage13b_summary.md').read_text()
    links = ('[Plan](../../../plan/stage13b_cross_scale_thinking_role_vlm_plan.md) · '
             '[All answers and reasoning](responses.md) · '
             '[Separate technical validation](technical.md) · '
             '[Decision](../../../outputs/stage13b/v1/stage13b_decision.json) · '
             '[Technical behavior](../../../outputs/stage13b/v1/audit/final_technical_behavior.json) · '
             '[Resources](../../../outputs/stage13b/v1/stage13b_resource_accounting.json)')
    (report / 'index.md').write_text(summary + '\n' + links + '\n')
    (report / 'status.md').write_text('# Stage13B closed at mandatory technical stop\n\n' + links + '\n\n' + summary)
    index = Path('reports/index.md')
    old = index.read_text()
    updated = old.replace('[Stage13B — cross-scale Thinking role: running]', '[Stage13B — mandatory technical stop / CROSS_SCALE_ROLE_UNRESOLVED]')
    queue_updates = []
    try:
        for row in ledger['jobs']:
            jid = row['slurm_job_id']
            registration = load(ROOT / 'audit/launches' / (jid + '.json'))['jobs'][0]
            assert registration['id'].startswith('vr_stage13b_v1_')
            assert row['state'] in ['COMPLETED', 'CANCELLED']
            status = 'succeeded' if row['state'] == 'COMPLETED' else 'cancelled'
            note = ('Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate.'
                    if status == 'succeeded' else 'Cancelled before allocation at the mandatory Stage13B technical stop.')
            proc = subprocess.run(['.venv/bin/python', 'infra/gpu_scheduler.py', 'update', '--project', '.',
                '--id', registration['id'], '--status', status, '--note', note], capture_output=True, text=True, check=True)
            def close(data):
                data.update(status=status, current_step=note, display_summary=note, finished_at=now())
                append_run_history(data, 'stage13b_gate_closure', f'Slurm {jid}: {row["state"]}; allocation released.')
            mutate_run_state(Path.cwd(), registration['exp_id'], close)
            queue_updates.append(dict(id=registration['id'],job=jid,status=status,stdout=proc.stdout))
    finally:
        index.write_text(updated)
    save(ROOT / 'audit/publication_receipt.json', dict(at=now(), raw_response_pages=pages,
        response_count=len(entries), queue_updates=queue_updates, follow_on_launched=False,
        report_sha256=sha(report/'index.md'), response_index_sha256=sha(report/'responses.md')))
    print('Published', len(entries), 'responses; closed', len(queue_updates), 'queue entries.')


if __name__ == '__main__':
    main()
