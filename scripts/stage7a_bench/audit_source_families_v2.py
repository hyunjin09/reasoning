"""Verify existing frozen source families without native-output inspection."""
from collections import defaultdict

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    freeze = read_json(OUT / 'cohort/sample_freeze.json')['native_screen']
    rows, hashes = [], {}
    for record in freeze.values():
        path = ROOT / record['manifest']
        assert sha(path) == record['sha256']
        selected = read_jsonl(path)
        assert len(selected) == record['count']
        rows.extend(selected)
        hashes[record['manifest']] = record['sha256']
    assert len({r['event_id'] for r in rows}) == len(rows) == 2376
    by_benchmark = defaultdict(list)
    for row in rows:
        assert row.get('model_outputs_used_for_selection', False) is False
        by_benchmark[row['benchmark']].append(row)
    reports = {}
    override_path = OUT / 'cohort/source_family_overrides.json'
    override_record = read_json(override_path) if override_path.exists() else {}
    overrides = override_record.get('overrides', {})
    if overrides:
        assert override_record['native_manifest_sha256'] == sha(OUT / 'cohort/benchmark_manifests/mmlongbench_doc_image_present_native.jsonl')
        assert set(overrides) <= {r['base_id'] for r in rows}
    for benchmark, selected in by_benchmark.items():
        bases, families, identities = defaultdict(set), defaultdict(set), defaultdict(set)
        members = defaultdict(set)
        for row in selected:
            base, family = row['base_id'], row['family_id']
            if base in overrides:
                override = overrides[base]
                assert family == override['original_family_id']
                assert row.get('document_sha256') == override['document_sha256']
                family = override['source_family_id']
            bases[base].add(family)
            families[family].add(base)
            for asset in row.get('source_asset_identity', row.get('image_assets', [])) or []:
                identities['rgb:' + asset['decoded_sha256']].add(family)
                members['rgb:' + asset['decoded_sha256']].add(base)
            if row.get('document_sha256'):
                identities['pdf:' + row['document_sha256']].add(family)
                members['pdf:' + row['document_sha256']].add(base)
            official = row.get('official_family_id')
            if official is not None:
                identities['official:' + str(official)].add(family)
                members['official:' + str(official)].add(base)
        assert all(len(group) == 1 for group in bases.values()), 'Paired base split across families'
        conflicts = {key: sorted(values) for key, values in identities.items() if len(values) > 1}
        assert not conflicts, (benchmark, conflicts)
        reports[benchmark] = dict(native_conditions=len(selected), native_bases=len(bases),
            source_families=len(families), largest_family_bases=max(map(len, families.values())),
            per_base_source_family={key: next(iter(value)) for key, value in bases.items()},
            frozen_original_family_count=len({r['family_id'] for r in selected}),
            repeated_families={key: sorted(value) for key, value in families.items() if len(value) > 1},
            shared_source_identities={key: sorted(value) for key, value in members.items() if len(value) > 1},
            family_scope='Official question category; no real image source' if benchmark == 'phantom_0'
                         else 'Frozen official/image/document source family',
            cross_family_identity_conflicts=conflicts, paired_conditions_stay_together=True)
    write_json(OUT / 'audit/native_source_family_integrity.json', dict(
        status='PASS', rows=len(rows), benchmarks=reports, manifest_sha256=hashes,
        implementation_sha256=sha(ROOT / 'scripts/stage7a_bench/audit_source_families_v2.py'),
        analysis_family_override_sha256=sha(override_path) if overrides else None,
        downstream_requirement='Use per_base_source_family for pilot/statistical grouping; preserve original native family_id as provenance.',
        native_outputs_read=False, causal_scores_read=False,
        scope='Within-benchmark family consistency across conditions, official identity and exact decoded images/PDF hashes. This is not an exhaustive near-duplicate or unseen-template generalization certificate.'), freeze=True)
    print('SOURCE_FAMILY_INTEGRITY_PASS',len(rows),'conditions')
    for name, report in reports.items():
        print(name,report['native_bases'],'bases',report['source_families'],'families')


if __name__ == '__main__':
    main()
