from visual_reasoning.stage8c.analysis_fp32 import development_decision


def inputs():
    base={str(i):dict(correct=i<64,normal_eos=True,at_length_cap=False,
        reasoning_tokens=100,tokens=110,actual_interventions=0,elapsed_seconds=1.)
        for i in range(128)}
    arms={g:{i:dict(r) for i,r in base.items()} for g in (1.,1.25,1.5,2.)}
    metadata={i:dict(subject='a' if int(i)<64 else 'b') for i in base}
    return arms,metadata


def test_equal_accuracy_prefers_lower_cap_increase_before_smaller_gain():
    arms,metadata=inputs()
    for g in (1.25,1.5):arms[g]['64']['correct']=True
    arms[1.25]['0'].update(at_length_cap=True,normal_eos=False)
    assert development_decision(arms,metadata)['dose']==1.5


def test_unsafe_accuracy_winner_does_not_override_eligible_dose():
    arms,metadata=inputs()
    arms[1.25]['64']['correct']=True
    for i in range(64,70):arms[2.][str(i)]['correct']=True
    for i in range(20):arms[2.][str(i)].update(at_length_cap=True,normal_eos=False)
    decision=development_decision(arms,metadata)
    assert decision['dose']==1.25
    assert 'cap_increase_gt10pp' in decision['details'][2.]['no_go_reasons']
