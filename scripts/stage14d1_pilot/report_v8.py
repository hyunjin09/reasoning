"""Render the completed fixed pilot from immutable scored/source records."""
import json
from pathlib import Path
from scripts.stage14d1_pilot.common import P, load, rows, save, sha, now
from scripts.stage14d1.contracts import ARMS


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(text)


def pp(x):
    return f'{100*x:+.2f}'


def main():
    result = load(P/'analysis/accuracy_and_pairs_final_v8.json')
    records = load(P/'analysis/scored_logical_rows_final_v8.json')['rows']
    source = load(P/'analysis/source_review_summary_v8.json')
    execution = load(P/'analysis/execution_metrics_v8.json')
    resources = load(P/'audit/resource_accounting_final_v8.json')
    originals = {r['item_id']: r for r in rows(P/'inference/families.jsonl')}
    by = {(r['item_id'], r['arm']): r for r in records}
    regressions = load(P/'annotations/regression_review_complete_v8.json')['items']
    selected = sorted(set(regressions+['471','423','1380','1537','2924','487']), key=int)
    cases = []
    case_text = ['# SAVA final casebook\n',
        'Selection: all nine families with a native-correct → any-treatment-wrong transition; all three primary QI rescues; the single unscorable family; and two fixed-panel examples with new correct readouts. These 15 cases are descriptive, not a new representative sample. Helper judgments remain distinct from solver answers and latent acquisition.\n']
    for item in selected:
        annotation_path = P/'annotations/readouts'/f'{item}.json'
        annotation = load(annotation_path)
        case = dict(item_id=item, image=originals[item]['image'], image_sha256=originals[item]['image_sha256'],
            question=originals[item]['question'], source_annotation=str(annotation_path),
            source_annotation_sha256=sha(annotation_path), source_final_answers_hidden=annotation['final_answers_hidden'],
            arms={a: by[item,a] for a in ARMS}, readouts=annotation['records'])
        cases.append(case)
        case_text += [f'## Item {item}\n', f"[Original image]({Path(case['image']).resolve()}) · [source review]({annotation_path.resolve()})\n",
                      case['question']+'\n', '| Arm | Reviewed answer | Status | Original parser answer | Raw solver |\n|---|---|---|---|---|\n']
        for a in ARMS:
            r = by[item,a]
            status = 'UNSCORABLE' if r['correct'] is None else 'CORRECT' if r['correct'] else 'WRONG'
            case_text.append(f"| {a} | {r['answer']} | {status} | {r['original_parser_answer']} | [raw]({Path(r['generation_path']).resolve()}) |\n")
        case_text.append(f"\nSource review was {'before' if annotation['final_answers_hidden'] else 'after'} final-answer inspection.\n")
        for r in annotation['records']:
            case_text.append(f"\n**{r['arm']} helper: {r['status']}**. {r['note']}\n")
            if r['generation_path']:
                raw = load(r['generation_path'])['raw_decoded_response']
                case_text += [f"[Exact raw helper]({Path(r['generation_path']).resolve()}); SHA256 `{r['generation_sha256']}`; alias `{r['alias_of']}`.\n",
                              '```text\n'+raw+'\n```\n']
    save(P/'analysis/casebook_final_v8.json', dict(at=now(), cases=cases, selection='All regressions + all primary rescues + unscorable + two fixed-panel acquisition examples'))
    write(P/'reports/casebook_final_v8.md', '\n'.join(case_text))

    lines = ['# Stage14D-1 SAVA — completed 72-family feasibility pilot\n',
        f'Completed {now()}. **All 72 families and 432 logical arm assignments are complete, represented by 345 distinct physical continuations. All GPU allocations are terminal.**\n',
        '**The pilot does not demonstrate a final-answer accuracy benefit from the tested SAVA implementation.** The primary QI−N contrast is −4.17 percentage points (95% family-bootstrap CI −12.50 to +4.17), with three rescues and six regressions. This is an uncertain negative estimate, not proof that every form of subgoal-addressed acquisition is ineffective.\n',
        '## Design and validity\n',
        'The cohort is the original source-selected, previously audited R72 development set: 36 global-required, 18 local-sufficient and 18 local-plus-global source opportunities. Selection used source metadata and frozen hash matching, not answer outcomes. These labels describe the historical source opportunity, not necessarily the controller’s actual query. This is a feasibility pilot, not an independent confirmation or full-benchmark accuracy estimate.\n',
        'Every arm starts from the same original image and frozen 512-token prefix, reconstructed with a fresh fixed family seed. The checkpoint is Qwen3-VL-4B-Thinking revision `1de27d8c51f12e819435303b9e84c4e25ba8401e`, BF16, vLLM 0.11.0, Torch 2.8.0, Transformers 4.57.1. Sampling: temperature 1.0, top-p .95, top-k 20, repetition penalty 1.0, presence penalty 0; unchanged continuation cap 81,920. Helpers use compact structured output and a 2,048-token cap. Original image preprocessing remains 602,112–4,014,080 pixels.\n',
        '| Arm | Operation |\n|---|---|\n| N | Fresh native continuation from the shared image-conditioned prefix |\n| G | Generic full-image lookback readout, then continuation |\n| Q | Subgoal query and text-only extra READ helper; the solver still receives its original image |\n| QI | Same query with full-image READ |\n| QIA | Same query, predicted address, and full-image READ |\n| QGL | Same query/address, original unmodified global image plus valid predicted crop, then continuation |\n',
        'The solver always retains the original image. Local views are helper inputs, generated from model-predicted coordinates; no human ROI, E* value or gold answer enters runtime. The global image is unmarked. GLOBAL/UNRESOLVABLE and invalid-address cases use frozen fallbacks. Helper JSON/provenance validity, query relevance, localization correctness, readout correctness, and solver completion are separate measurements.\n',
        '## Technical recovery and preservation\n',
        '1. Initial long-form helper outputs failed to commit JSON. The compact helper interface was repaired prospectively while keeping the native solver recipe fixed. The earlier QUERY/NONE grammar had a prompt/schema field-order mismatch that biased the branch space; both branches now pass independent grammar witnesses and generation controls. The original eight NONE outputs are not scientific evidence.\n',
        '2. Literal model-written quotations failed on LaTeX/Unicode serialization and unsupported citations. The final interface uses deterministic host-created question/prefix span IDs, exact spans and hashes; no fuzzy fabricated match is accepted. Numeric/color/assertion guards and adversarial tests remain. A cited prefix can still be wrong: provenance is not source truth. Native image identifiers and the missing shape property were repaired prospectively.\n',
        '3. LOCATE now emits integer 0–1000 coordinates, converted once to normalized boxes. Mode-first schema branches enforce LOCAL=1, MULTI=2, GLOBAL=0 and UNRESOLVABLE=0 boxes. Degenerate addresses are rejected without clipping or fabricated crops. Decimal grammar exclusion was disproved; the coordinate convention was a compatibility repair, not a proven full diagnosis of every bad box.\n',
        '4. Replay diagnostics found identical prompt/image/prefix inputs and, at case33’s token30 divergence, identical RNG states but differing logits under changing prefill schedules. Greedy also diverged in default batch8. Disabling prefix caching alone was insufficient; `VLLM_ENABLE_V1_MULTIPROCESSING=0` restored tested same-schedule reproducibility. The later full-cap admission repair changed batch shape: v7 repeated 8/8 exactly within schedule and across workers, but only5/8 matched the former batch8 reference. These failures remain preserved.\n',
        '5. Prospective v8 requires same-schedule exact64-token repeats at original and independent technical seeds, original-seed agreement with frozen v7, and original prompt-token equality. Both workers passed; all32 cross-node comparisons also matched exactly. This does not guarantee arbitrary batch-shape or full81,920-token bitwise identity, or restore a historical advanced RNG state.\n',
        '6. The old failed shard oversubscribed eventual KV capacity and stalled; repeated preemption is suspected, not directly counted. No OOM was recorded. Full-cap reservation now accounts for prompt/visual expansion and the entire81,920-token allowance, admitting two concurrent requests safely. New jobs use48-hour Slurm limits and no six-hour internal deadline.\n',
        'All36 complete original families retain their internally paired six arms. All36 previously incomplete families use the recovered schedule for all arms. Two old completed item2924 receipts are preserved outside primary analysis; selection was based on incomplete-family coverage, not correctness. Thus170 original +175 recovered physical receipts form the primary345. Historical failures, seeds, code/protocol versions and source records remain immutable.\n',
        'Final v6 technical gates:8/8 replay,7/8 query contracts,6/7 LOCATE contracts,31/31 READ contracts and48/48 transport slots. Synthetic outputs:20/20 valid/terminating and18/20 expected branch choices; the Roman positive-control NONE decisions remain false negatives rather than being prompted away. CPU coverage includes provenance/adversarial tests, image-ID handling, coordinate and mode/cardinality constraints, fallbacks, receipt reuse, capacity admission, family-coherent merge and bootstrap tests. The final merge/family/statistics/reuse suite passed28 tests. [Technical findings](resumption_v8_technical_findings.md) and [earlier diagnostic evidence](../../../stage14d1_sava_recovery/v1/reports/technical_recovery_final.md) provide exact records.\n',
        '## Final-answer results\n',
        '| Arm | Correct / assigned | Correct / scorable | Wrong | Unscorable | Cap hits | Rescue vs N | Regression vs N |\n|---|---|---|---:|---:|---:|---:|---:|\n']
    for a in ARMS:
        x=result['arms'][a]; pair=result['pairs'].get(a+'-N', {})
        lines.append(f"| {a} | {x['correct']}/72 ({100*x['known_correct_fraction']:.2f}%) | {x['correct']}/{72-x['unscorable']} ({100*x['scorable_accuracy']:.2f}%) | {x['wrong']} | {x['unscorable']} | {x['cap_hits']} | {pair.get('rescue','—')} | {pair.get('regression','—')} |\n")
    lines += ['\nThere are no missing executions. QIA item1537 is the only unscorable final: it reached81,920 tokens without closing its thought section. It is not counted as wrong. QIA’s known-correct lower bound is37/72=51.39%; its missingness bounds are51.39–52.78%. All other arms have72 scorable finals.\n',
        'The inherited scorer initially left48 logical slots (45 physical outputs) pending:37 physical outputs had extracted but noncanonical strings, seven needed explicit prose-final extraction, and one had no closed final. Gold-hidden response review transcribed44 explicit finals, preserving original parser strings and raw outputs. Examples include `\\text{A}`→A, explicit prose numerals, and an already written11/7 fraction accompanying11:7. No answer was derived from unfinished reasoning and no equivalence policy changed. Original automatic scores are preserved; use the reviewed final files below.\n',
        '| Contrast | Paired n | Difference (pp) | 95% family-bootstrap interval (pp) | Rescues / regressions |\n|---|---:|---:|---|---|\n']
    for key in ['QI-N','QI-G','QI-Q','QGL-QI','QGL-QIA','G-N','Q-N','QIA-N','QGL-N']:
        x=result['pairs'][key]; lo,hi=x['paired_bootstrap_95ci']
        lines.append(f"| {key} | {x['paired_scorable']} | {pp(x['paired_accuracy_difference'])} | [{pp(lo)}, {pp(hi)}] | {x['rescue']} / {x['regression']} |\n")
    lines += ['\nThe primary contrast is QI−N. Secondary contrasts are QI−G, QI−Q, QGL−QI and QGL−QIA; other arm−N contrasts are descriptive. Intervals use4,000 paired family-cluster bootstrap draws, seed20261019, frozen answer-format×structured strata, and equal family weighting. Secondary intervals are not multiplicity-adjusted. Aliases/windows/tokens are not independent samples.\n',
        'The QI−N estimate is negative in both execution blocks: original36 families−2.78pp (2 rescues/3 regressions), recovered36−5.56pp (1/3). This is descriptive sensitivity, not a randomized comparison of schedules. Source-opportunity subgroup correct counts are:\n',
        '| Historical source opportunity | Families | N | G | Q | QI | QIA | QGL |\n|---|---:|---:|---:|---:|---:|---:|---:|\n']
    for group,b in result['context_subgroups'].items():
        lines.append('| '+group+' | '+str(b['families'])+' | '+' | '.join(str(b['arms'][a]['correct'])+(' (+1 unscorable)' if b['arms'][a]['unscorable'] else '') for a in ARMS)+' |\n')
    lines += ['\nThese small, correlated source strata do not establish a causal global-context interaction.\n',
        '## Acquisition results, separately from answer accuracy\n',
        'All72 query/address reviews were completed before opening scientific finals. The controller emitted69 QUERY and3 NONE records. The host accepted62 QUERY plus all3 NONE; seven queries were rejected. Only22/62 accepted queries (22/72 assigned families) were judged fully task-relevant. Across all72, relevance was25 yes,33 partial,11 no and3 not applicable. Forty-seven queries concerned information already supplied or tentatively mentioned; this includes unresolved conjectures and must not all be called redundant. Two value-preloading flags were both rejected by the host.\n',
        'LOCATE was attempted62 times;60 addresses passed transport checks, producing49 local-view families. Among those49,14 regions were judged correct for the requested target,20 had partial coverage,13 selected the wrong target, one the wrong source and one was underspecified. Correct localization of a requested target does not prove that target is useful. No region was manually repaired.\n',
        'The acquisition-rate panel remains the frozen24-family source-stratified hash sample (12 global,6 local,6 local-plus-global), not the outcome-enriched casebook. All24 were reviewed before final-answer inspection. Whole-record correctness includes value, binding and supporting source. Unknown/absent/abstaining evidence is not imputed wrong.\n',
        '| Helper arm | Verified correct record /24 | Explicitly wrong /24 | Unknown /24 | Demand answered /24 | New correct visual information /24 |\n|---|---:|---:|---:|---:|---:|\n']
    for a,x in source['fixed_readout_sample_by_arm'].items():
        lines.append(f"| {a} | {x['explicit_source_correct']} | {x['explicit_source_wrong']} | {x['source_correctness_unknown']} | {x['demand_answered']} | {x['new_correct_visual_information']} |\n")
    lines += ['\nVerified-record yield: QI−G−12.50pp (95% CI−33.33,+8.33), QI−Q+12.50pp (−8.33,+33.33), QGL−QI+4.17pp (−8.33,+16.67), QGL−QIA0pp (−12.50,+12.50). The stricter new-correct-demand counts are2,2,3,3,4 for G,Q,QI,QIA,QGL. These sparse supporting observations do not prove fresh visual use or mediation. G can choose different facts from the targeted arms; record correctness alone is not a perfectly matched-target measure. [Full supporting bootstrap](../analysis/readout_stats_v8.json).\n',
        'Additional source reviews cover five technical cases outside the fixed24,17 source-flagged cases, three newly reviewed regression families, and three primary-rescue families:52 reviewed families total. All nine regression families are covered. The last six reviews are explicitly outcome-enriched and excluded from the fixed-panel rates. One AI reviewer performed the judgments, with prior source exposure and no independent reliability estimate.\n',
        '## Fallbacks, costs and execution\n',
        'The432 logical slots use345 primary physical solver calls;87 slots are exact-payload aliases. Query-arm aliases to N occur in10 families (seven rejected queries and three NONE). G always had its own physical continuation. Other aliases arise from exact identical injected records or address/global-view fallbacks. QGL used49 actual full-image-plus-local helper calls;13 accepted-query cases reused a full-image helper. A fallback is not a successful local acquisition.\n',
        '| Arm | Logical slots | Slots reusing another solver receipt | Alias to N | Median generated tokens | Median request latency (s) |\n|---|---:|---:|---:|---:|---:|\n']
    for a,x in execution['arms'].items():
        lines.append(f"| {a} | 72 | {x['physical_alias_slots']} | {x['alias_to_native']} | {x['solver']['output_tokens']['median']:,.1f} | {x['solver']['request_latency_seconds']['median']:.1f} |\n")
    lines += [f"\nActual cumulative Slurm allocation charge: **{resources['total_gpu_hours']:.6f} GPU-hours**, including all failed/technical attempts; the final two resumed jobs used{resources['resumption_gpu_hours']:.6f} GPU-hours. The prior total was12.682778GPU-hours. The former16-hour ceiling was superseded for this fixed remainder by the user’s instruction to finish after the resource HOLD; no extra scientific cohort or arm was added. New jobs had48-hour limits and ended after their queues. Final Slurm states for149690/149691 are COMPLETED. A post-completion release request for149691 followed receipt authentication during a shutdown/status transition; no rollout was interrupted.\n",
        'The primary345 solver calls generated5,198,520 tokens; median12,985, IQR5,919–21,143, maximum81,920. There were344 backend-stop completions and one cap completion. Reused scientific helpers comprise439 distinct calls and19,617 generated tokens; all439 stopped normally. Query72, LOCATE62, and physical READ305 calls are deduplicated across aliases. Helper visual tokens total326,214, solver visual tokens330,697. Measured image-preprocessing CPU time totals13.44s for helpers and12.87s for solvers; separately isolated GPU visual-encoder time is not available.\n',
        'Solver request latency median298.38s (IQR131.81–588.65), helper latency median62.71s. These include overlapping scheduling residence; summing them does not yield billed GPU-hours. Per-arm costs also share alias receipts. The Slurm ledger is authoritative and includes failed work/startup. Two archived completed partial-family outputs and eight earlier interrupted records remain outside primary metrics. [Execution costs](../analysis/execution_metrics_v8.json) · [allocation ledger](../audit/resource_accounting_final_v8.json).\n',
        '## Case interpretation\n',
        '- Item633: targeted helpers report rabbit99 while the source places it at100. QI/QIA regress from native76 to75, but QGL returns76 despite its wrong helper fact. This supports an explicit helper error; it does not establish a simple one-to-one mediation from that value to every final.\n',
        '- Item2919: G claims four gray cells per face; the source has12. Targeted image helpers abstain despite valid image transport. All treatment finals regress. Missing readouts are not labeled visual misreads.\n',
        '- Item2898: DA/DC are correctly named, but the needed inner/outer shading relation remains unaddressed. Item847 similarly repeats a correct row count instead of resolving position/offsets. Correct but unhelpful readouts can accompany regressions.\n',
        '- All three QI rescues were inspected after scoring. Item471’s helper is uncertain; item423 repeats six identical gray rectangles without the needed orientation/layout; item1380 says rectangular, already given, rather than resolving the string configuration. None provides a clearly new task-critical fact in the standardized QI helper readout. Final-answer rescue alone therefore cannot establish better acquisition.\n',
        '- Item2924 has a correct parallelogram readout but all final answers remain wrong. Item487 obtains a correct19-hexagon readout while native and all treatment finals are already correct. These preserve positive acquisition observations without inventing downstream benefit.\n',
        '[Final casebook with exact raw outputs, images, source notes and score provenance](casebook_final_v8.md). The earlier46-family [source-only casebook](source_casebook_v8.md) is preserved.\n',
        '## H1–H4 and one recommendation\n',
        '**H1, subgoal-query benefit: not demonstrated.** QI is below G by6.94pp (CI−15.28,+1.39) and below Q by4.17pp (−12.50,+4.17). Source-readout gains over Q are uncertain and do not exceed G on overall verified-record yield. Small new-fact counts leave uncertainty.\n',
        '**H2, source-address/global-local increment: not demonstrated.** QGL−QI is0pp (−4.17,+2.78); QGL−QIA is−1.41pp among71 scorable pairs (−7.25,+4.23). One additional fixed-panel new-correct readout is a limited positive observation. No crop-only or matched-image-budget extension was run, so pure global-context necessity or a cost-isolated crop effect is untested.\n',
        '**H3, downstream accuracy: no demonstrated improvement.** Primary QI−N is−4.17pp, with uncertainty spanning zero. Generic G has a small uncertain+2.78pp change. These data neither justify a positive SAVA efficacy claim nor precisely rule out small gains.\n',
        '**H4, target-selection bottleneck: supported descriptively, not causally isolated.** Few accepted queries are fully relevant; many are underspecified, repeated, or ask for mathematical unknowns rather than source-resolvable facts. An oracle-target counterfactual was not run. The pilot cannot prove how much a better target selector would recover.\n',
        '**Recommendation — not executed:** Before an online Stage14E controller or scale-up, validate a demand-resolution interface that distinguishes a genuinely unresolved, source-resolvable visual premise from an already supplied fact or a mathematical unknown, and abstains when that distinction cannot be made. Keep the next development question focused on target selection/readout sufficiency; this pilot provides no basis to prioritize additional crop machinery. A prospective protocol and independent evaluation of that change remain future work.\n',
        'The tested implementation remains a small development pilot with one stochastic continuation per family/arm, single-reviewer acquisition labels, previously observed families, mixed but family-coherent execution blocks, and extra-image/compute differences. No latent acquisition mediation or novelty claim is established. The old1,674-continuation/375GPU-hour Stage14D grid remains HOLD. Stage14C-V remains unfinished. **No Stage14E or other follow-on experiment was launched. STOP.**\n',
        '## Final artifact map\n',
        '- [Reviewed family/arm scores](../analysis/scored_logical_rows_final_v8.json) and [clean CSV](../analysis/scored_logical_rows_final_v8_clean.csv); original automatic scores and original CSV export are retained.\n',
        '- [Final paired estimates and source/schedule strata](../analysis/accuracy_and_pairs_final_v8.json).\n',
        '- [Gold-hidden response reviews](../annotations/response_review_v8.json), [regression coverage](../annotations/regression_review_complete_v8.json), [primary-rescue review](../annotations/primary_rescue_review_complete_v8.json).\n',
        '- [Generation/receipt freeze](../audit/scientific_generation_freeze_v8.json), [cross-node validation](../audit/resumption_v8_cross_node_validation.json), [historical preservation](../audit/final_historical_preservation_v8.json).\n',
        '- [Final package verification](../audit/final_result_verification_v8.json) and [reproduction notes](../audit/analysis_execution_notes_v8.json).\n']
    write(P/'reports/feasibility_main_v8.md', '\n'.join(lines))
    write(P/'reports/summary_v8.md', '# SAVA pilot complete\n\n72 families;432 logical arms;345 physical continuations. N39/72, G41/72, Q39/72, QI36/72, QIA37/71 scorable (one unscorable), QGL36/72. Primary QI−N−4.17pp,95%CI[−12.50,+4.17],3rescues/6regressions. No demonstrated SAVA accuracy gain. Technical recovery succeeded; acquisition and answer outcomes remain separate.\n\n'+f'All GPUs released; cumulative{resources["total_gpu_hours"]:.6f}GPU-hours. Future GPU jobs default48h and exit after work. [Full report](feasibility_main_v8.md). One target-selection recommendation, no follow-on launched.\n')
    print('Final report and15-case provenance casebook saved.')


if __name__ == '__main__':
    main()
