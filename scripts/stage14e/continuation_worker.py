"""Frozen N/S/M long continuations; no helper reruns or oracle reference access."""
import argparse
import traceback
from pathlib import Path
from scripts.stage14e.common import P, load, rows, save, sha, now
from scripts.stage14e.engine_runtime import Engine
from scripts.stage14e.split_execution import frozen_plan, physical_order
from scripts.stage14d1.contracts import safe_payload


def run(path):
    manifest = load(path)
    for p, digest in load(manifest['seal'])['files'].items():
        assert sha(p) == digest, p
    families = {r['item_id']: safe_payload(r) for r in rows(manifest['families_path'])}
    source = Path(manifest['acquisition_root'])
    states = load(source / 'acquisition_states.json')
    original = load(source / 'solver_execution_manifest.json')['rows']
    work = [families[i] for i in manifest['families']]
    assert all(r['eligible'] for r in work)
    engine = Engine(manifest)
    root = engine.root

    def task(row, name, cap=81920, **kwargs):
        return dict(id=row['item_id'] + '_' + name, row=row, kind='solver', cap=cap, **kwargs)

    try:
        repeats = []
        for rep in ['a', 'b']:
            repeats.append(engine.calls([task(r, 'check_' + rep, 64) for r in work[:2]], width=1))
        checks = []
        for r in work[:2]:
            i = r['item_id']
            a, b = repeats[0][i + '_check_a'], repeats[1][i + '_check_b']
            checks.append(dict(item_id=i, same_tokens=a['generated_token_ids'] == b['generated_token_ids'],
                               same_input=a['prompt_token_ids'] == b['prompt_token_ids']))
        save(root / 'technical_gate.json', checks)
        assert all(x['same_tokens'] and x['same_input'] for x in checks)
        tasks, logical = [], []
        for r in work:
            i = r['item_id']
            physical, assignments = frozen_plan(i, states[i], original)
            for rid in physical_order(physical):
                arm = rid.split('_', 1)[1]
                tasks.append(task(r, arm, suffix=physical[rid], condition=arm))
            for arm, assignment in assignments.items():
                inherited = next(x for x in original if x['item_id'] == i and x['arm'] == arm)
                logical.append(dict(inherited, generation_path=str(root / assignment['physical_id'] / 'generation.json'),
                                    acquisition_root=str(source)))
        save(root / 'solver_execution_manifest.json', dict(at=now(), rows=logical, physical_count=len(tasks),
              solver_width=1, acquisition_manifest_sha256=sha(source / 'solver_execution_manifest.json')))
        engine.calls(tasks, width=1)
        save(root / 'result.json', dict(at=now(), status='COMPLETED', families=len(work),
              logical_solvers=len(logical), physical_solvers=len(tasks), total_physical_calls=engine.count))
    except BaseException as exc:
        save(root / 'failure.json', dict(at=now(), error=repr(exc), traceback=traceback.format_exc(), completed=engine.count))
        raise
    finally:
        engine.budget_check()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest')
    run(parser.parse_args().manifest)
