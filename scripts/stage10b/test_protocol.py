from scripts.stage10b.protocol import paragraphs
from scripts.stage10b.protocol import wilson,agreement,decision,qualifying_runs,trajectory_counts


def test_paragraphs_retain_trailing_space_and_final_newline_content():
    text='First fact. \n\nCalculation. \n\nNew demand.\n'
    rows=paragraphs(text)
    assert [r['text'] for r in rows]==['First fact.','Calculation.','New demand.']
    assert all(text[r['start']:r['end']]==r['text'] for r in rows)
    assert ''.join(r['text'] for r in rows).replace(' ','')==''.join(text.split())


def test_paragraphs_preserve_internal_lines_and_empty_reasoning():
    assert paragraphs(' \n\t')==[]
    text='\nInventory:\n- first\n- second\n\nThus done.  '
    assert [r['text'] for r in paragraphs(text)]==['Inventory:\n- first\n- second','Thus done.']


def test_zero_denominators_and_degenerate_agreement_remain_undefined():
    assert wilson(0,0)['point'] is None
    assert wilson(0,10)['ci95'][0]==0
    a=agreement(['ABSENT']*4,['ABSENT']*4)
    assert a['raw']==1 and a['kappa'] is None


def test_go_gate_counts_independent_diverse_support_and_agreement():
    assert decision(11,{'MathVision':6,'MathVerse':5},{'a':6,'b':5},True)=='NO_GO'
    assert decision(12,{'MathVision':6,'MathVerse':6},{'a':6,'b':6},True)=='LIMITED_GO'
    assert decision(24,{'MathVision':16,'MathVerse':8},{'a':16,'b':8},True)=='STRONG_GO'
    assert decision(24,{'MathVision':17,'MathVerse':7},{'a':17,'b':7},True)=='LIMITED_GO'
    assert decision(24,{'MathVision':12,'MathVerse':12},{'a':20,'b':4},True)=='LIMITED_GO'
    assert decision(24,{'MathVision':12,'MathVerse':12},{'a':12,'b':12},False)=='LIMITED_GO'


def test_single_spike_and_nonconsecutive_missing_queries_do_not_qualify():
    assert qualifying_runs([0,1,2],[False,True,False])==[]
    assert qualifying_runs([0,2],[True,True])==[]
    assert qualifying_runs([0,1,2,3],[False,True,True,False])==[1]


def test_multiple_events_never_inflate_trajectory_denominators():
    events=[dict(trajectory_id='a',onset=10,semantic_clean=True,C5=False),
            dict(trajectory_id='a',onset=50,semantic_clean=True,C5=True),
            dict(trajectory_id='a',onset=90,semantic_clean=True,C5=True),
            dict(trajectory_id='b',onset=10,semantic_clean=True,C5=False)]
    r=trajectory_counts(['a','b','c'],events)
    assert r['eligible']==3 and r['new_demand']==2 and r['clean']==1
    assert r['primary']['a']['onset']==50
