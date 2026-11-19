"""Finalize only after human/model semantic scoring and conditional gates are resolved."""
import os,json
import pandas as pd
from scripts.stage10c.common import ROOT,load,save,sha,now
from scripts.stage10c import figures,account,report,audit
from scripts.stage10c.resource_snapshot import snapshot

def parquet(rows,path):
 assert not path.exists()
 pd.DataFrame([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows]).to_parquet(path,index=False)

def main():
 assert os.environ.get('SLURM_JOB_ID')
 decision=load(ROOT/'audit/execution_decisions.json');assert decision['frozen']
 primary=load(ROOT/'audit/primary_inference.json');reserve=decision['reserve_executed']
 assert not reserve or primary['reserve_gate_pass']
 assert reserve or not primary['reserve_gate_pass'],'Eligible reserve action must be explicitly resolved before completion'
 names=['primary','reserve'] if reserve else ['primary'];datasets=[load(ROOT/'audit'/f'{s}_scored.json') for s in names]
 inference=load(ROOT/'audit'/f'{names[-1]}_inference.json')
 if inference['main_gate_pass']:
  assert decision.get('optional_demand_swap_resolved'),'Resolve prospectively frozen optional block after positive gate'
  assert decision.get('null_sink_decision')
 else:assert not decision.get('demand_swap_executed')
 allrows={k:[r for d in datasets for r in d[k]] for k in ['pairs','free','teacher']}
 save(ROOT/'audit/final_scored.json',dict(at=now(),**allrows))
 save(ROOT/'stage10c_primary_inference.json',dict(inference,primary16=primary,reserve_executed=reserve,
   exactly_one_recommendation=('Integrate causal visual reopening into the main phase-structured framework and next test only minimal cross-task/model generalization.' if inference['main_gate_pass'] else 'Stop the reopening branch and finalize the paper around the already-established visual-to-text transition plus dynamic source retargeting as a separate causal phenomenon.'),
   followup_launched=False))
 save(ROOT/'stage10c_source_faithful_sensitivity.json',dict(at=now(),**inference['source_faithful_sensitivity']))
 if reserve:save(ROOT/'stage10c_reserve_extension.json',dict(at=now(),executed=True,primary_gate=primary['reserve_gate_pass'],ids=load(ROOT/'stage10c_frozen_candidate_split.json')['reserve_ids'],combined_n=len(allrows['pairs']),protocol_unchanged=True))
 parquet(allrows['free'],ROOT/'stage10c_free_generation_results.parquet');parquet(allrows['teacher'],ROOT/'stage10c_teacher_forced_nll.parquet')
 figures.main();snapshot('finalization_running');account.main();report.main();audit.main()
if __name__=='__main__':main()
