"""Immutable source-review packets for families with every matched receipt ready."""
import argparse
import json
from pathlib import Path
from scripts.stage14e2.common import P, PREVIOUS, load, rows, save, sha, now
from scripts.stage14e2.contracts import parse_readout


def main(batch):
    (P/'analysis').mkdir(exist_ok=True)
    seen = set()
    for path in (P/'analysis').glob('source_packet_*_v1.json'):
        seen.update(r['item_id'] for r in load(path)['families'])
    definition = load(P/'inference/diagnostic_tasks_v1.json')
    families = {r['item_id']:r for r in rows(PREVIOUS/'inference/diagnostic_families.jsonl')}
    refs = {r['item_id']:r for r in rows('outputs/stage14d1_sava_pilot/v1/data/offline_source_manifest.jsonl')}
    source = {r['item_id']:r for r in rows('outputs/stage14d0/inventory/source_and_raw_output_manifest.jsonl')}
    manifests = [load(P/f'manifests/readout_r{rank}_v1.json') for rank in range(2)]
    ready = []
    for i in definition['families']:
        if i in seen:
            continue
        attempt = next(m['id'] for m in manifests if i in m['families'])
        task_rows = [t for t in definition['rows'] if t['item_id']==i]
        paths = {t['condition']:P/'raw'/attempt/(i+'_'+t['condition'])/'generation.json'
            for t in task_rows if t['status']=='PHYSICAL'}
        if not all(p.with_name('result.json').exists() for p in paths.values()):
            continue
        outputs = []
        for t in task_rows:
            path = paths.get(t['condition'])
            if path:
                g = load(path)
                assert sha(path)==load(path.with_name('result.json'))['generation_sha256']
                parsed = parse_readout(g['raw_decoded_response'],t['helper_mode'],g['cap_hit'])
                outputs.append(dict(condition=t['condition'],generation_path=str(path),generation_sha256=sha(path),
                    tokens=g['tokens'],cap_hit=g['cap_hit'],**parsed))
            else:
                outputs.append(dict(condition=t['condition'],generation_path=None,status='ABSENT_ORIGINAL_TARGET',parsed=None))
        row = families[i]
        ready.append(dict(item_id=i,family_id=row['family_id'],image=row['image'],image_sha256=row['image_sha256'],
            question=row['question'],prefix=row['prefix'],prefix_sha256=row['prefix_sha256'],
            E_star_atoms=source[i]['E_star_atoms'],source_stratum=refs[i]['audit_context_stratum'],
            source_reference='outputs/stage14d0/inventory/source_and_raw_output_manifest.jsonl',outputs=outputs))
    assert ready,'No new complete matched families'
    save(P/f'analysis/source_packet_{batch:02d}_v1.json',dict(at=now(),families=ready,
        gold_or_final_accuracy_used=False,no_scientific_method_change_during_diagnostic=True))
    text=[]
    for r in ready:
        text += ['ID '+r['item_id']+' IMAGE '+r['image'],'QUESTION '+r['question'],
            'SOURCE '+json.dumps(r['E_star_atoms'],ensure_ascii=False),'PREFIX '+r['prefix']]
        for o in r['outputs']:
            text.append(o['condition']+' '+o['status']+' '+json.dumps(o.get('parsed'),ensure_ascii=False))
    with (P/f'analysis/source_packet_{batch:02d}_v1.txt').open('x') as out:
        out.write('\n\n'.join(text)+'\n')
    print('Ready matched family packets:',[r['item_id'] for r in ready])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('batch',type=int)
    main(parser.parse_args().batch)
