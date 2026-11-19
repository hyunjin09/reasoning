"""Assemble a read-only retrospective dossier; never run inference or alter sources."""
from pathlib import Path
import hashlib, json, re, os
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/research_history_all_stages_2026-11-19.md'
WORK=ROOT/'workspace/research_history_20261119'
rows=[dict(zip(('id','title','status','findings'),l.split('\t'))) for l in (WORK/'stages.tsv').read_text().splitlines()]
byid={r['id']:r for r in rows}
for r in rows:r.update(reports=[],memories=[],plans=[])
inv=(ROOT/'workspace/research_md_inventory_20261119.txt').read_text().splitlines()
def add(k,kind,*paths):
 for p in paths:
  assert (ROOT/p).is_file(),p
  if p not in byid[k][kind]:byid[k][kind].append(p)
# Phase memories, with explicit disambiguation for branches sharing stage numbers.
phase_special={
 'phase_1_piqd_smoke.md':'piqd1','phase_2_piqd_query_extraction.md':'piqd2','phase_2b_phase2_audit.md':'piqd2audit',
 'phase_a6000_platform_calibration.md':'a6000','phase_a6000_calibration_v2_stage3c9_restart.md':'a6000v2',
 'phase_7a_bench_benchmark_failure_enrichment.md':'7bench','phase_7a_bench_v2_mirage_track.md':'7benchv2',
 'phase_8b_retrieval_aligned_mathvision.md':'8b',
 'phase_9a_thinking_vs_cot.md':'9a_native','phase_9a_vab_necessity.md':'9a_vab','phase_9a_access_dynamics.md':'9a_dynamics',
 'phase_qwen3vl_official_eval_audit.md':'official',
 'phase_14d0_visual_difficulty_v2.md':'14d0difficulty',
 'phase_14c_execution_history_20261009.md':'14c',
}
for p in sorted((ROOT/'workspace/phase_memory').glob('phase_*.md')):
 k=phase_special.get(p.name)
 if not k:
  stem=p.stem.removeprefix('phase_')
  candidates=[k for k in byid if stem.startswith(k+'_')]
  assert candidates,p
  k=max(candidates,key=len)
 add(k,'memories',str(p.relative_to(ROOT)))
add('14d0','memories','outputs/stage14d0/state/phase_memory.md')
# Canonical reports; stages with several versions retain each relevant report.
for r in rows:
 k=r['id']; candidates=[f'outputs/stage{k}/summaries/stage{k}_summary.md',f'outputs/stage{k}/v1/stage{k}_summary.md']
 for p in candidates:
  if (ROOT/p).is_file():add(k,'reports',p)
