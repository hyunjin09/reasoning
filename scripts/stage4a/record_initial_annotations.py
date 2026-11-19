"""Materialize manually reviewed numeric identities and exact candidate positions.

These remain candidates until independent edits and token maps pass review.
"""
from scripts.stage4a.prepare_config import OUT,read_jsonl,write_jsonl


def main():
    # Explicit reviewer judgments, not matches accepted automatically.
    choices=[
        ('19',1,3,[41,1049,1119],['148','52'],[[205,65,248,90],[177,96,208,119]],
         ['Reads the upper zigzag angle1 label.','Checks the identity/value of angle2 while reconstructing the zigzag.','Returns to the upper angle1 label during figure reinspection.'],
         'Questioning/reinspection is retained as a local fact-identification demand, not evidence of successful refresh. The unidentified 42 at80 is not a valid angle2 event.'),
        ('244',1,3,[169,197,293],['68','57'],[[450,280,543,354],[868,280,957,354]],
         ['Identifies angle1 at A as58.','Identifies angle2 at B as47.','Returns to angle1 at A while reconstructing the triangle.'],
         'Angle labels1 and2 have unambiguous identities at the selected mentions; later native geometric errors are preserved.'),
        ('265',1,4,[204,229,704],['8','25'],[[287,382,312,414],[314,273,357,304]],
         ['Reads the coefficient7 of the7x-5 angle expression.','Reads the constant23 of angle4 expression2x+23.','Returns to the7x-5 expression pointing to angle5.'],
         'The intervening numeric7 in angle enumeration is not a formula coefficient; first preferred-gap reuse is704.'),
        ('716',0,1,[178,202,537],['24','30'],[[365,119,389,141],[289,205,314,225]],
         ['Reads a box edge dimension20 for surface area.','Reads the distinct box edge dimension25.','Reuses the20 box dimension while decomposing the solid.'],
         'Native height/depth naming is permuted. The annotated facts are the distinct box edge magnitudes, whose surface-area roles are symmetric; this is not a claim of correct orientation parsing.'),
        ('132',1,3,[96,160,305],['14','1.8'],[[183,92,214,115],[394,119,427,140]],
         ['Identifies horizontal CG length12.','Identifies FE height1.6.','Returns to CG length12 while reconstructing the similar-triangle diagram.'],
         'The repeated0.6 labels do not form an independently editable single source. Native2 is initially assigned to the wrong vertical GF segment and is excluded as a fact identity.'),
        ('263',0,2,[311,359,460],['2','5'],[[15,90,35,120],[190,90,210,120]],
         ['Reads coefficient3 of left side3x+1.','Reads coefficient4 of right side4x-2.','Reuses3x+1 to establish equal side lengths.'],
         'The first right-side mention318 is too close toA1;359 and460 are the earliest preferred-gap formula uses. Counterfactual equations retain positive side solutions in all four contexts.'),
    ]
    by={r['base_problem_id']:r for r in read_jsonl(OUT/'cohort/numeric_proposals.jsonl')}
    records=[]
    for base,ai,bi,positions,changed,boxes,reasons,note in choices:
        r=by[base];facts={f['fact_id']:f for f in r['facts']}
        selected={x:{'fact_id':fi,'original_value':facts[fi]['original_value'],'counterfactual_value':cf,
                     'roi_xyxy':box,'text_color':[0,0,0],'background_mode':'roi_bright_median'}
                  for x,fi,cf,box in zip(['A','B'],[ai,bi],changed,boxes)}
        events={}
        for e,x,pos,reason in zip(['A1','B','A2'],['A','B','A'],positions,reasons):
            f=facts[selected[x]['fact_id']]
            m=next(m for m in f['mentions'] if m['candidate_start_token']==pos)
            events[e]={**m,'fact':x,'semantic_judgment':reason,'event_type':'grounded_fact_identification_or_use',
                       'current_query_zero_based':pos-1}
        records.append({k:r[k] for k in ['base_problem_id','example_id','screen_order','source_image','artifact_dir','question']}|
                       {'facts':selected,'events':events,'review_note':note,'semantic_reviewed':True,
                        'edits_reviewed':False,'token_map_validated':False,'retained':False,
                        'attention_used':False,'causal_scores_available':False})
    target=OUT/'cohort/manual_annotations.jsonl'
    if target.exists():raise FileExistsError(target)
    write_jsonl(target,records)
    print(f'{len(records)} provisional semantic annotations; edits/token maps still pending')


if __name__=='__main__':main()
