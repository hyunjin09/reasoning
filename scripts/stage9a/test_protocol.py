"""Checks that protect arm comparability and recurrence denominators."""
import numpy as np
from visual_reasoning.stage9a.protocol import ARMS, COT, prompt, item_seed, reasoning_span, episode_metrics


def tokens(text):
    return [dict(decoded_token=c) for c in text]


def test_only_cot_instruction_differs():
    q="Which angle?\nA. 30\nB. 40"
    assert prompt(q,"instruct_direct")==prompt(q,"thinking")==q
    assert prompt(q,"instruct_cot")==q+"\n\n"+COT
    assert len({item_seed("17") for _ in ARMS})==1


def test_native_and_public_boundaries():
    assert reasoning_span(tokens("Check diagram.</think>42"),"thinking")["end"]==14
    public="Check diagram.\n\nFinal answer: 42"
    assert reasoning_span(tokens(public),"instruct_cot")["end"]==16
    speculative="The answer is maybe 4.\n\nLet us check the drawing first."
    assert reasoning_span(tokens(speculative),"instruct_cot")["boundary"]=="no_marker_full_assistant"


def test_gap_is_inactive_not_long_active_burst():
    x=np.zeros(400);x[:200]=.9;x[201]=.9
    m=episode_metrics(x,0,400)
    assert m["long_gap_at_risk"]==2 and m["long_gap_successes"]==0
    assert m["max_inactive_gap"]==1


def test_long_gap_and_censoring():
    x=np.zeros(400);x[0]=.9;x[130]=.9;x[380]=.9
    m=episode_metrics(x,0,400)
    assert m["long_gap_at_risk"]==2 and m["long_gap_probability"]==1
    assert m["late_fractions"]["0.5"]==1/3


def test_undefined_is_not_zero():
    m=episode_metrics([],0,0)
    assert m["episodes_per_1k"] is None and m["active_fraction"] is None
    m=episode_metrics([np.nan,.1,.2],0,3)
    assert m["valid_score_tokens"]==2 and m["active_fraction"]==0
    assert m["late_fractions"]["0.5"] is None and m["long_gap_probability"] is None
