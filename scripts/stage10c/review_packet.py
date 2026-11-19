"""Condition-blinded local64-token review; no NLL or mask labels exposed."""
import argparse,hashlib
from scripts.stage10c.common import ROOT,load,save,sha,now
p=argparse.ArgumentParser();p.add_argument('--split',default='primary',choices=['primary','reserve']);args=p.parse_args()
split=load(ROOT/'stage10c_frozen_candidate_split.json');by={r['trajectory_id']:r for r in split['rows']};gold={r['trajectory_id']:r for r in load(ROOT/'stage10c_b_gold_annotations.json')['rows']}
packet=[];keys=[]
for tid in split[args.split+'_ids']:
 path=ROOT/args.split/'cases'/tid/'result.json';r=load(path);e=by[tid]
 assert r['config_sha256']==sha(ROOT/'config.json')
 assert len(r['rows'])==5
 for x in r['rows']:
  rid=hashlib.sha256(('stage10c-blind-review:'+tid+':'+x['condition']).encode()).hexdigest()[:16]
  g=x['free'];packet.append(dict(review_id=rid,trajectory_id=tid,question=gold[tid]['local_B_question'],gold=gold[tid]['correct_B_fact'],
   accepted=gold[tid]['accepted_semantic_paraphrases'],pre_context=e['pre_text'],generated_pre_tokens_text=g['text'][:max(0,len(g['text'])-len(g['local_text']))],
   local_text=g['local_text'],local_tokens=g['local_tokens'],normal_eos=g['normal_eos']))
  keys.append(dict(review_id=rid,trajectory_id=tid,condition=x['condition'],result_path=str(path),result_sha256=sha(path)))
save(ROOT/'audit'/f'{args.split}_review_key.json',dict(at=now(),rows=keys))
save(ROOT/'audit'/f'{args.split}_review_packet.json',dict(at=now(),rows=sorted(packet,key=lambda r:r['review_id']),
  rule='Score only first64 tokens in local_text for frozen atomic B question. Prior context only resolves references. B_CORRECT/B_WRONG/B_UNRESOLVED/NO_FINAL_LOCAL_READ. Final completed assertion after explicit retractions; unrescinded contradictory assertions wrong. No final-answer scoring.',
  gold_sha256=sha(ROOT/'stage10c_b_gold_annotations.json'),condition_and_NLL_hidden=True))
print('BLINDED PACKET',args.split,len(packet))
