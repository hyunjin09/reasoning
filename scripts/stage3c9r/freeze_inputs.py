#!/usr/bin/env python3
"""Freeze existing inputs and same-path choices before any repair scoring."""

import argparse
import copy
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage3c9.assay import exact_readout_sequences
from visual_reasoning.stage3c9r.protocol import shared_partition

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/stage3c9r'
OLD = ROOT / 'outputs/stage3c9'


def read_json(path):
    return json.loads(Path(path).read_text())


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row, allow_nan=False) + '\n' for row in rows))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allocation', required=True)
    args = parser.parse_args()
    if OUT.exists():
        raise FileExistsError('Refusing to overwrite a Stage 3C.9R freeze')
    hashes = {}
    events, spans, neighbors, readouts = [], [], [], []
    bases = {}
    for role, expected in [('primary', 48), ('validation', 8)]:
        path = OLD / f'cohort/{role}_manifest.jsonl'
        rows = read_jsonl(path)
        assert len(rows) == expected
        bases[role] = [str(r['base_problem_id']) for r in rows]
        destination = OUT / f'cohort/{role}_manifest.jsonl'
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        hashes[str(path.relative_to(ROOT))] = sha(path)
        for item in rows:
            assert len(item['events']) == 3
            edit = read_json(ROOT / item['edit_metadata'])
            for name in [item['tokens_path'], item['edit_metadata'], *edit['paths'].values()]:
                path = ROOT / name
                path.resolve().relative_to(ROOT)
                hashes[str(path.relative_to(ROOT))] = sha(path)
            tokens = read_jsonl(ROOT / item['tokens_path'])
            exact_readout_sequences(tokens, item['final_use_readout'])
            for event in item['events']:
                exact_readout_sequences(tokens, event['local_use_readout'])
                shared_partition(event, end=event['local_use_readout']['token_index'])
                identity = {'base_problem_id': str(item['base_problem_id']),
                            'event_id': event['event_id'], 'cohort_role': role}
                events.append({**identity, **event})
                spans.append({**identity, **{k: event[k] for k in ('span_start_token', 'span_end_token', 'span_text')}})
                neighbors.append({**identity, **event['matched_neighbor_span']})
                readouts.append({**identity, 'local_use': event['local_use_readout'], 'final_use': item['final_use_readout']})
    assert not set(bases['primary']) & set(bases['validation'])
    for name, rows in [('events', events), ('event_spans', spans), ('neighbors', neighbors), ('readouts', readouts)]:
        write_jsonl(OUT / f'cohort/frozen_{name}.jsonl', rows)
    # All earlier Stage 3C.9 artifacts are immutable, including raw scientific scores.
    hashes.update({str(path.relative_to(ROOT)): sha(path) for path in OLD.rglob('*') if path.is_file()})
    config = copy.deepcopy(read_json(OLD / 'config/stage3c9_config.json'))
    config.update({'stage': '3C.9R', 'frozen_at': datetime.now(timezone.utc).isoformat(),
                   'source_plan': 'plan/stage3c9r_plan.md',
                   'source_plan_sha256': sha(ROOT / 'plan/stage3c9r_plan.md'),
                   'implementation_plan': 'workspace/stage3c9r_implementation_plan.md',
                   'implementation_plan_sha256': sha(ROOT / 'workspace/stage3c9r_implementation_plan.md')})
    config['runtime']['slurm_allocation'] = args.allocation
    config['runtime'].pop('clean_restart', None)
    config['runtime']['dtype'] = 'bfloat16'
    config['runtime']['vision_attention'] = 'sdpa'
    path = {**config['runtime']['canonical_scoring'],
            'partition': 'union_of_every_frozen_event_and_neighbor_token_end',
            'all_semantic_and_sham_arms_share_partition': True,
            'recipient': 'one_suppressed_execution_with_exact_CPU_cache_forks',
            'copying_changes_dtype': False, 'condition_or_example_path_switching': False}
    config['same_path'] = path
    config['optional_necessity'] = {'minimum_robust_events': 4, 'robust_effect_floor': .15,
                                    'definition': 'unique C2/C3 events passing at 0.15 with all other rules fixed'}
    write_json(OUT / 'config/stage3c9r_config.json', config)
    write_json(OUT / 'config/canonical_path.json', path)
    write_json(OUT / 'config/checkpoint_rules.json', {
        'implementation': 'visual_reasoning.stage3c9.analysis.classify_checkpoint',
        'implementation_sha256': sha(ROOT / 'code/visual_reasoning/stage3c9/analysis.py'),
        'primary_effect_floor': .05, 'RR_median_floor': .25,
        'source': 'O/C nonnegative, mean >= floor and > mean absolute sham source effect',
        'rescue': 'O/C positive, mean >= floor, median RR >= .25, mean > neighbor mean',
        'C3': 'C2 plus distinct-final O/C positive and mean >= floor',
        'repeated': 'two nonoverlapping C2/C3 events, start separation >=24',
        'scientific_pre_gate': False,
    })
    write_json(OUT / 'config/sensitivity_grid.json', {'floors': [.025, .05, .10, .15],
               'primary': .05, 'change_only_effect_floor': True, 'after_primary_freeze': True})
    write_json(OUT / 'config/immutable_inputs.json', {'sha256': hashes, 'base_ids': bases,
               'primary_events': 144, 'validation_events': 24, 'old_artifact_file_count': len(hashes)})
    print(json.dumps({'frozen': True, 'hashes': len(hashes), 'primary': 48, 'validation': 8}))


if __name__ == '__main__':
    main()
