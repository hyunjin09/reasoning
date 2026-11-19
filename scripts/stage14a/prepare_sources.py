"""Snapshot local sources and seal source-only candidate identities, never outcomes."""
import io
import json
from collections import defaultdict

import pyarrow as pa
from PIL import Image

from scripts.stage14a.common import ROOT, Path, digest, load, now, save, sha
from scripts.stage14a.sampling import map_versions, stratified_order
from scripts.stage12xs.selection import components


def main():
    old_inventory = load('outputs/stage8b/audit/input_inventory.json')
    source = Path(old_inventory['source'])
    image_root = Path(old_inventory['derived_image_root'])
    verse_root = Path('/data/dataset/MathVerse')
    assert source.resolve().is_relative_to('/data/dataset')
    assert image_root.resolve().is_relative_to('/data/dataset')
    assert sha(source) == old_inventory['source_sha256']
    with source.open('rb') as f:
        table = pa.ipc.open_stream(f).read_all().select(['id', 'question', 'options', 'answer', 'level', 'subject', 'decoded_image'])
    raw = table.to_pylist()
    assert len(raw) == 3040 and {r['id'] for r in raw} == {str(i) for i in range(1, 3041)}
    fm_path = Path('outputs/stage8c_v2/v1/stage8c_v2_family_manifest.json')
    xs_path = Path('outputs/stage12xs/v1/stage12xs_historical_exclusion_manifest.json')
    alias_path = Path('outputs/stage11b/v1/audit/freshness_repair_v2.json')
    fm, xs, aliases = load(fm_path), load(xs_path), load(alias_path)
    edges = xs['source_only_alias_edges'] + aliases['edges']
    comp = components([r['id'] for r in raw], list(fm['groups']) + [[e['a'], e['b']] for e in edges])
    members = defaultdict(list)
    for item, group in comp.items():
        members[group].append(item)
    family_of, family_rows = {}, []
    for ids in members.values():
        ids.sort(key=int)
        previous = sorted({fm['item_family'][i] for i in ids})
        family = previous[0] if len(previous) == 1 else 'stage12xs_family_' + digest('|'.join(previous))[:20]
        representative = min(ids, key=lambda i: (digest('stage14a-v1|mv-representative|' + i), int(i)))
        for item in ids:
            family_of[item] = family
        family_rows.append(dict(family_id=family, item_id=representative, member_item_ids=ids, inherited_family_ids=previous))
    census, integrity = [], []
    for r in raw:
        p = image_root / (r['id'] + '.jpg')
        assert p.resolve().is_relative_to('/data/dataset')
        image_hash = sha(p)
        with Image.open(p) as im:
            rgb = im.convert('RGB')
            pixel_hash = digest(str(rgb.size) + '|' + __import__('hashlib').sha256(rgb.tobytes()).hexdigest())
            size = list(im.size)
        with Image.open(io.BytesIO(r['decoded_image']['bytes'])) as im:
            reference = im.convert('RGB')
            reference_hash = digest(str(reference.size) + '|' + __import__('hashlib').sha256(reference.tobytes()).hexdigest())
        assert reference_hash == pixel_hash, ('export_pixel_mismatch', r['id'])
        census.append(dict(item_id=r['id'], problem_id='mathvision:' + r['id'], family_id=family_of[r['id']],
                           question=r['question'], question_hash=digest(r['question']), options=r['options'],
                           gold_answer=r['answer'], answer_type='multiple_choice' if r['options'] else 'open_ended',
                           subject=r['subject'], difficulty=r['level'], image=str(p), image_hash=image_hash,
                           decoded_image_hash=pixel_hash, image_size=size,
                           source=dict(dataset='MathLLMs/MathVision', split='test', row_index=int(r['id']) - 1,
                                       arrow=str(source), raw_sha256=old_inventory['source_sha256']),
                           corruption=False))
        integrity.append(dict(item_id=r['id'], embedded_and_exported_pixels_identical=True))
    by = {r['item_id']: r for r in census}
    candidates = [dict(f, **{k: by[f['item_id']][k] for k in ['subject', 'difficulty', 'answer_type']}) for f in family_rows]
    ordered = stratified_order(candidates, ['subject', 'difficulty', 'answer_type'], 'stage14a-v1|mathvision|')
    for rank, r in enumerate(ordered, 1):
        r.update(rank=rank, within_stratum_hash=digest('stage14a-v1|mathvision|' + r['family_id']))
    sources = {}
    # Hash every file in the two selected dataset roots and the Arrow source directory.
    for base in [source.parent, image_root, verse_root]:
        for p in sorted(base.rglob('*')):
            if not p.is_file():
                continue
            assert p.resolve().is_relative_to('/data/dataset')
            sources[str(p)] = dict(sha256=sha(p), bytes=p.stat().st_size)
    vraw = load(verse_root / 'testmini.json') + load(verse_root / 'testmini_text_only.json')
    groups = map_versions(vraw)
    expected = ['Text Dominant', 'Text Lite', 'Text Only', 'Vision Intensive', 'Vision Dominant', 'Vision Only']
    assert len(groups) == 788
    vfamilies, variants = [], []
    for problem, versions in sorted(groups.items(), key=lambda x: int(x[0])):
        family = 'mathverse:testmini:' + problem
        assert set(versions) == set(expected)
        for version in expected:
            r = versions[version]
            p = verse_root / 'images' / r['image'] if r['image'] else None
            if p:
                assert p.resolve().is_relative_to(verse_root.resolve()) and p.is_file()
                with Image.open(p) as im:
                    im.verify()
            variants.append(dict(family_id=family, problem_index=problem, version=version,
                                 source_id=r['sample_index'], source_namespace='testmini_text_only' if version == 'Text Only' else 'testmini',
                                 question=r['question'], question_hash=digest(r['question']),
                                 query_wo=r['query_wo'], query_cot=r['query_cot'], question_for_eval=r['question_for_eval'],
                                 image=str(p) if p else None, image_present=p is not None,
                                 image_hash=sources[str(p)]['sha256'] if p else None,
                                 gold_answer=r['answer'], answer_type=r['question_type'], source_metadata=r['metadata'],
                                 missing=False, corrupt=False, semantic_source_review='PENDING'))
        exemplar=versions['Text Only']
        vfamilies.append(dict(family_id=family, problem_index=problem, versions=expected,
                              modality_completeness='complete6', answer_type=exemplar['question_type'],
                              subject=exemplar['metadata']['subject'], gold_answer=exemplar['answer'],
                              gold_consistent=True, text_only_image_absent=not exemplar['image'],
                              semantic_source_review='PENDING'))
    save(ROOT/'audit/source_file_snapshot.json', dict(at=now(),files=sources))
    save(ROOT/'audit/mathvision_census_source_snapshot.json', dict(at=now(),rows=census,aliases=family_rows,integrity=integrity))
    save(ROOT/'stage14a_mathvision_candidate_order.json', dict(at=now(),frozen=True,rows=ordered,
         strata=['subject','difficulty','answer_type'], within_stratum='SHA256(stage14a-v1|mathvision|family_id)',
         interleaving='At step k choose maximum integer population-proportional deficit k*n_stratum-used_stratum*N; ties by seeded stratum hash.',
         representative='Minimum SHA256(stage14a-v1|mv-representative|problem_id) within conservative family.',
         alias_sources={str(p):sha(p) for p in [fm_path,xs_path,alias_path]},
         outcomes_inspected=False,eligibility_screening_started=False,target_final_qc=1000))
    save(ROOT/'audit/mathverse_mapping_source_snapshot.json', dict(at=now(),families=vfamilies,versions=variants,
         structural_checks_pass=True,semantic_checks_complete=False,source_gold_not_model_correctness=True))
    save(ROOT/'audit/source_lookup.json',dict(at=now(),datasets_link='absent',mathvision_raw=str(source),
         mathvision_problems=len(census),mathvision_conservative_families=len(family_rows),mathverse_families=len(vfamilies),
         mathverse_versions=len(variants),downloads=0,model_calls=0,gpu_hours=0,
         old_source_files_preserved=True))
    print('SOURCE_SNAPSHOT',len(census),len(family_rows),len(vfamilies),len(variants),len(sources),'files')


if __name__ == '__main__':
    main()
