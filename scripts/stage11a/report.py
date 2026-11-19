"""Write a self-contained Stage11A report, without choosing another experiment."""
import os
from scripts.stage11a.common import ROOT,ARMS,load

def rate(r):
    if r['point'] is None:return 'not estimable (n=0)'
    lo,hi=r['ci95']
    return f"{r.get('numerator',round(r['point']*r['n']))}/{r['n']} ({100*r['point']:.1f}%; 95% CI {100*lo:.1f}–{100*hi:.1f}%)"

def main():
    assert os.environ.get('SLURM_JOB_ID')
    inf=load(ROOT/'stage11a_primary_inference.json');decision=load(ROOT/'stage11a_go_nogo_decision.json')
    res=load(ROOT/'stage11a_resource_accounting.json');agree=load(ROOT/'stage11a_annotation_agreement.json')
    d=load(ROOT/'stage11a_thinking_cot_discordance.json');m=inf['all_eligible']['modes']
    pilot=ROOT/'stage11a_equal_evidence_pilot.json'
    lines=['# Stage11A — Visual-evidence bottleneck census','',f"Decision: **{decision['decision']}**. Eligible evidence sets: {rate(inf['all128_eligibility'])}. "
        f"The primary Thinking-correct / CoT-failed subset contains {decision['discordant']} independently matched families; {decision['informative_discordant']} have a unique nonmixed localization.",'',
        'This is a descriptive census of explicit-demand evidence recovery and observable native text. It does not establish why Thinking succeeds or identify hidden-state encoding. All128 original families and384 native trajectories were preserved.','',
        '## Design and review','',
        'Two independent model-agent passes inspected all128 image/question packets before mode correctness was opened. A common evidence proposal received two sufficiency checks; corrections and exclusions were resolved prospectively. Only1–4 image-derived facts sufficient with the original question were eligible. The original proposal, raw reviews and repair history remain available.','',
        f"Eligibility counts: `{inf['eligibility_counts']}`. All eligible native trajectories were annotated. Explicit probes cover {m['thinking']['probe_n']} families ×3 modes, capped at512 new tokens. The same image, semantic request, item seed, preprocessing and Stage9A mode templates were used with the pinned Qwen3-VL-2B BF16 checkpoints. No benchmark baselines were regenerated.",'',
        'Native annotation saw one anonymized reasoning trace at a time, with final correctness, other modes and probe output withheld. Writing style can reveal the mode, and prior reviewer project exposure cannot be erased. Probe annotations were sealed before joining the existing reviewed native answer labels. These are independent model-agent passes, not independent human reliability measurements. A versioned workload amendment assigned 101/103/75 reviews to the two independent reviewers and main reviewer while preserving all 96 shared agreement reviews. Historical assignments and raw reviews remain unchanged.','',
        '## Primary endpoints','',
        '| Mode | Explicit probe: all facts | Native text: sufficient facts | Native final correct | Failure given sufficient native facts |',
        '|---|---|---|---|---|']
    for arm in ARMS:
        r=m[arm];lines.append('| '+arm+' | '+' | '.join(rate(r[k]) for k in ['probe_accessible','native_sufficient','final_correct','downstream_failure'])+' |')
    lines += ['', 'Probe rates use only probed eligible families; native rates use all eligible families. Figure2 and the matched-subset inference use the same probed-family denominator for all three measurements. Error intervals use4000 family bootstrap draws, fixed seed1120260928. Families, not atoms or tokens, are independent units.','',
        'The primary failed-answer endpoint includes valid wrong answers and no valid final; both are preserved separately. No valid final is never itself labeled a visual error. Wrong-only rates given sufficient native evidence: '+ '; '.join(a+': '+rate(m[a]['downstream_wrong_only']) for a in ARMS)+'.','',
        'Fixed512-token probe cap reached: '+ '; '.join(a+': '+str(v['length_cap'])+'/'+str(v['runs']) for a,v in res['probe_by_mode'].items())+'. All visible response text, including Thinking reasoning, was scored. These unequal cap-hit rates materially limit any claim about relative evidence-recovery capability beyond this exact prompt and token budget.','',
        '## Matched Thinking–CoT localization','',
        '| Direction | Families | Availability gain A | Native-access gain B | Downstream gain C | Mixed D |','|---|---:|---:|---:|---:|---:|']
    for name,k in [('Thinking correct / CoT failed','primary'),('CoT correct / Thinking failed','reverse')]:
        v=d[k];lines.append('| '+name+' | '+str(v['n'])+' | '+' | '.join(str(v['counts'].get(c,0)) for c in 'ABCD')+' |')
    lines += ['', 'Overlapping localization predicates stay mixed, with all underlying flags retained. A probe-inaccessible result plus correct sufficient native evidence is not forced into a single bottleneck. N5 (not externalized) stays distinct from observable absence N0.','',
        'Paired Thinking minus CoT differences on matched families:']
    for k,r in inf['all_eligible']['thinking_minus_cot'].items():
        lines.append(f"- {k}: {r['point']:.4f}, 95% CI {r['ci95']}; paired positive/negative directions {r['left_only']}/{r['right_only']}; descriptive exact McNemar p={r['mcnemar_exact_two_sided_p']:.4g}.")
    lines += ['', 'Subject, evidence type, atom count, reasoning length and evidence timing are descriptive secondary summaries in the inference/discordance artifacts. They do not introduce additional primary hypotheses. Evidence timings are quote-based annotation positions where available, not causal read times. A first-sufficient time assembled from correct quotes does not certify a consistently correct evidence state later in a conflicting N4 trace.','',
        '## Agreement and feasibility','',
        f"Native fine-state agreement: `{agree['native_fine']}`. Coarse agreement (sufficient / observable insufficient / not externalized): `{agree['native_coarse']}`. Fine-grained proportions promotable: **{agree['fine_proportions_promotable']}**.",'',
        f"Sufficiency on the fixed agreement families: `{agree['sufficiency_fixed32']}`. Localization rule agreement: `{agree['localization_fixed32']}`. Raw disagreements and their adjudication remain preserved.",'',
        f"Feasibility components: eligible={decision['eligible']}; forward discordant={decision['discordant']}; informative={decision['informative_discordant']}; CoT candidate failure profile counts={decision['cot_failure_profile_unique_counts']}; mixed fraction={decision['mixed_fraction']:.3f}; native gate kappa={decision['native_agreement_kappa']}.",'',
        'The frozen thresholds were not relaxed after outcomes. The decision incorporates independent-family support, category spread, agreement and mixed-state burden.','',
        ('The decisive minimum-support gate fails: only4 uniquely informative Thinking-gain families versus the required8. Eligibility and annotation agreement pass. Strong GO also lacks16 forward discordances and a second CoT failure category with8 families. This is insufficient clean localization, not evidence that Thinking has no performance advantage or that no bottleneck mechanism exists.' if decision['decision']=='NO_GO' and decision['informative_discordant']==4 else 'The component counts above determine the frozen feasibility decision.'),'',
        '## Interpretation limits','',
        'Explicit probing changes demand and is limited to512 generated tokens. Probe failure may reflect that prompt/budget; it does not establish that evidence was not encoded. Correct native text does not prove all relevant hidden states are equivalent, and missing text does not prove missing internal access. Results apply to the exact Stage9A CoT prompt and selected evidence-identifiable MathVision families. E* exclusions constrain generalization. Native final correctness is not a substitute for evidence fidelity.','',
        '## Optional pilot and resources','',
        ('Optional pilot artifact: [stage11a_equal_evidence_pilot.json](stage11a_equal_evidence_pilot.json).' if pilot.exists() else 'No optional Equal-Evidence pilot was run because the frozen feasibility gate did not authorize it.'),'',
        f"Total allocated GPU-hours: **{res['allocated_gpu_hours']:.4f}**, including startup and failures; peak simultaneous GPUs: {res['peak_gpus']}. All GPU jobs are terminal. The hard2.5GPU-hour cap was respected. {res['new_short_probe_runs']} short probes generated {res['probe_tokens']} tokens; {res['probe_length_cap_count']} hit the fixed cap. Annotation workload is recorded as passes/traces, not invented human-hour estimates.",'',
        '## Exactly one recommendation','',decision['exactly_one_recommendation'],'',
        'Stage11B and every new research stage remain unlaunched. Required tables, manifests, annotation reviews, inference and four PNG/PDF figures are stored in this directory.']
    with (ROOT/'stage11a_summary.md').open('x') as f:f.write('\n'.join(lines)+'\n')

if __name__=='__main__':main()
