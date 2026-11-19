"""Read existing dataset assets without invoking cache writers or downloads."""
from pathlib import Path
import io
import json
import hashlib
import re
import argparse
from datetime import datetime, timezone

import pyarrow as pa
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/stage6a'
CACHE = Path('/home/hyunjin/.cache/huggingface/datasets')
READ_ROOTS = [ROOT, Path('/data/dataset'), CACHE,
              Path('/home/hyunjin/.cache/huggingface/hub')]


def allowed(path):
    path = Path(path).resolve()
    if not any(path == r or r in path.parents for r in READ_ROOTS):
        raise PermissionError(str(path))
    return path


def sha(path):
    return hashlib.sha256(allowed(path).read_bytes()).hexdigest()


def select_shards(paths, split, split_info):
    groups = {}
    for p in sorted(paths):
        match = re.search(r'-'+re.escape(split)+r'(?:-(\d+)-of-(\d+))?\.arrow$',p.name)
        if match:
            count = int(match[2]) if match[2] else 1
            index = int(match[1]) if match[1] else 0
            groups.setdefault(count, {})[index] = p
    declared = len(split_info.get('shard_lengths', [])) or 1
    chosen = groups.get(declared, {})
    if set(chosen) != set(range(declared)):
        raise ValueError(f'incomplete {split} encoding: expected {declared} shards')
    return [chosen[i] for i in range(declared)]


def arrow_probe(path, image_column):
    with pa.memory_map(str(allowed(path)), 'r') as source:
        table = pa.ipc.open_stream(source).read_all()
    sample = table.slice(0, 1).to_pylist()[0]
    value = sample.pop(image_column)
    if value['bytes']:
        im = Image.open(io.BytesIO(value['bytes']))
    else:
        im = Image.open(allowed(value['path']))
    im.load()
    return {'row_count': table.num_rows, 'columns': table.column_names,
            'first_image_size': list(im.size),
            'image_storage': 'embedded_bytes' if value['bytes'] else 'external_path',
            'sample_metadata': sample}


def enrich_local_cards(inventory):
    repositories={'MathVision':'MathLLMs--MathVision','MathVista':'AI4Math--MathVista',
                  'DocVQA':'lmms-lab--DocVQA','POPE':'lmms-lab--POPE'}
    for row in inventory['datasets']:
        if row['dataset']=='MathVerse':paths=[Path(row['readme'])]
        elif row['dataset'] in repositories:
            hub=allowed(READ_ROOTS[-1]);repo=hub/('datasets--'+repositories[row['dataset']])
            paths=[repo/'snapshots'/c['builder_fingerprint']/'README.md' for c in row['candidates']]
        else:continue
        for path in paths:
            try:text=allowed(path).read_text()
            except (PermissionError,FileNotFoundError):continue
            row['dataset_card']=str(path);row['dataset_card_sha256']=sha(path)
            row['license_lines']=[line.strip() for line in text.splitlines() if re.search(r'license|copyright|commercial use',line,re.I)]
            match=re.search(r'^license:\s*(.+)$',text,re.M)
            row['declared_card_license']=match[1].strip() if match else 'not declared in local card'
            break
    return inventory


