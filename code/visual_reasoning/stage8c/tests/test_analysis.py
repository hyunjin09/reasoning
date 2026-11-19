import pytest
from visual_reasoning.stage8c.analysis import transitions, paired_inference, development_decision


def row(correct):
    return dict(correct=correct,normal_eos=True,at_length_cap=False,reasoning_tokens=100,
                tokens=110,actual_interventions=0,elapsed_seconds=1.)


def test_unresolved_is_not_silently_a_wrong_to_correct_transition():
    base={'a':row(None),'b':row(False),'c':row(True)}
    arm={'a':row(True),'b':row(True),'c':row(False)}
    assert transitions(base,arm)==dict(WtoC=1,CtoW=1,CtoC=0,WtoW=0,unresolved=1)


def test_family_bootstrap_preserves_paired_difference():
    base={str(i):row(False) for i in range(6)}
    arm={str(i):row(True) for i in range(6)}
    result=paired_inference(base,arm,{str(i):str(i//2) for i in range(6)},draws=200)
    assert result['delta_accuracy']==1 and result['family_ci95']==[1.,1.]
    assert result['families']==3 and result['mcnemar_two_sided_p']==pytest.approx(.03125)


def test_development_null_stops_and_unresolved_blocks_selection():
    base={str(i):row(i<64) for i in range(128)}
    arms={g:{i:dict(r) for i,r in base.items()} for g in (1.,1.25,1.5,2.)}
    metadata={str(i):dict(subject='a' if i<64 else 'b') for i in range(128)}
    assert development_decision(arms,metadata)['status']=='stop_dev_no_go'
    arms[1.25]['64']['correct']=True
    assert development_decision(arms,metadata)['dose']==1.25
    arms[2.]['0']['correct']=None
    assert development_decision(arms,metadata)['status']=='awaiting_blind_extraction'
