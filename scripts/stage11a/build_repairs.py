"""Prospective semantic repairs only; no native traces or model outcomes loaded."""
from copy import deepcopy
from scripts.stage11a.common import ROOT,load,save,sha,now

proposal=ROOT/'audit/e_star_proposal.json'
rows={r['item_id']:deepcopy(r) for r in load(proposal)['rows']}
for who in ['a','b']:assert load(ROOT/'annotations'/f'sufficiency_{who}.json')['sealed']
changed={}

def fact(ident,key,typ,value,request,visibility='direct'):
    return dict(fact_id=key,evidence_type=typ,source_ref=rows[ident]['image']+' | '+request,roi_normalized=None,
        gold_value=value,accepted_paraphrases=[value],exact_lexical_required=False,visibility=visibility,probe_request=request)

def add(ident,typ,value,request,visibility='direct'):
    rows[ident]['facts'].append(fact(ident,'repair_'+str(len(rows[ident]['facts'])+1),typ,value,request,visibility))

def record(ident,reason):
    r=rows[ident];r['reason']=r['sufficiency_reason']=reason;r['sufficiency']='SUFFICIENT';r['eligibility']='E_STAR_ELIGIBLE';changed[ident]=r

def exclude(ident,reason,label='E_STAR_TOO_LARGE'):
    r=rows[ident];r.update(eligibility=label,sufficiency='AMBIGUOUS' if label=='E_STAR_AMBIGUOUS' else 'INSUFFICIENT',facts=[],reason=reason,sufficiency_reason=reason);changed[ident]=r

add('2214','incidence','D lies on segment AB.','On which outer triangle side does D lie?')
add('2214','incidence','E lies on segment AC.','On which outer triangle side does E lie?')
rows['2214']['facts']=rows['2214']['facts'][1:]
record('2214','Explicit outer-side incidences complete the four-base similarity argument. DE parallel BC follows from the text-given trapezoid and these incidences, so it is omitted as redundant.')
f=rows['1789']['facts'][1];f['gold_value']='The second fold brings the original right corner to the midpoint of the first fold crease.';f['accepted_paraphrases']=[f['gold_value']]
record('1789','The second fold destination is its visible crease midpoint, fixing the previously unspecified position.')
add('1430','ordering/comparison','The horizontal outer sides of the flag are the longer sides.','Which direction contains the longer outer flag sides?')
record('1430','The outer aspect-ratio orientation is now explicit, alongside the partition and white-region identity.')
add('1974','incidence','PQ is the left vertical side of the outer rectangle.','Locate side PQ in the outer rectangle.')
record('1974','Three layout/count facts and the named-side orientation determine the requested ratio without including derived side ratios.')
add('2876','length label','The bottom horizontal side has length 8.','What length is labeled on the bottom horizontal edge?')
record('2876','The visible horizontal dimension fixes orientation for the two corner folds.')
add('711','color','All five component triangles are shaded.','Which component triangles are shaded?')
rows['711']['facts'][0]['gold_value']='The complete horizontal span is labelled 30 cm.'
rows['711']['facts'][0]['accepted_paraphrases']=[rows['711']['facts'][0]['gold_value']]
record('711','The target shaded-region membership is explicit alongside the full span and hypotenuse arrangement.')
r=rows['991'];r['facts'][0]['probe_request']='What size rank does the top block have among all blocks?';r['facts'][0]['source_ref']=r['image']+' | '+r['facts'][0]['probe_request']
r['facts'][3]=fact('991','repair_count','count','There are four blocks in the stack.','How many blocks are in the stack?','trivial_aggregation')
record('991','Total count replaces the redundant bottom rank. Count plus three ranks fixes the fourth, and no query supplies the count.')
r=rows['2580'];r['facts']=[fact('2580','repair_boundary','diagram topology','Segments AE, ED, DC and CA form a simple quadrilateral in that cyclic order.','Describe the boundary formed by segments AE, ED, DC and CA, including whether it crosses itself.'),r['facts'][1],r['facts'][3]]
record('2580','The noncrossing quadrilateral boundary identifies the text-given A/C right angles and prevents a reflected configuration, without giving a derived angle or parallelism.')
r=rows['1478'];r['facts'][3]['probe_request']='On which triangle sides do the leftmost and lowest vertices of R lie?';r['facts'][3]['source_ref']=r['image']+' | '+r['facts'][3]['probe_request']
record('1478','The last request no longer names the hypotenuse placement supplied by a separate fact; joint probe cross-leak is removed.')
directions=[('top','2','below'),('bottom','3','above'),('left','3','to the right of'),('right','4','to the left of')]
for f,(side,value,direction) in zip(rows['1146']['facts'],directions):
    f['gold_value']=f'The smaller rectangle’s {side} side is {value} m {direction} the larger rectangle’s {side} side.'
    f['accepted_paraphrases']=[f['gold_value']]
    f['probe_request']=f'State the labeled distance and direction from the larger rectangle’s {side} side to the smaller rectangle’s {side} side.'
    f['source_ref']=rows['1146']['image']+' | '+f['probe_request']
record('1146','Four oriented-distance facts explicitly locate the inner sides; unsigned gaps no longer silently assume nesting.')
r=rows['191'];r['facts']=[
    fact('191','repair_diameter','spatial relation','Each small circle has a radius of the large circle as its diameter.','Which segment of the large circle serves as a diameter of each small circle?'),
    fact('191','repair_directions','diagram topology','The small-circle diameter segments occupy exactly the four radius rays of two perpendicular diameters of the large circle.','Describe the full arrangement of the small-circle diameter directions around the large-circle center.'),
    fact('191','repair_blue','color','The B labels identify the pairwise overlap lenses of the small circles.','Which regions carry B in relation to the small circles?'),
    fact('191','repair_green','color','The G labels identify the part of the large disk outside all the small disks.','Which regions carry G in relation to the circles?')]
record('191','Four explicit geometric/color relations replace bundled center/tangency/count/no-triple-overlap premises. Review the full-set diameter-direction relation for genuine atomicity; exclude if it is only a hidden inventory.')
r=rows['2864'];r['facts']=[fact('2864','repair_boundary','diagram topology','The requested twelve-sided polygon follows the outer boundary of the drawn line-segment network inside the circle.','How does the requested twelve-sided polygon relate to the boundary of the drawn line-segment network inside the circle?')]
record('2864','A single boundary identity locates the target region in the network already fully specified by the question; no six-label inventory or solved area is supplied.')
exclude('2144','Arc-center facts omit triangle/shoulder placement and arc endpoints. Completing the construction exceeds the four primitive-fact bound; the omitted geometry cannot be mentally imported.')
exclude('2781','The common set omits the opposite triangular-end attachment identifying EF as prism height; adding face adjacency exceeds four primitive facts. Do not combine independent face shape and adjacency assertions merely to fit the cap.')
exclude('784','Step counts and lengths omit closure topology. Adding straight bottom/left boundaries to the four required label/count facts exceeds the primitive-fact cap; a multi-premise contour template is not counted as one fact.')
exclude('947','The pictured adjacency and tour totals fix the outer simple circuit, but the question does not forbid revisits; a concrete positive-road-length counterexample gives a shorter tour. Preserve the unresolved task convention.','E_STAR_AMBIGUOUS')
save(ROOT/'audit/e_star_repair_proposal_v1.json',dict(at=now(),frozen=True,source_proposal_sha256=sha(proposal),rows=list(changed.values()),
    reason='Prospective exact-set sufficiency, truth, atomicity and probe-leak repair before any model outcomes.',model_outcomes_opened=False))
print('REPAIR_ROWS',len(changed))
