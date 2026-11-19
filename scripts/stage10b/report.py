"""Write the requested single-recommendation census report."""
from scripts.stage10b.common import ROOT,load


def proportion(r):
    if r['point'] is None:return f"undefined (0/{r['n']})"
    lo,hi=r['ci95'];return f"{r['successes']}/{r['n']} = {100*r['point']:.1f}% [{100*lo:.1f}, {100*hi:.1f}]"


def main():
    infer=load(ROOT/'stage10b_yield_inference.json');gate=load(ROOT/'stage10b_go_nogo_decision.json')
    agree=load(ROOT/'stage10b_annotation_agreement.json');resource=load(ROOT/'stage10b_resource_accounting.json')
    p=infer['pooled'];timing=p['timing'];corpus=load(ROOT/'stage10b_corpus_manifest.json')
    lines=['# Stage10B: recurrent visual-demand census','',
        f"**{gate['decision'].replace('_',' ')}: {p['clean']} clean candidate trajectories among {p['eligible']} eligible.** "
        f"{p['new_demand']} trajectories satisfy the semantic C1–C4 criteria. "
        'These are passive candidate associations; this stage does not establish causal reopening or repeated visual/textual phase alternation.','',
        '## Corpus and execution','',
        'All128 frozen Stage9A MathVision and96 Stage8A main MathVerse native Qwen3-VL-2B-Thinking trajectories were retained. '
        'No correctness, detector, length or intervention-outcome selection was applied. '
        f"The corpus contains {sum(r['reasoning_tokens'] for r in corpus['rows']):,} reasoning tokens. "
        'No exact image duplicates were found; conservative problem/image trajectory is the independent unit. '
        'Capped/abnormal runs remain observed-prefix evidence. No original trace was modified or regenerated.','',
        'Two independent model-agent semantic passes reviewed the question/image/reasoning packets without routing, accuracy or causal outcomes. '
        'Main-agent adjudication sealed A, the text interval, B onset/identity, prior availability and ROIs before passive values were opened. '
        'The second passes then reviewed target-specific routing under the frozen32-token rule. '
        'Long negative traces were screened through demand/observation passages and context; this is not exhaustive human token-by-token annotation. '
        'Positive candidates received full prior-text verification. Reported yields are operational explicit-demand census estimates for these corpora.','',
        '## Trajectory-level endpoints','',
        'Percentages have Wilson95% intervals. Events/windows from one trajectory are never independent samples.','',
        '| Source | E1: C1–C5 / eligible | E2: C1–C4 / eligible | E3: C5 given C1–C4 |',
        '|---|---|---|---|']
    for name,r in [*infer['datasets'].items(),('Pooled',p)]:
        lines.append(f"| {name} | {proportion(r['E1'])} | {proportion(r['E2'])} | {proportion(r['E3'])} |")
    lines += ['',f"Timing among clean primary events: n={timing['n']}, median={timing['median']}, IQR={timing['q25_q75']} generated tokens after B onset. "
              'Lag is the onset of the qualifying routing run; an explicit observation may occur elsewhere within the same32-token window. The complete0–31 distribution is saved in the inference JSON and Figure3.',
              f"Taxonomy (earliest clean event per trajectory): {p['taxonomy']}. Additional clean events ({infer['clean_event_count']} total events) are secondary.",'',
              f"Using the strongest annotated topology among all clean events in each trajectory (secondary): {infer['secondary_taxonomy_any_clean_event']}. No clean S2 return recurrence was identified; the plan permits Strong GO from S1 cases.",'',
              f"Unresolved target/routing coverage affects {len(p['unresolved_C5_trajectories'])} semantic-positive trajectories. "
              f"The observed-to-best-case missing-data yield bounds are {p['missing_data_yield_bounds']}; these bounds are not confidence intervals. "
              'Missing routing and unlocalizable targets are not evidence of absent re-access.','',
              '## Agreement and preserved negatives','',
              'Raw independent labels are preserved separately from adjudication. Agreement between model-agent passes is not independent human-rater reliability.','',
              '| Measure | n | Raw agreement | Cohen kappa |','|---|---:|---:|---:|']
    for key in ('semantic_trajectory','availability_matched','availability_union','C5_event','clean_trajectory'):
        r=agree[key];lines.append(f"| {key} | {r['n']} | {r['raw']} | {r['kappa']} |")
    lines += ['',f"Onset agreement within±8 tokens: {agree['onset']['within8']}/{agree['onset']['n']} ({agree['onset']['raw']:.3f}). Source identity: {agree['source']['same']}/{agree['source']['n']} ({agree['source']['raw']:.3f}). "
              f"Acceptable for Strong GO: {agree['acceptable_for_strong_go']}. "
              'Detection/onset/availability/interval/source disagreements and resolutions are retained in the agreement/adjudication artifacts.','',
              f"Event-union availability agreement is low because {agree['unmatched_event_groups']} of157 retained event groups were nominated by only one pass, including repeated already-textualized and partial negative cases. Matched-event availability passes the prospectively frozen gate, but broad event-inventory agreement remains a limitation. C5 agreement uses shared adjudicated targets and does not erase semantic detection disagreements.",'',
              '| Primary negative category | Independent trajectories |','|---|---:|']
    lines.extend(f'| {k} | {v} |' for k,v in infer['primary_negative_categories'].items())
    lines += ['', '## Measurement and interpretation limits','',
        'C1 means that a visual fact/subgoal is semantically resolved in the trace; it does not certify factual correctness or visual causation. '
        'C2 permits a distinct derived conclusion even when shorter than24 tokens. '
        f"Requiring at least24 tokens from the end of the A quote to B onset descriptively leaves {infer['minimum24token_interval_sensitivity']['clean']} clean trajectories "
        f"and {infer['minimum24token_interval_sensitivity']['new_demand']} semantic-positive trajectories. This raw anchor-gap sensitivity is not a pure text-interval duration estimate or replacement primary rule. "
        'Completion and length-quartile results, target types and dataset strata are included in the inference JSON.','',
        'C5 requires at least two consecutive target-selective measurements (target/control patch-mean ratio≥1.5 and within-image target mass≥.05), '
        'plus frozen detector positivity or an explicit B observation within32 tokens. These prospective screening thresholds are not a validated causal classifier. '
        'Detector positivity alone and raw global image attention do not qualify. Historical MathVision routing uses unchanged layers19–22 and the frozen Stage8A detector. '
        'MathVerse historical event summaries do not supply arbitrary new-B patch routing. '
        f"Passive repair was used for {resource['passive_repaired_trajectories']} trajectories; it teacher-forced frozen prefixes with64-token eager chunks "
        'and checked observer/no-op feature/logit/cache behavior. Original native per-query routing for those traces was not saved, so reconstruction is explicitly distinguished from historical observation.','',
        'A low yield can reflect task distribution, already-textualized evidence, continuous inspection, model behavior, operational annotation limits or routing identifiability. '
        'It is not proof that recurrent perceptual demand is impossible. Stage10AR single-transition evidence and Stage4A source retargeting remain separate findings.','',
        '## Resources and deliverables','',
        f"New GPU allocation: **{resource['allocated_gpu_hours']:.4f} GPU-hours**; "
        f"{resource['passive_repaired_trajectories']}/32 maximum passive-repair trajectories. "
        'New generations:0. Causal interventions:0. All Stage10B GPU jobs are terminal. '
        f"Annotation burden: {resource['annotation']['reviewer_trajectory_judgments']} independent reviewer–trajectory judgments plus main adjudication; human labor hours were not measured.",'',
        'All11 required artifacts are present in this directory; optional passive-repair data are included only when executed. '
        'Four standalone PNG/PDF figures are under `figures/`. Raw passes, semantic seals, routing evidence, provenance checks and resource receipts are under `audit/` and `annotations/`.','',
        '## Exactly one recommendation','',gate['recommendation'],'',
        '**STOP:** no causal follow-on, new model, benchmark or synthetic construction was launched.','']
    path=ROOT/'stage10b_summary.md'
    with path.open('x') as f:f.write('\n'.join(lines))


if __name__=='__main__':main()
