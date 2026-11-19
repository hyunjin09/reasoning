"""Freeze lineage and identities before source-prefix review or target generation."""
import hashlib
import pandas as pd
from pathlib import Path
from scripts.stage12us.common import ROOT, load, save, sha, now
from scripts.stage12ts.review import all_tasks as thinking_tasks, folder_for as thinking_folder
from scripts.stage12cr.review import folder_for as cot_folder


def main():
    plan = Path('plan/stage12us_reasoning_state_production_vs_utilization_plan.md')
    assert not ROOT.exists(), 'Never overwrite a prepared study'
    df = pd.read_parquet('outputs/stage12ts/v1/stage12ts_cot_thinking_transitions.parquet')
    selected = df[(df.bottleneck.isin(['B4', 'B1'])) & (df.c == False) & (df.t == True)]
    primary = selected[selected.bottleneck == 'B4'].to_dict('records')
    secondary = selected[selected.bottleneck == 'B1'].to_dict('records')
    assert len(primary) == 5 and len(secondary) == 2
    remaining = df[~df.family_id.isin(selected.family_id)].to_dict('records')
    technical = sorted(remaining, key=lambda r: hashlib.sha256(
        ('stage12us-v1|technical|' + r['family_id']).encode()).hexdigest())[:2]
    identity_keys = ['item_id', 'family_id', 'bottleneck', 'subject', 'level', 'answer_type']
    cohorts = {name: [{k: r[k] for k in identity_keys} for r in rows]
               for name, rows in [('primary', primary), ('secondary', secondary), ('technical', technical)]}
    historical = {}
    for stage in ['stage12b', 'stage12br', 'stage12bs', 'stage12c', 'stage12cr', 'stage12ts']:
        for p in sorted(Path('outputs', stage, 'v1').rglob('*')):
            if p.is_file(): historical[str(p)] = sha(p)
    save(ROOT/'audit/preserved_history.json', {'at': now(), 'files': historical})
    save(ROOT/'audit/cohorts.json', {'at': now(), 'cohorts': cohorts,
         'technical_selection': 'First two SHA256(stage12us-v1|technical|family_id) among remaining54; no correctness filter.'})
    facts = {r['item_id']: r['facts'] for r in load('outputs/stage12c/v1/stage12c_frozen_bottleneck_manifest.json')['rows']}
    tt = {t['item_id']: t for t in thinking_tasks()}
    ct = {t['item_id']: t for t in load('outputs/stage12cr/v1/stage12cr_cot_manifest.json')['tasks']}
    for cohort, rows in cohorts.items():
        for row in rows:
            item = row['item_id']
            for source, task, folder in [('T', tt[item], thinking_folder(tt[item])), ('C', ct[item], cot_folder(ct[item]))]:
                g = load(folder/'generation.json')
                receipt = load(folder/'result.json')
                assert receipt['generation_sha256'] == sha(folder/'generation.json')
                save(ROOT/'audit/source_packets'/f'{source}_{item}.json', dict(
                    cohort=cohort, **row, source=source, question=tt[item]['prompt'], facts=facts[item],
                    generation_path=str(folder/'generation.json'), generation_sha256=sha(folder/'generation.json'),
                    raw=g['raw_decoded_response']))
    save(ROOT/'audit/initial_freeze.json', dict(at=now(), plan_path=str(plan), plan_sha256=sha(plan),
         historical_files=len(historical), cohorts_sha256=sha(ROOT/'audit/cohorts.json'),
         no_stage12us_generation=True, original_plan_preserved=True,
         selected_action='Execute only Stage12U-S with two technical families before primary generation; hard7GPUh.'))
    if Path('reports/index.md').exists():
        (ROOT/'audit/reports_index_before.md').write_text(Path('reports/index.md').read_text())
    phase = Path('workspace/phase_memory/phase_12us_reasoning_state_transfer.md')
    phase.write_text(f'''# Phase12U-S: Externalized reasoning-state production vs utilization

## Current Objective
Execute the approved image-free 2x2 reasoning-prefix transfer study, then stop.

## Active Constraints
Preserve prior B-S/C-R/T-R/T-S evidence. Five B4 primary and two B1 descriptive families; source traces never regenerated. Answer-safe prefixes and content labels sealed before transfers. Three fixed seeds per scientific condition. Original question; assistant continuation; no image. Target<5/hard7 allocated GPUh; no hidden-state intervention or follow-on.

## Current State
- Done: policy, plan and prior closure read; cohort identities and historical hashes frozen {now()}.
- In progress: exhaustive source-prefix review and native-template injection implementation.
- Blocked: none.

## Evidence That Matters
D144: all five B4 Thinking rescues fail under CoT and prior E* oracle. This establishes the targeted cohort, not the mechanism. Two B1 T-only cases are descriptive. Prior review was partial; this stage independently audits the complete retained prefixes.

## Failed Attempts and Lessons
No new attempt yet. R1-R4 and cap hits do not automatically mean incorrect answers; preserve technical missingness. Model recipes differ; interpretation is intended-checkpoint regimes rather than a pure Thinking switch.

## Open Candidates
Production, utilization, repair, text insufficiency remain open under the approved transfer matrix.

## Next-Step Decision
- Bottleneck: whether successful Thinking text is portable or the target checkpoint uses/repairs fixed text better.
- Memory: D144 downstream signal and bounded source-trace annotation limits.
- Chosen action: the fully approved Stage12U-S assay, including source audits, two-family technical gate, scientific transfers, controls, analysis and closure.
- Rationale: directly separates textual-state production from continuation behavior on the frozen discrepant families.
- Stop condition: finish required artifacts and exactly one recommendation, or stop at a failed technical gate/hard budget. No automatic next experiment.

### Step Result
Prospective identity/preservation freeze only; no Stage12U-S output exists.
''')
    for name in ['workflow_state.md', 'research_plan.md']:
        p = Path('workspace')/name
        p.write_text(f'**Stage12U-S active — {now()}:** approved 5 B4 + 2 B1 reasoning-prefix transfer study. Source audit before two-family technical gate; no generation yet; hard7GPUh. State: workspace/phase_memory/phase_12us_reasoning_state_transfer.md.\n\n'+p.read_text())
    with Path('workspace/decision_log.md').open('a') as f:
        f.write(f'\n\n## D145 — {now()}: Stage12U-S reasoning-state transfer approved\n'
                'Use the exact five frozen B4 and two B1 C−T+ families. Freeze answer-safe canonical prefixes and evidence/derivation states before image-free assistant-prefix continuation. Validate on two disjoint identity-hash-selected families. No source regeneration, decoding search or hidden-state experiment; three seeds, target<5/hard7GPUh. D144 supports cohort selection, not mechanism attribution.\n')
    print({k: [r['item_id'] for r in v] for k,v in cohorts.items()}, 'preserved', len(historical))


if __name__ == '__main__': main()
