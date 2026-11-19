"""Freeze outcome-independent Stage8C v2 inputs; reuse existing external data."""
import hashlib
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage8c.cohort import image_signature, family_groups, proportional_sample, distribution

ROOT = Path('outputs/stage8c_v2/v1')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(obj, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def main():
    assert not Path('datasets').exists() and not Path('datasets').is_symlink()
    source = Path('outputs/stage8b/v2/cohort/census_manifest_v1.jsonl')
    rows = [json.loads(x) for x in source.read_text().splitlines()]
    assert len(rows) == 3040
    inventory = json.loads(Path('outputs/stage8b/audit/input_inventory.json').read_text())
    assert sha(inventory['source']) == inventory['source_sha256']
    excluded, prior_sources, external = set(), {}, {}
    old = Path('outputs/stage8b1a/cohort/census256_manifest_v1.jsonl')
    excluded.update(json.loads(x)['item_id'] for x in old.read_text().splitlines())
    prior_sources[str(old)] = sha(old)
    allowed = [Path('.').resolve(), Path('/data/dataset'),
               Path('/home/hyunjin/.cache/huggingface/datasets'), Path('/home/hyunjin/.cache/huggingface/hub')]
    for p in sorted(Path('outputs').glob('stage*/cohort/*manifest*.jsonl')):
        if p.parts[1].startswith(('stage8b', 'stage8c')):
            continue
        entries = [json.loads(x) for x in p.read_text().splitlines()]
        used = False
        for r in entries:
            rid = str(r.get('dataset_id', ''))
            match = re.search(r'mathvision_(\d+)', str(r.get('base_id', '')))
            if str(r.get('dataset', '')).lower() == 'mathvision' and rid.isdigit():
                excluded.add(rid); used = True
            elif match:
                excluded.add(match.group(1)); used = True
            for key in ('image', 'image_path'):
                val = r.get(key)
                if not isinstance(val, str) or not val.endswith(('.jpg', '.png', '.jpeg')):
                    continue
                path = Path(val)
                if not any(path.absolute().is_relative_to(root) for root in allowed):
                    continue
                path = path.resolve()
                if not any(path.is_relative_to(root) for root in allowed):
                    continue
                if path.is_file() and str(path) not in {x['image'] for x in rows}:
                    external[str(path)] = r.get('question', '')
                    used = True
        if used:
            prior_sources[str(p)] = sha(p)
    pairs = Path('outputs/stage7a_bench/structural_audit/paired_variant_mapping.jsonl')
    excluded.update(str(json.loads(x)['id']) for x in pairs.read_text().splitlines())
    prior_sources[str(pairs)] = sha(pairs)
    for r in rows:
        assert Path(r['image']).resolve().is_relative_to('/data/dataset')
        assert sha(r['image']) == r['image_sha256']
    external_rows = [dict(item_id='prior_'+hashlib.sha256(p.encode()).hexdigest()[:16], image=p, question=q)
                     for p, q in sorted(external.items())]
    all_rows = rows + external_rows
    signatures = {r['item_id']: image_signature(r['image']) for r in all_rows}
    family, groups, edges = family_groups(all_rows, signatures, [('1707', '1245')])
    excluded_families = {family[rid] for rid in excluded if rid in family}
    excluded_families.update(family[r['item_id']] for r in external_rows)
    rng = random.Random(820260920)
    randomized = list(rows); rng.shuffle(randomized)
    representatives, seen = [], set()
    for r in randomized:
        fid = family[r['item_id']]
        if fid in excluded_families or fid in seen:
            continue
        seen.add(fid)
        seed = int.from_bytes(hashlib.sha256(('stage8c_v2:'+r['item_id']).encode()).digest()[:4], 'big') & 0x7fffffff
        representatives.append(dict(r, family_id=fid, answer_format='multiple_choice' if r['options'] else 'free_response',
                                    problem_type=None, visual_density=None, entity_count=None, seed=seed))
    dev = proportional_sample(representatives, 128, rng)
    dev_ids = {r['item_id'] for r in dev}
    rest = [r for r in representatives if r['item_id'] not in dev_ids]
    test = proportional_sample(rest, 512, rng)
    timing = proportional_sample(test, 256, rng)
    audit = proportional_sample(test, 128, rng)
    assert not ({r['family_id'] for r in dev} & {r['family_id'] for r in test})
    at = datetime.now(timezone.utc).isoformat()
    save(ROOT/'stage8c_v2_family_manifest.json', dict(at=at, input_only=True, rows=len(rows),
        families=len(set(family[r['item_id']] for r in rows)), groups=groups, edges=edges,
        item_family=family, signatures=signatures, excluded_item_ids=sorted(excluded),
        excluded_families=sorted(excluded_families), eligible_representatives=len(representatives),
        prior_sources_sha256=prior_sources, external_prior_images=external_rows,
        grouping='Connected components: decoded RGB, trimmed normalized raster, phash Hamming<=10, specific numeric-normalized question>=80 chars, known1707/1245. All uncertain candidates grouped, never separated using outcomes.',
        limitations='Conservative perceptual/template grouping can overmerge; not exhaustive proof against independently redrawn semantic constructions.',
        population_distribution=distribution(rows), eligible_distribution=distribution(representatives)))
    for name, data in [('dev128', dev), ('test512', test)]:
        save(ROOT/f'stage8c_v2_{name}_manifest.json', dict(at=at, selection_seed=820260920,
             rows=data, distribution=distribution(data), distinct_families=len(data), outcomes_used=False))
    save(ROOT/'audit/subsets.json', dict(at=at, timing256=[r['item_id'] for r in timing],
         local_read128=[r['item_id'] for r in audit], frozen_before_outcomes=True))
    save(ROOT/'audit/remaining_family_representatives.json', dict(rows=[r for r in rest if r['item_id'] not in {x['item_id'] for x in test}],
         status='eligible reserve inventory only; no extension cohort selected before the narrow gate'))
    cfg = json.loads(Path('outputs/stage8b_block3a/v1/audit/native_config.json').read_text())
    cfg = {k: cfg[k] for k in ('model_checkpoint', 'model_revision', 'detector_freeze', 'detector_freeze_sha256',
            'max_new_tokens', 'generation_parameters', 'presence_penalty', 'min_pixels', 'max_pixels')}
    cfg.update(at=at, output_dir=str(ROOT), node='node02', gpus=2, workers_per_gpu=1,
               technical_items=[json.loads(x) for x in old.read_text().splitlines()][:4],
               gains=[1.,1.25,1.5,2.], technical_tokens=256, protocol='stage8c_v2')
    save(ROOT/'audit/prepared_config.json', cfg)
    save(ROOT/'audit/input_inventory.json', dict(at=at, dataset=inventory, source_manifest_sha256=sha(source),
         all3040_images_verified=True, no_download=True, project_datasets_link='absent',
         required_roots_reused=True, manifests_sha256={str(p):sha(p) for p in ROOT.glob('*manifest.json')},
         prior_sources_sha256=prior_sources))
    print(json.dumps(dict(eligible_families=len(representatives), excluded_items=len(excluded),
         prior_external_images=len(external_rows), all_families=len(groups), edges=len(edges),
         dev_distribution=distribution(dev), test_distribution=distribution(test)), indent=2))


if __name__ == '__main__':
    main()
