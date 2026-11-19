"""CoT scientific report and exactly five prescribed figures."""
import json,html
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scripts.stage12cr.common import ROOT,load,now
from scripts.stage12cr.review import all_tasks,folder_for

def fmt(p):
 if p['estimate'] is None:return f"undefined (0/{p['denominator']})"
 lo,hi=p['wilson95'];return f"{p['numerator']}/{p['denominator']} ({p['estimate']:.1%}; Wilson95% {lo:.1%}–{hi:.1%})"

def savefig(fig,name):
 (ROOT/'figures').mkdir(exist_ok=True)
 for ext in ['png','pdf']:fig.savefig(ROOT/f'figures/{name}.{ext}',dpi=180,bbox_inches='tight')
 plt.close(fig)

def responses():
 dest=__import__('pathlib').Path('reports/stage12cr/v1');dest.mkdir(parents=True,exist_ok=True)
 index=['# Stage12C-R full responses','','CoT scientific responses and Thinking technical-only outputs; no Thinking correctness labels.','']
 for t in all_tasks():
  folder=folder_for(t)
  if not (folder/'result.json').exists():continue
  g=load(folder/'generation.json');tid=t['task_id'];path=dest/f'{tid}.md'
  if not path.exists():path.write_text(f"# {tid}\n\n{t['family_id']} · {g['tokens']} tokens · {g['finish_reason']}\n\n## Input\n\n{t['prompt']}\n\n## Full raw response\n\n"+g['raw_decoded_response']+'\n')
  index.append(f"- [{tid}]({tid}.md) — {g['tokens']} tokens; {g['finish_reason']}")
 (dest/'index.md').write_text('\n'.join(index)+'\n')