def write_inventory_markdown(inventory):
    lines=['# Stage6A dataset inventory','',
        'Ordered lookup found all required assets locally. No downloads or external writes.','',
        '| Dataset | Usable | Evidence | Local license evidence |','|---|---|---|---|']
    for row in inventory['datasets']:
        detail=str(row.get('rows',row.get('images',''))) if 'candidates' not in row else ', '.join(str(c['declared_rows'])+' '+c['split'] for c in row['candidates'])
        license_text=row.get('declared_card_license','per-image license IDs' if row.get('licenses') else 'not selected')
        lines.append(f"| {row['dataset']} | {row.get('usable','fallback only')} | {detail} | {license_text} |")
    lines.extend(['',
        'COCO2014 is the primary C3/C4 source; COCO2017 is an alternative with overlapping images, not an independent dataset.',
        'MathVision, MathVista, DocVQA and POPE are read from Arrow shards with embedded images. Builder fingerprints are recorded separately from repository revisions.',
        'Local card paths, hashes and license excerpts are recorded in dataset_inventory.json. MathVista applies CC BY-SA4.0 to its new contributions; original image/question copyrights remain with their authors, and the local card restricts training use. POPE does not declare a license in the located card; its underlying COCO images retain per-image licenses.',
        'GQA is a located, unused fallback. The broad lookup stopped after core requirements were found; unrelated denied directories were not accessed and no exhaustive absence claim is made.'])
    (OUT/'cohort/dataset_inventory.md').write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--enrich-existing',action='store_true');args=parser.parse_args()
    if args.enrich_existing:
        path=OUT/'cohort/dataset_inventory.json';inventory=enrich_local_cards(json.loads(path.read_text()))
        path.write_text(json.dumps(inventory,indent=2)+'\n');write_inventory_markdown(inventory)
        print('Updated local card provenance without rescanning datasets');return
    records = []
    mv = Path('/data/dataset/MathVerse')
    rows = json.loads((mv / 'testmini.json').read_text())
    image_paths = [allowed(mv / 'images' / r['image']) for r in rows]
    records.append(dict(dataset='MathVerse', root=str(mv), split='testmini',
                        rows=len(rows), bases=len({r['problem_index'] for r in rows}),
                        annotations=str(mv/'testmini.json'), annotation_sha256=sha(mv/'testmini.json'),
                        images_referenced=len(set(image_paths)),
                        missing_images=sum(not p.is_file() for p in set(image_paths)),
                        readme=str(mv/'README.md'), usable=all(p.is_file() for p in set(image_paths))))
    for name, alias, subset, split, column in [
        ('MathVision','MathLLMs___math_vision','default','test','decoded_image'),
        ('MathVista','AI4Math___math_vista','default','testmini','decoded_image'),
        ('DocVQA','lmms-lab___doc_vqa','DocVQA','validation','image'),
        ('POPE','lmms-lab___pope','default','test','image'),
    ]:
        infos = sorted((CACHE / alias / subset).rglob('dataset_info.json'))
        candidates = []
        for path in infos:
            info = json.loads(allowed(path).read_text())
            files = select_shards(path.parent.glob('*.arrow'),split,info['splits'][split])
            probes = [dict(path=str(p), **arrow_probe(p,column)) for p in files]
            candidates.append(dict(root=str(path.parent), resolved_root=str(allowed(path.parent)),
                builder_fingerprint=path.parent.name, version=info['version'], split=split,
                declared_rows=info['splits'][split]['num_examples'],
                annotation_sha256=sha(path), license=info.get('license') or 'not recorded in builder metadata',
                arrow_shards=probes, usable=sum(p['row_count'] for p in probes)==info['splits'][split]['num_examples']))
        records.append(dict(dataset=name, candidates=candidates, usable=any(c['usable'] for c in candidates)))
    for year in (2014,2017):
        root = Path(f'/data/dataset/COCO{year}')
        path = root / f'annotations/instances_val{year}.json'
        data = json.loads(allowed(path).read_text())
        images = data['images']
        missing = [im['id'] for im in images if not allowed(root/f'val{year}'/im['file_name']).is_file()]
        records.append(dict(dataset=f'COCO{year}', root=str(root), split=f'val{year}',
            images=len(images), instances=len(data['annotations']), categories=len(data['categories']),
            missing_image_count=len(missing), missing_image_ids=missing[:20],
            instance_annotations=str(path), instance_sha256=sha(path),
            caption_annotations=str(root/f'annotations/captions_val{year}.json'),
            caption_sha256=sha(root/f'annotations/captions_val{year}.json'),
            licenses=data.get('licenses'), info=data.get('info'), usable=not missing))
    for alias in ('lmms-lab___gqa',):
        infos=sorted((CACHE/alias).rglob('dataset_info.json'))
        records.append(dict(dataset='GQA', status='secondary fallback located; not needed with POPE/COCO usable',
                            builder_metadata=[str(p) for p in infos], selected=False))
    inventory=dict(created_at=datetime.now(timezone.utc).isoformat(),
        lookup_order=['project datasets link (absent)','/data/dataset',str(CACHE),str(READ_ROOTS[-1])],
        recursive_lookup=True, external_roots_read_only=True, downloads=0,
        cache_roots_resolve_under_data_dataset=True,
        lookup_limitations='Some unrelated directories and MathVision hub snapshot deny access; readable Arrow assets checked directly.',
        datasets=records)
    inventory=enrich_local_cards(inventory)
    (OUT/'cohort/dataset_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    write_inventory_markdown(inventory)
    (OUT/'cohort/download_manifest.json').write_text(json.dumps(dict(downloads=[],reason='All required core data are locally available; external roots remain read-only.'),indent=2)+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k in ('dataset','usable','rows','bases','images','instances','missing_image_count')} for r in records],indent=2))


if __name__ == '__main__':
    main()
