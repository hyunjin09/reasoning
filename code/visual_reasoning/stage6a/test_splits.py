from visual_reasoning.stage6a.splits import connected_groups,assign_split


def test_transitive_image_template_links_do_not_cross_groups():
    groups=connected_groups(['a','b','c','d'],[('a','b'),('c','b')])
    assert groups==[['a','b','c'],['d']]
    assert connected_groups(['d','c','b','a'],[('b','c'),('b','a')])==groups


def test_new_unrelated_sources_do_not_change_existing_assignments():
    before={g[0]:assign_split(g[0]) for g in connected_groups(['a','b','c'],[('a','b')])}
    after={g[0]:assign_split(g[0]) for g in connected_groups(['a','b','c','d'],[('a','b')])}
    assert all(after[k]==v for k,v in before.items())
def test_extension_inherits_and_preserves_existing_assignments():
    from visual_reasoning.stage6a.splits import extension_assignments
    prior={'a':{'group_id':'g1','split':'discovery'},'b':{'group_id':'g2','split':'confirmation'}}
    result=extension_assignments(prior,['x','y'],[['a','x'],['b','y']])
    assert result['x']['split']=='discovery'
    assert result['y']['split']=='confirmation'
    assert prior['a']=={'group_id':'g1','split':'discovery'}


def test_extension_bridge_is_excluded_without_reshuffling_prior():
    from visual_reasoning.stage6a.splits import extension_assignments
    prior={'a':{'group_id':'g1','split':'discovery'},'b':{'group_id':'g2','split':'confirmation'}}
    result=extension_assignments(prior,['x'],[['a','x'],['b','x']])
    assert result['x']['split']=='excluded_cross_fold_bridge'
    assert result['x']['linked_existing_group_ids']==['g1','g2']


def test_extension_validation_overlap_does_not_enter_confirmation():
    from visual_reasoning.stage6a.splits import extension_assignments
    result=extension_assignments({},['x'],[['v','x']],overlap_ids={'v':'validation'})
    assert result['x']['split']=='excluded_validation_overlap'
