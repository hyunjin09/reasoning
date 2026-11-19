"""Manual semantic annotations use native successful traces and source truth only."""
import hashlib
from scripts.stage10ar.common import ROOT,OLD,DATA,PROTOCOL,load,save,sha,now

# A1 end; A2 end (None if absent); A3 end; A4 complete aggregate fact.
ANNOTATIONS={
0:("There's a yellow circle on the top left,",'and a yellow star next to it.',"So that's two yellow objects.","So that's two yellow objects."),
1:("there's a red star at the top right,",'a green star at the bottom left,','red circle (bottom middle), green star (bottom left).',"That's two."),
2:('the small red triangle at the top left,','the red diamond in the middle right,','- Green star (right middle)','Wait, so red objects are the two: the small red triangle and the red diamond.'),
3:('- Blue square: not a circle.','- Green diamond: not a circle.','- Red square: not a circle.','So the only circle is the green one.'),
4:("there's a blue star at the top.","there's a blue square.",'and the blue ones are the star and the square.',"So that's two blue objects."),
5:("there's a blue star.","Then, there's a blue circle.",'Then the red diamond, yellow square, blue circle, and yellow diamond.',"That's two."),
6:('The red objects are the red circle and',None,'The red objects are the red circle and the red square.',"So that's two red objects."),
7:('- Blue circles: there are two (small and large)','- Blue triangles: two (small and medium)','- Blue square: one','- Blue square: one'),
8:("There's a green circle on the left.",'The other shapes are blue circles,','The other shapes are blue circles, yellow stars, blue triangles.','So only one green object, which is the green circle.'),
9:('- The blue triangle: that\'s a triangle, not a circle.','- The yellow square: square, not a circle.','The yellow one at the bottom is a small yellow circle.',"So that's three."),
10:("there's a blue diamond (the square with blue color) and",None,"there's a blue diamond (the square with blue color) and a blue circle.","That's two."),
11:("There's a yellow square at the top left,",'a yellow circle in the middle,','- Bottom right: green circle (not yellow)','So only two yellow objects: the square and the circle.'),
12:("There's a red circle at the bottom left, right?",'green diamonds,','green diamonds, green circle, green triangle, blue triangle, red circle.','So only one red object.'),
13:('a yellow diamond (which is a square rotated, but not a triangle),','a red triangle,','and a blue triangle.','So there are two triangles: the red one and the blue one.'),
14:('- The green star is not red.','- The red square is one red object.','- The red star is a third red object.',"Wait, that's three."),
15:('- The red diamond (square-like) is a diamond, not a circle.',"- The green circle: that's a circle.",'- The green triangle: triangle, not a circle.',"So that's two circles."),
16:("There's a blue circle, right?",'red circle,','red circle, green star, yellow triangle, red diamond, yellow small triangle.','So the only blue one is the blue circle.'),
17:("there's a yellow star (that's a star, not a triangle),",'a blue star (also a star),','(the first one), then a blue star, a green circle, a yellow star, a green triangle, a blue star, a green circle.',"That's two triangles."),
18:("It's a red triangle.","- The blue shape at the bottom left: that's a blue triangle.",'a small green star, a blue star, a green square.',"So that's two triangles."),
19:('The yellow one is the small triangle, right?',"There's a red triangle,",'green diamond, blue square.','So the yellow object is just the small yellow triangle.'),
20:("There's a red circle, right?",'green circles (two),','yellow square, green star, green triangle, green square.','Wait, the red objects—only the red circle.'),
21:("There's a green triangle, right?",'a green triangle, a green star,','another red circle, and a red star.','The green triangle is the only one.'),
22:("There's a green circle,",'a red square,','a yellow triangle, and another red star.',"So that's two yellow objects."),
23:("In the image, there's a blue star.",'a blue star, a yellow diamond,','a yellow circle, a green square.','So only the blue one is a star.'),
24:('The yellow one is a circle, right?',None,"There's one yellow circle.","There's one yellow circle."),
25:('The red square is there, right?',"Let's check all the shapes: green star,",'blue circle, yellow diamond, green square.','So only one red object, which is the red square.'),
26:("There's a blue triangle at the top,",'a blue star on the left,','the image has: a blue triangle (top center), a blue star (left side), and a blue star (right side).',"So that's three blue objects."),
27:('The yellow objects are the yellow circle and',None,'The yellow objects are the yellow circle and the yellow diamond.',"So that's two yellow objects."),
28:('The green objects are the green circles and','The green objects are the green circles and the green triangle.',"There's a green circle on the left, another green circle on the right, and a green triangle at the top.","That's 3."),
29:('The shapes present are triangles (green),','a square (red),','a red star, and a blue diamond.',"there's one red star."),
30:('- The top right has a blue square, not yellow.',"- The top middle has a yellow star, that's one.",'- The red circle is red, blue star is blue, small blue star is blue, red triangle is red.',"So that's two yellow objects."),
31:("In the image, there's a red star,",'a blue star,','So the stars are red, blue, and green.',"That's three stars."),
}


