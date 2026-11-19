from copy import deepcopy

import pytest

from scripts.stage7a_bench.control_provenance_v2 import verify_control_records


def packet():
    asset = dict(slot='image_1', decoded_sha256='native_pixels')
    policy = dict(path='policy.json', sha256='policy_hash')
    entry = dict(event_id='chart', row=dict(image_assets=[asset]),
        source_groups={'T': [10], 'X': [20]}, source_annotation=dict(
            source_value_policy=policy, candidates=dict(correct='1.9', target_semantic='1.4',
                alternative_original='1.5', alternative_semantic='1.0')))
    controls = {}
    reviews = {}
    for source, original, changed in [('T', '1.9', '1.4'), ('X', '1.5', '1.0')]:
        for kind, value in [('semantic', changed), ('sham', original)]:
            name = source+'_'+kind
            controls[name] = dict(source=source, original=original, value=value,
                path=name+'.png', sha256=name+'_hash', recipient=[0, 0, 5, 5])
            reviews[name] = dict(source=source, original_literal=original, reviewed_literal=value,
                path=name+'.png', sha256=name+'_hash', recipient=[0, 0, 5, 5],
                literal_correct=True, source_identity_preserved=True, other_source_unchanged=True,
                semantics_valid=True, sham_rendering_matched=True)
    manifest = dict(event_id='chart', source_asset=asset, source_value_policy=policy,
                    causal_scores_used=False, controls=controls)
    review = dict(event_id='chart', status='MANUALLY_REVIEWED_LOCAL_CONTROLS',
        causal_or_passive_scores_used=False, threshold_changed=False, controls=reviews,
        redundant_encoding_review=dict(status='accounted', note='Independent source evidence.'))
    return entry, manifest, review


def test_independent_target_and_wrong_source_values_remain_separate():
    args = packet()
    verify_control_records(*args)
    assert args[1]['controls']['T_semantic']['value'] == '1.4'
    assert args[1]['controls']['X_semantic']['value'] == '1.0'


@pytest.mark.parametrize('fault', ['wrong_target', 'wrong_alternative', 'changed_sham', 'scores',
    'missing_sham', 'unknown_source', 'unreviewed_literal', 'changed_mask', 'source_image',
    'unreviewed_redundancy', 'extra_unreviewed_control'])
def test_control_orientation_and_review_corruption_is_rejected(fault):
    entry, manifest, review = packet()
    if fault == 'wrong_target': manifest['controls']['T_semantic']['value'] = '1.0'
    if fault == 'wrong_alternative': manifest['controls']['X_semantic']['value'] = '1.4'
    if fault == 'changed_sham': manifest['controls']['T_sham']['value'] = '1.4'
    if fault == 'scores': review['causal_or_passive_scores_used'] = True
    if fault == 'missing_sham':
        del manifest['controls']['X_sham']; del review['controls']['X_sham']
    if fault == 'unknown_source': del entry['source_groups']['X']
    if fault == 'unreviewed_literal': review['controls']['T_semantic']['literal_correct'] = False
    if fault == 'changed_mask': review['controls']['T_semantic']['recipient'] = [0, 0, 6, 6]
    if fault == 'source_image': manifest['source_asset'] = dict(slot='image_1', decoded_sha256='other')
    if fault == 'unreviewed_redundancy': review['redundant_encoding_review'] = {}
    if fault == 'extra_unreviewed_control': manifest['controls']['I_semantic'] = deepcopy(manifest['controls']['T_semantic'])
    with pytest.raises(ValueError): verify_control_records(entry, manifest, review)


def test_missing_alternative_edits_remain_unavailable():
    args = packet()
    for container in args[1:]:
        for name in ['X_semantic', 'X_sham']: del container['controls'][name]
    verify_control_records(*args)
    assert 'X_semantic' not in args[1]['controls']


def file_packet():
    entry, manifest, review = packet()
    entry['row'] = dict(image_path='/data/dataset/reviewed_photo.jpg',
        image_sha256='original_bytes', image_assets=[])
    entry['native_input'] = dict(decoded_image_sha256='original_pixels', image_size=[120, 80])
    manifest['source_asset'] = dict(kind='file', path=entry['row']['image_path'], slot='image_1',
        bytes_sha256='original_bytes', decoded_sha256='original_pixels', size=[120, 80])
    return entry, manifest, review


def test_canonical_file_control_identity_uses_frozen_bytes_and_native_pixels():
    verify_control_records(*file_packet())


@pytest.mark.parametrize('field,value', [('path', '/data/dataset/other.jpg'),
    ('bytes_sha256', 'other_bytes'), ('decoded_sha256', 'other_pixels'),
    ('size', [121, 80]), ('slot', 'image_2')])
def test_file_control_cannot_substitute_another_native_asset(field, value):
    entry, manifest, review = file_packet()
    manifest['source_asset'][field] = value
    with pytest.raises(ValueError): verify_control_records(entry, manifest, review)
