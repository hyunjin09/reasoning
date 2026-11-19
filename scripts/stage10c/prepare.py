"""Deterministic selection from the exact frozen Stage10B gap sensitivity."""
import hashlib
from scripts.stage10c.common import ROOT,OLD,SEED,load,save,sha,now
from scripts.stage10c.protocol import matched_windows,choose_control
from scripts.stage10b.routing import roi_indices

def main():
 infer=load(OLD/'stage10b_yield_inference.json');ids=set(infer['minimum24token_interval_sensitivity']['primary_event_ids'])
 events=[e for e in load(OLD/'audit/analyzed_events.json')['rows'] if e['event_id'] in ids]
 assert len(events)==24 and len({e['trajectory_id'] for e in events})==24
 corpus={r['trajectory_id']:r for r in load(OLD/'stage10b_corpus_manifest.json')['rows']}
 order=lambda e:hashlib.sha256(('stage10c-primary-920260927:'+e['trajectory_id']).encode()).hexdigest()
 strata={d:sorted([e for e in events if e['dataset']==d],key=order) for d in ('MathVision','MathVerse')}
 primary=[e['trajectory_id'] for d,rows in strata.items() for e in rows[:8]];reserve=[e['trajectory_id'] for d,rows in strata.items() for e in rows[8:]]
 assert len(primary)==16 and len(reserve)==8
 technical=[strata['MathVision'][8]['trajectory_id'],strata['MathVerse'][8]['trajectory_id'],strata['MathVision'][9]['trajectory_id']]
 selected=[];controls=[]
 for e in sorted(events,key=order):
  r=corpus[e['trajectory_id']];packet=load(r['packet_path']);meta=load(r['native_directory']+'/input.json');b=e['onset'];pre,post=matched_windows(b)
  assert e['semantic_clean'] and e['C5'] and e['intervening_tokens']>=24
  offsets=packet['token_character_offsets'];chars=lambda lo,hi:packet['full_reasoning_text'][offsets[lo]:offsets[hi]]
  row=dict(e,corpus=r,split='primary' if e['trajectory_id'] in primary else 'reserve',technical=e['trajectory_id'] in technical,
   pre_window=pre,post_window=post,local_score_window=[b,b+64],pre_text=chars(*pre),native_local_text=chars(b,b+64),
   selection_hash=order(e),packet_sha256=sha(r['packet_path']))
  selected.append(row)
  grid=meta['visual_mapping']['merged_grid_shape'];target=roi_indices(e['target_roi_normalized'],grid);old_control=roi_indices(e.get('irrelevant_roi_normalized'),grid)
  control=choose_control(target,old_control,grid,set());assert target and len(target)==len(control) and not(set(target)&set(control))
  controls.append(dict(trajectory_id=e['trajectory_id'],event_id=e['event_id'],grid=grid,target_indices=target,control_indices=control,
   target_absolute=[meta['visual_token_indices'][i] for i in target],control_absolute=[meta['visual_token_indices'][i] for i in control],
   frozen_target_roi=e['target_roi_normalized'],historical_irrelevant_roi=e.get('irrelevant_roi_normalized'),
   matching='Exact token count, same image, disjoint; closest compact extension/subset around frozen irrelevant ROI centroid, else farthest corner. Main semantic check required.',semantic_check=False))
 save(ROOT/'stage10c_frozen_candidate_split.json',dict(at=now(),frozen=True,seed=SEED,selection='SHA256(stage10c-primary-920260927:+trajectory_id) within dataset; first8 each primary; rest reserve',primary_ids=primary,reserve_ids=reserve,technical_ids=technical,
  pool_source='Exact Stage10B >=24 anchor-gap sensitivity primary event IDs, including the already-sealed later event for MathVision475; no new semantic event.',
  sources_sha256={str(OLD/p):sha(OLD/p) for p in ['stage10b_yield_inference.json','audit/analyzed_events.json','stage10b_corpus_manifest.json']},rows=selected))
 save(ROOT/'audit/roi_control_draft.json',dict(at=now(),rows=controls,review_complete=False))
 print('FROZEN primary',primary,'reserve',reserve,'technical',technical,flush=True)
if __name__=='__main__':main()
