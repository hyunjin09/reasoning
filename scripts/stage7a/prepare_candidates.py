"""Freeze a finite source-only candidate order and local dataset provenance."""
import hashlib
import itertools
import random
from collections import Counter
from pathlib import Path
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha
from scripts.stage6a.inventory import allowed


def main():
    # Required lookup sequence: inspect the project link first, then local roots.
    link = ROOT / 'datasets'
    link_status = str(allowed(link)) if link.exists() or link.is_symlink() else 'absent'
    old_inventory = read_json(ROOT / 'outputs/stage6a/cohort/dataset_inventory.json')
    local = []
    for dataset in old_inventory['datasets']:
        if dataset['dataset'] not in ['MathVerse', 'MathVision', 'MathVista', 'DocVQA', 'POPE', 'COCO2014']:
            continue
        files = [s['path'] for c in dataset.get('candidates', []) for s in c['arrow_shards']]
        files += [dataset[k] for k in ['annotations', 'instance_annotations', 'caption_annotations'] if k in dataset]
        checked = []
        for raw in files:
            resolved = allowed(raw)
            if not resolved.is_file():
                raise FileNotFoundError(resolved)
            checked.append(dict(path=str(resolved), size_bytes=resolved.stat().st_size))
        local.append(dict(dataset=dataset['dataset'], usable=True, checked_files=checked,
                          previous_inventory_provenance='outputs/stage6a/cohort/dataset_inventory.json'))
    write_json(OUT / 'cohort/dataset_inventory.json', dict(
        lookup_order=[{'project_datasets_link': link_status}, '/data/dataset',
                      'HF cache aliases resolve into /data/dataset; additional lookup not needed'],
        datasets=local, downloads=[], external_writes=False), freeze=True)
    inventory_path = ROOT / 'workspace/dataset_inventory.md'
    entry = ('\n\n## Stage7A lookup — 2026-09-10\n\n'
             'The project datasets link is ' + link_status + '. Required MathVerse, MathVision, MathVista, '
             'DocVQA, POPE and COCO2014 files were rechecked under `/data/dataset` '
             '(including resolved existing HF cache aliases). All required local sources are present; '
             'no download or external write. Exact paths/sizes: '
             '`outputs/stage7a/cohort/dataset_inventory.json`. Freshness is audited separately from availability.\n')
    if '## Stage7A lookup' not in inventory_path.read_text():
        inventory_path.write_text(inventory_path.read_text() + entry)

    historical = read_jsonl(ROOT / 'outputs/stage6a/audit/source_identity_catalog.jsonl')
    excluded = {r['base_id'].removeprefix('historical_') for r in historical}
    doc_ids = {r['source_image_id'] for r in historical if r['dataset'] == 'DocVQA'}
    rows = read_jsonl(ROOT / 'outputs/stage6a/cohort/semantic_candidate_order.jsonl')
    rows = [r for r in rows if r['base_id'] not in excluded
            and not (r['dataset'] == 'DocVQA' and r['metadata']['docId'] in doc_ids)]
    pools = {}
    for dataset in ['MathVerse', 'MathVision', 'MathVista', 'DocVQA']:
        pool = [r for r in rows if r['dataset'] == dataset]
        random.Random(70910).shuffle(pool)
        # Source-only editability priority: localized tables, then geometry.
        if dataset == 'MathVista':
            pool.sort(key=lambda r: r.get('metadata', {}).get('source') != 'TabMWP')
        pools[dataset] = pool
    c1 = [r for group in itertools.zip_longest(*(pools[d] for d in ['MathVista', 'MathVision', 'MathVerse']))
          for r in group if r is not None][:240]
    selected = [dict(**r, cohort='C1') for r in c1]
    selected += [dict(**r, cohort='C2') for r in pools['DocVQA'][:96]]
    for order, row in enumerate(selected):
        row['stage7a_candidate_order'] = order
        row['selection_used_model_outputs'] = False
        row['review_status'] = 'pending source/ROI/truth and historical image identity review'
    write_jsonl(OUT / 'cohort/source_candidate_order.jsonl', selected, freeze=True)
    write_json(OUT / 'audit/historical_exclusion_registry.json', dict(
        source='outputs/stage6a/audit/source_identity_catalog.jsonl',
        source_sha256=sha(ROOT / 'outputs/stage6a/audit/source_identity_catalog.jsonl'),
        base_ids=sorted(excluded), doc_ids=sorted(doc_ids),
        conservative_scope='Exclude every catalogued source, including unused reservations; pixel/near-image check remains required.'), freeze=True)
    print(dict(Counter(r['dataset'] for r in selected)))


if __name__ == '__main__':
    main()
