import re

import pytest

from scripts.stage6a.annotate_controlled_states import source_patterns
from scripts.stage6a.source_annotations import validate_prefix_membership


def test_incomplete_annotation_extension_is_allowed_only_before_release():
    validate_prefix_membership({'old','new1'},{'old'},{'new1','new2'})
    with pytest.raises(AssertionError,match='Incomplete'):
        validate_prefix_membership({'old','new1'},{'old'},{'new1','new2'},complete=True)
    validate_prefix_membership({'old','new1','new2'},{'old'},{'new1','new2'},complete=True)


def test_prefix_extension_cannot_drop_originals_or_add_other_bases():
    for reviewed in [{'new1'}, {'old','foreign'}]:
        with pytest.raises(AssertionError):
            validate_prefix_membership(reviewed,{'old'},{'new1'})


def test_reviewed_directional_alias_does_not_merge_two_given_angles():
    row=dict(cohort='C1',base_id='two_angles',target={'entity':'known angle'},
        annotation_sources=[dict(source_id='A',aliases=r'\bclockwise marked angle\b')])
    patterns=source_patterns(row,{'two_angles':r'\bcounterclockwise marked angle\b'})
    assert re.search(patterns['T'],'counterclockwise marked angle')
    assert not re.search(patterns['T'],'clockwise marked angle')
    assert not re.search(patterns['T'],'known angle')
    assert re.search(patterns['A'],'clockwise marked angle')