extras={
 'piqd1':['outputs/piqd/phase1/phase1_summary.md','outputs/piqd/phase1_diag/phase1_summary.md'],
 'piqd2':['outputs/piqd/phase2/phase2_summary.md','outputs/piqd/phase2_diag/phase2_summary.md'],
 'piqd2audit':['outputs/piqd/phase2/phase2_audit.md'],
 '3b3':['outputs/stage3b3_redesign/summaries/stage3b3_redesign_summary.md'],
 'a6000':['outputs/a6000_calibration/summaries/a6000_calibration_summary.md'],
 'a6000v2':['outputs/a6000_calibration_v2/summaries/a6000_calibration_v2_summary.md'],
 '6a':['outputs/stage6a/summaries/stage6a_cohort_summary.md'],
 '7benchv2':['outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_summary.md','outputs/stage7a_bench_v2/summaries/phantom_behavior_summary.md'],
 '8b':['outputs/stage8b/summaries/transfer32_results.md','outputs/stage8b/v2/summaries/transfer32_results.md'],
 '8b1a':['outputs/stage8b1a/summaries/native256_completion.md'],
 '9a_native':['outputs/stage9a/v1/stage9a_summary.md'],
 '9a_dynamics':['outputs/stage9a_dynamics/amendment_v1/stage9a_summary.md','outputs/stage9a_dynamics/amendment_v1/stage9a3_transition_addendum.md','outputs/stage9a_dynamics/amendment_v1/stage9a_compute_amendment_v1.md'],
 'official':['outputs/qwen3vl_official_eval/v1/qwen3vl_mathvision_official_protocol_audit.md','outputs/qwen3vl_official_eval/v1/qwen3vl_mathvision_prompt_diff.md','outputs/qwen3vl_official_eval/v1/qwen3vl_official_sanity_summary.md'],
 '12cr':['outputs/stage12cr/v1/stage12cr_cot_summary.md','outputs/stage12cr/v1/stage12tr_summary.md'],
 '12xs':['outputs/stage12xs/v2/stage12xs_summary.md'],
 '14b':['outputs/stage14b/summaries/stage14b_final_summary.md'],
 '14c':['outputs/stage14c/summaries/stage14c_final_summary.md','outputs/stage14c/summaries/stage14c_D1_summary.md','outputs/stage14c/summaries/stage14c_sensitivity_summary.md','outputs/stage14c/summaries/stage14c_g1_source_summary.md'],
 '14cv':['outputs/stage14c_v_blindtest_validation/summaries/stage14c_v_R_primary_summary.md'],
 'blindviewer':['outputs/blindtest_human_audit/v1/blindtest_audit_summary.md','outputs/blindtest_human_audit/v1/blindtest_review_guide.md'],
 '14d':['outputs/stage14d/reports/stage14d_technical_calibration_summary.md'],
 '14d0':['outputs/stage14d0/reports/stage14d0_native_trace_audit_results.md','outputs/stage14d0/reports/decision_and_unresolved_limitations.md'],
 '14d0supp':['outputs/stage14d0_answer_evidence_supplement_v1/supplementary_report.md'],
 '14d0difficulty':['outputs/stage14d0_visual_difficulty/v2/report.md','outputs/stage14d0_visual_difficulty/v2/method_design_implications.md'],
 '14d1':['outputs/stage14d1_sava/reports/feasibility_main.md'],
 '14d1recovery':['outputs/stage14d1_sava_recovery/v1/reports/technical_recovery_final.md'],
 '14d1pilot':['outputs/stage14d1_sava_pilot/v1/reports/feasibility_main_v8.md'],
 '14e':['outputs/stage14e_acquisition_development/v1/reports/final_research_report_v1.md','outputs/stage14e_acquisition_development/v1/reports/sava_failure_postmortem_v1.md','outputs/stage14e_acquisition_development/v1/reports/prior_art_and_hypotheses_v1.md','outputs/stage14e_acquisition_development/v1/reports/diagnostic_v1.md','outputs/stage14e_acquisition_development/v1/reports/development_revision_v2.md','outputs/stage14e_acquisition_development/v1/reports/final_acquisition_review_v1.md','outputs/stage14e_acquisition_development/v1/reports/postmortem_source_coverage_supplement_v1.md','outputs/stage14e_acquisition_development/v1/reports/diagnostic_interpretation_limits_v1.md'],
 '14e2':['outputs/stage14e_readout_mechanism/v1/reports/final_diagnostic_report_v1.md','outputs/stage14e_readout_mechanism/v1/reports/diagnostic_tables_v1.md'],
}
for k,paths in extras.items():add(k,'reports',*paths)
# Plan registry: every plan/checklist/protocol mapped; a plan's existence is not evidence of execution.
global_plans=[]
for p in sorted((ROOT/'plan').glob('*.md')):
 n=p.stem; k=None
 if n=='overview':global_plans.append(str(p.relative_to(ROOT)));continue
 if n.startswith('a6000_calibration_v2'):k='a6000v2'
 elif n.startswith('a6000'):k='a6000'
 elif n.startswith('stage7a_bench'):
  k='7benchv2' if ('v2' in n or n.endswith('_v2_mirage_track')) else '7bench'
 elif n.startswith('stage14c_blindtest'):k='14cv'
 elif n.startswith('stage14d0_visual'):k='14d0difficulty'
 elif n.startswith('stage14d1_technical_recovery'):k='14d1recovery'
 elif n.startswith('stage14d1_autonomous_full'):k='14d1pilot'
 elif n.startswith('stage9a_'):
  if 'vab_' in n:k='9a_vab'
  elif any(t in n for t in ['dynamics','compute_amendment','finish_execution','resource_addendum']):k='9a_dynamics'
  else:k='9a_native'
 else:
  stem=n.removeprefix('stage')
  candidates=[i for i in byid if stem==i or stem.startswith(i+'_')]
  if candidates:k=max(candidates,key=len)
 assert k,(p,'UNMAPPED')
 add(k,'plans',str(p.relative_to(ROOT)))
