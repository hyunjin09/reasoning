import json
from pathlib import Path
import pytest
from transformers import AutoProcessor
from visual_reasoning.stage5a.annotation import exact_semantic_candidate, eligibility, temporal_annotation, cf_eligible
from visual_reasoning.stage5a.annotation import semantic_axes

ROOT=Path(__file__).resolve().parents[3]

@pytest.fixture(scope='module')
def tokenizer():
    cfg=json.loads((ROOT/'outputs/stage5a/config/stage5a_config.json').read_text())
    return AutoProcessor.from_pretrained(cfg['model_checkpoint'],local_files_only=True).tokenizer

def test_native_square_root_boundary_preserves_real_history(tokenizer):
    rows=[json.loads(x) for x in (ROOT/'outputs/stage5a/cohort/prospective_screen_manifest.jsonl').read_text().splitlines()]
    r=next(r for r in rows if r['base_problem_id']=='369')
    tokens=[json.loads(x) for x in (ROOT/r['native_reuse']['artifact_dir']/'tokens.jsonl').read_text().splitlines()]
    text=''.join(t['decoded_token'] for t in tokens)
    start=text.rfind('side opposite 60° is √3',0,text.find('</think>'))+len('side opposite 60° is ')
    c=exact_semantic_candidate(tokens=tokens,match_start=start,match_end=start+2,counterfactual_value='√5',tokenizer=tokenizer)
    assert '√3' in c['original_divergent_suffix_text']
    assert '√5' in c['counterfactual_divergent_suffix_text']
    n=c['ed_generated_index']
    assert c['history_before_ed_token_ids']==[t['token_id'] for t in tokens[:n]]
    assert tokenizer.decode(c['original_divergent_suffix_ids'],clean_up_tokenization_spaces=False)==c['original_divergent_suffix_text']

def test_identity_exclusion_blocks_both_cohorts_but_ambiguous_source_only_blocks_atlas():
    assert eligibility({'candidate_excluded':True},True,[{}])==(False,False)
    assert eligibility({'identity_exclusion_reason':'prior image'},True,[{}])==(False,False)
    assert eligibility({'atlas_excluded_reason':'unclear truth'},True,[{}])==(True,False)

def test_selected_sequence_cannot_establish_full_native_refresh():
    got=temporal_annotation({'source':'A'},'unreviewed native prefix')
    assert got['temporal_role']=='NONE'
    assert got['previous_source'] is None
    assert got['prior_explicit_availability'] is None
    assert got['temporal_unresolved']

def test_joint_claim_is_not_validated_by_editing_only_one_numeric_label():
    review={'readout':'100','truth':'100'};fact={'cf_allowed':True,'value':'100','counterfactual':'110'}
    assert cf_eligible(review,fact,'110',['A'])
    assert not cf_eligible(review,fact,'110',['A','B'])
    assert not cf_eligible({'readout':'BC','truth':'AQ'},fact,'BC',['A'])

def test_numeric_readout_and_foil_must_match_the_physical_edit():
    fact={'cf_allowed':True,'value':'100','counterfactual':'110'}
    assert not cf_eligible({'readout':'50','truth':'50'},fact,'110',['A'])
    assert not cf_eligible({'readout':'100','truth':'100'},fact,'120',['A'])

def test_demand_only_readout_has_no_explicit_visual_claim():
    got=semantic_axes({'correctness':'INCORRECT','semantic_role':'CURRENTLY_DEMANDED','has_explicit_visual_claim':False})
    assert got['local_correctness']=='NO_EXPLICIT_CLAIM'
    assert got['readout_correctness']=='INCORRECT'
    assert not got['has_explicit_visual_claim']
    assert semantic_axes({'correctness':'UNDECIDABLE'})['local_correctness']=='UNDECIDABLE'

def test_large_negative_mention_effect_is_not_weak_alignment():
    from visual_reasoning.stage5a.protocol import classify_event
    got=classify_event(local_correctness='CORRECT',final_correct=True,vsd={'T':1.,'M':-2.,'I':0.},
                       w8_t=1.,ce_minus_sham=None,temporal='NONE',mention_differs=True)
    assert not got['alignment_only_candidate']
