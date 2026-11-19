"""Compact handoff after the required V3 technical stop."""
from datetime import datetime, timezone
from pathlib import Path
from harness_state import mutate_run_state
from workflow_hooks import refresh_report_index
from scripts.stage8c.prepare import ROOT, sha, save


at = datetime.now(timezone.utc).isoformat()
for i, why in [(1,'stopped:validation onset-coverage harness'),
               (2,'stopped:manual validation position IDs'),
               (3,'STOP:required V3 numerical reconstruction failure')]:
    def change(data, why=why):
        data.update(status='failed', current_step=why, display_summary=why, finished_at=at, updated_at=at)
    mutate_run_state(Path('.').resolve(), f'stage8c_v2_technical_v{i}', change)
refresh_report_index(Path('.').resolve())
p = Path('reports/index.md')
p.write_text(p.read_text().replace('## GPU Jobs',
    'Latest stage: [Stage8C v2 technical STOP](../outputs/stage8c_v2/v1/stage8c_v2_summary.md). '
    'Zero scientific trajectories; V3 failed; GPUs released.\n\n'
    'Previous completed research: [Block3A yield stop](../outputs/stage8b_block3a/v1/stage8b_block3a_summary.md).\n\n## GPU Jobs', 1))

Path('workspace/workflow_state.md').write_text(f'''# Workflow state — Stage8C v2 STOP at technical V3

Updated {at}.

- User-approved Stage8C v2 prepared; exactly2 node02 GPUs through scheduler/Slurm.
- Frozen dev128/test512, timing256 and review128; one identified family/item,
  no split/prior-family overlap. Existing model/data reused, no downloads.
- 10 CPU tests pass. Two validation-harness issues diagnosed and repaired with
  previous configs preserved. Third attempt118518 reached V3 and failed the
  frozen visual-contribution reconstruction tolerance on both audited items.
- No tolerance relaxation or further GPU retry. Error magnitudes were not saved;
  root cause unknown. This is a technical validity stop, not an efficacy null.
- Scientific trajectories:0. No selected dose, held-out/timing result or semantic
  audit. Required downstream artifacts explicitly not-run; no scientific plots.
- All allocations released;118514/118515/118518 consumed approximately0.1083 GPUh.
  No scientific completion ETA until validity is established.
- One recommendation: diagnose/repair visual decomposition, preserve the cohort,
  then revalidate V1–V6. That follow-up and Block3B are not launched.
- Prior Block3A's18 artifact/158 supporting hashes verified unchanged.

[Report](../outputs/stage8c_v2/v1/stage8c_v2_summary.md) · [Validation](../outputs/stage8c_v2/v1/stage8c_v2_technical_validation.json) · [Phase](phase_memory/phase_8c_v2_visual_gain.md) · [Checklist](../plan/stage8c_v2_execution_checklist.md).
''')

