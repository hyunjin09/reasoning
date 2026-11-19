"""Completion diagnostics only. Never load a source answer or correctness label."""
import pandas as pd
from scripts.stage12cr.common import ROOT,OLD,load,save,sha,now

def prefixes():
 rows=[]
 for t in load(ROOT/'stage12tr_same12_manifest.json')['rows']:
  tid=t['task_id'];a=load(OLD/'generations'/tid/'generation.json');b=load(ROOT/'generations'/tid/'generation.json')
  x=a['generated_token_ids'];y=b['generated_token_ids'];lcp=0
  for i,j in zip(x,y):
   if i!=j:break
   lcp+=1
  rows.append(dict(task_id=tid,item_id=t['item_id'],family_id=t['family_id'],old_tokens=len(x),new_tokens=len(y),
      old_cap=a['cap_hit'],new_cap=b['cap_hit'],common_prefix_tokens=lcp,old_full_prefix_matches=lcp==len(x),
      first40960_identical=(lcp>=40960) if len(x)>=40960 and len(y)>=40960 else None,
      old_generation_sha256=sha(OLD/'generations'/tid/'generation.json'),new_generation_sha256=sha(ROOT/'generations'/tid/'generation.json')))
 pd.DataFrame(rows).to_parquet(ROOT/'stage12tr_prefix_diagnostics.parquet',index=False)

def finish():
 p1=load(ROOT/'stage12tr_same12_decision.json');phases=[('same12',p1)]
 if p1['pass']:
  p2=load(ROOT/'stage12tr_fresh12_decision.json');phases.append(('fresh12',p2))
 else:p2=None
 rows=[]
 for phase,d in phases:
  for r in d['rows']:rows.append(dict(phase=phase,**{k:r[k] for k in ['task_id','item_id','family_id','R1','R2','R3','R4','R5']}))
 pd.DataFrame(rows).to_parquet(ROOT/'stage12tr_pathology_labels.parquet',index=False)
 pref=pd.read_parquet(ROOT/'stage12tr_prefix_diagnostics.parquet').to_dict('records')
 lines=['# Stage12T-R Thinking completion validation','',f"**{phases[-1][1]['decision']}**. {now()}",'',
 'Technical-only cap intervention40960→81920. Same checkpoint, original image/question, BF16/vLLM runtime, per-family seed, temperature1/top-p.95/top-k20/repetition1/presence0. No task correctness or rescue analysis.','',
 '| Phase | Input valid | Scoreable | Pre-outcome caps | Normal stops | Closed think | Decision |','|---|---:|---:|---:|---:|---:|---|']
 for phase,d in phases:
  c=d['counts'];rr=d['rows'];lines.append(f"| {phase} | {c['INPUT_VALID']}/12 | {c['SCOREABLE']}/12 | {c['TRUNCATED_BEFORE_OUTCOME']} | {sum(r['normal_stop'] for r in rr)} | {sum(r['closed_think'] for r in rr)} | {d['decision']} |")
 lines+=['','| Phase | All cap hits | Token median | Token Q1–Q3 | Token max | R1/R2/R3/R4/R5 counts |','|---|---:|---:|---|---:|---|']
 for phase,d in phases:
  rr=d['rows'];lengths=pd.Series([r['tokens'] for r in rr]);labels='/'.join(str(sum(r[f'R{i}'] for r in rr)) for i in range(1,6))
  lines.append(f"| {phase} | {sum(r['cap_hit'] for r in rr)} | {lengths.median():g} | {lengths.quantile(.25):g}–{lengths.quantile(.75):g} | {lengths.max()} | {labels} |")
 lines+=['','Per-case technical behavior; extracted answer values are retained in the technical result files, without correctness labels.','','| Phase | Item | Tokens | Scoreable | Pre-outcome cap | Closed think | Final channel | R1–R5 positive |','|---|---|---:|---|---|---|---|---|']
 for phase,d in phases:
  for rr in d['rows']:
   labels=','.join(f'R{i}' for i in range(1,6) if rr[f'R{i}']) or 'none'
   lines.append(f"| {phase} | {rr['item_id']} | {rr['tokens']} | {rr['SCOREABLE']} | {rr['TRUNCATED_BEFORE_OUTCOME']} | {rr['closed_think']} | {rr['final_channel_present']} | {labels} |")
 lines+=['','Original capped trajectories:','','| Item | Original tokens | Extended tokens | Prefix match | Scoreable final | New cap |','|---|---:|---:|---|---|---|']
 for pr in pref:
  if not pr['old_cap']:continue
  rr=next(r for r in p1['rows'] if r['task_id']==pr['task_id'])
  lines.append(f"| {pr['item_id']} | {pr['old_tokens']} | {pr['new_tokens']} | {pr['old_full_prefix_matches']} (LCP {pr['common_prefix_tokens']}) | {rr['SCOREABLE']} | {rr['cap_hit']} |")
 lines += ['',f"{sum(r['old_full_prefix_matches'] for r in pref)}/12 old trajectories are exact token prefixes of the longer-cap rerun. Prefix divergence limits attribution to a pure cap change; it does not change the technical completion gate.",'',
 'Both previously capped items2198 and3011 now finalize, but their common prefixes end at37338 and37768 tokens, respectively, before the old40960 cap. Item2864 also diverges (52-token common prefix). Thus this check validates observed completion under the extended recipe without establishing a pure budget cause for the earlier failures.','',
 'Pathology review is semantic, with per-case reasons and review coverage retained in audit/technical_annotations. Exact prior traces reuse preserved annotations; items2864 and2143 use documented positive-witness sections plus the complete final channel. This is single-agent review, not independent inter-rater reliability.','',
 'The cause of any prefix divergence is not established. It was not used to tune the runtime, sampling settings, cohort, or completion gates.','',
 'Prefix-matching capped trajectories that later finalize support a budget limitation for those trajectories; prefix-matching trajectories still uncommitted at81920 support persistent nonconvergence under this recipe. Neither result is a task-performance conclusion.','',
 'Fresh validation was frozen before phase1 using SHA256(stage12tr-fresh-validation-v1|family_id),5MC/7open, excluding original12. '+('It was run only after the same12 gate passed.' if p1['pass'] else 'It was NOT_RUN because the same12 gate failed.'),'',
 'No repetition threshold, third cap, decoding search, full61-family T study or correctness scoring. Raw outputs/token IDs and R1–R5 labels are retained. Resource accounting includes startup, hard2.5GPUh per phase; all released at closure.','',
 '[Full responses](../../../reports/stage12cr/v1/index.md).','',
 'Technical authorization only: '+('The81920 recipe is validated for a later separately authorized Thinking scientific study; no such study launched.' if p2 and p2['pass'] else 'The tested completion regime is not validated for scientific rescue estimation; no further search performed.'), '',phases[-1][1]['decision']]
 (ROOT/'stage12tr_summary.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
 import sys
 prefixes() if sys.argv[1]=='prefixes' else finish()
