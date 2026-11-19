from visual_reasoning.stage9a_dynamics.amendment import stratified_select,choose_demand,matched_control


def test_exact_balanced_disjoint_reserves_independent_of_input_order():
    rows=[dict(family_id=f'f{i}',subject=f's{i%5}',difficulty=i%3,answer_format=i%2) for i in range(128)]
    selected=stratified_select(rows,64)
    assert selected==stratified_select(list(reversed(rows)),64)
    ids={r['family_id'] for r in selected};assert len(ids)==64
    reserve=[r for r in rows if r['family_id'] not in ids]
    extension=stratified_select(reserve,32)
    assert len(extension)==32 and not ids.intersection(r['family_id'] for r in extension)
    for subject in {r['subject'] for r in rows}:
        full=sum(r['subject']==subject for r in rows);main=sum(r['subject']==subject for r in selected)
        assert abs(main-full/2)<=.5


def test_semantic_event_preference_and_control_exclusion():
    rows=[dict(event_id=str(i),demand_token=d,normalized_position=d/1000,valid_full_radius16=valid)
          for i,(d,valid) in enumerate([(100,True),(250,True),(400,True),(300,False),(600,True)])]
    chosen=choose_demand(rows);assert chosen['demand_token']==400
    control,kind=matched_control(400,0,1000,[100,250,400,600])
    assert control[1]-control[0]==33
    assert all(control[1]<=d-32 or control[0]>=d+33 for d in [100,250,400,600])
    assert abs(control[0]-(400-16))==49
    assert choose_demand(rows[:2])['demand_token']==100
