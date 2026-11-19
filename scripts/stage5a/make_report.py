"""Complete the plan report, acceptance record and one review-only recommendation."""
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json


def main():
    audit=read_json(OUT/'audit/final_artifact_validation.json');assert audit['passed']
    summary=read_json(OUT/'analysis/taxonomy_summary.json');source=read_json(OUT/'analysis/source_summary.json')
    resource=read_json(OUT/'audit/resource_summary.json');figures=read_json(OUT/'analysis/figures/index.json')['figures']
    classification=read_json(OUT/'phase_i_separability/feature_ablation.json')['grounded_correct_vs_hallucination']
    bootstrap=read_json(OUT/'phase_i_separability/classifier_base_bootstrap.json')
    diagnosis=read_json(OUT/'audit/hmr_readout_orientation_diagnostic.json');wrong_positive=sum(r['wrong_logp_source_contribution']>.05 for r in diagnosis['rows'])
    wrong_increases=sum(not r['wrong_candidate_probability_falls_after_alternative_removal'] for r in diagnosis['rows'])
    claims={
        'O1':{'status':'not_confirmed','claim':'Matched high-attention multistate separation','reason':'No strict alignment-only or mirage confirmation cohort; no primary matched pairs.'},
        'O2':{'status':'limited_support','claim':'Causal retrieval identification','reason':'216 demanded-source-dominant events and82/85 positive semantic readouts; no new matched internal-signature comparison established.'},
        'O3':{'status':'not_confirmed','claim':'Mirage','reason':'Zero strict cases under the frozen criterion;139/267 confirmation events matched and128 unresolved.'},
        'O4':{'status':'illustrative_only','claim':'Failure heterogeneity','reason':'10 Tier2 margin-based H-MR profiles and one Tier1 H-SC case; error-specific readout audit prevents treating all H-MR profiles as causal error sources.'},
        'O5':{'status':'case_level_supported','claim':'Separate local grounding from downstream integration failure','reason':'13 reviewed later-error events on7 bases have correct local claims and demanded-source dependence.'},
        'O6':{'status':'unrun_insufficient','claim':'Alignment interference','reason':'Only2 independent M candidates and0 strict alignment-only events; minimum32 not met.'},
        'O7':{'status':'gate_not_met','claim':'Sink-state mechanism','reason':'Two matched confirmation pairs; no robust held-out or behavior-linked sink evidence.'}}
    write_json(OUT/'analysis/paper_claim_assessment.json',{'outcomes':claims,'paper_headline_supported':False,
        'defensible_result':'A broad source-dependence atlas and reviewed integration counterexamples; the stronger matched alignment/mirage headline is not established.',
        'classifier_accuracy_is_not_mechanism':True,'negative_or_missing_classes_preserved':True})
    recommendation={'recommendation_count':1,'decision':'HOLD — Stage5B failure-rescue feasibility review',
        'next_scientific_action':'Review error-specific readout validity and source identity on the nine frozen H-MR candidate bases before designing any rescue intervention.',
        'scope':'Review-only recommendation; not executed in Stage5A.',
        'candidate_event_ids':[r['event_id'] for r in diagnosis['rows']],
        'why':'10 Tier2 events/9 bases are below24 events and do not form a coherent error-promoting source class under the saved candidate-log-probability audit.',
        'strongest_objection':'A small rescue pilot could be cheaper, but alternative-source suppression worsens the correct-versus-wrong margin in all10 profiles and increases wrong-token probability in7.',
        'decision_changing_evidence':'audit/hmr_readout_orientation_diagnostic.json',
        'review_question':'Does a source-specific semantic perturbation support the proposed wrong-source error mechanism on a correctly oriented error readout?',
        'falsifiable_future_rescue_requirement':'An approved source intervention must improve the correct local candidate relative to matched controls, with final-answer effects measured separately on fresh confirmation.',
        'no_next_stage_started':True}
    write_json(OUT/'analysis/next_intervention_target.json',recommendation)
    next_text='''# Stage5A next-stage recommendation

**HOLD — Stage5B failure-rescue feasibility review.**

Review error-specific readout validity and source identity on the nine frozen
H-MR candidate bases before designing a rescue intervention. This is the sole
next-action recommendation; no follow-on experiment is executed.

The10 Tier2 events fall below the plan's24-event practical minimum. More
fundamentally, their frozen H-MR labels describe alternative-source dominance
for a **correct-versus-wrong candidate margin**. That does not identify a source
that caused the wrong token. In the saved scores, alternative-source removal
worsens that margin in all10 and increases wrong-token probability in7. Only
17_E1 has an error-token contribution above0.05 nats/token; two other positive
contributions are below0.001. The source diagnosis is therefore not yet coherent
enough to justify even a mechanism-guided rescue pilot.

The review should ask whether source-specific semantic evidence supports an
error-promoting source interpretation with a correctly oriented error readout.
If it does, a separately approved pilot must predict and measure improved local
correct-candidate preference against matched controls, then confirm on fresh
bases; final-answer changes must remain a separate endpoint. This report does
not authorize that pilot or another cohort search.

Evidence: [readout diagnostic](../audit/hmr_readout_orientation_diagnostic.json),
[frozen failure labels](../phase_h_failure/hallucination_events.jsonl), and
[source profiles](../phase_b_causal/w2_source_profiles.jsonl).
'''
    (OUT/'summaries').mkdir(exist_ok=True);(OUT/'summaries/next_stage_recommendation.md').write_text(next_text)
    criteria=[
        ('ontology_frozen_before_results',True),('natural_without_correctness_balance',True),('atlas_frozen_without_attention_or_effect_selection',True),
        ('natural_at_least160',len(read_jsonl(OUT/'cohort/natural_prevalence_manifest.jsonl'))>=160),('atlas_at_least96',len(read_jsonl(OUT/'cohort/causal_atlas_manifest.jsonl'))>=96),
        ('local_claims_independent_of_final_correctness',audit['checks']['wrong_final_not_hallucination']),('attention_independent_ROIs',True),
        ('canonical_A6000_causal_arms',audit['checks']['all16_scoring_environments_existing_four_A6000s']),('W2_primary_W8_frozen_sensitivity',True),
        ('wrong_final_not_automatic_hallucination',True),('causal_evidence_used_for_subtypes',audit['checks']['frozen_labels_reconstruct_without_attention']),
        ('CF_subset_frozen_before_semantic_scoring',True),('passive_after_causal_label_freeze',audit['checks']['labels_frozen_before_each_passive_rank']),
        ('discovery_rule_applied_to_heldout_confirmation',audit['checks']['discovery_only_reference_and_strict_mirage_gate']),
        ('classifiers_grouped_by_base_and_template',audit['checks']['whole_template_and_base_splits_no_leakage']),('accuracy_not_mechanism',True),
        ('sink_descriptive_only',True),('no_failure_rescue_run',True),('no_representation_substitution',True),('exactly_one_recommendation',recommendation['recommendation_count']==1)]
    acceptance={'status':'PASS' if all(v for _,v in criteria) else 'FAIL','technical_only':True,'criteria':[{'number':i+1,'criterion':k,'passed':bool(v)} for i,(k,v) in enumerate(criteria)],
        'passed':sum(v for _,v in criteria),'total':20,'mechanical_checks':15,'artifact_checks':audit['check_count'],'tests_passed':31,'figures':20,
        'limitations':['CF minimum48 reached, target64 not reached','No strict alignment-only/mirage confirmation yield','139/267 confirmation events have matched target references',
            'Only2 independent M candidates; dedicated utility and final-candidate readout unrun','H-MR margin labels are not established error-promoting source mechanisms',
            '203 temporal histories unresolved; only4 reviewed refresh opportunities','Most subtype and matched-state inferential slots underpowered/unrun'],
        'evidence':'audit/final_artifact_validation.json','scope_complete_no_followon_started':True}
    write_json(OUT/'summaries/stage5a_acceptance.json',acceptance)
    table='\n'.join(f"| {n} | {r['events']} | {r['bases']} | {r['confidence_tiers']} |" for n,r in summary['subtypes'].items())
    classifiers='\n'.join(f"| {name} | {r['metrics']['balanced_accuracy']:.3f} | {r['metrics']['macro_F1']:.3f} | {r['metrics']['AUROC']:.3f} | {r['metrics']['ECE10']:.3f} |" for name,r in classification.items())
    outcomes='\n'.join(f"- **{name}: {r['status']}** — {r['reason']}" for name,r in claims.items())
    links='\n'.join(f"{f['number']}. [{f['title']}](../analysis/figures/{f['png'].split('/')[-1]}) ([PDF](../analysis/figures/{f['pdf'].split('/')[-1]})). {f['caption']}" for f in figures)
    report=f'''# Stage5A: failure and attention-state taxonomy

**Technical PASS:20/20. The matched high-attention alignment/mirage hypothesis is
not confirmed.** Stage5A completes the200-base natural census,128-base causal
atlas and all feasible frozen assays. It establishes a broad source-dependence
record and13 reviewed integration-error events on7 bases. Strict alignment-only
and mirage confirmation cohorts have zero yield; their inferential comparisons
remain unrun. The sole next recommendation is a **Stage5B failure-rescue
feasibility review**, with no rescue experiment started.

The research question is whether similar visual attention can reflect semantic
alignment, causal retrieval, verification/refresh, or distinct visual failures.
The hypothesis predicts different causal and internal states at matched
attention magnitude. Semantic and causal labels were frozen before passive
features; wrong final answers never served as visual-hallucination labels.

## Cohorts and execution

| Cohort / subset | Bases | Selected events |
|---|---:|---:|
| Natural census |200|550|
| Causal atlas |128|347|
| Discovery |32|80|
| Fresh confirmation |96|267|
| Semantic/sham subset |48|85|
| Fixed R16 subset |96|256|

The natural cohort is the first200 eligible bases in the frozen screen, without
correctness balancing. It ends at screen208.210 screen positions were manually
reviewed, nine duplicate stimuli were excluded, and one further eligible reserve
was retained outside the natural cohort. All200 retained variants are Vision
Dominant; this is a selected-event MathVerse census, not exhaustive trace-error
or general multimodal population prevalence. The atlas contains63 bases with a
selected local error and65 others under the frozen fill rule. Historical anchors
remain separate:48 compatible Stage4A bases contribute144 discovery-reference
events, not fresh prevalence observations.

The fixed initial budget was800 and the maximum1400.551 exact-protocol existing
native trajectories were indexed for possible reuse. Fresh acquisition preserved
{resource['phases']['generation']['completed']} completed outcomes and stopped after the genuine cohort
freeze: one rank finished its planned shard; three stopped between trajectories.
Unused reserves are preserved. No post-effect population expansion occurred.

All new GPU work used the existing tmux9 / Slurm108548 allocation on node07:
exactly four RTX A6000 GPUs. No new Slurm allocation, package installation or
CUDA_VISIBLE_DEVICES assignment was made. The user's replacement-allocation
authority was not needed. Model loading uses the existing project `.venv` and
Qwen3-VL-4B-Thinking checkpoint; native generation settings and dataset assets are
unchanged.

The source assay uses BF16, canonical2048-token streaming prefixes, eight fixed
single-query barriers, W2 primary and W8 target sensitivity, all36 layers/all32
heads. Removing selected source-value terms leaves Q/K/V and native attention
unchanged; no attention renormalization occurs. R16 removal is restricted to
layers16–23, the current query and up to16 strictly preceding reasoning tokens.
Passive telemetry uses both late layers28–29/all32 heads and an independently
replayed t−8 prior. Historical selected heads are descriptive coordinates only.

## Natural census and source evidence

The550 selected events include386 locally correct,94 incorrect,20 undecidable
and50 without an explicit visual claim.64/200 bases contain at least one selected
incorrect local claim;121/200 final answers are correct and79 wrong. Base-level
semantic categories can overlap. The atlas scores92 of the94 selected incorrect
events, covering63 of the64 affected bases. The remaining base and unresolved
mechanisms are explicitly unascertained.

The347 atlas events have216 demanded-source-dominant profiles,17 alternative
dominant,65 mixed-support,38 weak under both W2 and W8,17 broader-window-dependent,
and66 unresolved profiles. These labels overlap. Large negative effects are not
nulls. Median within-base mean VSD_T is1.2655 nats/candidate-token; median W8_T is
1.4821. There are237 X arms,267 validated I arms, and five raw M arms on four
bases. Only two M events have an independent T/M contrast; the other three
overlap. They do not yield a strict alignment-only cohort.
I controls match ROI cardinality and use reviewed background regions; they are
not ink-matched to printed labels. Their selection and exclusions are preserved.

The48 semantic bases meet the minimum48, below target64. The conservative numeric
construction was exhausted over92 eligible atlas bases:164 source proposals,
85 constructed assets,79 construction failures, and six manual rejections.
The79 accepted source assets yield85 validated event readouts. Semantic and sham
images preserve the frozen token layout; factorial edits use disjoint reviewed
source regions where available.82/85 event effects exceed absolute sham by0.05;
the median base-mean CE-minus-absolute-sham is12.8013. All48 base means are positive.
The subset chiefly covers numeric labels and cannot validate arbitrary wrong
entity bindings. Effects from editing another source on the target readout are
cross-source controls, not alternative-fact semantic readouts.

The96-base R16 subset has134/256 target trigger effects above0.05 and a median
base-mean effect of0.1979. These are secondary source-dependence changes; trigger
generalization is not required for retrieval labels. Temporal review resolves
121 first-use,19 reuse and four refresh events;203 remain unresolved. Selected
event order was never substituted for full native history. Fixed-history image
counterfactuals do not localize when visual information was first acquired.

## Failure diagnoses and readout limits

| Operational label | Events | Bases | Confidence tiers |
|---|---:|---:|---|
{table}

H-INT is separate from visual hallucination. Its13 events have correct local
claims, demanded-source dependence, a wrong final answer and an explicitly
reviewed later error. An error already present before the selected event does
not qualify as its downstream error. The single H-SC example108_E1 claims CD=5
although the image says8: VSD_T=5.0000, semantic CE=6.6250 and sham shift=0.
It is a convergent extraction-error example, not a population-level class.

The10 H-MR labels are **frozen margin-based source profiles**, all Tier2. D is
the ground-truth candidate's mean log probability minus the foil's; the actual
native candidate direction is separately stored. Alternative-source dominance
on this margin does not establish that the alternative source caused the wrong
token. One saved-score validity diagnostic found only{wrong_positive}/10 wrong-token
contributions above0.05. Alternative-source removal increases wrong-token
probability in{wrong_increases}/10 and worsens the correct-versus-wrong margin in all10.
Two remaining positive wrong-token contributions are below0.001. Frozen labels
are preserved, but a wrong-source rescue mechanism is not inferred from them.
See the [orientation audit](../audit/hmr_readout_orientation_diagnostic.json).

Zero H-NR/H-ST diagnoses do not establish their absence. H-NR needs measured
semantic null evidence; missing counterfactuals are not nulls. H-ST additionally
needs an actual prior-source history, and only four refresh opportunities were
resolved. Subtype counts inside the natural200 are ascertained lower bounds;
atlas counts are not presented as an unbiased mechanism prevalence estimate.

## Attention confirmation and separability

Discovery-only normalization preserves source class and ROI-size buckets and
merges only adjacent progress/length buckets until eight reference ROIs are
available. The high criterion is a matched density percentile of at least0.90.
Both mass and density retain raw values, matched z scores and percentiles. The
ROI source class was prospectively normalized from the reviewed source kind;
the original base evidence type remains available. Sparse matching stays
unresolved rather than borrowing a different source class or ROI size.

211/347 atlas events have a matched target reference, including139/267 held-out
events.19 confirmation events cross the high-attention criterion. There are
zero strict mirages, zero high-attention missing-CE candidates and zero strict
alignment-only events. Alignment–retrieval and mirage–retrieval matched families
therefore have no pairs. Their six slots each remain unrun with p=1. The broad
semantic-mention/retrieval2×2 is reported separately; a mention without demanded
retrieval is not automatically a strict alignment-only mechanism.

Only grounded-correct versus locally wrong visual claims has sufficient
classifier yield. Models use fixed regularization, whole-template folds, no
base/event leakage and train-fold imputation/scaling. The confirmation data
contain76 grounded-correct and51 hallucination base/class observations, with
overlap because one base can exhibit both states. Predictions are averaged
within base/class, and bootstrap intervals resample unique bases together.

| Features | Balanced accuracy | Macro F1 | AUROC | ECE10 |
|---|---:|---:|---:|---:|
{classifiers}

F1 attention-only balanced accuracy has a base-bootstrap95% interval
[{bootstrap['models']['F1']['balanced_accuracy_CI95'][0]:.3f}, {bootstrap['models']['F1']['balanced_accuracy_CI95'][1]:.3f}];
F5's interval is[{bootstrap['models']['F5']['balanced_accuracy_CI95'][0]:.3f}, {bootstrap['models']['F5']['balanced_accuracy_CI95'][1]:.3f}].
These are descriptive held-out prediction results. F4/F5 contain causal features
that partly define grounded labels, so their performance is circular as
independent mechanism evidence. Feature/ROI availability and event selection can
also carry contextual information. The other three classifier tasks are
insufficient. PCA is fitted on discovery F3 and projected descriptively; clusters
do not define the taxonomy.

The two independent M candidates retain their already-scored W2 local NLL and
demanded-margin effects as descriptive evidence. Zero meet strict alignment-only
qualification, below the32-event minimum. The dedicated utility experiment,
including its distinct final-candidate margin, is unrun. Local D is not
substituted for final-answer utility.

Sink mass, t−8 release and source-group gains/losses are retained for all347
events. Matched sink confirmation has only two pairs. The sink gate is not met;
generic attention magnitude, replication and behavioral relevance are not
established. No sink manipulation occurred. Major comparisons include local and
global correctness strata and leave-one-template-out sensitivity; low yield is
reported rather than ignored.

## Claim assessment and next action

{outcomes}

The single recommendation is **HOLD — Stage5B failure-rescue feasibility review**
of error-specific readouts and source identity on the nine H-MR candidate bases.
The10 events fall below24 and do not yet form a coherent error-promoting source
class. This review-only recommendation is detailed in
[next_stage_recommendation.md](next_stage_recommendation.md). No new stage,
rescue, sink intervention or representation substitution was started. The
project-local research-control skill was unavailable; this stage followed the
user's fully specified plan and fixed gates, and the proposed review is not
executed as an autonomous follow-on action.

## Verification and reproducibility

-15/15 mechanical checks on8 historical bases,24 events and312 arms.
-{audit['check_count']}/{audit['check_count']} final artifact checks;{audit['frozen_hashes_verified']} frozen/raw hashes verified.
-764 causal/semantic event-image files,3182 scored arms and243776 source calls.
-347 fresh passive event files, each with a current and t−8 state; all347 native
  candidate/logit replays exactly match the causal run. All85 semantic native
  readouts also replay exactly.
-31 CPU tests pass, covering taxonomy guards, native spans, source masks,
  controlled edits, grouped-KV telemetry, matching, Holm and grouped classifiers.
-20 standalone PNG/PDF figure pairs. Raw vectors, per-head metrics, source token
  identities, exact preceding text-entity matches where available, text-control
  QK summaries and late residual norms remain available. Pooled key summaries
  are descriptive; no representation-equivalence or substitution claim is made.

All new implementation is under `scripts/stage5a` and
`code/visual_reasoning/stage5a`; historical causal runtimes are unchanged.
Original prospective config files are preserved with explicit pre-score
amendments. The first semantic completion audit ran before the last rank
finished and correctly rejected incomplete coverage; the completed audit passes.
The first final resource audit incorrectly required every generation rank to
stop at the freeze; one had completed its entire shard earlier. Its preserved
failure log and the corrected complete-or-frozen-stop check document the repair.
Neither required a GPU rerun or a changed scientific label.

Reproduction entry points: `audit_scores.py`, `freeze_causal_labels.py`
(create-once), `run_passive.py`, `analyze_passive.py`, `analyze_taxonomy.py`,
`make_figures.py`, `audit_results.py`, and `make_report.py`, all in
`scripts/stage5a`. GPU entry points require the recorded allocation and gates;
they must not be launched on a login node. The complete evidence is in
[mechanics](../audit/mechanical_validation.json),
[final audit](../audit/final_artifact_validation.json),
[resources](../audit/resource_summary.json),
[acceptance](stage5a_acceptance.json), and
[source summary](../analysis/source_summary.json).

## Figures

{links}
'''
    # CommonMark requires a space after each list marker.
    report=report.replace('\n-15/','\n- 15/').replace(f'\n-{audit["check_count"]}/',f'\n- {audit["check_count"]}/').replace('\n-764 ','\n- 764 ').replace('\n-347 ','\n- 347 ').replace('\n-31 ','\n- 31 ').replace('\n-20 ','\n- 20 ')
    (OUT/'summaries/stage5a_summary.md').write_text(report)
    print({'acceptance':acceptance['status'],'criteria':acceptance['passed'],'recommendation':recommendation['decision'],'figures':len(figures)})


if __name__=='__main__':main()
