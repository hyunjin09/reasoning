"""Prospective minimal A3 evidence edits; executed only after the main gate."""
from scripts.stage10ar.common import ROOT,load,save,sha,now

# One local evidence span; counterfactual adds one target object, sham keeps truth.
EDITS={
 'image001_shape':('yellow diamond (bottom right)','yellow star (bottom right)','yellow diamond-shaped object (bottom right)'),
 'image028_color':('and a green triangle at the top.','and a green triangle at the top, plus another green circle.','and a green triangular object at the top.'),
 'image016_color':('red circle, green star','blue circle, green star','red circular object, green star'),
 'image018_shape':('a green square.','a green triangle.','a green square-shaped object.'),
 'image020_color':('yellow square, green star','red square, green star','yellow square-shaped object, green star'),
 'image011_color':('- Bottom right: green circle (not yellow)','- Bottom right: yellow circle (yellow)','- Bottom right: green circular object (not yellow)'),
 'image025_color':('yellow diamond, green square.','yellow diamond, another red square.','yellow diamond, green square-shaped object.'),
 'image003_shape':('- Red square: not a circle.','- Red circle: that is a circle.','- Red square: not circular.'),
 'image029_shape':('a green square,','a green star,','a green square-shaped object,'),
 'image023_shape':('a green square.','a green star.','a green square-shaped object.'),
 'image021_shape':('a blue circle,','a blue triangle,','a blue circular object,'),
 'image013_shape':('a yellow diamond (which is a square rotated, but not a triangle)',
                    'a yellow triangle (which is a triangle)',
                    'a yellow diamond (a rotated square, not a triangle)'),
}


def main():
    review=load(ROOT/'audit/semantic_review.json');events={r['query_id']:r for r in review['rows']};rows=[]
    for query,spans in EDITS.items():
        e=events[query];assert query in review['primary_ids'] and e['chars']['A3']<e['chars']['A4']
        original=e['native_reasoning'][:e['chars']['A3']];old,cf,sham=spans;assert original.count(old)==1,(query,old)
        rows.append(dict(query_id=query,image_id=e['image_id'],attribute=e['attribute'],anchor='A3',
            original_span=old,counterfactual_span=cf,sham_span=sham,original_prefix=original,
            counterfactual_prefix=original.replace(old,cf),sham_prefix=original.replace(old,sham),
            original_count=e['source_count'],counterfactual_count=e['source_count']+1,
            edit_rationale='One evidence-bearing inventory clause gains exactly one target object; all other text is retained. The sham preserves the object identity/count.',
            semantics_reviewed_before_interventions=True))
    assert len(rows)==12
    save(ROOT/'audit/optional_a3_annotations.json',dict(at=now(),frozen=True,rows=rows,intervention_outcomes_used=False,
        selection_rule='Twelve primary events with A3<A4 and a manually verified local inventory/clause edit. Five color/seven shape; no effect ranking.',
        caveat='Minimal local edits retain earlier descriptions and subtotals; they can conflict with the edited inventory. This optional test does not rewrite every textual carrier.',
        main_gate_required=True,semantic_review_sha256=sha(ROOT/'audit/semantic_review.json')))
    print('OPTIONAL_A3_EDITS_FROZEN',len(rows))


if __name__=='__main__':main()
