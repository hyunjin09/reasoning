import math
from visual_reasoning.stage9a3.dataset import scene, prompt


def test_scene_is_reproducible_and_queries_recount_actual_attributes():
    for i in range(52):
        a=scene(i);assert a==scene(i)
        assert len(a['objects']) in (6,7)
        assert {q['attribute'] for q in a['queries']}=={'color','shape'}
        for q in a['queries']:
            assert q['count']==sum(o[q['attribute']]==q['target'] for o in a['objects'])
            assert sorted(q['options'].values())==[1,2,3,4,5]
            assert q['options'][q['answer']]==q['count']


def test_visible_objects_do_not_touch_or_leave_frame():
    for i in range(52):
        objects=scene(i)['objects']
        for j,a in enumerate(objects):
            x,y=a['center'];radius=a['diameter']/2
            assert radius<=x<=256-radius and radius<=y<=256-radius
            for b in objects[:j]:
                assert math.dist(a['center'],b['center'])>=radius+b['diameter']/2+6


def test_prompt_is_common_and_only_uses_question_and_options():
    q=scene(0)['queries'][0];text=prompt(q)
    assert 'Think step by step. You must write intermediate steps.' in text
    assert text.endswith('Respond in curly braces format: {A}')
    assert text==prompt(dict(q,answer='Z',count=100))
