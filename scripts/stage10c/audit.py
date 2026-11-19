"""Final provenance, independent counts, exact conditions and budget audit."""
import os
from datetime import datetime
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
from scripts.stage10c.common import ROOT,load,save,sha,now
from scripts.stage10c.analysis import summarize,gate

def main():
 assert os.environ.get('SLURM_JOB_ID')
 split=load(ROOT/'stage10c_frozen_candidate_split.json');gold=load(ROOT/'stage10c_b_gold_annotations.json');controls=load(ROOT/'stage10c_roi_controls.json');cfg=load(ROOT/'config.json');v=load(ROOT/'stage10c_technical_validation.json')
 assert len(split['primary_ids'])==16 and len(split['reserve_ids'])==8 and len(set(split['primary_ids']+split['reserve_ids']))==24
 assert len(v['rows'])==3 and set(x['trajectory_id'] for x in v['rows'])==set(split['technical_ids']) and v['pass_all']
 assert all(r['pass_all'] for r in v['rows']) and all(t in split['reserve_ids'] for t in split['technical_ids'])
 assert gold['sealed'] and controls['sealed'] and not gold['causal_outcomes_opened'] and not controls['causal_outcomes_opened']
 assert datetime.fromisoformat(gold['at'])<datetime.fromisoformat(v['at'])
 for p,h in cfg['source_sha256'].items():assert sha(p)==h,p
 for p,h in cfg['frozen_artifact_sha256'].items():assert sha(p)==h,p
 for p,h in split['sources_sha256'].items():assert sha(p)==h,p
 count=0
 for r in split['rows']:
  assert r['pre_window']==[r['onset']-24,r['onset']] and r['post_window']==[r['onset'],r['onset']+24]
  assert r['intervening_tokens']>=24 and r['prior_availability']=='ABSENT'
  for p,h in r['corpus']['source_sha256'].items():assert sha(p)==h,p;count+=1
  assert sha(r['corpus']['image'])==r['corpus']['image_sha256']
 for r in controls['rows']:
  assert r['semantic_check'] and len(r['target_absolute'])==len(r['control_absolute'])>0 and not(set(r['target_absolute'])&set(r['control_absolute']))
 data=load(ROOT/'audit/final_scored.json');r=load(ROOT/'stage10c_primary_inference.json');expected=set(split['primary_ids']+(split['reserve_ids'] if r['reserve_executed'] else []))
 assert {x['trajectory_id'] for x in data['pairs']}==expected and len(data['pairs'])==len(expected)
 assert len(data['free'])==len(data['teacher'])==5*len(expected)
 for key in ('free','teacher'):
  assert all(n==5 for n in Counter(x['trajectory_id'] for x in data[key]).values())
  assert len({(x['trajectory_id'],x['condition']) for x in data[key]})==len(data[key])
 for x in data['teacher']:
  assert x['exact_frozen_native_tokens'] and len(x['evidence_token_ids'])==x['tokens']==len(x['token_log_probabilities'])
  assert abs(x['mean_nll']+sum(x['token_log_probabilities'])/x['tokens'])<1e-10
 for name in (['primary','reserve'] if r['reserve_executed'] else ['primary']):
  m=load(ROOT/'audit'/f'{name}_manifest.json')
  for p,h in m['source_sha256'].items():assert sha(p)==h,p
  assert m['validation_sha256']==sha(ROOT/'stage10c_technical_validation.json')
  review=load(ROOT/'audit'/f'{name}_review.json');assert review['sealed'] and review['packet_sha256']==sha(ROOT/'audit'/f'{name}_review_packet.json')
 expected_summary=summarize(data['pairs']);check=gate(data['pairs'],expected_summary,True)
 assert expected_summary['primary']==r['primary'] and check['outcome']==r['outcome'] and check['main_gate_pass']==r['main_gate_pass']
 for key,file in [('free','stage10c_free_generation_results.parquet'),('teacher','stage10c_teacher_forced_nll.parquet')]:assert len(pd.read_parquet(ROOT/file))==len(data[key])
 res=load(ROOT/'stage10c_resource_accounting.json');assert res['all_gpu_jobs_terminal'] and res['allocated_gpu_hours']<4
 assert not r['followup_launched'] and r['exactly_one_recommendation']
 artifacts=['stage10c_causal_reopening_spec.md','stage10c_frozen_candidate_split.json','stage10c_b_gold_annotations.json','stage10c_roi_controls.json',
 'stage10c_technical_validation.json','stage10c_free_generation_results.parquet','stage10c_teacher_forced_nll.parquet','stage10c_primary_inference.json',
 'stage10c_source_faithful_sensitivity.json','stage10c_resource_accounting.json','stage10c_summary.md']
 if r['reserve_executed']:artifacts.append('stage10c_reserve_extension.json')
 decision=load(ROOT/'audit/execution_decisions.json')
 if decision.get('demand_swap_executed'):artifacts.append('stage10c_demand_swap.json')
 figs=[p for p in (ROOT/'figures').glob('*') if p.suffix in ('.png','.pdf')];assert len(figs)==(10 if r['outcome']=='A' else 8)
 hashes={str(ROOT/p):sha(ROOT/p) for p in artifacts};hashes.update({str(p):sha(p) for p in figs})
 save(ROOT/'audit/final_audit.json',dict(at=now(),pass_all=True,independent_trajectories=len(expected),native_source_files_verified=count,
   exact_frozen_conditions=True,gold_before_interventions=True,three_technical_cases_verified=True,gate_recomputed=True,
   allocated_gpu_hours=res['allocated_gpu_hours'],all_gpu_jobs_terminal=True,artifact_sha256=hashes,followup_launched=False))
 print('FINAL AUDIT PASS',len(artifacts),'artifacts;',len(expected),'trajectories; Outcome',r['outcome'])
if __name__=='__main__':main()
