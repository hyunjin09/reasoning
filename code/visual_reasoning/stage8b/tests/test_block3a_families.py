from visual_reasoning.stage8b.block3a_families import replication_by_family


def test_rescaled_image_aliases_do_not_inflate_independent_yield():
    pairs=[dict(item_id=str(i),family_id=f'original{i}',analysis_family_id=f'f{i if i<15 else 0}',category='a' if i<8 else 'b',qk_T_X=1,share_T_X=.2) for i in range(16)]
    pairs+=pairs[:4]
    result=replication_by_family(pairs)
    assert result['items']==16 and result['families']==15
    assert not result['pass']


def test_category_breadth_uses_its_own_contrasts_within_each_family():
    pairs=[dict(item_id=str(i),family_id=f'f{i}',analysis_family_id=f'f{i}',category=c,qk_T_X=value,share_T_X=value/10) for i in range(20) for c,value in [('a',-1),('b',10)]]
    result=replication_by_family(pairs)
    assert result['metrics']['qk_T_X']['median']>0
    assert result['metrics']['qk_T_X']['categories']['a']['median']==-1
    assert not result['pass']