# Additional non-stage history and lessons are linked, not treated as independent experiments.
context=['workspace/research_plan.md','workspace/workflow_state.md','workspace/decision_log.md','workspace/dataset_inventory.md','workspace/env_state.md','reports/index.md']
for p in context:assert (ROOT/p).is_file(),p

def digest(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def link(p,label=None):
 return f'[{label or p}](<{os.path.relpath(ROOT/p,OUT.parent)}>)'
def anchor(k):return 'stage-'+k
sources=[]
for r in rows:
 for typ in ['reports','memories','plans']:
  for p in r[typ]:sources.append({'stage':r['id'],'type':typ,'path':p,'sha256':digest(p)})
for p in context+global_plans:sources.append({'stage':'global','type':'context','path':p,'sha256':digest(p)})
# Preserve report/phase content. Only local links and heading levels are adapted for this container.
# Missing original links are retained as code and explicitly recorded, never invented.
broken=[]
def embed(p):
 txt=(ROOT/p).read_text()
 def rewrite(m):
  label,target=m.group(1),m.group(2).strip()
  if target.startswith('<') and target.endswith('>'):target=target[1:-1]
  if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target):return m.group(0)
  file,sep,frag=target.partition('#')
  if not file:return f'[{label}](<{os.path.relpath(ROOT/p,OUT.parent)}#{frag}>)'
  q=ROOT/file if file.startswith(('outputs/','workspace/','reports/','plan/','runs/','scripts/','code/','infra/')) else ROOT/Path(p).parent/file
  q=Path(os.path.normpath(q))
  # No access outside allowed roots. Existence checked only inside project.
  try:q.relative_to(ROOT)
  except ValueError:return m.group(0)
  if q.exists():return f'[{label}](<{os.path.relpath(q,OUT.parent)}'+('#'+frag if sep else '')+'>)'
  broken.append({'source':p,'target':target});return f'{label} (`{target}`; unresolved link in source)'
 # Skip fenced blocks to preserve raw code/path strings.
 result=[];fence=False
 for line in txt.splitlines():
  if re.match(r'^\s*(```|~~~)',line):fence=not fence
  if not fence:
   line=re.sub(r'\[([^\]\n]+)\]\(([^)\n]+)\)',rewrite,line)
   line=re.sub(r'^(#{1,6}) ',lambda m:'#'*min(6,len(m[1])+3)+' ',line)
  result.append(line)
 return '\n'.join(result)

