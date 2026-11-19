"""Record main-reviewed semantic decisions; never loads routing artifacts."""
from scripts.stage10b.common import ROOT,load,save,now

p=load(ROOT/'audit/semantic_adjudication_packet.json')
d=load(ROOT/'audit/semantic_adjudication_worksheet.json')
pairs={r['pair_id']:r for r in p['pairs']};groups={r['pair_id']:r for r in d['event_groups']}
# All proposed temporal pairs were compared by B fact and source, independently
# of whether either annotator accepted C1–C4. None paired a different source.
for r in d['proposed_pair_source_review']:
 q=pairs[r['pair_id']];r.update(same_source_fact=True,reason='Main source/fact comparison: '+q['a']['B_fact_required']+' / '+q['b']['B_fact_required']+'. Same requested source fact; onset and eligibility disagreements remain raw.')
for key,g in groups.items():
 q=pairs[key];e=q['a'] or q['b']
 g.update(source_pair_same=True if q['a'] and q['b'] else None,
          reason='Retain exact semantic evidence and prior-text assessment from independent review. '+e['reason'])

def choose(n,who,reason,**overrides):
 k=f'pair_{n:04d}';g=groups[k];g['selected_id']=pairs[k][who]['annotation_event_id'];g['overrides'].update(overrides);g['reason']=reason+' See audit/main_semantic_review_notes.md; no routing values opened.'

choose(14,'b','Monday70−60=10 is a derived conclusion before new Tuesday heights; minimal C2 qualifies.')
choose(30,'a','The third-flag count remains explicitly tentative (p363 maybe); p364 so valid alone does not establish a separate resolved A/text phase before fourth flag.')
choose(35,'b','Both passes identify first absent answer duck groups; image2 bottom band is localized, excludes balance scene.')
choose(42,'a','First cube-option inventory follows unresolved net inspection; C2 not established. Later p28 retained separately.')
choose(57,'b','Clock hands are converted to minutes before next previously unread clock; derived conclusion meets C2.')
choose(68,'b','Only new5 label/binding is absent;3 was already hypothesized. Anchor observation to the actual5 clause.',B_observation_quote='then the next is 5 (on the right)')
choose(73,'b','Both passes identify shaded-region identity; source image confirms top gray cap is a localized part of the named shaded region, with disjoint white-circle control.')
choose(79,'b','AB=√2AC is a distinct derived relation before first AB6 label; same-paragraph C2 qualifies.',target_roi_normalized=pairs['pair_0079']['a']['target_roi_normalized'])
choose(98,'b','Earlier claimed A mostly restates given projection geometry/ratio; no sufficiently resolved image-only A.',C1=False)
choose(124,'a','Earlier right-prism hypothesis partially supplies perpendicular relation; conservative PARTIAL/C4 false.')
choose(125,'b','Continuous unresolved angle-position reconstruction before angle4=30; C2 false.')
choose(126,'b','AD10/DE4 then parallel-to-similar-triangles inference precedes absent x−2/5 labels.')
choose(128,'a','First GH3.15 demand begins at numeric label clause, after area expression; preceding paragraph opening restates a known altitude.')
choose(137,'b','Extra5y/MP is optional after requested side10 is solved; no unresolved required visual subgoal.',C3=False)
choose(150,'b','Numeric4 and its segment assignment are absent. Misbinding to OC conflicts with radius2.5 but does not make the new label textualized.',taxonomy='S3')
choose(152,'a','Earlier angle1/2 adjacency already hypothesized implied22; conservative PARTIAL for later angle2=42.',prior_availability='PARTIAL',C4=False)
choose(154,'a','Semantic new shaded-region need accepted, but broad near-whole-image box fails defensible target specificity. Preserve ROI ambiguity.')
# Main prior/source checks for single nominations and agreed candidates are in
# the evidence notes, rather than replacing raw reasons or independent labels.
for n in [27,43,54,56,58,59,64,65,66,67,69,74,76,77,78,116,117,118,119,129,130,134,135,136,138,142,147,149]:
 g=groups[f'pair_{n:04d}'];g['reason']='Main full-prior/source adjudication confirms the retained local semantic sequence, with limitations recorded in audit/main_semantic_review_notes.md. '+g['reason']
# Same semantic target nominated with substantially different onset anchors.
for keep,drop,who,reason in [(151,153,'b','Generic p5 relabeling does not yet identify numeric angle4; freeze first specific p9 angle4=50 demand.'),(119,120,'a','Generic p1 additional-information request is clarified as A-position/other-angle need in p3; retain p3 identifiable need, ROI remains ambiguous.')]:
 kg=groups[f'pair_{keep:04d}'];dg=groups.pop(f'pair_{drop:04d}');kg['annotation_ids']+=dg['annotation_ids']
 chosen=next(x for x in kg['annotation_ids'] if x.startswith(who+':'));kg.update(selected_id=chosen,source_pair_same=True,reason=reason+' Main semantic review before signal reveal; raw onset disagreement retained.')

def category(a,b):
 s=a or b or ''
 if 'SHORT' in s:return 'TRACE_TOO_SHORT'
 if any(x in s for x in ('PARTIAL','AMBIGUOUS','REINTERPRETATION')):return 'TARGET_AMBIGUOUS'
 if any(x in s for x in ('CONTINUOUS','INTERVAL')):return 'NO_TEXT_INTERVAL'
 if any(x in s for x in ('UNRESOLVED','NO_RESOLVED','NO_EARLIER','NO_IMAGE','NO_PRIOR_IMAGE','NO_STABLE')):return 'NO_RESOLVED_VISUAL_A'
 if any(x in s for x in ('SUFFICIENT','TEXTUALIZED','PRIOR_','FRONTLOADED','FRONT_LOADED','GIVEN_','RECHECK','REPEATED','COMPLETE_ANGLE','TEXT_GEOMETRY')):return 'B_ALREADY_TEXTUALIZED'
 if 'SINGLE_INITIAL' in s or 'INITIAL_CORRESPONDENCE' in s:return 'NO_TEXT_INTERVAL'
 if 'QUESTION_GEOMETRY' in s:return 'NO_RESOLVED_VISUAL_A'
 return 'NO_NEW_REQUIRED_DEMAND'
rows={r['trajectory_id']:r for r in p['rows']}
for r in d['trajectories']:
 q=rows[r['trajectory_id']];r['negative_category']=category(r['raw_negative_reason_a'],r['raw_negative_reason_b'])
 r['reason']='Main reconciliation preserves both independent trajectory evidence records; candidate decisions override generic screening categories where present.'
 r['independent_negative_evidence']={w:q[w].get('negative_evidence') for w in 'ab'}
for r in d['trajectories']:
 if r['trajectory_id']=='mathverse_161':r['negative_category']='NO_RESOLVED_VISUAL_A'
 if r['trajectory_id']=='mathverse_65':r['negative_category']='NO_TEXT_INTERVAL'
 if r['trajectory_id']=='mathverse_746':r['negative_category']='TARGET_AMBIGUOUS'
 if r['trajectory_id']=='mathverse_263':r['negative_category']='NO_NEW_REQUIRED_DEMAND'
d.update(at=now(),review_complete=True,routing_opened=False,event_groups=list(groups.values()))
save(ROOT/'audit/semantic_adjudication_decisions.json',d)
print('Explicit decisions recorded',len(groups),'groups; no routing loaded')
