from scripts.stage10ar.analyze import summarize,robustness


def rows():
    return [dict(image_id=f'i{i:02d}',attribute='color' if i<12 else 'shape',target='target',source_count=2,
        condition=c,anchor=f'A{a}',correct=a>=3) for i in range(24) for c in ('image_off','text_only') for a in range(5)]


def test_joint_step_has_four_unit_contrasts_and_zero_late_necessity():
    r=summarize(rows())
    assert all(v['point']==1 and v['familywise95_ci']==[1,1] for v in r['primary'].values())
    assert r['curves']['image_off']['A0']['necessity']==1
    assert r['curves']['image_off']['A4']['necessity']==0
    assert robustness(rows())['all_directions_positive']


def test_missing_A2_does_not_change_primary_pairs():
    r=summarize([r for r in rows() if not(r['image_id']=='i00' and r['anchor']=='A2')])
    assert r['A2_secondary']['n_images']==23
    assert r['curves']['text_only']['A2']['n']==23
    assert all(v['point']==1 for v in r['primary'].values())
