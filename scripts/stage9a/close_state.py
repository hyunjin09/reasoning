"""Close only Stage 9A documentation after its completion contract passes."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from harness_state import append_run_history, mutate_run_state
from workflow_hooks import refresh_report_index

ROOT = Path.cwd()
OUT = ROOT / 'outputs/stage9a/v1'


def main():
    audit = json.loads((OUT / 'audit/final_validation.json').read_text())
    assert audit['completed'] and audit['gpus_released']
    assert audit['required_artifacts'] == 13 and audit['figures'] == 5
    causal = json.loads((OUT / 'stage9a_causal_validation.json').read_text())
    stamp = datetime.now(timezone.utc).isoformat()
    report = 'outputs/stage9a/v1/stage9a_summary.md'
    summary = ('Stage 9A COMPLETE / STOP. All 384 native trajectories, 700 semantic reviews, '
               '610 source/readout reviews, 384 answer reviews and 50 causal checks complete; '
               '13 artifacts, five figures and 18 focused tests verified. '
               'Zero of four primary contrasts supports the proposed positive Thinking-specific regime; '
               'nine length-matched families and causal samples 16/16/18 limit inference. '
               'Exactly one recommendation: stop the Stage 9 bottleneck/bypass branch and retain '
               'reasoning-conditioned dynamic visual retrieval. All GPUs released; no follow-on launched.')
    for name in ('workflow_state.md', 'research_plan.md'):
        path = ROOT / 'workspace' / name
        text = path.read_text()
        first = (f'**CURRENT — {stamp}: {summary}** '
                 f'[Report](../{report}) · [Phase](phase_memory/phase_9a_thinking_vs_cot.md).')
        path.write_text(first + '\n\n' + text.split('\n\n', 1)[1])
    env = ROOT / 'workspace/env_state.md'
    text = env.read_text()
    env.write_text(
        f'**Stage 9A COMPLETE / no active allocation — {stamp}.** '
        'Native workers120903–120906 and causal workers121562–121564 completed and released. '
        f'Native inference70.24 GPU-hours; causal events{causal["runtime_gpu_hours"]:.3f} GPU-hours, excluding startup. '
        'Causal workers each used one node06 A6000/4CPUs/30G; CPU-only121568/node03 completed in9m02s. '
        'Slurm accounting storage disabled; job receipts and measured runtimes preserved. '
        'Existing .venv, BF16 models and dataset reused; no install/download or tmux. '
        '[Final validation](../outputs/stage9a/v1/audit/final_validation.json). '
        'Earlier entries below are historical.\n\n' + text.split('\n\n', 1)[1])

    phase = ROOT / 'workspace/phase_memory/phase_9a_thinking_vs_cot.md'
    text = phase.read_text()
    sections = {
        'Current State': (
            '- Complete: all384 native trajectories;700 semantic nominations (539 accepted,126 rejected,35 unknown); '
            '610 source/readout and384 answer reviews;50 frozen causal events.\n'
            '- Complete: all13 artifacts and5 figures, frozen primary/matched/adjusted analyses, secondary accuracy,18 focused tests.\n'
            '- Result:0/4 positive primary Thinking−CoT contrasts; density2.437 versus5.122 episodes/1k tokens. '
            'Only9 matched-length families; causal16/16/18 below arm inference threshold. No equivalence claim.\n'
            '- All50 native-prefix/capture/self-sham checks pass; all native artifact hashes verified. '
            'All allocations released. No blocked or pending work for Stage9A.\n'
            f'- Evidence: `{report}` and `outputs/stage9a/v1/audit/final_validation.json`.'),
        'Failed Attempts and Lessons': (
            'Node07 preflight stalled in startup RPC/filesystem I/O before inference; underlying cause unknown. '
            'Cancelled and recovered on authorized node06 with the same frozen science. No repeated node07 trial.\n\n'
            'The proposed positive regime gate was not met. Total episode count, per-token density, paired demand support '
            'and secondary accuracy must stay distinct. Source/length eligibility shortfalls remain uncertainty, not zero or equivalence.'),
        'Open Candidates': 'None selected. Stage9A is complete; later stages or rescue experiments require a new user instruction.',
        'Next-Step Decision': (
            '- Current bottleneck: no authorized work remains.\n'
            '- Evidence used: frozen primary effects, nine matched families,50 causal checks and final integrity/release audit.\n'
            '- Exactly one recommendation: stop the Stage9 bottleneck/bypass branch and retain the existing '
            'reasoning-conditioned dynamic visual-retrieval framing.\n'
            '- No new action selected or executed. Do not widen the caliper, tune prompts/thresholds, '
            'replace the cohort or launch same-prefix/bypass work to rescue this result.\n'
            '- Stop condition met:13 outputs,5 figures,one recommendation,all GPUs released.\n\n'
            '### Step Result\n'
            f'Completed {stamp}. The primary hypothesis is unsupported in this native comparison; '
            'matched/causal precision limits prevent an equivalence claim. Historical execution observations follow.')
    }
    for heading, body in sections.items():
        pattern = rf'(?ms)^## {re.escape(heading)}\n.*?(?=^## |\Z)'
        # The final section includes historical checkpoints: preserve those after its old Step Result.
        if heading == 'Next-Step Decision':
            start = text.index('## Next-Step Decision\n')
            history = text.index('Resource update:', start)
            text = text[:start] + f'## {heading}\n{body}\n\n' + text[history:]
        else:
            text, n = re.subn(pattern, lambda _: f'## {heading}\n{body}\n\n', text, count=1)
            assert n == 1, heading
    text = re.sub(r'\n### Final closure — .*\Z', '', text, flags=re.S)
    text += f'\n### Final closure — {stamp}\n{summary}\n'
    phase.write_text(text)

    decision = ROOT / 'workspace/decision_log.md'
    text = decision.read_text()
    if '## D-096 ' not in text: decision.write_text(text + f'\n\n## D-096 — Stage9A completed at its negative advancement gate ({stamp})\n\n'
        'All128 families across three arms retained;0/4 positive primary Thinking−CoT contrasts. '
        'The positive exploratory total-episode contrast coexists with lower per-token density; '
        'nine matched pairs and16/16/18 causal events cannot certify a robust arm difference or equivalence. '
        'Demand alignment exceeds circular shifts in all arms. Secondary reviewed accuracy45.31/29.69/25.00% '
        '(Thinking/CoT/Direct) does not override the mechanism gate.\n\n'
        'Promoted lesson: keep total counts distinct from exposure-normalized recurrence, and report actual paired '
        'annotation support instead of comparing unpaired arm means as a paired effect. Preserve uncertain '
        'calibration, fine-subtype coverage and causal/length precision; no unsupported causal diagnosis.\n\n'
        f'Evidence: `{report}`, `stage9a_primary_effects.json`, `stage9a_causal_validation.json` and final audit '
        'under outputs/stage9a/v1. Exactly one recommendation: stop the Stage9 bottleneck/bypass branch and retain '
        'reasoning-conditioned dynamic visual retrieval. No next experiment launched; all GPUs released.\n')

    checklist = ROOT / 'plan/stage9a_execution_checklist.md'
    historical_checklist = checklist.read_text() if checklist.exists() else ''
    checklist.write_text(f'# Stage9A completion checklist\n\nVerified {stamp}. Original plan and execution protocol preserved.\n\n'
        '- [x] Frozen128-family cohort and native three-arm protocol; all-arm parity preflight.\n'
        '- [x]384 native trajectories preserved; all underlying artifact hashes verified.\n'
        '- [x]700 masked semantic,610 masked source/readout,384 masked extraction reviews completed.\n'
        '- [x]50 outcome-independent frozen causal events replayed, all native-prefix/capture/sham gates passed.\n'
        '- [x]Four primary endpoints, fixed-caliper matching, family-clustered regression, demand controls and sensitivities.\n'
        '- [x]Secondary accuracy, subtype support limitations and resource burden documented.\n'
        '- [x]All13 required artifacts and five figures in PNG/PDF verified;18 focused tests passed.\n'
        '- [x]All scheduler workers terminal, all GPUs released. Remaining compute: zero.\n'
        '- [x]Exactly one recommendation and STOP; no follow-on or rescue experiment.\n\n'
        '[Final report](../outputs/stage9a/v1/stage9a_summary.md) · '
        '[Validation](../outputs/stage9a/v1/audit/final_validation.json)\n\n'
        '## Historical checklist and resource estimates\n\n' + historical_checklist)

    queue = json.loads((ROOT / 'state/gpu_experiment_queue.json').read_text())['jobs']
    for job in (j for j in queue if j['id'].startswith('stage9a_')):
        assert job['status'] in ('succeeded', 'cancelled'), job['id']
        exp = job['exp_id']
        if exp == 'stage9a' or not (ROOT / 'state/runs' / (exp + '.json')).exists():
            continue
        def reconcile(data, job=job):
            data.update(status='completed' if job['status']=='succeeded' else 'cancelled',
                        current_step=job['notes'], display_summary=job['notes'])
            append_run_history(data, 'completion_reconciled', 'Verified terminal scheduler state and preserved job receipts; allocation released.')
        mutate_run_state(ROOT, exp, reconcile)
    for exp in ('stage9a', 'stage9a_v1'):
        def complete(data):
            data.update(status='completed', current_step='Stage9A complete; negative advancement gate; STOP',
                        display_summary=summary, result_path=report, finished_at=stamp)
            append_run_history(data, 'stage9a_completed', summary)
        mutate_run_state(ROOT, exp, complete)
    refresh_report_index(ROOT)
    print('Stage9A documentation and run states closed; no new action launched')


if __name__ == '__main__':
    main()
