from scripts.stage14c.review_packets import response_view


def test_unclosed_thinking_never_exposes_reasoning_as_answer():
    value=response_view('Reasoning: answer could be A but I am still checking.','T')
    assert value['final_body']=='' and not value['native_think_closed']


def test_uses_last_native_close():
    value=response_view('bad answer</think>revision</think>Final answer: B<|im_end|>','T')
    assert value['final_body']=='Final answer: B' and not value['excerpted']


def test_long_response_is_explicitly_excerpted_and_preserves_tail():
    value=response_view('start '+('x'*20000)+' Final answer: C','I',limit=300)
    assert value['excerpted'] and value['final_body_tail'].endswith('Final answer: C')
    assert value['omitted_characters']>0 and 'caution' in value
