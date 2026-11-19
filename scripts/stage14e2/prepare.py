"""Freeze matched readout contrasts and diagnostic-only value-free target names."""
from pathlib import Path
from scripts.stage14e2.common import P, PREVIOUS, load, save, sha, rows, now
from scripts.stage14e.contracts_v2 import reader_prompt


def main():
    ids = load(PREVIOUS/'manifests/diagnostic_v1c.json')['families']
    families_path = PREVIOUS/'inference/diagnostic_families.jsonl'
    families = {r['item_id']:r for r in rows(families_path)}
    old_path = PREVIOUS/'inference/original_targets.json'
    original = load(old_path)
    target_path = PREVIOUS/'inference/diagnostic_target_identities.json'
    targets = load(target_path)
    replacements = {
        '52': 'Read the wall segments and openings around the chambers containing O and E. Locate their positions relative to the circular walls. Do not choose a reachable answer.',
        '333': 'Read the shading of the regions formed by the drawn circles. Identify each region by the circle boundaries surrounding it. Do not compute an area.',
        '641': 'Read the sequence and orientation of the fish along the drawn cord from the ring toward the free end. Identify fish by their visible position and color, and trace the drawn strand. Do not give the final total.',
        '1067': 'Read the relative positions and incidences of the labeled points and edges of the square and rectangle. Identify the boundaries of the shaded region. Do not derive a length.',
        '2471': 'Read the relative positions of the square and rectangle edges and labeled endpoints. Identify the boundaries of their shaded regions. Do not calculate the requested ratio.',
        '2702': 'Read the positions of white and black tiles in the displayed floor using row and column positions. Do not extrapolate to a larger floor.',
        '2924': 'Read the endpoints of the drawn octagon diagonals and the boundaries around the shaded region. Use visible labels or consistent clockwise vertex positions. Do not calculate an area.'}
    for i, query in replacements.items():
        targets[i]['query'] = query
    save(P/'inference/diagnostic_targets_v1.json', targets)
    save(P/'audit/target_only_QC_v1.json', dict(at=now(), reviewed_ids=ids,
        prior_source_path=str(target_path), prior_source_sha256=sha(target_path),
        replaced_queries=replacements, reviewer='Main AI agent; no independent human certification',
        rule='Specify entities/properties to read; no expected numerical values, asserted relation outcomes, corrective anti-pattern hints or solved quantities.',
        limitations='Source-informed target selection is diagnostic assistance, never deployable input. Same fixed query in every matched T condition.',
        outcomes_of_new_diagnostic_exist=False, prior_development_outcomes_observed=True))
    tasks = []
    for i in ids:
        r = families[i]
        for arm in ['O_C', 'O_T', 'T_C', 'T_T', 'T_N']:
            target = original[i] if arm.startswith('O') else targets[i]
            item = dict(item_id=i, condition=arm, cap=8192,
                helper_mode='compact' if arm.endswith('_C') else 'thinking',
                diagnostic_oracle_target=arm.startswith('T'),
                seed=r['seed'], images=[] if arm=='T_N' else [r['image']],
                status='PHYSICAL' if target['status']=='QUERY' else 'ABSENT_ORIGINAL_TARGET')
            if item['status']=='PHYSICAL':
                item['prompt'] = reader_prompt(r, target, with_prefix=True)
                item['prompt_sha256'] = __import__('hashlib').sha256(item['prompt'].encode()).hexdigest()
            tasks.append(item)
    assert len(tasks)==120 and sum(t['status']=='PHYSICAL' for t in tasks)==108
    index = {(t['item_id'],t['condition']):t for t in tasks}
    for i in ids:
        for a,b in [('O_C','O_T'),('T_C','T_T'),('T_T','T_N')]:
            for field in ['prompt_sha256','seed','cap']:
                assert index[i,a].get(field)==index[i,b].get(field)
    save(P/'inference/diagnostic_tasks_v1.json', dict(at=now(), rows=tasks,
        families=ids, logical=120, physical=108, no_final_answer_outcomes_used=True))
    runtime = load(PREVIOUS/'protocol/runtime_v1.json')
    runtime['runtime'].update(max_model_len=16384,max_num_seqs=4)
    runtime.update(helper_mode='Prospectively matched open/closed thinking; unconstrained decoding in both',
        protocol_version='stage14e2_readout_mechanism_v1')
    runtime['caps']['read']=8192
    save(P/'protocol/runtime_v1.json',runtime)
    manifest_paths=[]
    for rank in range(2):
        path=P/f'manifests/readout_r{rank}_v1.json'
        save(path,dict(id=f'readout_r{rank}_v1',families=ids[rank::2],rank=rank,gpus=1,gpu_type='a6000',
            wall_seconds=172800,budget_reservation_seconds=10800,
            expected_gpu_hours=[.5,1.2],hard_total_cycle_gpu_seconds=86400,
            runtime=str(P/'protocol/runtime_v1.json'),families_path=str(families_path),
            tasks_path=str(P/'inference/diagnostic_tasks_v1.json'),
            seal=str(P/'audit/diagnostic_seal_v1.json'),
            budget_grant_path=str(P/f'audit/readout_r{rank}_budget_grant.json')))
        manifest_paths.append(str(path))
    files=[str(p) for p in Path('scripts/stage14e2').glob('*.py')]
    files += ['scripts/stage14e/run.sh','scripts/stage14e/resource_guard.py',
        'scripts/stage14e/contracts_v2.py','scripts/stage14d1/contracts.py',str(families_path),
        str(old_path),str(P/'inference/diagnostic_targets_v1.json'),str(P/'inference/diagnostic_tasks_v1.json'),
        str(P/'protocol/runtime_v1.json'),'plan/stage14e2_deliberative_source_reading_plan_v1.md']+manifest_paths
    save(P/'audit/diagnostic_seal_v1.json',dict(at=now(),files={f:sha(f) for f in files},
        primary='T_T minus T_C useful source-correct acquisition',
        secondary=['O_T minus O_C','T_T minus T_N','whole-source coverage','explicit errors'],
        no_new_diagnostic_outcomes_exist=True))
    print('Frozen24families/120logical/108physical reads; two single-GPU shards')


if __name__=='__main__':
    main()
