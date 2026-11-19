from visual_reasoning.stage9a_dynamics.protocol import cumulative_interval, local_windows, demand_control


def test_windows_partition_native_reasoning_with_no_overlap():
    assert local_windows(7,30)==[(7,9),(9,11),(11,13),(13,16),(16,18),(18,20),(20,23),(23,25),(25,27),(27,30)]
    assert cumulative_interval(16)==(17,None)
    assert cumulative_interval(None) is None


def test_control_matches_exposure_and_avoids_annotated_demands():
    event,control=demand_control(5,16,0,500,[5,100],[])
    assert event==(1,22)
    assert control[1]-control[0]==21
    assert all(control[1]<=d-32 or control[0]>=d+33 for d in (5,100))


def test_unavailable_shifted_control_stays_missing():
    assert demand_control(5,16,0,20,[5],[])[1] is None
