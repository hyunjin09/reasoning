import pytest
from visual_reasoning.stage8b.block3a_review import align_read


def test_claim_alignment_preserves_first_semantic_read_even_without_episode():
    pieces=['A ','red ','square',' appears. Later red square.']
    claim=dict(quote='A red square',quote_start=0,readout='red square')
    result=align_read(pieces,claim,[dict(episode_index=0,start_token=40,end_token=45)])
    assert result['claim_start_token']==1 and result['claim_end_token']==3
    assert not result['retrieval_eligible']
    result=align_read(pieces,claim,[dict(episode_index=0,start_token=2,end_token=3)])
    assert result['retrieval_eligible'] and result['episode_index']==0
    with pytest.raises(ValueError):align_read(pieces,{**claim,'quote_start':2},[])