Path('workspace/phase_memory/phase_8c_v2_visual_gain.md').write_text(f'''# Phase8C v2: retrieval-triggered native visual gain

## Current Objective

Execute the approved diverse MathVision gain benchmark. Execution is stopped at
its mandatory V3 technical gate; no scientific efficacy result exists.

## Active Constraints

Exactly2 node02 GPUs via scheduler/Slurm; no tmux. Frozen BF16 pinned2B,
MathVision protocol, detector/layers19–22 and gains1/1.25/1.5/2. Preserve prior
stages and new input-only cohorts. Every V1–V6 must pass before science. No
oracle input, tolerance retuning, automatic expansion or Block3B.

## Current State

- Done: conservative prior-use/image-family audit; dev128, test512, timing256 and
  review128 frozen; local data/model reused.
- Done: wrapper/guarded runner/scoring scaffolding and10 CPU tests. Three short
  technical allocations; first two harness issues repaired with direct evidence.
- Stopped:118518 V3 reconstruction exceeded frozen tolerance on both initial
  prefixes2579/2433. Downstream scientific work not run; no selected dose.
- Blocked: visual decomposition validity. Cause unknown; scalar maxima were not
  serialized before failure. All stage GPUs released,0.1083 GPUh total.
- Most recent useful observation: native/no-op/cache comparisons preceded the
  decomposition assertion, but that does not establish the full technical gate.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Frozen128/512 distinct identified families | outputs/stage8c_v2/v1/stage8c_v2_family_manifest.json | Preserve outcome-independent membership | confirmed |
| Prior rescaled alias1707/1245 | workspace/decision_log.md D-082 | Exact pixel hashes alone insufficient | confirmed |
| V3 fails both initial prefixes | outputs/stage8c_v2/v1/technical_v3/worker0/failure.json; worker1/failure.json | Mandatory stop before dose sweep | confirmed |
| Earlier comparisons passed by code flow | scripts/stage8c/validate_v3.py; same failure traces | Partial validity; full coverage incomplete | confirmed, limited |
| Prior Block3A176 frozen hashes unchanged | outputs/stage8c_v2/v1/audit/final_verification.json | Historical evidence preserved | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
|118514,81s|Per-prefix nonempty-onset guard rejected2433|supported by saved old native traces: no onset; other prefixes supply triggered cases|Require both cases across audit, not every prefix active|Original unsupported per-prefix guard|
|118515,57s|Manual V4 caller shape1441 vs721|supported by source and CPU regression; omitted current-token position IDs|Reuse existing suffix_position_ids in independent reference call|Direct cached call with full mask and omitted positions|
|118518,57s|V3 relative-L2<=.02 AND abs<=.125 assertion fails|unknown; failed scalar values not saved|Stop; preserve both failures; record metrics before assertions in a future approved repair|Looser tolerance or another unexamined GPU retry|

Two harness failures triggered a focused source/CPU diagnostic, not dose tuning.
The final numerical failure was not repaired or rerun. It says nothing about
natural Value insufficiency or intervention performance.

## Open Candidates

Fixed gain candidates remain untested. Numerical-rounding and implementation
explanations for V3 are unestablished; no cause promoted as fact.

## Next-Step Decision

- Current bottleneck: mandatory V3 validity failure.
- Relevant memory item used: both118518 worker failure files and plan§15.
- Chosen next action: STOP and preserve explicit not-run outputs and report.
- Why this action: the approved plan prohibits science after a failed validity
  check; CPU tests do not substitute for GPU decomposition evidence.
- What not to repeat: change tolerances, choose doses, regenerate cohorts or
  interpret missing performance results as a scientific null.
- Stop condition: reached. One recommendation is a separately resumed bounded
  decomposition diagnosis/repair followed by V1–V6. No follow-up launched.

### Step Result

- Action taken: prepared input-independent cohorts and technical intervention,
  tested on exactly2 node02 GPUs, honored V3 stop.
- Result:0 scientific trajectories; dev/test/timing/audit unmeasured.
- Evidence saved: outputs/stage8c_v2/v1/stage8c_v2_summary.md; technical validation,
  three attempt logs/configs, explicit not-run outputs and final verification.
- Failure or issue: V3 fails; numerical magnitudes unavailable, cause unknown.
- Lesson learned: validation must serialize measured errors before asserting;
  absence of a technical pass cannot be replaced by plausible BF16 reasoning.
- Next implication: preserve frozen inputs and await next user instruction. All
  GPUs released; no current ETA. Updated {at}.
''')

p = Path('plan/stage8c_v2_execution_checklist.md')
s = p.read_text()
s = s.replace('- [ ] Audit all relevant prior items and visual-family aliases.',
              '- [x] Audit identified prior items and visual-family aliases; limitations recorded.')
s = s.replace('- [ ] Freeze diverse dev128/test512, timing256, semantic audit128 and provenance.',
              '- [x] Freeze dev128/test512, timing256, semantic audit128 and provenance.')
s = s.replace('- [ ] Implement and test gain, cache rollback and frozen online trigger.',
              '- [x] Implement gain/cache/trigger;10 CPU tests pass. GPU numerical validity still fails.')