header='''# Complete research history and findings — PIQD / Stage0 through Stage14E2

**Retrospective snapshot: 19 November 2026 (Asia/Seoul).** This document organizes the project's recorded work, findings, technical repairs, failed gates and unfinished branches. It does not change any original plan, annotation, score or scientific conclusion. No new inference, GPU work, reannotation or scientific experiment was performed to create it.

The research is **paused after the completed Stage14E2 diagnostic**, at the user's request. The overarching objective—an experimentally supported method for better task-critical visual evidence acquisition—remains unachieved. A completed experiment is distinguished throughout from a successful hypothesis or a completed wider plan.

## How to use this document

1. Read the **scientific synthesis** for the project's conclusions and their limits.
2. Use the **stage index** and **stage-by-stage findings** for a chronological account. PIQD is an early parallel instrumentation branch; stage numbering is not a claim of independent cohorts or exact calendar ordering.
3. Open each stage's **full source reports and phase history** for every detailed finding, table, uncertainty interval, technical issue and limitation recorded in those consolidated sources. These are embedded, not merely summarized away. Original artifact links and SHA-256 fingerprints are included.
4. Use the **plan register** to find every plan/checklist/amendment, including plans whose scientific runs never started.

Scope of “everything”: all identified stage/phase records and their consolidated finding reports, including special audits and repairs. Individual raw generations, tensors, case images, logs and casebooks remain in the immutable linked artifacts rather than being duplicated wholesale. This is a source-grounded research history, not an independent recomputation or fresh audit of every raw outcome. Historical recommendations and “current/running” statements inside archived source blocks describe their original date; the synthesized stage status and explicitly cited later amendment determine status here.

## Contents

- [Scientific synthesis](#scientific-synthesis)
- [Stage index](#stage-index)
- [Stage-by-stage findings](#stage-by-stage-findings)
- [Interpretation rules and documentation discrepancies](#interpretation-rules)
- [Resources and preserved unfinished work](#resources)
- [Full reports and phase histories](#full-records)
- [Plan and protocol register](#plan-register)
- [Coverage and provenance](#coverage)

<a id="scientific-synthesis"></a>
## Scientific synthesis

### 1. The question evolved from visual attention to task-critical evidence acquisition

The early work asked when reasoning models route attention to image content, whether those paths carry causally relevant information, and which internal carriers support it. Later work distinguished faithful reads from wrong-source, prior-filled, extraction and downstream errors. Stage9–10 tested functional visual dependence and handoff; Stage11–14 separated evidence availability from downstream reasoning. The current method objective is: **identify the unresolved source-resolvable premise required by the current reasoning step, acquire it from the original image in the correct global context, and use it without corrupting the solver.**

### 2. Dynamic source use is supported; attention alone is not acquisition

Counterfactual content, source switching, Value-path restoration and A→B→A demand changes establish bounded causal source dependence in selected assays. The effect is distributed across layers, recent time and representations. Raw attention, QK, alpha-V, sink release, lexical mentions and passive trajectories are not interchangeable with actual evidence acquisition or causal error attribution. Several attractive routing/attention interventions failed to change the relevant evidence readout or final outcome.

### 3. Functional evidence handoff exists in a controlled setting; a broad Thinking-specific late-access regime was not established

Stage10A-R supports a functional transition to text-sufficient computation in its controlled synthetic assay. Stage9A's 64-family MathVision masked-continuation study did not support the preregistered greater late direct-image-access necessity for Thinking versus prompted CoT. Null-sink controls and baseline completion materially changed the interpretation of finite-access tests. This does not show that Thinking never uses images, that all visual processing ends at a precise token, or that cached representations contain no image information.

### 4. Supplying usable textual evidence can rescue many failures, but it changes the task interface

Stage14B's large-scale MathVision result is **234/418 = 55.98%** rescued among scored native-wrong Instruct followups, CI **[51.08%,60.80%]**, with 31 unresolved followups separately retained. That supports an evidence-supply bottleneck, not an estimate that 55.98% of errors are purely perceptual. BlindTest shows the boundary: original E* supplied many rescues but even more regressions. Entity-explicit prose helped substantially, while typed structured fields harmed performance. Source faithfulness, answer safety, sufficiency, naming, formatting and downstream usability must be checked separately.

### 5. Thinking's advantage persists under equal evidence, but its mechanism is unresolved

Stage13A found a preregistered equal-evidence advantage of **+11.11pp [5.56,17.06]**; Stage14B found **+14.69pp [12.10,17.39]** on 926 common scored evidence pairs. These compare deployed checkpoints with model-specific recipes, not a same-weight toggle at equal compute. Small prefix-transfer studies show portable useful textual states in selected cases, but held-out candidate scarcity and uncertain priming/buffer tests prevent a general production/utilization mechanism claim.

### 6. Native source errors are associated with wrong answers; global structure is an actionable difficulty signal

The Stage14D-0 audit found many explicitly wrong or misbound required facts in both models. The representative-panel paired Thinking–Instruct error contrast **−3.60pp [−7.86,+0.40]** did not establish a clean perception advantage. Evidence correctness strongly associated with final correctness within each model; global-required facts had higher explicit-error coverage than local-sufficient facts. These are retrospective, source-eligible, single-AI-reviewed associations. Unmentioned/ambiguous facts are not acquired-wrong labels, and correct final answers can coexist with wrong intermediate evidence.

### 7. No tested acquisition method has yet established the desired improvement

| Experiment | Acquisition result | Downstream result | Supported conclusion |
|---|---|---|---|
| 72-family SAVA | Only 22/62 accepted queries fully relevant; 14/49 local views correctly localized; QI new correct facts 3/24 vs generic 2/24 | QI36/72 vs native39/72; −4.17pp [−12.50,+4.17] | No supported benefit; targeting, localization and reading all remain obstacles |
| Stage14E Source-Premise Ledger, fresh32 | 0/32 useful vs original reader1/32; −3.125pp [−9.375,0] | Both treatments20/32 vs native19/32, same single rescue with already-known helper information | Development improvement did not generalize; answer change is not proof of new acquisition |
| Stage14E2 deliberative reader, development24 | Diagnostic-target reasoning4/24 vs compact4/24; 0pp [−16.67,+12.50] | Not measured | Additional helper reasoning did not improve primary useful acquisition; complete new source structure recovered in neither mode |

The strongest current operational finding is that naming an object, producing valid JSON, preserving source provenance or showing the image again does not ensure recovery of the **specific task-critical relational structure**. This remains a diagnosed operational obstacle, not a uniquely identified causal explanation. No new experiment is selected or authorized by this retrospective document.

### Claim-level status

| Claim | Evidence status | Boundary |
|---|---|---|
| C1: evidence handoff | Supported functionally in bounded controlled assays | Not universal MathVision timing, neural erasure or a general Thinking-only regime |
| C2: evidence supply can rescue failure | Supported strongly on the source-eligible MathVision cohort | Representation-changing intervention; cross-task/format heterogeneity; not pure perception attribution |
| C3: deployable acquisition methodology improves evidence fidelity | Not demonstrated by SAVA, ledger or deliberative-reader studies | Negative/uncertain results preserved; better final numbers alone do not certify acquisition |

### Terminology used across the history

| Term | Meaning and caution |
|---|---|
| E* | Researcher/source-derived textual evidence; source validity, sufficiency and answer safety remain separate checks |
| I / T | Instruct / Thinking model variants in later studies; early ROI T instead means the demanded target source |
| Direct / CoT | Unprompted or answer-contract baseline versus explicitly prompted reasoning; the exact contract varies by stage |
| Native | The original image-conditioned solver condition; later interrupted-continuation studies use a fresh seeded continuation from a frozen prefix |
| VSD | The stage-defined visual-source contribution/necessity readout; not a universal unitless acquisition score |
| E0 / E1 / E2 | Annotated entity mention / fact made explicit / downstream use in early temporal audits; not certified internal acquisition times |
| ROI | A source region; predicted boxes, manually defined offline references and diagnostic targets have different evidential status |
| Cap / unscorable / missing | Distinct completion, answer-interpretation and execution states; each stage's frozen endpoint determines how they enter rates |
| Family | Conservative independent source/problem grouping; events, seeds, windows and variants are nested observations |
| pp / CI | Percentage points / uncertainty interval; the original report specifies weighting, bootstrap unit and multiplicity |
| B1–B4 | Stage12 behavioral bottleneck profiles (evidence recovery, context access/use, downstream, mixed); not latent neural diagnoses |
| Useful acquisition | Later method endpoint: source-correct, bound, task-relevant new evidence or justified reinspection, with explicit errors disqualifying the readout; known facts alone receive no new-acquisition credit |

<a id="stage-index"></a>
## Stage index

“Complete” means the authorized bounded action was completed, which can include a failed scientific gate. “Stopped” means a precondition blocked the proposed later phase. See linked dossiers for exact denominators and qualifications.

| Stage / branch | Final recorded status |
|---|---|
'''
parts=[header]
for r in rows:parts.append(f'| [{r["title"]}](#{anchor(r["id"])}) | {r["status"]} |\n')
parts.append('\n<a id="stage-by-stage-findings"></a>\n## Stage-by-stage findings\n')
for r in rows:
 parts.append(f'\n<a id="{anchor(r["id"])}"></a>\n### {r["title"]}\n\n**Status:** {r["status"]}.\n\n{r["findings"]}\n\n')
 refs=r['reports']+r['memories']
 parts.append('**Evidence:** '+ ' · '.join(link(p,Path(p).name) for p in refs[:3])+f'. [Full reports/history](#record-{r["id"]}).\n')
