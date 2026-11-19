"""Main image review: prospective local gold, native strata and control support."""
from PIL import Image
import numpy as np
from scripts.stage10c.common import ROOT,load,save,sha,now
from scripts.stage10c.protocol import choose_control
# (local B question, correct fact, accepted alternatives/rule, type, native64 label)
G={
'mathvision_458':('Is the kangaroo inside the triangle?','No; it is outside the triangle (inside circle and square).','Accept outside/not in triangle; reject inside triangle.','relational','B_WRONG'),
'mathverse_751':('Where is point C on the cylinder?','C is the lower point on the right circular end, directly below B; D is lower left.','Accept right/lower end below B or BC diameter on right end; generic bottom circle does not resolve C.','relational','B_UNRESOLVED'),
'mathvision_31':('How many ducks are in the first answer group A?','A contains6 ducks. Other groups B4,C3,D2,E1.','The first source-local assertion in the native evidence is A6; require A binding. Later unrelated group errors do not change this atomic endpoint.','numeric','B_CORRECT'),
'mathverse_91':('What angle does the30-degree visual label mark?','Angle CAB (equivalently CAO) at A between AC and the horizontal AB is30 degrees.','Require30 and correct A/AC-to-AB binding. AOB or OAB=30 is wrong, not an equivalent name.','relational','B_WRONG'),
'mathvision_1526':('What color is option A top face?','Option A top face is gray. Its front is white; right face has two gray and two white quarters.','First atomic B fact is option A gray top. Accept gray upper face of first cube. Other faces are secondary unless top claim is retracted.','categorical','B_CORRECT'),
'mathverse_9':('Is C marked as a right angle?','C carries a right-angle mark; angle ACB=90 degrees.','Accept C right/perpendicular AC and BC/ACB90; Chinese equivalents.','relational','B_CORRECT'),
'mathverse_19':('What numerical value is marked at angle4?','Angle4 is50 degrees.','Require50 bound to angle4; Chinese or English or degrees symbol.','numeric','B_CORRECT'),
'mathverse_102':('Does AB pass through center O?','AB passes through O and is a diameter.','Accept collinear A,O,B or diameterAB, or A-to-O-to-B horizontal line.','relational','B_CORRECT'),
'mathvision_758':('What are the second flag grid dimensions?','Four rows and five columns:20 cells,12 black.','Accept4-by5 or5-by4 grid/20 cells with equivalent rectangular partition. Explicit five rows/four columns is transposed and wrong if orientation is claimed. Retracted4x4/5x5 guesses with no resolution are unresolved.','structured','B_UNRESOLVED'),
'mathvision_145':('Where is the first/top blue water region?','It occupies rows1–2 and columns3–4 on the5-row8-column grid (top-left origin).','Accept upper-middle location with adequate grid/source binding, correct extent, or a representative occupied cell such as row2,column3 without claiming exclusive one-cell extent. A different orientation must be mapped explicitly.','relational','B_CORRECT'),
'mathvision_482':('What are the bottom-row front-face pip counts?','Three bottom dice have left-to-right front counts5,3,2.','Require correct bottom-row structure and bindings; two bottom dice with5,5 is wrong. If explicitly retracted without replacement, unresolved.','structured','B_UNRESOLVED'),
'mathvision_409':('What do the second clock hands indicate?','Long minute hand points to1 (5 minutes); short hour hand points near5:5:05.','Accept5:05 or correct hand bindings. Hour1/2 and minute10/50 is wrong.','structured','B_WRONG'),
'mathverse_186':('Where is D relative to the circle and what is OD?','D is inside the circle on chord/line AC; OD is perpendicular to AC/CE and is not a radius to the circumference.','Require interior D/not on circle plus perpendicular relation if asserted. Calling OD a radius or D on circumference is wrong.','relational','B_WRONG'),
'mathverse_316':('What expression labels side AB?','AB is labeled x−2; BC has5.','First atomic B assertion requires x−2 bound to AB. Other inferred sides are secondary unless AB claim is changed.','numeric','B_CORRECT'),
'mathverse_331':('Is P east or west of the north ray from A?','P is left/west of north, bearing315 degrees.','Accept west/northwest/left of north/AP counterclockwise45 degrees from north; explicit source-left claim suffices even if subsequent interpretation is tentative.','relational','B_CORRECT'),
'mathvision_469':('What is the right-hand coin arrangement?','Six coins form a hollow ring/hexagon, each touching its two neighbors.','Require ring/hexagon adjacency, not only the already-known count6.','structured','B_CORRECT'),
'mathverse_216':('Where is the small triangle right-angle mark?','F is the right-angle vertex of triangleDEF; the3 label is on FE.','First atomic B assertion is right angle atF, accepted via square mark or DF perpendicularFE.','relational','B_CORRECT'),
'mathvision_475':('What weights are shown in the answer-option stones?','A5,B7,C9,D11,E13 kilograms.','Accept ordered weights5,7,9,11,13 or explicit C9 with no contradictory option ordering.','structured','B_CORRECT'),
'mathvision_202':('What is option B graph left shape?','For negative x it is an angular V with minimum at(−1,0), meeting(0,1), not a smooth left semicircle.','Require V/absolute-value/straight segments with vertex−1,0; describing only one increasing line for the whole negative-x region is wrong. Retracted incomplete replacement remains unresolved.','structured','B_UNRESOLVED'),
'mathverse_52':('Where is angle2?','At E between the leftward ruler edge EA and the triangle edge EF.','Accept E top-right intersection between leftward horizontal ruler line and EF; top right alone without edge/vertex identification unresolved.','relational','B_UNRESOLVED'),
'mathvision_649':('How many unit cubes are in option A?','Option A has6 cubes:3 across back,2 further on left arm,1 further on right.','Require6 bound to optionA;4/5 incorrect; retracted count followed by unresolved incomplete recount is unresolved.','numeric','B_UNRESOLVED'),
'mathvision_2749':('Which region is shaded?','Inside the large circle and outside both smaller white circles.','Accept large disk minus union of two small disks; not either small disk.','relational','B_CORRECT'),
'mathvision_885':('What does the vertical arrow label indicate?','Upward motion/speed1m/h, not a1m garden height.','Require correct unit m/h or meters per hour and rate interpretation; height1m is wrong even if m/h label is copied.','numeric','B_WRONG'),
'mathverse_308':('What is the height GH?','GH=3.15.','Accept3.15 bound to GH/height from G toFE; not GE6.3.','numeric','B_CORRECT')}
rows=load(ROOT/'stage10c_frozen_candidate_split.json')['rows'];out=[]
for r in rows:
 tid=r['trajectory_id'];q,f,accept,typ,label=G[tid]
 out.append(dict(trajectory_id=tid,event_id=r['event_id'],B_subgoal=r['B_fact_required'],local_B_question=q,
  correct_B_fact=f,accepted_semantic_paraphrases=accept,outcome_type=typ,native_observation_quote=r['B_observation_quote'],
  native_evidence_span=r['observation_span'],native64_text=r['native_local_text'],historical_native_label=label,
  image=r['corpus']['image'],image_sha256=r['corpus']['image_sha256'],source_image_inspected=True,
  pre24_text=r['pre_text'],pre_contains_new_B_fact=False,
  pre_review_note='Terminal text suffix contains reasoning/restated prior facts or unresolved hypotheses. No newly resolved B-source observation precedes sealed onset. Paragraph-level interval spans are coarse; anchor unchanged.',
  scoring_unit='First atomic source fact in sealed B evidence; complete native span retained for NLL.',
  cohort_membership_unchanged_by_gold=True))