s = s.replace('- [ ] Submit V1–V6 on exactly2 node02 GPUs; all must pass.',
              '- [x] Submit technical audit on exactly2 node02 GPUs; preserve three attempts.\n'
              '- [ ] V1–V6 all pass: **NO — V3 FAILED; STOP.**')
s = s.replace('- [ ] Final outputs/figures, one recommendation, resource release and STOP.',
              '- [x] Technical-stop report, explicit not-run artifacts, one recommendation and resource release.\n'
              '- [ ] Scientific figures/results: not generated; prerequisite gate failed.')
p.write_text(s+f'\nStop timestamp:{at}. No development/held-out/timing/semantic results. '
             'Validation error magnitudes were not serialized; cause unknown. All original configs '
             'and prior-stage hashes preserved.\n')

for name, prefix in {
    'workspace/research_plan.md': f'**CURRENT — Stage8C v2 STOP at technical V3 ({at}).** '
        'Frozen dev128/test512 and subsets preserved. Both audited prefixes fail predeclared BF16 visual '
        'decomposition tolerance; zero scientific runs, no dose. All GPUs released. '
        '[Report](../outputs/stage8c_v2/v1/stage8c_v2_summary.md). No Block3B or follow-up launched.\n\n',
    'workspace/env_state.md': f'**CURRENT — Stage8C v2 technical STOP ({at}).** '
        'Slurm118514/118515/118518 terminal/released; each used2 node02 A6000s/8CPUs/100G. '
        'Total195 allocated seconds,0.1083 GPUh. Existing .venv, BF16 model and local data reused; '
        'no installation/download. No active stage allocation.\n\n',
    'workspace/dataset_inventory.md': f'**Stage8C v2 input freeze complete ({at}).** '
        'Existing3040 MathVision images/Arrow reused and hashed.575 prior item IDs excluded before '
        'family expansion;2,147 eligible representatives. Frozen128 development/512 held-out '
        'independent identified families plus timing/review subsets.15 realized subjects,5 levels; '
        'metadata limitations recorded. No download; scientific generation0 due technical stop. '
        'Provenance:`outputs/stage8c_v2/v1/audit/input_inventory.json`.\n\n'
}.items():
    p=Path(name);p.write_text(prefix+p.read_text())

p=Path('workspace/decision_log.md')
p.write_text(p.read_text()+f'''

## D-086 — Stage8C v2 technical V3 stop preserves untested scientific scope

{at}. Two initial validation-harness errors were repaired using native trace
coverage and a focused CPU position-ID reproduction. The third2-GPU/node02 run
118518 reached the numerical visual-decomposition assertion and failed on both
initial prefixes. Preserve the predeclared relative-L2.02/abs.125 bounds; no
further retry or science. Exact failure magnitudes were not serialized, so cause
is unknown. Gain/no-op/cache comparisons preceding the failure do not establish
a complete V1–V6 pass. Frozen128/512 cohorts and prior-stage evidence remain
unchanged.0 scientific trajectories, no dose, no efficacy conclusion;0.1083 GPUh,
all allocations released. One recommendation: bounded decomposition diagnosis
and repair followed by full revalidation. No follow-up or Block3B launched.
Evidence:`outputs/stage8c_v2/v1/stage8c_v2_summary.md` and technical validation.
''')

files=[ROOT/'audit/technical_stop_freeze.json',ROOT/'audit/final_verification.json',
       Path('workspace/phase_memory/phase_8c_v2_visual_gain.md'),Path('plan/stage8c_v2_execution_checklist.md')]
files += list(Path('code/visual_reasoning/stage8c').rglob('*.py')) + list(Path('scripts/stage8c').glob('*'))
save(ROOT/'audit/completion_seal.json',dict(at=at,status='STOP_TECHNICAL_V3',
     hashes={str(p):sha(p) for p in files if p.is_file()}))
print('Technical stop documented; resources and stage state synchronized.')
