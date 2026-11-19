import torch
from visual_reasoning.stage8c.forensics import error_record,source_partition


def test_partition_counts_masked_and_invalid_visual_positions():
    p=source_partition(total=8,visual=[2,3],valid=[0,1,2,3,5,6])
    assert p['pass_partition'] and p['nonvisual_positions']==[0,1,5,6]
    assert p['masked_positions']==[4,7] and p['uncovered_count']==0
    assert not source_partition(total=8,visual=[2,7],valid=[0,1,2])['pass_partition']


def test_forensic_record_retains_failure_magnitude_and_location():
    a=torch.tensor([[1.,2.],[3.,4.]])
    b=a.clone();b[1,0]+=1
    r=error_record(a,b)
    assert not r['pass_bounds'] and r['largest_error_index']==[1,0]
    assert r['max_abs']==1 and r['native_at_max']==3 and r['reconstructed_at_max']==4
