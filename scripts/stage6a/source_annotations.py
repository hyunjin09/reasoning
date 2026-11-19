"""Read reviewed source-annotation sidecars without changing native manifests."""
import json
from scripts.stage6a.inventory import OUT


def validate_prefix_membership(reviewed, original, remaining, *, complete=False):
    reviewed,original,remaining=map(set,(reviewed,original,remaining))
    assert not original&remaining,'Source-review strata must be disjoint'
    assert original<=reviewed<=original|remaining,'Missing original prefix or unexpected reviewed base'
    if complete:assert reviewed==original|remaining,'Incomplete committed prefix review'


def source_records():
    path=OUT/'config/c1_secondary_sources.json'
    if not path.exists():return {}
    records=json.loads(path.read_text())
    assert len(records)==34
    combined={key:dict(record,annotation_provenance=str(path),
        annotation_scope='All frozen34MathVerse bases; source-image annotation after intact generation began; no membership/stimulus change')
        for key,record in records.items()}
    extra_path=OUT/'config/c1_secondary_remaining_sources.json'
    if extra_path.exists():
        extra=json.loads(extra_path.read_text())
        scope=json.loads((OUT/'config/c1_secondary_remaining_annotation_scope.json').read_text())
        assert set(extra)<=set(scope['base_ids']) and not set(extra)&set(combined)
        if scope['status']=='COMPLETE':assert set(extra)==set(scope['base_ids'])
        combined.update({key:dict(record,annotation_provenance=str(extra_path),
            annotation_scope='All75remaining frozen eligible MathVision/MathVista bases; source-only annotation, no outcome-selected subset or stimulus/membership change')
            for key,record in extra.items()})
    assert all(r['status'] in ['pass_full_source_and_crop_review','no_additional_numeric_fact'] for r in combined.values())
    for record in combined.values():
        ids=[s['source_id'] for s in record['sources']]
        assert len(ids)==len(set(ids)) and 'T' not in ids
    return combined


def secondary_sources():
    return {key:[dict(source,annotation_provenance=record['annotation_provenance'],
        annotation_scope=record['annotation_scope']) for source in record['sources']]
        for key,record in source_records().items()}


def target_alias_patterns():
    return {key:record['target_aliases'] for key,record in source_records().items()
        if record.get('target_aliases')}
