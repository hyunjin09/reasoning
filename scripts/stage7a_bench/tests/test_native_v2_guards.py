"""Scientific guards must reject invalid inputs before CUDA/model loading."""
import json
import pytest
from scripts.stage7a.common import sha
from scripts.stage7a_bench.native_v2 import check_manifest, validate_rows


def row(**changes):
    return dict(dict(event_id='q1', benchmark='phantom_0', prompt='What is shown?',
                     no_image=True, image_path=None), **changes)


def test_no_image_cannot_carry_image_state():
    with pytest.raises(ValueError, match='No-image row'):
        validate_rows([row(image_path='image.png')])


def test_unsupported_embedded_input_fails_instead_of_silent_text_fallback():
    with pytest.raises(ValueError, match='single-image'):
        validate_rows([row(no_image=False, image_column='images')])


def test_exact_freeze_and_structural_gate_required(tmp_path):
    path = tmp_path / 'manifest.jsonl'
    path.write_text(json.dumps(row()) + '\n')
    freeze = {'native_screen': {'p': {'sha256': sha(path), 'count': 1}}}
    audit = {'phantom_0': {'count': 64, 'eligible_track_b': True}}
    assert check_manifest(path, freeze, audit)[0]['event_id'] == 'q1'
    with pytest.raises(ValueError, match='structural audit'):
        check_manifest(path, freeze, {})
    path.write_text(json.dumps(row(prompt='A changed question')) + '\n')
    with pytest.raises(ValueError, match='not uniquely frozen'):
        check_manifest(path, freeze, audit)


def test_duplicate_ids_and_traversal_fail():
    with pytest.raises(ValueError, match='duplicate'):
        validate_rows([row(), row()])
    with pytest.raises(ValueError, match='Unsafe'):
        validate_rows([row(event_id='../q1')])
