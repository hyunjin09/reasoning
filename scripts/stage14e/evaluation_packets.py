"""Freeze acquisition receipts and prepare source-only packets before solver review."""
import argparse
import json
from pathlib import Path
from scripts.stage14e.common import P, load, rows, save, sha, now


def main(attempt):
    root = P / 'raw' / attempt
    assert load(root / 'result.json')['status'] == 'ACQUISITION_COMPLETED'
    states = load(root / 'acquisition_states.json')
    families = {r['item_id']: r for r in rows(P / 'inference/evaluation_families.jsonl')}
    source = {r['item_id']: r for r in load(P / 'offline/evaluation_source_references_v1.json')}
    assert set(states) == set(families) and len(states) == 32
    files = {str(p): sha(p) for p in root.rglob('*.json')
             if 'snapshot_history' not in str(p) and p.name not in ['progress.json', 'allocation_progress.json']}
    save(P / 'audit/evaluation_acquisition_freeze_v1.json', dict(at=now(), files=files, root=str(root)))
    ids = list(families)
    for block in range(4):
        lines = []
        for i in ids[block*8:(block+1)*8]:
            r = families[i]
            lines.extend([f"ID {i} IMAGE {r['image']}", 'QUESTION ' + r['question'],
                          'SOURCE ' + json.dumps(source[i]['E_star_atoms'], ensure_ascii=False),
                          'PREFIX ' + r['prefix']])
            for arm in ['S', 'M']:
                lines.append(arm + ' CONTROLLER ' + json.dumps(states[i][arm], ensure_ascii=False))
            for arm in ['S', 'M', 'M_noimage']:
                record = states[i]['read_plan'].get(arm)
                raw = load(record['generation_path'])['raw_decoded_response'] if record else 'NO READOUT'
                lines.append(arm + ' READ ' + raw)
        with (P / 'analysis' / f'evaluation_acquisition_packet_{block}.txt').open('x') as f:
            f.write('\n\n'.join(lines))
    print('32-family source-only packets frozen; no long solver outputs opened')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('attempt')
    main(parser.parse_args().attempt)
