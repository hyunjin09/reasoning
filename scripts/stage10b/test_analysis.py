from scripts.stage10b.analyze import inference,classify


def event(tid,ident,onset,semantic,c5,category):
    return dict(trajectory_id=tid,event_id=ident,onset=onset,semantic_clean=semantic,C5=c5,
                classification=category,lag=3 if c5 else None,taxonomy='S1',target_type='number')


def test_known_positive_is_not_counted_again_as_missing_and_bounds_use_families():
    rows=[event('a','a1',10,True,False,'ROUTING_DATA_MISSING'),
          event('a','a2',20,True,True,'CLEAN_REACCESS'),
          event('b','b1',10,True,False,'ROUTING_DATA_MISSING'),
          event('b','b2',20,True,False,'TARGET_AMBIGUOUS'),
          event('c','c1',10,True,False,'ATTENTION_ONLY')]
    r=inference(['a','b','c','d'],rows)
    assert r['clean']==1 and r['new_demand']==3
    assert r['unresolved_C5_trajectories']==['b']
    assert r['missing_data_yield_bounds']==[.25,.5]
    assert r['observed_C5_only']['n']==2
    assert r['primary_event_ids']==['a2'] and r['timing']['offsets']==[3]


def test_semantic_failure_remains_negative_even_with_passive_reaccess():
    e=dict(semantic_clean=False,C5=True,prior_availability='SUFFICIENT',C1=True,C2=True,C3=True)
    assert classify(e)=='B_ALREADY_TEXTUALIZED'
    assert inference([],[])['E3']['point'] is None