def main():
    baseline={r['query_id']:r for r in load(OLD/'stage9a5_thinking_full_baseline.json')['rows']}
    tasks={r['query_id']:r for r in load(OLD/'audit/inference_tasks.json')['rows']}
    gold={r['query_id']:r for r in load(DATA/'stage9a3_synthetic_dataset_manifest.json')['queries']};rows=[]
    for index,markers in ANNOTATIONS.items():
        pref='color' if index%2==0 else 'shape';q=f'image{index:03d}_{pref}';fallback=None
        if not baseline[q]['correct']:
            fallback='Parity-preferred query lacks a correct valid FULL answer.'
            q=f'image{index:03d}_'+('shape' if pref=='color' else 'color')
        b=baseline[q];assert b['correct'] and b['reasoning_closed'] and not b['unscorable']
        g=load(b['generation_path']);text=g['reasoning_text'];a1,a2,a3,fact=markers
        end=lambda s:text.index(s)+len(s)
        chars=dict(A0=0,A1=end(a1),A2=end(a2) if a2 else None,A3=end(a3),A4=end(fact))
        assert 0<chars['A1']<chars['A3']<=chars['A4'],(q,chars)
        if a2:assert chars['A1']<chars['A2']<chars['A3'],(q,chars)
        rationale='A3 closes the source-correct inventory/remainder classification; count follows from the question and stated objects without the image. Earlier evidence remains an open/incomplete list.'
        if chars['A3']==chars['A4']:rationale='No earlier unambiguously closed inventory determines the answer; A3 coincides with the first complete aggregate fact. No artificial separation.'
        if index==17:rationale+=' Initial yellow-star misclassification is corrected in the later quoted scene description; no intervention outcome selected this revision.'
        rows.append(dict(query_id=q,image_id=b['image_id'],attribute=tasks[q]['attribute'],target=tasks[q]['target'],
            task=tasks[q],source_count=gold[q]['count'],source_answer=gold[q]['answer'],full_correct=True,
            generation_path=b['generation_path'],result_path=b['result_path'],generation_sha256=sha(b['generation_path']),
            native_reasoning=text,chars=chars,markers=dict(A0='',A1=a1,A2=a2,A3=a3,A4=fact),fact_text=fact,
            A1_rationale='First attribute-relevant identification/exclusion; remaining scene/target multiplicity unresolved.',
            A2_rationale='Second distinct evidence unit, still underdetermined.' if a2 else 'No distinct intermediate partial-accumulation state: the second unit closes the scoped inventory, or only one evidence unit is stated.',
            A3_rationale=rationale,query_fallback_reason=fallback,
            annotation_scope='Manual native-text and source-semantic review; no Stage10AR outcomes exist or were opened.'))
    key=lambda r:hashlib.sha256(('stage10ar-v1-920260927:'+r['image_id']).encode()).hexdigest()
    groups={a:sorted([r for r in rows if r['attribute']==a],key=key) for a in ('color','shape')}
    assert all(len(rs)>=12 for rs in groups.values())
    primary=sorted(groups['color'][:12]+groups['shape'][:12],key=key);reserve=sorted(groups['color'][12:]+groups['shape'][12:],key=key)
    assert len(primary)==24 and len(reserve)==8
    save(ROOT/'audit/semantic_review.json',dict(at=now(),sealed=True,rows=rows,primary_ids=[r['query_id'] for r in primary],reserve_ids=[r['query_id'] for r in reserve],
        native_FULL_correctness_used=True,intervention_outcomes_used=False,protocol_sha256=sha(PROTOCOL),annotation_script_sha256=sha(__file__)))
    print('SEALED_ANNOTATIONS',len(rows),'PRIMARY',len(primary),'RESERVE',len(reserve),flush=True)


if __name__=='__main__':main()