def main():
 r=load(ROOT/'stage12cr_cot_primary_inference.json');d=load(ROOT/'stage12cr_cot_decision.json')
 tech=load(ROOT/'audit/denominator_seal.json');review=load(ROOT/'stage12cr_cot_second_review.json')
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 fig,ax=plt.subplots(figsize=(8,4));bs=['B1','B2','B3','B4'];x=np.arange(4)
 ax.bar(x,[r['by_stratum'][b]['frozen_total'] for b in bs],color='#dce2e8',label='Frozen native failures')
 ax.bar(x,[r['by_stratum'][b]['numerator'] for b in bs],width=.45,color='#287eac',label='CoT rescues')
 for j,b in enumerate(bs):
  p=r['by_stratum'][b];ax.text(j,p['frozen_total']+.2,f"{p['numerator']}/{p['denominator']} scoreable",ha='center',fontsize=8)
 ax.set_xticks(x,bs);ax.set_ylim(0,14);ax.set_ylabel('Independent families');ax.legend();ax.set_title('Frozen failure map with CoT rescue overlay')
 savefig(fig,'A1_failure_map_cot_rescue')
 fig,ax=plt.subplots(figsize=(6,4))
 for j,k in enumerate(['A-P1','A-P2']):
  p=r['primary'][k];a=p['estimate']
  if a is not None:
   lo,hi=p['wilson95'];ax.errorbar(j,a,yerr=[[a-lo],[hi-a]],fmt='o',capsize=6,color='#287eac');ax.text(j,hi+.04,f"{p['numerator']}/{p['denominator']}; missing {p['missing']}",ha='center')
 ax.set_xticks([0,1],['B1','B4']);ax.set_xlim(-.6,1.6);ax.set_ylim(-.05,1.18);ax.set_ylabel('CoT rescue fraction');ax.set_title('Primary rescue estimates: Wilson95% intervals')
 savefig(fig,'A2_primary_cot_rescue')
 fig,ax=plt.subplots(figsize=(8,4));ks=['RESCUE','REGRESSION','BOTH_CORRECT','BOTH_WRONG','UNSCOREABLE_TECHNICAL'];vv=[r['overall_paired']['counts'][k] for k in ks]
 ax.bar(range(5),vv,color=['#238d71','#b35e68','#287eac','#8994a1','#c9cdd3'])
 for i,v in enumerate(vv):ax.text(i,v+.2,str(v),ha='center')
 ax.set_xticks(range(5),['Rescue','Regression','Both correct','Both wrong','Missing pair']);ax.set_ylabel('Independent families');ax.set_title('Same-checkpoint native-to-CoT transitions')
 savefig(fig,'A3_native_cot_transitions')
 fig,ax=plt.subplots(figsize=(7,4));bottom=np.zeros(3)
 for state,label,color in [('TRACE_E_FULL','Full','#19856c'),('TRACE_E_PARTIAL','Partial','#d8b64b'),('TRACE_E_WRONG_OR_CONFLICTING','Wrong/conflicting','#b95b61'),('TRACE_E_NOT_EXTERNALIZED','Not externalized','#939ba8')]:
  v=[r['visible_evidence_B1'][n]['counts'].get(state,0) for n in ['rescued','not_rescued','unscoreable']];ax.bar(range(3),v,bottom=bottom,color=color,label=label);bottom+=v
 ax.set_xticks(range(3),['Rescued','Not rescued','Unscoreable']);ax.set_ylabel('B1 families');ax.set_title('Visible evidence externalization in CoT');ax.legend(fontsize=8)
 savefig(fig,'A4_B1_visible_evidence')
 fig,ax=plt.subplots(figsize=(9,4));cats=['RESOLVED','PRESERVED','CHANGED','NO_PRIOR_PATHOLOGY','NEW_PATHOLOGY','UNSCOREABLE_TECHNICAL'];pp=r['pathology_B4']['NO_union']
 ax.bar(range(6),[pp[c]['count'] for c in cats],color='#dce2e8',label='All B4');ax.bar(range(6),[pp[c]['rescued'] for c in cats],width=.45,color='#287eac',label='CoT rescues')
 ax.set_xticks(range(6),['Resolved','Shared label','Changed','No prior R1–R3','New','Unscoreable'],fontsize=8);ax.set_ylabel('Independent families');ax.set_title('B4 convergence behavior relative to native/oracle R1–R3');ax.legend()
 savefig(fig,'A5_B4_pathology_resolution')
 responses()
 lines=['# Stage12C-R CoT scientific rescue','',f"**{d['decision']}**. {now()}",'',
 f"CoT rescued {r['primary']['A-P1']['numerator']} of the 11 frozen B1 families ({r['primary']['A-P1']['missing']} technically missing) and {r['primary']['A-P2']['numerator']} of 11 B4 families. The five-rescue threshold was not reached in either primary stratum. This is a sparse rescue result under the frozen prompt and recipe, not an invalidity finding.",'',
 'Same frozen61-family MathVision cohort and157 E* facts;12 C responses reused unchanged and49 newly generated. Prior E/N/O labels and original Stage12C artifacts preserved. This is a same-checkpoint prompt intervention; Thinking completion does not gate or enter the scientific analysis.','',
 "Pinned Qwen3-VL-4B-Instruct; original image/question plus ` Let's think step by step.`; temperature0.7,top-p0.8,top-k20,repetition1,presence1.5,cap32768. Same BF16/vLLM runtime, preprocessing and per-family seed. No retries.",'',
 f"Technical: {tech['counts']['INPUT_VALID']}/61 input-valid, {tech['counts']['SCOREABLE']}/61 scoreable, {tech['counts']['TRUNCATED_BEFORE_OUTCOME']} pre-outcome caps. R1–R4 never automatically exclude; missing outcomes are not wrong answers.",'',
 'Four responses hit the cap: three lacked an outcome; item1951 retained a unique final commitment despite the truncated final box. Item2013 stopped normally but lacked a unique requested answer. These four missing outcomes and the cap-after-answer case were classified before correctness was opened.','',
 'CoT pathology counts: '+', '.join(f"R{i}={sum(v[f'R{i}'] for v in tech['rows'])}/61" for i in range(1,6))+'. Repetition and reopening remain behavior measurements rather than exclusions.','',
 '| Endpoint | Estimate | Frozen total | Missing |','|---|---|---:|---:|']
 for k in ['A-P1','A-P2']:
  p=r['primary'][k];lines.append(f"| {k}: {'B1' if k=='A-P1' else 'B4'} CoT rescue | {fmt(p)} | {p['frozen_total']} | {p['missing']} |")
 lines += ['',f"A-P3 B1−B4 selectivity: {r['primary']['A-P3']['estimate']}; bootstrap95% {r['primary']['A-P3']['percentile95']}.4000 equal-weight family draws, fixed seed{r['bootstrap_seed']}, stratified B1/B4. Exact observed rescue/frozen-total and missingness bounds are in the inference JSON; missing outcomes are never imputed wrong.",'',
 f"Descriptive only: B2 rescue {fmt(r['by_stratum']['B2'])}; B3 rescue {fmt(r['by_stratum']['B3'])}. No primary inference is made from these tiny strata.",'',
 'B1 denotes incomplete demonstrated evidence recovery:7explicit-wrong/4unresolved-only. B2=1/B3=3 are descriptive. Small cells limit precision; this developmental cohort does not estimate benchmark-wide prevalence.','',
 'Secondary paired N→C comparison, jointly scoreable families only:','', '```json',json.dumps(r['overall_paired'],indent=2),'```','',
 'B1 subtypes (no subgroup significance tests):','','```json',json.dumps(r['b1_subtypes'],indent=2),'```','',
 'Visible evidence: all26 complete native-failure traces annotated against frozen E* without correctness or bottleneck labels. Explicit contradictions take precedence over FULL; NOT_EXTERNALIZED does not imply internally absent evidence. Evidence-recovery-consistent rescue is C+ with TRACE_E_FULL; it is not causal proof of hidden retrieval.','','The single rescued B1 trace still contains conflicting source bindings; there are zero evidence-recovery-consistent B1 rescues. No B4 family is rescued, so this cohort supplies no successful B4 example with which to establish a convergence-repair bridge.','','```json',json.dumps(r['visible_evidence_B1'],indent=2),'```','',
 'B4 pathology transitions retain native and oracle separately plus their union. R4 long advancing computation is descriptive; FigureA5 compares R1–R3.','','```json',json.dumps(r['pathology_B4'],indent=2),'```','',
 f"Review:61 C-only first scores; {review['audit']['second_pass_calls']} second reviews covering all ambiguities plus the deterministic20% unambiguous-family audit. Same-agent separate-pass quality control, not independent inter-rater reliability. No Thinking correctness was opened.",'',
 'Resource accounting: stage12cr_cot_resource_accounting.json (allocated GPU time includes startup; hard5GPUh).','']
 for name in ['A1_failure_map_cot_rescue','A2_primary_cot_rescue','A3_native_cot_transitions','A4_B1_visible_evidence','A5_B4_pathology_resolution']:lines.append(f'- [{name}](figures/{name}.png) · [PDF](figures/{name}.pdf)')
 lines+=['','[Full unabridged responses](../../../reports/stage12cr/v1/index.md).','', '**Exactly one scientific recommendation:** '+d['recommendation'],'','STOP. Recommendation not executed.']
 (ROOT/'stage12cr_cot_summary.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
