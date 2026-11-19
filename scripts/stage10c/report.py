from collections import Counter
from scripts.stage10c.common import ROOT,load

def main():
 r=load(ROOT/'stage10c_primary_inference.json');res=load(ROOT/'stage10c_resource_accounting.json');scored=load(ROOT/'audit/final_scored.json');d=load(ROOT/'audit/execution_decisions.json')
 lines=['# Stage10C — causal visual reopening','',f"**Outcome {r['outcome']}; full causal reopening + source-specificity gate: {r['main_gate_pass']}.**",'',
  '## Design and validity','',
  f"{r['n']} independent natural problem/image trajectories were tested. The original16-case primary split contains8 MathVision and8 MathVerse cases; reserve executed: {r['reserve_executed']}. "
  'Selection reused the exact24-event Stage10B anchor-gap sensitivity; no native-correctness or intervention-effect selection. '
  'All gold B facts, matched equal-count controls and scoring rules were sealed before interventions. Exactly three fixed reserve-compatible technical cases passed all10 checks.','',
  'The model is pinned Qwen3-VL-2B-Thinking, BF16/TF32-off, eager language/SDPA vision, native preprocessing. '
  'Historical traces were sampled; the local Stage10C branches are greedy. Fresh unmasked greedy baselines were therefore generated, and no-op equality was checked against the corresponding unmasked greedy path, not against sampled historical suffixes. '
  'All branches share the original teacher-forced native prefix. PRE masks predict tokens[B−24,B); POST masks predict[B,B+24). '
  'All28 decoder layers use the previously validated standard image-key operator, with access restored at the24-token boundary. Earlier image-derived cache remains intact.','',
  'The behavioral endpoint scores the first atomic source-local B assertion represented by the frozen native evidence span in the64-token window[B,B+64). '
  'It does not require complete solution of a broad inventory or final benchmark answer. The broader B demand and complete native evidence span remain in the gold artifact. '
  'Scores were assigned from condition-blinded local text and frozen image-grounded rules; no independent human-rater claim is made. '
  'Teacher forcing measures mean NLL of the entire native B-evidence span, including wrong native assertions and spans extending beyond64 tokens. '
  'Thus NLL measures support for the native assertion and is interpreted with correctness strata.','',
  '## Primary paired endpoints','',
  'Equal trajectory weighting;4,000 paired bootstrap draws, seed920260927. Behavioral units are proportion differences; mechanistic units are nats/token. '
  'Adjusted intervals are98.75% marginal percentile intervals (Bonferroni family-wise95% across four endpoints).','',
  '| Endpoint | Point | Ordinary95% CI | Adjusted CI | Positive / negative / tied pairs |','|---|---:|---|---|---|']
 for k,v in r['primary'].items():lines.append(f"| {k} | {v['point']:.6f} | {v['ci95']} | {v['familywise95_ci']} | {v['positive']} / {v['negative']} / {v['tied']} |")
 lines+=['','P1=PRE accuracy−POST-all accuracy; P2=POST-all NLL−PRE NLL; P3=irrelevant accuracy−target accuracy; P4=target NLL−irrelevant NLL.','',
  f"Frozen gate components: {r['gate_components']}. The plan's main gate uses positive directions with dataset, faithful-stratum, deletion and technical checks; intervals describe uncertainty. "
  'A point-direction pass is not an assertion that all adjusted intervals exclude zero.','',
  '| Dataset | n | P1 | P2 | P3 | P4 |','|---|---:|---:|---:|---:|---:|']
 for name,x in r['datasets'].items():lines.append('| '+name+' | '+str(x['n'])+' | '+' | '.join(f"{x['primary'][k]['point']:.6f}" for k in ['P1','P2','P3','P4'])+' |')
 lines+=['','## Native strata and robustness','',
  'The preregistered source-faithful stratum uses the original sampled native64-token continuation, assessed before interventions. Fresh greedy baseline correctness is a separate sensitivity.','',
  '| Stratum | n | P1 | P2 | P3 | P4 |','|---|---:|---:|---:|---:|---:|']
 for name,x in r['source_faithful_sensitivity'].items():lines.append('| '+name+' | '+str(x['n'])+' | '+(' | '.join(f"{x['primary'][k]['point']:.6f}" for k in ['P1','P2','P3','P4']) if x['n'] else 'undefined | undefined | undefined | undefined')+' |')
 lines+=['',f"Minimum P1–P4 after deleting any one or any pair: {r['robustness']['minimum_points']}. Full deletion tables and target-type strata are in the inference JSON.",'',
  '| Condition | Correct | Wrong | Unresolved | No local read | Reached64-token cap | EOS |','|---|---:|---:|---:|---:|---:|---:|']
 for c in ['NATIVE','PRE_ALL_OFF','POST_ALL_OFF','POST_TARGET_OFF','POST_IRRELEVANT_OFF']:
  rr=[x for x in scored['free'] if x['condition']==c];co=Counter(x['label'] for x in rr)
  lines.append(f"| {c} | {co['B_CORRECT']} | {co['B_WRONG']} | {co['B_UNRESOLVED']} | {co['NO_FINAL_LOCAL_READ']} | {sum(x['reached_local_cap'] for x in rr)} | {sum(x['normal_eos'] for x in rr)} |")
 lines+=['','The64-token cap is the intended local assay endpoint, not a claim that a final benchmark answer was completed. Free branches retain frozen absolute scoring coordinates even when content diverges.','',
  '## Interpretation and limits','',
  {'A':'The frozen gate supports bounded sequential reopening with source specificity under the tested standard mask.',
   'B':'The reopening component passes, while source specificity does not meet the full gate.',
   'C':'Source-specific causal dependence passes without a clear robust PRE-to-POST increase; this supports retargeting rather than phase reopening.',
   'D':'Neither robust component passes. Do not promote causal reopening from this tested candidate cohort.'}[r['outcome']], '',
  'Read the endpoints separately: a positive native-span NLL effect indicates reduced support for the frozen native text, not necessarily loss of a correct local visual read. '
  'The dataset and faithful-stratum tables determine whether the behavioral evidence converges with that effect. '
  f"The fresh unmasked greedy continuation resolves B correctly in {sum(x['y'][0] for x in scored['pairs'])}/{len(scored['pairs'])} cases, "
  f"whereas {sum(x['historical_faithful'] for x in scored['pairs'])}/{len(scored['pairs'])} original sampled native spans were source-faithful. "
  'This limited behavioral resolution under the fixed window constrains the interpretation of a failed gate; it is not evidence that causal reopening is impossible.','',
  'The result applies to this selected natural candidate cohort, model, fixed local budget and intervention. '
  'PRE is a reviewed terminal text suffix; the original paragraph annotations are coarse, and semantic reasoning status is not an independently established low-necessity state. '
  'Prior image-derived state and redundant pathways remain available. A null does not establish mechanism impossibility or diagnose its cause. '
  'No full A→B→A return cycle or universal alternation is tested. Stage10AR controlled4B transition, Stage4A source retargeting and Stage10B natural passive census remain separately supported evidence.','',
  f"Reserve executed: {d['reserve_executed']}. Demand-swap executed: {d.get('demand_swap_executed',False)}. Conditional decisions: {d['reason']}. No post-null anchor/window or model search.",'',
  '## Resources and artifacts','',f"Allocated GPU-hours: **{res['allocated_gpu_hours']:.4f}**; peak simultaneous GPUs:{res['peak_gpus']}; all GPU jobs terminal. "
  'Accounting includes validation/startup/failures. No new benchmark-scale generation, download or tmux allocation. '
  'Eleven mandatory artifacts and four figure pairs are saved here; optional outputs appear only if executed, and the integrated fifth figure appears only for OutcomeA. '
  'Native evidence, raw blinded ratings, manifests, source hashes and Slurm receipts remain preserved. '
  'CPU collector125320 started without its intended dependency and failed an incomplete-queue assertion before review or analysis. '
  'Its evidence was preserved; bounded collection ran only after both GPU workers were verified complete. The scientific runs were unaffected.','',
  '## Exactly one recommendation','',r['exactly_one_recommendation'],'','**STOP:** no follow-on experiment launched.','']
 with (ROOT/'stage10c_summary.md').open('x') as f:f.write('\n'.join(lines))
if __name__=='__main__':main()
