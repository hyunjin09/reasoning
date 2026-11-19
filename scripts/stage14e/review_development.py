"""Source-only packets and immutable freeze for the completed revised diagnostic."""
import argparse
import json
from scripts.stage14e.common import P, load, rows, save, sha, now


def main(attempt):
    root = P / 'raw' / attempt
    assert load(root / 'result.json')['status'] == 'COMPLETED'
    states = load(root / 'ledger_states.json')
    execution = load(root / 'read_execution_manifest.json')['logical']
    families = {r['item_id']: r for r in rows(P / 'inference/diagnostic_families.jsonl')}
    refs = {r['item_id']: r['E_star_atoms'] for r in rows(
        'outputs/stage14d0/inventory/source_and_raw_output_manifest.jsonl')}
    files = {str(p): sha(p) for p in root.rglob('*.json')
             if 'snapshot_history' not in str(p) and p.name not in ['progress.json', 'allocation_progress.json']}
    save(P / 'audit' / (attempt + '_raw_freeze.json'), {'at': now(), 'files': files})
    ids = list(states)
    for block in range((len(ids) + 5) // 6):
        lines = []
        for i in ids[block*6:(block+1)*6]:
            r = families[i]
            lines.extend([f"ID {i} IMAGE {r['image']}", 'QUESTION ' + r['question'],
                          'SOURCE ' + json.dumps(refs[i], ensure_ascii=False), 'PREFIX ' + r['prefix'],
                          'CONTROLLER ' + json.dumps(states[i], ensure_ascii=False)])
            for x in [x for x in execution if x['item_id'] == i]:
                raw = load(x['generation_path'])['raw_decoded_response'] if x['generation_path'] else 'NO READOUT'
                lines.append(x['condition'] + ' ' + x['status'] + ' ' + raw)
        path = P / 'analysis' / f'{attempt}_review_{block}.txt'
        with path.open('x') as f:
            f.write('\n\n'.join(lines))
    print('Frozen', len(files), 'files; packets', (len(ids) + 5) // 6)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('attempt')
    main(parser.parse_args().attempt)
