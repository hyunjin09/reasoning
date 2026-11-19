from copy import deepcopy
import pytest
from scripts.stage7a_bench.pilot_selection_v2 import validate_selection
from scripts.stage7a_bench.causal_provenance_v2 import object_sha


def fixture(failures=16, faithful=16):
    entries=[];decisions=[];families={};selected={'failure':[],'faithful':[]}
    for stratum,n in [('failure',failures),('faithful',faithful)]:
        for i in range(n):
            key=f'{stratum}{i}'
            e=dict(id=key,base_id=key,event_id=key,benchmark='charxiv',condition='image_present',
                analysis_family_id='shared' if i<2 else key,causal_pilot_frozen=False,
                causal_state=None,selection_used_causal_or_passive_scores=False,
                row=dict(no_image=False),source_groups={'T':[1],'X':[2],'G':[1,2]},
                reviewed_claim=dict(demand='singleton',locally_correct=stratum=='faithful'),
                semantic_review=dict(screen_label='F1',final_correctness=False),downstream_review=None)
            entries.append(e);families[key]=e['analysis_family_id']
            decisions.append(dict(id=key,entry_sha256=object_sha(e),eligible=True,pilot_stratum=stratum,
                candidate_class='local_error' if stratum=='failure' else 'strong_faithful',
                structurally_identifiable=True,review_note='Reviewed native claim and distinct source geometry.',
                causal_or_passive_scores_used=False))
            if i<32:selected[stratum].append(key)
    screen={'image_present':dict(benchmark='charxiv',condition='image_present',frozen=200,
        generated=200,unavailable=0,reviewed=200,pending_generation=0,pending_review=0,screen_complete=True)}
    return screen,{'image_present':200},entries,decisions,selected,families


def test_complete_selection_uses_claim_truth_and_preserves_family_dependence():
    args=fixture();before=deepcopy(args);out=validate_selection(*args)
    assert out['status']=='VALIDATED_SELECTION_NOT_FROZEN'
    assert out['entry_gate_passed'] is True and out['selected_counts']=={'failure':16,'faithful':16}
    assert out['selected_unique_families']<32
    assert all(e['causal_pilot_frozen'] is False for e in out['selected_entries'])
    assert args==before


@pytest.mark.parametrize('change,match',[
    ('incomplete','complete'),('paired_missing','conditions'),('wrong_family','family'),
    ('changed_entry','digest'),('scores_used','scores'),('too_few_controls','faithful'),
    ('missing_failure','all'),('wrong_stratum','stratum'),('duplicate','Duplicate'),
    ('phantom','visual'),('unidentifiable','identifiability')])
def test_invalid_pilot_selection_is_rejected(change,match):
    a=list(fixture())
    if change=='incomplete':a[0]['image_present']['reviewed']=199
    if change=='paired_missing':a[1]['silent_no_image']=64
    if change=='wrong_family':a[5]['failure0']='other'
    if change=='changed_entry':a[2][0]['reviewed_claim']['locally_correct']=True
    if change=='scores_used':a[3][0]['causal_or_passive_scores_used']=True
    if change=='too_few_controls':a[4]['faithful'].pop()
    if change=='missing_failure':a[4]['failure'].pop()
    if change=='wrong_stratum':a[3][0]['pilot_stratum']='faithful'
    if change=='duplicate':a[4]['failure'].append(a[4]['failure'][0])
    if change=='phantom':
        a[2][0]['row']['no_image']=True;a[3][0]['entry_sha256']=object_sha(a[2][0])
    if change=='unidentifiable':a[3][0]['structurally_identifiable']=False
    with pytest.raises(ValueError,match=match):validate_selection(*a)


def test_small_failure_exception_uses_all_and_does_not_fabricate_minimum():
    out=validate_selection(*fixture(4,16))
    assert out['small_failure_exception'] is True
    assert out['selected_counts']=={'failure':4,'faithful':16}
    assert out['entry_gate_counts']['strong_faithful']==16


def test_target32_requires32_when_pool_has_more_and_retains_all_pool_counts():
    a=list(fixture(40,40));out=validate_selection(*a)
    assert out['selected_counts']=={'failure':32,'faithful':32}
    assert out['eligible_counts']=={'failure':40,'faithful':40}
    a[4]['failure'].pop()
    with pytest.raises(ValueError,match='32'):validate_selection(*a)


def test_excluded_pool_entry_is_preserved_with_reason_and_cannot_be_selected():
    a=list(fixture(17,16));a[3][-17].update(eligible=False,review_note='Source independence unavailable.')
    # index16 is the final failure candidate.
    a[4]['failure'].remove('failure16')
    out=validate_selection(*a)
    assert out['excluded_ids']==['failure16']
    a[4]['failure'].append('failure16')
    with pytest.raises(ValueError,match='eligible'):validate_selection(*a)


def test_repeated_claims_from_one_native_example_cannot_satisfy_entry_gate():
    a=list(fixture())
    for e,r in zip(a[2],a[3],strict=True):
        e['base_id']='same_native';e['analysis_family_id']='same_family';r['entry_sha256']=object_sha(e)
    a[5]={'same_native':'same_family'}
    with pytest.raises(ValueError,match='sixteen distinct'):validate_selection(*a)
