"""Carry verified, outcome-blind v1 preparation into the approved v2 scope."""
import copy
import datetime
import json
from pathlib import Path

from scripts.stage7a.common import read_json, read_jsonl, sha, write_json, write_jsonl

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'outputs/stage7a_bench'
OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    now = datetime.datetime.now().astimezone().isoformat()
    plan = ROOT / 'plan/stage7a_benchmark_failure_enrichment_plan_v2_mirage_track.md'
    old_download = read_json(OLD / 'cohort/download_manifest.json')
    prior_inventory = read_json(OLD / 'cohort/dataset_inventory.json')
    entries = {r['candidate_id']: r for r in old_download['entries']}
    paths = {
        'mathvision_wild': ('testmini_photo/metadata.jsonl', ['testmini_photo', 'testmini_screenshot'], 304, 608),
        'mathsight': ('Dataset/661/final-vision-661-new.jsonl', ['multimodal661'], 661, 1893),
        'mmlongbench_doc': ('data/train-00000-of-00001.parquet', ['train'], 1091, 134),
        'charxiv': ('val.parquet', ['validation reasoning'], 1000, 1000),
    }
    candidates = []
    for name in ['mathvision_wild', 'mmlongbench_doc', 'charxiv', 'mathsight']:
        row = copy.deepcopy(next(r for r in prior_inventory['candidates'] if r['candidate_id'] == name))
        d = entries[name]
        relative, splits, count, assets = paths[name]
        base = Path(d['proposed_destination'])
        # The photo release uses a split-named annotation file; discover exactly
        # that metadata location rather than assume the prior card's schema.
        annotation = base / relative
        if name == 'mathvision_wild' and not annotation.exists():
            matches = [base / f['relative_path'] for f in d['files']
                       if f['relative_path'].endswith(('.json', '.jsonl')) and 'photo' in f['relative_path']]
            assert len(matches) == 1, matches
            annotation = matches[0]
        assert annotation.is_file(), annotation
        row.update(track=['A', 'B'] if name == 'mathsight' else ['A'], priority=len(candidates) + 1,
                   local_version_revision=d['official_revision'], available_local_splits=splits,
                   local_row_count=count, local_image_document_count=assets,
                   local_path=str(base), annotation_path=str(annotation), image_path=str(base),
                   usable=True, status=d['status'],
                   reason='Verified pinned v1 downloads reused; original receipts retained.',
                   official_evaluation_metadata='Release ground truth; local-claim evaluation remains separately reviewed.')
        row['license_readme']['local_available'] = (base / 'README.md').is_file()
        row['license_readme']['readme_path'] = str(base / 'README.md')
        if name == 'mathvision_wild':
            row['paired_variants'] = '304 exact ID/answer pairs; 64 pairs visually reviewed under v1 before any model output.'
        if name == 'mathsight':
            row.update(paired_variants='661 annotation rows map to 631 shared basenames in all three image variants; visual validity pending.',
                       source_roi_annotations='No ROI fields; image identity, subject and difficulty only.')
            row['license_readme']['declared_license'] = 'MIT'
        if name == 'mmlongbench_doc':
            row['reason'] += ' One PDF quarantined for SHA256 mismatch; another accepted only on exact pinned SHA256 despite incorrect LFS size.'
        candidates.append(row)
    new = [
        ('mmmu_pro', 'MMMU-Pro', 'MMMU/MMMU_Pro', 'LOCAL_FOUND_SCHEMA_PENDING'),
        ('mmmu_pro_bclean', 'MMMU-Pro B-Clean-style subset', 'MIRAGE B-Clean', 'PROTOCOL_AND_LABELS_PENDING'),
        ('phantom_0', 'Phantom-0', 'masadi-99/MIRAGE data/phantom_0', 'NOT_LOCATED_RELEASE_LOOKUP_PENDING'),
        ('microvqa', 'MicroVQA', 'jmhb/microvqa', 'NOT_LOCATED_RELEASE_LOOKUP_PENDING'),
        ('medxpertqa_mm', 'MedXpertQA-MM', 'TsinghuaC3I/MedXpertQA', 'NOT_LOCATED_RELEASE_LOOKUP_PENDING'),
        ('vqa_rad', 'VQA-RAD', 'OSF 89kps; Cauldron training conversion', 'ORIGINAL_RELEASE_LOOKUP_PENDING'),
        ('rexvqa', 'ReXVQA', 'rajpurkarlab/ReXVQA', 'NOT_LOCATED_RELEASE_LOOKUP_PENDING'),
    ]
    for name, canonical, alias, status in new:
        candidates.append(dict(candidate_id=name, canonical_name=canonical, local_alias=alias,
            track=['B'], priority=len(candidates) + 1, local_version_revision=None,
            available_local_splits=[], local_row_count=None, local_image_document_count=None,
            local_path=None, annotation_path=None, image_path=None, paired_variants=None,
            source_roi_annotations=None, official_evaluation_metadata=None,
            license_readme=None, usable=False, status=status,
            reason='Ordered allowed-root lookup recorded before any new download. Exact release/schema verification pending.'))
    inventory = dict(created_at=now, approved_plan=str(plan.relative_to(ROOT)),
        track_a_lookup='outputs/stage7a_bench/audit/dataset_lookup_initial.json',
        track_b_lookup='outputs/stage7a_bench_v2/audit/dataset_lookup_track_b.json',
        candidates=candidates, reserve_candidates=['visualpuzzles', 'visulogic', 'hallusionbench', 'gqa', 'pope'],
        coverage_limit='Named roots/cache namespaces checked; unreadable or unnamed locations remain unknown.')
    write_json(OUT / 'cohort/dataset_inventory.json', inventory, freeze=True)
    lines = ['# Stage7A-Bench v2 dataset inventory', '', 'Inventory written before new Track B downloads.', '',
             '| Benchmark | Track | Availability | Rows |', '|---|---|---|---|']
    lines += [f"| {r['canonical_name']} | {'/'.join(r['track'])} | {r['status']} | {r['local_row_count']} |" for r in candidates]
    (OUT / 'cohort/dataset_inventory.md').write_text('\n'.join(lines) + '\n')
    for filename, content in [('benchmark_candidates.json', candidates),
        ('track_a_candidates.json', [r['candidate_id'] for r in candidates if 'A' in r['track']]),
        ('track_b_candidates.json', [r['candidate_id'] for r in candidates if 'B' in r['track']]),
        ('benchmark_priority.json', dict(primary=[r['candidate_id'] for r in candidates],
            reserves=inventory['reserve_candidates'], track_rankings_separate=True))]:
        write_json(OUT / 'config' / filename, content, freeze=True)
    reuse = ['cohort/benchmark_manifests/mathvision_wild_structural.jsonl',
             'cohort/benchmark_manifests/mathvision_wild_prospective_order.jsonl',
             'structural_audit/mathvision_wild_manual_notes.json',
             'structural_audit/paired_variant_mapping.jsonl']
    copied = []
    for relative in reuse:
        source, target = OLD / relative, OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert sha(target) == sha(source)
        else:
            target.write_bytes(source.read_bytes())
        copied.append(dict(source=str(source.relative_to(ROOT)), target=str(target.relative_to(ROOT)), sha256=sha(source)))
    freeze = read_json(OLD / 'cohort/sample_freeze.json')
    math_freeze = copy.deepcopy(freeze['structural']['mathvision_wild'])
    math_freeze['manifest'] = math_freeze['manifest'].replace('stage7a_bench/', 'stage7a_bench_v2/')
    math_freeze['inherited_from_v1'] = True
    write_json(OUT / 'cohort/sample_freeze.json', dict(structural={'mathvision_wild': math_freeze},
        native_screen={}, causal_pilot={}, model_generation_started=False), freeze=True)
    write_json(OUT / 'cohort/download_manifest.json', dict(created_at=now, status='TRACK_B_DISCOVERY',
        entries=[], inherited_track_a_manifest='outputs/stage7a_bench/cohort/download_manifest.json',
        inherited_sha256=sha(OLD / 'cohort/download_manifest.json'),
        sequential_only=True, policy_approval_required=False,
        authorization='User explicitly authorized writes to /data/dataset; approved v2 plan.',
        proposed_external_root='/data/dataset/reasoning_steps_stage7a_bench'), freeze=True)
    write_json(OUT / 'audit/v1_carryforward.json', dict(at=now, approved_plan_sha256=sha(plan),
        records=copied, no_v1_native_or_causal_results_exist=True,
        v1_evidence_preserved=True, hallusion_review_deferred=True,
        interpretation='Same S/R definitions; completed outcome-blind structural audit reused without resampling.'), freeze=True)
    (OUT / 'audit/approved_plan_snapshot.md').write_bytes(plan.read_bytes())
    print(json.dumps(dict(primary_candidates=len(candidates), carried_structural_examples=64,
        new_track_b_downloads=0, plan_sha256=sha(plan))))


if __name__ == '__main__':
    main()