parts.append('''
<a id="interpretation-rules"></a>
## Interpretation rules and documentation discrepancies

- **Technical PASS ≠ scientific success.** Stage3B.7, Stage8C v2/repair, Stage11C/R, Stage12A/R/C, Stage13B/C and original SAVA technical records have distinct reasons for stopping. Do not convert an invalid or unrun assay into a null scientific result.
- **Attention ≠ causal support ≠ first acquisition.** W2/W8 ablations measure source necessity at selected readouts. Large routing changes can leave evidence preference largely intact. Previously cached visual information survives many “no direct access” masks.
- **A wrong final is not a wrong visual fact.** Actual-wrong-token support, wrong-versus-correct margins, binding errors, extraction errors and downstream errors are separate measurements. No-image correctness is not automatically PRIOR_FILL.
- **An observed claim is not proof of its hidden origin.** Native traces, separately elicited D1 evidence, helper READ outputs, offline E*, and diagnostic oracle targets remain separate. No missing/ambiguous claim is relabelled as acquisition failure.
- **Rescue must be accompanied by regressions and missingness.** BlindTest is the clearest counterexample to reporting only rescue rates. Scored-pair percentages, assigned-family bounds and marginal accuracy have different denominators.
- **Source evidence is not infallible or neutral.** Structured layouts can carry many subfacts; answer-safety and task equivalence are not implied by gold agreement. Source uncertainties such as MMStar997 and withheld Stage14D-0 facts remain recorded; no historical score is silently repaired here.
- **Repeated cases/seeds are not independent families.** Stage13A reused Stage12Y's families, Stage14B confirmation repeats source-selected cases, and Stage14E2 reused development cases. A new generation or a later stage number does not create untouched confirmation data.
- **Model comparisons are recipe/checkpoint comparisons.** The official audit verified Instruct temperature .7/top-p .8/presence1.5/cap32,768 versus MathVision Thinking temperature1/top-p .95/presence0/cap40,960. Later approved long Thinking studies used81,920. Equal hyperparameters are not automatically a fair native comparison; differing recipes do not isolate a pure thinking mechanism.
- **Precision and execution path matter.** Most model inference was BF16; FP32 contribution accounting or Stage8C v3 FP32 intervention calculations do not imply every model weight/run was FP32. Native source-sum rounding, cache chunking, vLLM scheduling, input serialization and replay semantics were recurring technical constraints.
- **Historical snapshots are stale in places.** Some phase-memory “Current State” sections precede later result sections. Stage2B/2C have final reports despite old pending notes. The Stage9A main report still says controls pending, but its Stage9A.3 transition addendum explicitly preserves74/87 and cancels13. Stage7A's final report contains an older sentence saying interpretation pending; its completed assessment and tables govern. Stage14C-V remains unfinished overall despite completed R results and saved C generations.
- **Source-informed targets in Stage14E are imperfect diagnostic controls.** Some included qualitative hints; the final report explicitly rejects treating them as a clean identity-only oracle upper bound. They did not enter the deployable final method. The limitation cannot be erased by calling them technical controls.
- **Confidence intervals do not cover every uncertainty.** Most bootstrap intervals capture family sampling variation, not single-AI annotation error, reference uncertainty, model/runtime confounding or repeated-seed variance. Different stages used different frozen multiplicity/weighting rules; retain their reported intervals rather than pooling them.

<a id="resources"></a>
## Resources and preserved unfinished work

This is not a newly recomputed cumulative project compute ledger. Older records mix measured device/request time, throughput projections and actual Slurm allocation charges; adding them would double-count reused work and mix units. Stage-specific accounting links in the full reports are authoritative for their stated scope.

| Work | Recorded accounting / status |
|---|---|
| Stage6A |117.4163 measured device-hours; not an allocation-charge total |
| Official Qwen audit |0.571111 charged GPU-hours |
| Stage13A |8.568611 charged GPU-hours |
| Stage14B |193.218 observed/proxy GPU-hours in its report; preserve its accounting definition |
| Stage14D calibration |About0.363056 charged GPU-hours; old375-hour main proposal remains HOLD |
| Historical SAVA technical+pilot work |21.365278 charged GPU-hours retained in later accounting; do not misstate this as within the earlier16-hour ceiling |
| Stage14E development cycle |7.148889 additional charged GPU-hours |
| Stage14E2 |1.668611 additional charged GPU-hours |
| Current autonomous24-hour allowance |8.8175/24 charged hours cumulatively recorded; historical SAVA is separate, not erased |

Remaining/unrun branches include: the old Stage14D1,674-continuation experiment (HOLD); Stage14C-V C review/final closure; deferred MathSight/MicroVQA/MedXpertQA-MM; gated Stage8C held-out gain test; Stage9A reserve/query-text extensions; blocked oracle/transfer/cross-scale mechanisms; and Stage14E2's unused fresh32 evaluation. The later fresh32 is not Stage14E's already-evaluated32. No paused goal or follow-on is resumed by this documentation task.

<a id="full-records"></a>
## Full source reports and phase histories

The following expandable blocks retain the complete text of selected consolidated reports and every stage phase memory. Content is historical evidence: “next,” “pending,” “GO,” and “STOP” refer to the original report's scope/date. Headings are nested and relative links are rebased for this file; scientific text and numbers are not corrected silently. Broken original links are shown explicitly. SHA-256 values refer to the **unchanged original source bytes**, not the adapted presentation. Original plans are indexed separately below.
''')
for r in rows:
 parts.append(f'\n<a id="record-{r["id"]}"></a>\n### {r["title"]}: source dossier\n\n[Return to stage findings](#{anchor(r["id"])}). **Synthesized status:** {r["status"]}.\n')
 for typ,caption in [('reports','Full result / audit report'),('memories','Historical phase memory (including failures and decisions)')]:
  for p in r[typ]:
   parts.append(f'\n<details>\n<summary>{caption}: {p}</summary>\n\nOriginal: {link(p)}  \nSHA-256: `{digest(p)}`\n\n{embed(p)}\n\n</details>\n')
 if not r['reports']:parts.append('\nNo separate final summary was identified for this branch; its phase history and plans are retained. This is not a claim of successful scientific completion.\n')
