"""Score fixed reviews and paired NLL once; no automatic experimental launch."""
import argparse,os
from scripts.stage10c.common import ROOT,load,save,sha,now,SEED
from scripts.stage10c.analysis import summarize,gate
from scripts.stage10c.runtime import CONDITIONS

def main(splitname):
 assert os.environ.get('SLURM_JOB_ID')
 pp=ROOT/'audit'/f'{splitname}_review_packet.json';review=load(ROOT/'audit'/f'{splitname}_review.json')
 assert review['sealed'] and review['packet_sha256']==sha(pp)
 ratings={r['review_id']:r for r in review['rows']};key=load(ROOT/'audit'/f'{splitname}_review_key.json')['rows'];assert set(ratings)=={r['review_id'] for r in key}
 gold={r['trajectory_id']:r for r in load(ROOT/'stage10c_b_gold_annotations.json')['rows']};events={r['trajectory_id']:r for r in load(ROOT/'stage10c_frozen_candidate_split.json')['rows']}
 free=[];teacher=[];pairs=[]
 for tid in sorted({r['trajectory_id'] for r in key}):
  chosen=[r for r in key if r['trajectory_id']==tid];path=chosen[0]['result_path'];raw=load(path);conditions={r['condition']:r for r in raw['rows']};ys=[];ns=[]
  assert all(sha(r['result_path'])==r['result_sha256'] for r in chosen)
  for c in CONDITIONS:
   k=next(r for r in chosen if r['condition']==c);a=ratings[k['review_id']];r=conditions[c];g=r['free'];n=r['nll']
   assert a['label'] in ['B_CORRECT','B_WRONG','B_UNRESOLVED','NO_FINAL_LOCAL_READ'] and a['reason']
   if a.get('evidence_quote'):assert a['evidence_quote'] in g['local_text'],k
   y=int(a['label']=='B_CORRECT');ys.append(y);ns.append(n['mean_nll'])
   free.append(dict(trajectory_id=tid,dataset=events[tid]['dataset'],condition=c,**g,label=a['label'],correct=y,reason=a['reason'],evidence_quote=a.get('evidence_quote'),review_id=k['review_id'],result_sha256=k['result_sha256']))
   teacher.append(dict(trajectory_id=tid,dataset=events[tid]['dataset'],condition=c,**n,delta_nll=n['mean_nll']-conditions['NATIVE']['nll']['mean_nll']))
  pairs.append(dict(trajectory_id=tid,dataset=events[tid]['dataset'],target_type=gold[tid]['outcome_type'],y=ys,nll=ns,
    historical_label=gold[tid]['historical_native_label'],historical_faithful=gold[tid]['historical_native_label']=='B_CORRECT',greedy_faithful=ys[0]==1))
 save(ROOT/'audit'/f'{splitname}_scored.json',dict(at=now(),free=free,teacher=teacher,pairs=pairs,review_sha256=sha(ROOT/'audit'/f'{splitname}_review.json')))
 if splitname=='reserve':pairs=load(ROOT/'audit/primary_scored.json')['pairs']+pairs
 result=summarize(pairs);result.update(gate(pairs,result,load(ROOT/'stage10c_technical_validation.json')['pass_all']))
 result.update(at=now(),seed=SEED,bootstrap_draws=4000,independent_unit='problem/image trajectory',multiplicity='98.75% marginal percentile intervals for four primary endpoints; Bonferroni familywise95%.',
  source_faithful_sensitivity=dict(historical_native=summarize([r for r in pairs if r['historical_faithful']]),
   historical_wrong=summarize([r for r in pairs if r['historical_label']=='B_WRONG']),historical_unresolved=summarize([r for r in pairs if r['historical_label'] not in ['B_CORRECT','B_WRONG']]),
   fresh_greedy=summarize([r for r in pairs if r['greedy_faithful']])),
  by_target_type={t:summarize([r for r in pairs if r['target_type']==t]) for t in sorted({r['target_type'] for r in pairs})},
  interpretation='Standard all-layer finite image-key masking, native image-derived cache retained; fixed local outcome window.',
  scored_sources_sha256={str(ROOT/'audit'/f'{s}_scored.json'):sha(ROOT/'audit'/f'{s}_scored.json') for s in (['primary','reserve'] if splitname=='reserve' else ['primary'])})
 save(ROOT/'audit'/f'{splitname}_inference.json',result)
 print('INFERENCE',splitname,result['outcome'],'main',result['main_gate_pass'],'reserve',result['reserve_gate_pass'])
 for k,v in result['primary'].items():print(k,v)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--split',default='primary',choices=['primary','reserve']);main(p.parse_args().split)
