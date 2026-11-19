from scripts.stage9a4.decisions import baseline_gates,next_cutoff,reserve_eligible


def rows(n=64):
    return [dict(correct=i<40,cot=i<58,option='A' if i<58 else None,
                 at_length_cap=i>=58) for i in range(n)]


def test_all_four_baseline_thresholds_and_noop():
    r=rows();assert baseline_gates(r,True)['pass']
    assert not baseline_gates(r,False)['pass']
    r[39]['correct']=False;r[38]['correct']=False
    assert not baseline_gates(r,True)['G1_accuracy']


def test_cap_exception_requires_every_capped_trace_answered():
    r=rows()
    for x in r:x['option']='A';x['at_length_cap']=True
    assert baseline_gates(r,True)['G4_completion']
    r[-1]['option']=None
    assert not baseline_gates(r,True)['G4_completion']


def test_zero_gate_precedes_finite_selection():
    assert next_cutoff(.05,{64:0})==('stop_no_necessity',None)


def test_sequential_search_never_adds_extra_cutoffs():
    assert next_cutoff(.2,{64:.05})==('selected',64)
    assert next_cutoff(.2,{64:.1})==('run',128)
    assert next_cutoff(.2,{64:.1,128:.1})==('run',256)
    assert next_cutoff(.2,{64:.1,128:.1,256:.1})==('stop_no_finite',None)


def test_reserve_needs_selected_uncertain_finite_condition():
    assert reserve_eligible(64,.02,[-.04,.10])
    assert not reserve_eligible(None,.02,[-.04,.10])
    assert not reserve_eligible(64,.02,[-.04,.04])