parts.append('\n<a id="plan-register"></a>\n## Plan and protocol register\n\nEvery Markdown file directly under `plan/` is listed below. Plans/checklists specify intentions and amendments, not independently completed experiments.\n')
for r in rows:
 if r['plans']:
  parts.append(f'\n### {r["title"]}\n\n')
  for p in r['plans']:parts.append(f'- {link(p)}\n')
parts.append('\n### Global context\n\n')
for p in global_plans+context:parts.append(f'- {link(p)}\n')
parts.append(f'''\n<a id="coverage"></a>\n## Coverage and provenance\n\n- {len(rows)} organized stage/branch/audit entries.
- {sum(len(r['reports']) for r in rows)} embedded consolidated result/audit documents.
- {sum(len(r['memories']) for r in rows)} embedded phase/history records, including every `workspace/phase_memory/phase_*.md` plus the original Stage14D-0 output-local memory.
- {sum(len(r['plans']) for r in rows)+len(global_plans)} indexed plan/checklist/protocol/amendment Markdown files.
- Source inventory, mapping, hashes and validation: {link('workspace/research_history_20261119/source_manifest.json')}.
- Reproducible assembly: {link('scripts/build_research_history_20261119.py')} and {link('workspace/research_history_20261119/stages.tsv')}.

The reconstruction preserves negative evidence and distinguishes historical observations from current synthesis. It does not assert that every artifact in this large repository is independently verified, every source fact is correct, or every chronological note is consistent. Per-case/raw evidence remains available through the original reports and manifests.\n''')
if broken:
 parts.append('\n### Unresolved links inherited from source documents\n\nThese are documentation issues, not missing scientific results inferred from a link alone. Exact source and target are retained for later repair; no original was modified.\n\n| Source | Original target |\n|---|---|\n')
 for x in sorted({(d['source'],d['target']) for d in broken}):parts.append(f'| {link(x[0],Path(x[0]).name)} | `{x[1]}` |\n')
# Snapshot hashes ensure the build never changes its sources.
for s in sources:assert digest(s['path'])==s['sha256']
OUT.write_text(''.join(parts))
phase_paths={str(p.relative_to(ROOT)) for p in (ROOT/'workspace/phase_memory').glob('phase_*.md')}
covered={s['path'] for s in sources}
assert phase_paths<=covered
assert {str(p.relative_to(ROOT)) for p in (ROOT/'plan').glob('*.md')}<=covered
manifest={'snapshot_date':'2026-11-19','task':'retrospective documentation only','report':str(OUT.relative_to(ROOT)),'report_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'stage_entries':rows,'sources':sources,'unresolved_source_links':broken,'coverage':{'stages':len(rows),'reports':sum(len(r['reports']) for r in rows),'memories':sum(len(r['memories']) for r in rows),'plans':sum(len(r['plans']) for r in rows)+len(global_plans),'all_phase_memories_mapped':True,'all_plans_mapped':True,'sources_unchanged_during_build':True}}
(WORK/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report':str(OUT.relative_to(ROOT)),'bytes':OUT.stat().st_size,'lines':len(OUT.read_text().splitlines()),**manifest['coverage'],'unresolved_original_links':len(broken)},indent=2))
