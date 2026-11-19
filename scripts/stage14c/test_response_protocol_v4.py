import pytest
from scripts.stage14c.response_protocol_v4 import extract
from scripts.stage14c.design_core import _canonical


@pytest.mark.parametrize('text',['5*','{5*}',r'\boxed{2}*','$2','2...'])
def test_unbalanced_operator_or_markup_requires_review(text):
    value=extract(text,'I','integer','stop')
    assert value['needs_review'] and value['status']=='NEEDS_RESPONSE_REVIEW'


@pytest.mark.parametrize('text',['**2**','*2*','$2$',r'$\boxed{2}$',r'\boxed{2}','{2}','Final answer: **2**'])
def test_balanced_native_format_retains_commitment(text):
    value=extract(text,'I','integer','stop')
    assert _canonical(value['answer'],'integer',None)==2 and not value['needs_review']


def test_choice_adapter_and_unclosed_thinking_unchanged():
    assert extract('Final answer: A','I','choice','stop')['answer']=='A'
    assert extract('Final answer: A','T','choice','length')['status']=='UNSCORABLE'
