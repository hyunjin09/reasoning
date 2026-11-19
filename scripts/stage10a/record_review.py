"""Record manually reviewed semantic spans from gold-free native trajectories."""
from pathlib import Path
from scripts.stage9a3.prepare import load,save,sha,now
from scripts.stage10a.anchors import locate,choose_cohort

ROOT=Path('outputs/stage10a/v1');OLD=Path('outputs/stage9a5/v1')
# image, attribute, first explicit aggregate fact, subsequent use, count, option-binding flag.
ANNOTATIONS=[
(0,'color',"So that's two yellow objects.","So yellow is two.",2,False),
(1,'shape',"That's two.","So only two stars.",2,False),
(2,'color',"Wait, so red objects are the two: the small red triangle and the red diamond.","So that's two red objects.",2,False),
(3,'shape',"So the only circle is the green one.","So the number of circle objects is 1.",1,False),
(4,'color',"So that's two blue objects.","Total 2.",2,False),
(5,'shape',"So only the yellow square is a square.","So only 1 square.",1,False),
(6,'color',"So that's two red objects.","So the answer should be D:2.",2,True),
(7,'shape',"- Blue square: one","So the blue square is the only square.",1,False),
(8,'color',"So only one green object, which is the green circle.","So the answer should be E: 1.",1,True),
(9,'shape',"So that's three.","So only three circles.",3,False),
(10,'color',"That's two.","That's two.",2,False),
(11,'color',"So only two yellow objects: the square and the circle.","So the answer should be C:2.",2,True),
(12,'color',"So only one red object.","So the answer should be E:1.",1,True),
(13,'shape',"So there are two triangles: the red one and the blue one.","Yep, that's two.",2,False),
(14,'color',"Wait, that's three.","So if there are three red objects, then the answer is A:3.",3,True),
(15,'shape',"So that's two circles.","So the answer should be A: 2.",2,True),
(16,'color',"So the only blue one is the blue circle.","So that's 1.",1,False),
(17,'shape',"That's two triangles.","So if there are two triangles, then the answer is B:2.",2,True),
(18,'color',"so that's two green objects.","Option E is 2.",2,True),
(19,'shape',"So only the blue square is a square.","So only 1 square.",1,False),
(20,'color',"Wait, the red objects—only the red circle.","So that's one.",1,False),
(21,'shape',"The green triangle is the only one.","So the answer should be 1, which is option C.",1,True),
(22,'color',"So that's two yellow objects.","Yep, that's two.",2,False),
(23,'shape',"So only the blue one is a star.","So the number of star objects is 1.",1,False),
(24,'color',"There's one yellow circle.","So the answer should be D: 1.",1,True),
(25,'shape',"Let's count: 1 (red) + 1 (green) = 2.","So the answer should be D: 2.",2,True),
(26,'color',"So that's three blue objects.","So D:3.",3,True),
(27,'color',"So that's two yellow objects.","Option D is 2.",2,True),
(28,'color',"That's 3.","So total 3.",3,False),
(29,'shape',"Let's count: there's one red star.","So the number of star objects is 1.",1,False),
(30,'color',"So that's two yellow objects.","So D:2 is the answer.",2,True),
(31,'shape',"That's three stars.","So total 3.",3,False),
]


def main():
    packet=OLD/'audit/full_review_packet.json';raw=load(packet);review={r['query_id']:r for r in raw['rows']}
    tasks={r['query_id']:r for r in load(OLD/'audit/inference_tasks.json')['rows']};rows=[]
    for i,attribute,fact,post,value,binding in ANNOTATIONS:
        q=f'image{i:03d}_{attribute}';r=review[q];assert r['automatic_option'] is not None and r['reasoning_closed']
        bounds=locate(r['reasoning_text'],fact,post)
        rows.append(dict(query_id=q,image_id=tasks[q]['image_id'],attribute=attribute,target=tasks[q]['target'],
            fact_text=fact,post_use_text=post,emitted_count=value,post_contains_option_binding=binding,
            native_reasoning=r['reasoning_text'],native_reasoning_tokens=r['reasoning_tokens'],
            anchor_rationale='First asserted aggregate count (including explicit singleton); later recount/verification or count-to-option use in native reasoning, before final channel.',
            query_fallback_reason='Preferred shape trace has no valid native final.' if i in (11,27) else None,
            generation_sha256=r['generation_sha256'],full_final_valid=True,**bounds))
    primary,reserve=choose_cohort(rows)
    save(ROOT/'audit/semantic_review.json',dict(at=now(),sealed=True,used_intervention_outcomes=False,
        used_final_correctness=False,gold_answer_keys_opened=False,packet_sha256=sha(packet),
        full_readout_packet='Only native reasoning and final-validity flag were displayed; masked Stage9A.5 rows were not used.',
        rows=rows,primary_ids=[r['query_id'] for r in primary],reserve_ids=[r['query_id'] for r in reserve],
        selection='Parity query preference, final-validity fallback, deterministic12+12 attribute-balanced image hash selection.'))
    print('REVIEW',len(rows),'PRIMARY',len(primary),'RESERVE',len(reserve),flush=True)


if __name__=='__main__':main()
