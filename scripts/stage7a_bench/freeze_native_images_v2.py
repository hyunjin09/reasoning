"""Freeze200 output-blind native IDs and supported paired input conditions."""
import argparse
import copy
import hashlib
from pathlib import Path
from urllib.parse import quote

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json, write_jsonl
from scripts.stage7a_bench.image_inputs_v2 import image_assets_many, user_content
from scripts.stage7a_bench.prepare_structural_v2 import metadata_rows

OUT = ROOT / 'outputs/stage7a_bench_v2'


def family_groups(rows, assets):
    parent = {r['example_id']: r['example_id'] for r in rows}
    def root(key):
        while parent[key] != key:
            key = parent[key]
        return key
    seen = {}
    for row in rows:
        qid = row['example_id']
        keys = ['official_family:' + str(row['family_id'])]
        keys += ['rgb:' + a['decoded_sha256'] for a in assets[qid]]
        if row['benchmark'] == 'mathvision_wild' and qid in {'11', '427'}:
            keys.append('manual_near_duplicate:removed_cubes_11_427')
        for key in keys:
            if key in seen:
                left, right = sorted([root(qid), root(seen[key])])
                parent[right] = left
            else:
                seen[key] = qid
    groups = {}
    for row in rows:
        groups.setdefault(root(row['example_id']), []).append(row['example_id'])
    mapping = {}
    for members in groups.values():
        family = rows[0]['benchmark'] + '_group_' + hashlib.sha256('|'.join(sorted(members)).encode()).hexdigest()[:20]
        for qid in members:
            mapping[qid] = family
    return mapping, list(groups.values())


def freeze(benchmark):
    state_path = OUT / 'cohort/sample_freeze.json'
    state = read_json(state_path)
    audit = read_json(OUT / 'structural_audit/benchmark_structural_summary.json')[benchmark]
    assert audit['count'] == 64 and (audit['eligible_track_a'] or audit['eligible_track_b'])
    manifest_dir = OUT / 'cohort/benchmark_manifests'
    prospective = read_jsonl(manifest_dir / f'{benchmark}_prospective_order.jsonl')
    rows = prospective if benchmark == 'mathvision_wild' else metadata_rows(benchmark)
    assert [r['example_id'] for r in rows] == [r['example_id'] for r in prospective]
    rows = rows[:200]
    assert len(rows) == 200
    assets = image_assets_many(rows)
    family, groups = family_groups(rows, assets)
    modes = (['photo', 'screenshot'] if benchmark == 'mathvision_wild' else
             ['image_present'] if benchmark == 'charxiv' else
             ['image_present', 'silent_no_image', 'explicit_guess'])
    variants = {}
    if benchmark == 'mathvision_wild':
        clean = [dict(row, image_path=row['paired_clean_image_path']) for row in rows[:64]]
        variants['screenshot'] = image_assets_many(clean)
    prefix = read_json(OUT / 'config/paired_condition_rules.json')['explicit_guess_prefix']
    entries, frozen_manifests = {}, []
    for mode in modes:
        records = []
        selected = rows if mode == modes[0] else rows[:64]
        for row in selected:
            qid = row['example_id']
            prompt = row.get('question', 'Solve the problem shown in the image.')
            if row.get('options') and 'Answer Choices:' not in prompt:
                options = row['options']
                pairs = options.items() if isinstance(options, dict) else [(chr(65+i), option) for i, option in enumerate(options)]
                prompt += '\n\n' + '\n'.join(f'{letter}. {option}' for letter, option in pairs)
            if mode == 'explicit_guess':
                prompt = prefix + prompt
            no_image = mode in {'silent_no_image', 'explicit_guess'}
            base_id = benchmark + '__' + quote(qid, safe='')
            event = base_id + '__' + mode
            if Path(event).name != event:
                raise ValueError('Unsafe event id: ' + event)
            record = dict(event_id=event, base_id=base_id, benchmark=benchmark,
                example_id=qid, condition=mode, family_id=family[qid], official_family_id=row['family_id'],
                question=row.get('question'), prompt=prompt, no_image=no_image, image_path=None,
                image_assets=[] if no_image else variants.get(mode, assets)[qid],
                image_layout='inline_markers' if benchmark == 'mmmu_pro' else 'images_first',
                answer=row.get('answer', row.get('answer_preview')),
                subject=row['subject'], source_record=copy.deepcopy(row),
                source_asset_identity=assets[qid],
                model_outputs_used_for_selection=False, task_quality='Requires independent semantic adjudication')
            # Validate marker layout without allocating decoded pixel arrays.
            user_content(record, [(a['slot'], None) for a in record['image_assets']])
            if benchmark == 'mathvision_wild':
                asset = record['image_assets'][0]
                record.update(image_path=asset['path'], image_sha256=asset['bytes_sha256'], image_assets=[])
            records.append(record)
        path = manifest_dir / f'{benchmark}_{mode}_native.jsonl'
        write_jsonl(path, records, freeze=True)
        key = benchmark + '_' + mode
        entries[key] = dict(manifest=str(path.relative_to(ROOT)), sha256=sha(path), count=len(records),
            source_pool=len(prospective), conditions_frozen_together=True,
            selection=f'First{len(records)} frozen prospective IDs; as-released tasks, quality qualifications preserved; no output-based replacement',
            structural_audit_sha256=audit['manual_notes_sha256'])
        frozen_manifests.append(str(path.relative_to(ROOT)))
    # No GPU run can start these files until this sequential final registration.
    latest = read_json(state_path)
    assert latest == state, 'Concurrent sample freeze mutation; reconcile before registration'
    for key, value in entries.items():
        if key in latest['native_screen']:
            assert latest['native_screen'][key] == value
        else:
            latest['native_screen'][key] = value
    write_json(state_path, latest)
    write_json(OUT / 'audit' / f'{benchmark}_native_freeze.json', dict(
        completed=True, count=200, benchmark=benchmark, modes=modes, family_groups=groups,
        family_rule='Union of official family or identical decoded image; manually known MathVision-Wild11/427 near-duplicate',
        model_outputs_read=False, causal_effects_read=False, manifests=frozen_manifests,
        source_dependencies={p: sha(ROOT / p) for p in ['scripts/stage7a_bench/freeze_native_images_v2.py',
            'scripts/stage7a_bench/image_inputs_v2.py', 'scripts/stage7a_bench/prepare_structural_v2.py',
            'outputs/stage7a_bench_v2/config/image_pairing_sample_rules.json']}), freeze=True)
    print('NATIVE_FROZEN', benchmark, len(rows), modes, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('benchmark', choices=['mathvision_wild', 'charxiv', 'mathsight', 'mmmu_pro', 'microvqa', 'medxpertqa_mm'])
    freeze(parser.parse_args().benchmark)
