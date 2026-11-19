"""Source-only role tags with explicit uncertainty, never replay-derived labels."""
import re

PATTERNS=[
 ('CONSISTENCY_CHECK',r"let.s (?:check|verify)|double.check|consistent|verify|checking|checks out"),
 ('REINTERPRETATION',r'wait, no|wait, maybe|alternatively|another (?:way|possibility|interpretation)|misread|mistake|incorrect|but wait|actually'),
 ('REPRESENTATION_SETUP',r'let(?:.s| us)? (?:set|define|place|put|denote|assign|use)|coordinate system|suppose|assume|let [a-zαβθ] (?:be|=)|origin'),
 ('INTERMEDIATE_CALCULATION',r'\d\s*[-+*/×=]|=\s*[-+]?\d|⇒|calculate|calculating|compute|computing|substitut|simplif|solve for'),
 ('DERIVED_RELATION',r'equals?|equal to|formula|therefore|implies|theorem|=|perpendicular|parallel|proportional'),
 ('ENTITY_BINDING',r'points? [A-Z]|point|vertex|vertices|label|collinear|colinear|intersect|between|from [A-Z] to [A-Z]'),
 ('VISUAL_EVIDENCE',r'(?:image|diagram|picture|figure) (?:shows|has|is)|shown|gray|white|see (?:that|the)'),
 ('SUBGOAL_CONCLUSION',r'we (?:have|found|know)|thus|hence|so the|this (?:gives|means)'),
 ('META_REASONING',r"let.s|need to|want to|trying|try to|perhaps|maybe|i think|question|problem|wait"),
]


def annotate(parts,item):
    seen=set();seen_values=set();rows=[]
    for k,text in enumerate(parts,1):
        normalized=re.sub(r'\s+',' ',text).strip().lower()
        hits=[(cat,m.group(0)) for cat,pat in PATTERNS if (m:=re.search(pat,text,re.I))]
        category=hits[0][0] if hits else 'OTHER'
        repetition=normalized in seen
        assertion=bool(re.search(r'=|\b(?:is|are|equals|has|must|therefore|thus)\b',text,re.I))
        image=category=='VISUAL_EVIDENCE'
        derived=category in ['DERIVED_RELATION','INTERMEDIATE_CALCULATION','SUBGOAL_CONCLUSION']
        facts=({'798':r'1.unit thick|1 unit thick|one cube|one unit',
                '2975':r'collinear|colinear|secant|between B and T|near.*far|far.*near',
                '750':r'three (?:other )?sides|partition|end.to.end|without gaps|sum.*(?:equals|equal to).*AB',
                '2908':r'(?:mutually|externally) tangent|tangent to each other|touch each other'}[item])
        fact_reference=bool(re.search(facts,text,re.I))
        values=set(re.findall(r'(?<!\w)\d+(?:\.\d+)?|[αβθ]',text));new_values=sorted(values-seen_values)
        rows.append(dict(item_id=item,step_index=k,category=category,
            introduces_new_factual_proposition=False if repetition else (True if assertion else None),
            image_or_derived='IMAGE_CLAIM' if image else 'DERIVED' if derived else 'UNRESOLVED',
            depends_on_frozen_E_star=True if fact_reference else None,
            introduces_new_numeric_symbolic_value=bool(new_values),new_numeric_symbolic_markers=new_values,
            corrects_earlier_error=True if re.search(r'wait, no|mistake|incorrect|misread',text,re.I) else None,
            restates_prior_content=repetition,
            role_basis=hits[0][1] if hits else 'No unambiguous cue; OTHER',
            annotation_method='Deterministic source-text role cues; ambiguous proposition/origin/dependency/correction flags remain null. Restatement uses normalized exact prior text.',
            semantic_truth_certified=False))
        seen.add(normalized);seen_values.update(values)
    # Fully read short source; correct broad lexical defaults before replay.
    if item=='798':
        categories=['META_REASONING','REINTERPRETATION','REPRESENTATION_SETUP','REINTERPRETATION','META_REASONING','DERIVED_RELATION','DERIVED_RELATION','REINTERPRETATION','REPRESENTATION_SETUP','REINTERPRETATION','INTERMEDIATE_CALCULATION','CONSISTENCY_CHECK','REINTERPRETATION','REINTERPRETATION','VISUAL_EVIDENCE','META_REASONING','META_REASONING','REINTERPRETATION','META_REASONING','DERIVED_RELATION','REINTERPRETATION','DERIVED_RELATION','INTERMEDIATE_CALCULATION','DERIVED_RELATION','INTERMEDIATE_CALCULATION','DERIVED_RELATION','DERIVED_RELATION','CONSISTENCY_CHECK']
        assert len(categories)==len(rows)
        for row,cat in zip(rows,categories):
            row['category']=cat;row['annotation_method']+=' Primary role manually reviewed from complete short source before replay.'
    return rows
