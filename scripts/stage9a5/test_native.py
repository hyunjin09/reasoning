from scripts.stage9a5.native import thinking_prompt,sections
from scripts.stage9a3.literal_review import terminal_option


def test_only_cot_line_is_removed():
    p='How many?\noptions: {A: 1}\nThink step by step. You must write intermediate steps.\nRespond in curly braces format: {A}'
    assert thinking_prompt(p)=='How many?\noptions: {A: 1}\nRespond in curly braces format: {A}'


def test_capped_scratchpad_option_is_not_final():
    r=sections([1,2,3],99,lambda ids:'Maybe {B}')
    assert r['final_text']=='' and r['reasoning_tokens']==3
    assert not r['reasoning_closed'] and terminal_option(r['final_text']) is None


def test_closed_native_reasoning_and_final_are_separated():
    r=sections([1,2,99,4,5],99,lambda ids:str(ids))
    assert r['reasoning_tokens']==2 and r['final_text']=='[4, 5]' and r['reasoning_closed']


def test_duplicate_think_closure_is_flagged():
    r=sections([1,99,2,99,3],99,lambda ids:str(ids))
    assert r['closure_count']==2 and not r['reasoning_closed']