assert set(G)=={r['trajectory_id'] for r in rows}
save(ROOT/'stage10c_b_gold_annotations.json',dict(at=now(),sealed=True,causal_outcomes_opened=False,reviewer='main image-grounded prospective review',rows=out,
 split_sha256=sha(ROOT/'stage10c_frozen_candidate_split.json'),rule_sha256=sha('plan/stage10c_execution_protocol_v1.md')))
draft=load(ROOT/'audit/roi_control_draft.json');by={r['trajectory_id']:r for r in rows}
for c in draft['rows']:
 if c['trajectory_id']=='mathvision_2749':
  # Original irrelevant box expansion crossed other gray source content. Restrict
  # matched control to image-white interiors/background, before any outcomes.
  r=by[c['trajectory_id']];im=np.asarray(Image.open(r['corpus']['image']).convert('RGB'));t,h,w=c['grid']
  white=[]
  for i in range(h*w):
   x=min(im.shape[1]-1,int((i%w+.5)/w*im.shape[1]));y=min(im.shape[0]-1,int((i//w+.5)/h*im.shape[0]))
   if im[y,x].min()>245:white.append(i)
  exclude=set(range(h*w))-set(white)
  c['control_indices']=choose_control(c['target_indices'],c['control_indices'],c['grid'],exclude)
  meta=load(r['corpus']['native_directory']+'/input.json');c['control_absolute']=[meta['visual_token_indices'][i] for i in c['control_indices']]
  c['matching']+=' Main image review excludes every nonwhite patch center to avoid other gray target content; compactness is secondary to semantic irrelevance and exact count.'
 c['semantic_check']=True;c['semantic_note']='Control does not overlap frozen B ROI or an additional annotated currently required source; previously resolved A/image background/other unused item is allowed.'
 assert len(c['target_indices'])==len(c['control_indices']) and not(set(c['target_indices'])&set(c['control_indices']))
 c['target_count']=len(c['target_indices']);c['control_count']=len(c['control_indices'])
save(ROOT/'stage10c_roi_controls.json',dict(at=now(),sealed=True,causal_outcomes_opened=False,rows=draft['rows'],draft_sha256=sha(ROOT/'audit/roi_control_draft.json')))
save(ROOT/'audit/demand_swap_constructions.json',dict(at=now(),frozen=True,execute_only_if_full_gate=True,rows=[
 dict(trajectory_id='mathvision_409',original_clause='Second clock (second from left):',alternative_clause='Third clock (third from left):',alternative_roi=[.53,.1,.72,.88],gold='Third clock long hand5/25 minutes and short hand near5:5:25.',reason='Earlier clocks only were resolved; third was a frozen later new source.'),
 dict(trajectory_id='mathvision_758',original_clause="Second flag: Let's check.",alternative_clause="Fourth flag: Let's check.",alternative_roi=[.59,.1,.73,.86],gold='Fourth flag5 rows by5 columns,25 cells,15 black.',reason='Fourth flag is still unseen at second-flag demand; later frozen annotation supplies distinct source identity.')],
 maximum_trajectories=2,no_image_or_prior_reasoning_edit=True,token_length_match_required=True))
print('Gold/control sealed',len(out),'no outcomes opened; optional constructions2')
