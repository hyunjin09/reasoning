"""Release one retained benchmark after verified gates and prior native reviews."""
import re

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha
from scripts.stage7a_bench.completed_screen_v7 import load_completed_screen
from scripts.stage7a_bench.mathwild_gate_checkpoint_v6 import verify_mathwild_gate

OUT = ROOT / 'outputs/stage7a_bench_v2'
EXPECTED_COUNTS = {
    'mathvision_wild': {'photo': 200, 'screenshot': 64},
    'mmmu_pro': {'image_present': 200, 'silent_no_image': 64, 'explicit_guess': 64},
    'mmlongbench_doc': {'image_present': 200},
}


def select_retained_rows(rows, selection, run_id):
    benchmark = selection.get('benchmark')
    if benchmark not in EXPECTED_COUNTS:
        raise ValueError('Only the three retained remaining benchmarks may be released')
    if selection.get('status') != 'FROZEN_REDUCED_REMAINDER':
        raise ValueError('An explicit frozen reduced release is required')

    def verified(ref, directory):
        path = (ROOT / ref['path']).resolve()
        if not path.is_relative_to(directory) or sha(path) != ref['sha256']:
            raise ValueError('Release evidence path or frozen hash changed')
        return path

    authority = read_json(OUT / 'config/mathwild_gate96_selection_v5.json')['amendment']
    if selection['amendment'] != authority:
        raise ValueError('Release differs from the user-approved scope amendment')
    verified(authority, ROOT / 'plan')
    gate = verify_mathwild_gate(selection['mathwild_gate'])
    passed = gate['decision'] == 'CONTINUE_FROZEN_MATHWILD_SAMPLE'
    if gate['decision'] not in ('CONTINUE_FROZEN_MATHWILD_SAMPLE', 'STOP_MATHWILD_LOW_YIELD'):
        raise ValueError('MathWild feasibility remains unresolved')
    if benchmark == 'mathvision_wild' and not passed:
        raise ValueError('MathWild stopped at its fixed96-review gate')
    required = [] if benchmark == 'mathvision_wild' or not passed else ['mathvision_wild']
    if benchmark == 'mmlongbench_doc':
        required.append('mmmu_pro')
    if set(selection['prerequisites']) != set(required):
        raise ValueError('All preceding retained native screens require complete reviewed coverage')
    for name in required:
        bindings = read_json(verified(selection['prerequisites'][name], OUT / 'config'))
        load_completed_screen(name, bindings)

    freeze = read_json(OUT / 'cohort/sample_freeze.json')['native_screen']
    specs = {key[len(benchmark)+1:]: value for key, value in freeze.items()
             if key.startswith(benchmark+'_')}
    if {key: value['count'] for key, value in specs.items()} != EXPECTED_COUNTS[benchmark]:
        raise ValueError('Original retained sample sizes and conditions must be preserved')
    if selection['manifests'] != {value['manifest']: value['sha256'] for value in specs.values()}:
        raise ValueError('Every original retained condition manifest must be frozen')
    full, allowed = {}, []
    for condition, spec in specs.items():
        path = verified(dict(path=spec['manifest'], sha256=spec['sha256']),
                        OUT / 'cohort/benchmark_manifests')
        items = full[condition] = read_jsonl(path)
        if (len(items) != spec['count'] or any(row['benchmark'] != benchmark or
                row['condition'] != condition for row in items)):
            raise ValueError('Native input differs from its frozen benchmark condition')
        allowed.extend(items[96:] if benchmark == 'mathvision_wild' and condition == 'photo' else items)
    by_id = {row['event_id']: row for row in allowed}
    batches = selection['batches']
    names = [batch['run_id'] for batch in batches]
    ids = [event for batch in batches for event in batch['event_ids']]
    if (len(by_id) != len(allowed) or len(names) != len(set(names)) or
            any(not re.fullmatch(r'[a-z0-9_]+', name) for name in names) or
            len(ids) != len(set(ids)) or set(ids) != set(by_id) or names.count(run_id) != 1):
        raise ValueError('Release would omit, repeat or exceed the retained frozen remainder')
    selected = None
    for batch in batches:
        members = set(batch['event_ids'])
        ordered = [row for row in allowed if row['event_id'] in members]
        if (not ordered or len({row['condition'] for row in ordered}) != 1 or
                batch['event_ids'] != [row['event_id'] for row in ordered]):
            raise ValueError('Each batch must preserve frozen order within one separate condition')
        if batch['run_id'] == run_id:
            if rows != full[ordered[0]['condition']]:
                raise ValueError('Worker must load its complete exact condition manifest before selection')
            selected = ordered
    return selected
