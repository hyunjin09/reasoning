"""Check causal contrast orientation and the independent-family denominator."""
import pytest
from visual_reasoning.stage9a_dynamics.analysis import family_metrics, contrast


def panel(arm, family='f', demand=None, control=None):
    rows=[]
    for name, value in [('cutoff_full',1),('cutoff_512',0),('cutoff_2048',1),
                        ('local20_3',0),('local20_4',1)]:
        rows.append(dict(family_id=family,arm=arm,condition_id=name,assay='local' if name.startswith('local') else 'cumulative',accuracy_no_credit=value))
    for role,value in [('demand',demand),('control',control)]:
        if value is not None:rows.append(dict(family_id=family,arm=arm,condition_id=role,assay='demand',role=role,accuracy_no_credit=value))
    return rows


def test_demand_direction_and_within_family_late_average():
    metrics=family_metrics(panel('instruct_cot',demand=0,control=0)+panel('thinking',demand=0,control=1))
    assert all(r['primary']['late_damage']==.5 for r in metrics)
    result=contrast(metrics,'demand_minus_control')
    assert result['mean']==1 and result['n_families']==1
    assert result['family_directions']=={'positive':1,'negative':0,'tie':0}


def test_missing_demand_is_not_a_zero():
    metrics=family_metrics(panel('instruct_cot')+panel('thinking',demand=0,control=1))
    result=contrast(metrics,'demand_minus_control')
    assert result['n_families']==0 and result['mean'] is None


def test_duplicate_condition_rejected():
    rows=panel('thinking')
    with pytest.raises(ValueError,match='Duplicate'):
        family_metrics(rows+[rows[0]])


def test_family_threshold_and_effect_units():
    rows=[]
    for i in range(20):
        for arm in ('instruct_cot','thinking'):
            data=panel(arm,str(i));data[1]['accuracy_no_credit']=int(arm=='instruct_cot');rows+=data
    result=contrast(family_metrics(rows),'cutoff512_damage')
    assert result['n_families']==20 and result['mean']==1
    assert result['ci']==[1,1] and result['bootstrap_replicates']==4000
    result=contrast(family_metrics([r for r in rows if r['family_id']!='19']),'cutoff512_damage')
    assert result['n_families']==19 and result['ci'] is None


def test_null_sink_damage_orientation_and_exact_matching():
    from scripts.stage9a_dynamics.analyze_controls import paired_control_rows
    full=dict(task_id='t',condition_id='cutoff_full',accuracy_no_credit=1,accuracy_raw=1)
    standard=dict(task_id='t',condition_id='local20_4',accuracy_no_credit=0,accuracy_raw=0,
                  intervals=[[80,100]],assay='local',benchmark_label='wrong')
    sink=dict(task_id='t',standard_condition='local20_4',accuracy_no_credit=1,accuracy_raw=1,
              intervals=[[80,100]])
    row=paired_control_rows([sink],[full,standard])[0]
    assert row['standard_damage']==1 and row['null_sink_damage']==0
    assert row['null_minus_standard_damage']==-1
    with pytest.raises(AssertionError):
        paired_control_rows([dict(sink,intervals=[[60,100]])],[full,standard])


def test_local_events_do_not_inflate_family_weight():
    from scripts.stage9a_dynamics.secondary_analysis import grouped_family_mean
    result=grouped_family_mean([dict(family_id='a',value=1),dict(family_id='a',value=3),
                               dict(family_id='b',value=0)],'value')
    assert result['n_families']==2 and result['mean']==1 and result['ci'] is None


def test_exposure_respects_actual_termination_and_query_zero():
    from scripts.stage9a_dynamics.secondary_analysis import continuation_summary
    row=dict(arm='thinking',assay='cumulative',condition_id='cutoff_0',first_divergence_token=None,
             tokens=5,native_tokens=5,accuracy_no_credit=1,accuracy_raw=1,benchmark_label='correct',
             completion='normal completed',normal_eos=True,at_length_cap=False,identical_native=True,
             intervals=[[1,None]])
    result=continuation_summary([row])[0]
    assert result['total_masked_queries']==4 and result['exposed_trajectories']==1
    result=continuation_summary([dict(row,intervals=[[6,None]])])[0]
    assert result['total_masked_queries']==0 and result['exposed_trajectories']==0
