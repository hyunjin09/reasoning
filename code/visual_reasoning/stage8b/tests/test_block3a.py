import pytest
from visual_reasoning.stage8b.block3a import routing_subtype, select_anchors, pair_reads, replication


def test_subtype_uses_native_top_source_and_frozen_threshold():
    def r(q, **shares): return dict(qk_T_X=q, candidate_visual_shares=shares)
    assert routing_subtype('L-', r(.4,T=.3,X=.2)) == 'R1'
    assert routing_subtype('L-', r(2,T=.3,X=.2)) == 'R3'
    assert routing_subtype('L+', r(2,T=.3,X=.2)) == 'SELECTIVE_LPLUS'
    assert routing_subtype('L-', r(2,T=.1,X=.3)) == 'R2'
    assert routing_subtype('L-', r(2,T=.3,X=.3)) == 'R4'
    assert routing_subtype('L-', r(2,T=.3,X=.1,I=.4)) == 'R4'
    assert routing_subtype('L?', r(.4,T=.3,X=.2)) == 'R4'
    assert routing_subtype('L-', r(.4,T=.3)) == 'R4'


def test_selection_keeps_earliest_failure_and_independent_families():
    rows=[dict(event_id='a',item_id='1',family_id='f1',review_order=1,local='L-',qk_T_X=3),
          dict(event_id='b',item_id='1',family_id='f1',review_order=2,local='L-',qk_T_X=-2),
          dict(event_id='c',item_id='2',family_id='f2',review_order=3,local='L+',qk_T_X=.4),
          dict(event_id='d',item_id='3',family_id='f3',review_order=4,local='L+',qk_T_X=.2)]
    assert [r['event_id'] for r in select_anchors(rows,n=2)] == ['a','d']


def test_pairs_require_same_subgoal_and_never_reuse_rollouts():
    rows=[dict(item_id='1',family_id='f',subgoal='a',seed=s,local=l,event_id=str(s),category='binding') for s,l in [(1234,'L-'),(1235,'L+'),(1236,'L-'),(1237,'L+'),(1238,'L-')]]
    rows += [dict(item_id='1',family_id='f',subgoal='b',seed=1235,local='L-',event_id='other',category='binding')]
    pairs=pair_reads(rows)
    assert [(p['success'],p['failure']) for p in pairs] == [('1235','1236'),('1237','1238')]
    assert not pair_reads([rows[1],rows[-1]])


def test_replication_cannot_pass_low_yield_or_one_category():
    pairs=[dict(family_id=f'f{i}',category='binding' if i<10 else 'value',qk_T_X=1,share_T_X=.1) for i in range(20)]
    assert replication(pairs)['pass']
    assert not replication(pairs[:15])['pass']
    assert not replication([{**p,'category':'binding'} for p in pairs])['pass']
    assert not replication([{**p,'qk_T_X':-1,'share_T_X':-.1} for p in pairs])['pass']
