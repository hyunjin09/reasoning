from visual_reasoning.stage6a.segmentation import segment_native


def test_unicode_partial_tokens_stay_with_their_character():
    pieces=['Read.\n','','é',' is a label.\n','</think>','\n42']
    spans=segment_native([{'decoded_token':p,'token_id':i} for i,p in enumerate(pieces)])
    assert spans[0]['token_end']==1
    assert spans[1]['token_start']==1
    assert spans[1]['text']=='é is a label.\n'
    assert spans[-1]['section']=='final'
    assert spans[-1]['text']=='\n42'


def test_boundaries_inside_a_token_expand_without_overlap_or_retokenization():
    pieces=['First.\nSecond',' sentence.\n','</think>','Answer.']
    spans=segment_native([{'decoded_token':p,'token_id':i} for i,p in enumerate(pieces)])
    for s in spans:
        assert s['text']==''.join(pieces[s['token_start']:s['token_end']])
    assert all(a['token_end']<=b['token_start'] for a,b in zip(spans,spans[1:]))
    assert spans[0]['boundary_expanded_to_native_token']


def test_sentence_fallback_retains_all_reasoning_text():
    pieces=['A is 3. ','B is 4. ','So 7.','</think>','7']
    spans=segment_native([{'decoded_token':p,'token_id':i} for i,p in enumerate(pieces)])
    assert ''.join(s['text'] for s in spans if s['section']=='reasoning')==''.join(pieces[:3])
    assert len([s for s in spans if s['section']=='reasoning'])==3
