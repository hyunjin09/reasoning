"""Produce the eighteen prescribed Stage6A tables from a completed release.

The recommendation is the plan's yield branch, never an authorization to execute
another stage. Unknown labels and incomplete generations remain in accounting.
"""
import json
from collections import Counter, defaultdict

from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write
from scripts.stage6a.source_annotations import secondary_sources


def records(name):
    with (OUT / name).open() as stream:
        for line in stream:
            yield json.loads(line)


def read(name):
    return json.loads((OUT / name).read_text())


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')


def c1_availability_summary(base_ids, validated_conditions, complete):
    """Count audited stress assets separately from natural generation completion."""
    availability = ['intact', 'mild', 'strong', 'mask']
    return dict(
        mean_available_conditions=sum(sum(c in validated_conditions[k] for c in availability) for k in base_ids) / len(base_ids),
        counterfactual_and_mask_available_pairs=sum(all(c in validated_conditions[k] for c in ['counterfactual', 'mask']) for k in base_ids),
        mean_eos_conditions=sum(sum(complete(k, c) for c in availability) for k in base_ids) / len(base_ids),
        counterfactual_and_mask_eos_pairs=sum(complete(k, 'counterfactual') and complete(k, 'mask') for k in base_ids))


def main():
    integrity = read('audit/release_integrity.json')
    assert integrity['status'] == 'PASS', 'Finish release integrity audit first'
    release = read('cohort/primary_release_manifest.json')
    events = list(records('cohort/primary_release_events.jsonl'))
    event_map = {r['event_id']: r for r in events}
    bases = {r['base_id']: r for r in events}
    native = {r['event_id']: r for name in ['traces/controlled_native_index.jsonl', 'c4_natural_failure/generations.jsonl']
        for r in records(name) if r['event_id'] in event_map}
    assert set(native) == set(event_map)
    final = {r['event_id']: r for r in records('traces/final_correctness.jsonl')}
    assert set(final) == set(event_map)
    annotation_audit = read('audit/controlled_annotation_integrity.json')
    assert annotation_audit['status'] == 'PASS'
    prefix_bases = annotation_audit['complete_manual_prefix_bases']
    prefix_spans = annotation_audit['manual_prefix_spans']
    secondary_regions = sum(len(rows) for rows in secondary_sources().values())
    prefix_scope = f'C1 complete numeric-source prefix review covers {prefix_spans} spans across all {prefix_bases} frozen eligible bases, with {secondary_regions} secondary numeric ROIs. The fixed scope is the first 20 native reasoning spans, or the whole reasoning if shorter. Remaining whole-trajectory geometry is not fully annotated.'
    atlas = read('c4_natural_failure/matching_diagnostics.json')
    prevalence = read('c4_natural_failure/unbiased_prevalence.json')
    assert prevalence['completed_generation_records'] == 1000 and prevalence['pending_claim_reviews'] == 0
    control_review = read('c4_natural_failure/matched_control_review.json')
    atlas_members = list(records('c4_natural_failure/case_control_manifest.jsonl'))
    expected_controls = {r['base_id'] for r in atlas_members if r['atlas_role'] == 'no_detected_control'}
    assert control_review['status'] == 'PASS' and expected_controls == set(control_review['reviewed_control_ids']), 'Complete the matched-control image/context review'
    resource = read('audit/resource_summary.json')
    inventory = read('cohort/dataset_inventory.json')
    c1_freeze = read('cohort/c1_membership_freeze.json')
    by_cohort = {c: [r for r in bases.values() if r['cohort'] == c] for c in ['C1', 'C2', 'C3', 'C4']}
    conditions = defaultdict(dict)
    for row in events: conditions[row['base_id']][row['condition']] = row
    def complete(key, condition):
        row = conditions[key].get(condition)
        return bool(row and native[row['event_id']]['complete'])

    # Every explicitly reviewed source candidate receives one final accounting
    # entry, using its original authoring decision rather than a guessed cause.
    queue = list(records('cohort/primary_c1_review_queue.jsonl'))
    construction = {r['base_id'] for r in records('cohort/c1_primary_v2_base_manifest.jsonl')}
    semantics = read('config/primary_c1_authored_semantics.json')
    early = {r['base_id']: r for r in records('cohort/primary_c1_semantic_exclusions.jsonl')}
    exclusions = []
    for row in queue:
        key = row['base_id']
        if key in construction: continue
        decision = semantics.get(key, early.get(key, {}))
        reason = decision.get('reason', decision.get('defer_reason', decision.get('historical_duplicate_evidence')))
        assert reason, key
        exclusions.append(dict(base_id=key, cohort='C1', dataset=row['dataset'], stage='pre_generation_source_review',
            reason_code=decision.get('status', 'excluded_semantic_review'), reason=reason,
            evidence='config/primary_c1_authored_semantics.json; cohort/primary_c1_semantic_exclusions.jsonl', model_outcomes_used=False))
    assert len(queue) == len(construction) + len(exclusions)
    for row in c1_freeze['excluded']:
        exclusions.append(dict(base_id=row['base_id'], cohort='C1', stage='native_completion_readout_review',
            reason_code=row['membership_status'], reason=row['eligibility_reason'], evidence=row['review_packet'],
            native_completion_used=True, correctness_used=False))
    source_reviews = list(records('audit/c3_present_source_mask_review.jsonl')) + list(records('audit/c3_absent_source_review.jsonl'))
    for row in source_reviews:
        if row['status'] != 'pass': exclusions.append(dict(base_id=row['base_id'], cohort='C3',
            stage='pre_generation_source_mask_review', reason_code=row['status'], reason=row['reason'],
            evidence=row['review_evidence'], model_outcomes_used=False))
    c2_exclusions=list(records('cohort/c2_semantic_release_exclusions.jsonl'))
    exclusions += [{**r, 'stage':'source_mapping_revalidation_during_native_acquisition'} for r in c2_exclusions]
    write(OUT / 'cohort/exclusions.jsonl', exclusions)
    accounting = dict(status='COMPLETE', C1=dict(explicit_source_candidates=len(queue), constructed=len(construction),
        pre_generation_excluded=len(queue)-len(construction), terminal_native_reviewed=c1_freeze['candidate_bases'],
        native_ineligible=len(c1_freeze['excluded']), retained=len(by_cohort['C1'])),
        C2=dict(source_families=32, source_mapping_exclusions=len(c2_exclusions), retained_families=len(by_cohort['C2'])),
        C3=dict(source_families_reviewed=len(source_reviews), pre_generation_excluded=sum(r['status'] != 'pass' for r in source_reviews),
            retained_families=len(by_cohort['C3'])), C4=dict(initial_fixed_sample=600, prescribed_fixed_extension=400,
            acquired=len(by_cohort['C4']), replacements_after_native_outcome=0),
        upstream_candidate_order='cohort/semantic_candidate_order.jsonl',
        upstream_object_join_filters='cohort/object_candidate_exclusions.jsonl',
        scope='Explicit source reviews are distinct from broad dataset inventory and upstream mechanical candidate enumeration.')
    save('cohort/screening_accounting.json', accounting)

    tables = []
    def table(title, columns, rows): tables.append(dict(number=len(tables)+1, title=title, columns=columns, rows=rows))
    inventory_rows = []
    for row in inventory['datasets']:
        if 'rows' in row:
            evidence = f"{row['split']}: {row['rows']} rows, {row['bases']} bases, {row['images_referenced']} referenced images"
        elif 'images' in row:
            evidence = f"{row['split']}: {row['images']} images, {row['instances']} instances"
        elif row.get('candidates'):
            evidence = '; '.join(f"{c['split']}: {sum(s['row_count'] for s in c['arrow_shards'])} locally verified Arrow rows" for c in row['candidates'])
        else:
            evidence = row['status']
        inventory_rows.append([row['dataset'], row.get('usable', 'Located fallback; not validated for this stage'), evidence])
    table('Dataset availability and inventory', ['Dataset', 'Usable', 'Local evidence'], inventory_rows)
    table('Downloaded versus reused assets', ['Action', 'Count', 'Evidence'],
        [['Downloads', len(read('cohort/download_manifest.json')['downloads']), 'Ordered local lookup found core datasets'],
         ['Locally reused dataset entries', len(inventory['datasets']), 'Includes located unused fallbacks; no external writes'],
         ['Reused mechanics-v1 condition results', 59, 'Hash-validated reuse; not additional physical generations']])
    counts = Counter((r['cohort'], r['dataset']) for r in bases.values())
    table('Per-dataset retained base counts', ['Cohort', 'Dataset', 'Bases'], [[*key, n] for key, n in sorted(counts.items())])
    manipulation = read('audit/manipulation_audit.json')['records']
    counts = Counter((r['condition'], r['status']) for r in manipulation if r['cohort'] == 'C1')
    table('C1 saved-pixel manipulation validity', ['Condition', 'Status', 'Events'], [[*key, n] for key, n in sorted(counts.items())])
    c1_keys = [r['base_id'] for r in by_cohort['C1']]
    c1_conditions = sorted(set().union(*(set(conditions[k]) for k in c1_keys)))
    table('C1 counterfactual, mask and sham coverage', ['Condition', 'Assets', 'Natural EOS'],
        [[c, sum(c in conditions[k] for k in c1_keys), sum(complete(k, c) for k in c1_keys)] for c in c1_conditions])
    cells = ['AR', 'A_only', 'R_only', 'Neither']
    c2_rows = [r for r in events if r['cohort'] == 'C2']
    cell_counts = Counter(r['condition'] for r in c2_rows)
    cell_usable = {c: sum(native[r['event_id']]['complete'] for r in c2_rows if r['condition'] == c) for c in cells}
    table('C2 alignment-by-retrieval cells', ['Cell', 'Events', 'Natural EOS', 'Correct', 'Incorrect', 'Other/unknown'],
        [[c, cell_counts[c], cell_usable[c], *[sum(final[r['event_id']]['final_answer_correctness'] == label for r in c2_rows if r['condition'] == c) for label in ['CORRECT', 'INCORRECT']],
            sum(final[r['event_id']]['final_answer_correctness'] not in ['CORRECT', 'INCORRECT'] for r in c2_rows if r['condition'] == c)] for c in cells])
    table('C2 within-base pairing', ['Property', 'Families'],
        [['All four prompts and the same source image', sum(set(conditions[r['base_id']]) == set(cells) for r in by_cohort['C2'])],
         ['All four native traces reach EOS', sum(all(complete(r['base_id'], c) for c in cells) for r in by_cohort['C2'])]])
    c3_present = [r['base_id'] for r in by_cohort['C3'] if r['present']]
    c3_absent = [r['base_id'] for r in by_cohort['C3'] if not r['present']]
    table('C3 present and absent object families', ['Stratum', 'Source-valid bases', 'Intact EOS', 'Full-mask EOS'],
        [['Present', len(c3_present), sum(complete(k, 'intact') for k in c3_present), sum(complete(k, 'mask') for k in c3_present)],
         ['Absent', len(c3_absent), sum(complete(k, 'intact') for k in c3_absent), 'Not applicable; no fabricated target ROI']])
    roi = read('audit/roi_audit.json')
    table('C3 source ROI quality', ['Measure', 'Value'],
        [['Reviewed polygon-mask present families', len(c3_present)], ['Reviewed natural-negative families', len(c3_absent)],
         ['Geometry counts', {k: v for k, v in roi['geometry_counts'].items() if k.startswith('C3:')}],
         ['Opaque target pixels imply zero category information', False]])
    labels = list(records('c4_natural_failure/hallucination_labels.jsonl'))
    c4_counts = Counter(r['object_hallucination_presence'] for r in labels)
    table('C4 unbiased whole-trace object-error yield', ['Label', 'Images', 'Fraction of fixed sample'],
        [[label, n, n / len(labels)] for label, n in sorted(c4_counts.items())])
    atlas_rows = list(records('c4_natural_failure/case_control_manifest.jsonl'))
    counts = Counter((r['atlas_role'], r['split']) for r in atlas_rows)
    table('C4 separate matched atlas composition', ['Role', 'Split', 'Bases'], [[*key, n] for key, n in sorted(counts.items())])
    spans = Counter((r['cohort'], r['section']) for r in records('traces/reasoning_spans.jsonl'))
    table('Native span counts', ['Cohort', 'Section', 'Spans'], [[*key, n] for key, n in sorted(spans.items())])
    transitions = Counter((r['cohort'], r['transition_kind']) for r in records('traces/transition_annotations.jsonl'))
    table('Demand-transition annotations', ['Cohort', 'Kind', 'Spans'], [[*key, n] for key, n in sorted(transitions.items())])
    temporal = Counter()
    for row in records('traces/demand_annotations.jsonl'):
        temporal[row['cohort'], 'span', row['first_reuse_refresh']] += 1
        for role in row['source_temporal_roles'].values(): temporal[row['cohort'], 'individual source', role] += 1
    table('First-use, reuse and refresh annotations', ['Cohort', 'Unit', 'Role', 'Count'], [[*key, n] for key, n in sorted(temporal.items())])
    correctness = Counter((r['cohort'], r['local_visual_correctness'], final[r['event_id']]['final_answer_correctness']) for r in records('traces/local_correctness.jsonl'))
    table('Local visual versus final correctness', ['Cohort', 'Local visual label', 'Final label', 'Reasoning spans'], [[*key, n] for key, n in sorted(correctness.items())])
    folds = Counter((r['cohort'], r['split']) for r in bases.values())
    table('Discovery and confirmation composition', ['Cohort', 'Split', 'Bases'], [[*key, n] for key, n in sorted(folds.items())])
    duplicate = read('audit/stimulus_duplicate_audit.json')
    table('Template and stimulus duplication audit', ['Measure', 'Value'],
        [[k, duplicate[k]] for k in ['status', 'reviewed_identity_records', 'flagged_perceptual_pairs', 'primary_exact_pixel_groups', 'declared_template_families', 'errors']])
    anchors = Counter()
    for row in records('traces/future_causal_anchor_manifest.jsonl'):
        for kind in row['anchor_types']: anchors[row['cohort'], kind] += 1
    table('Future semantic causal-anchor candidates', ['Cohort', 'Kind', 'Anchors'], [[*key, n] for key, n in sorted(anchors.items())])
    assert len(tables) == 18

    assert read('audit/manipulation_audit.json')['status'] == 'PASS'
    coverage = c1_availability_summary(c1_keys, conditions, complete)
    stratum = Counter(r['dataset'] for r in by_cohort['C1'])
    gates = dict(C1=len(c1_keys) >= 90 and len(stratum) == 3 and min(stratum.values()) >= 24 and coverage['mean_available_conditions'] >= 3 and coverage['counterfactual_and_mask_available_pairs'] >= 72,
        C2=sum(cell_usable.values()) >= 96 and all(n >= 24 for n in cell_usable.values()),
        C3=sum(complete(k, 'intact') for k in c3_present + c3_absent) >= 120 and sum('mask' in conditions[k] for k in c3_present) >= 50 and sum(complete(k, 'intact') for k in c3_absent) >= 50,
        C4_unbiased_acquisition=len(labels) == 1000,
        C4_atlas=atlas['matched_pairs'] >= 60)
    controlled_pass = all(gates[c] for c in ['C1', 'C2', 'C3'])
    recommendation = 'GO — Cohort Repair' if not controlled_pass else 'GO — Natural Failure Extension' if not gates['C4_atlas'] else 'GO — Stage 6B Causal Retrieval-Dynamics Analysis'
    acceptance = dict(status='CONTROLLED_PASS_NATURAL_ATLAS_INSUFFICIENT' if controlled_pass and not gates['C4_atlas'] else 'ALL_SIZE_GATES_PASS' if controlled_pass else 'CONTROLLED_GATE_REPAIR_REQUIRED',
        gates=gates, C1=dict(retained=len(c1_keys), per_dataset=dict(stratum), **coverage),
        C2=dict(cell_eos=cell_usable), C3=dict(present=len(c3_present), absent=len(c3_absent)), C4=dict(unbiased_images=len(labels), matched_pairs=atlas['matched_pairs']),
        annotation_scope='Conservative semantic annotations with explicit unknowns. '+prefix_scope,
        gate_scope='Plan section53 construction availability gates use validated conditions. Native EOS is reported separately; it does not redefine available stress assets. Frozen intact eligibility and every terminal generation remain required.',
        recommendation=recommendation, next_stage_executed=False, internal_state_features_used_for_selection=False,
        release_sha256=release['release_events_sha256'])
    folder = OUT / 'summaries'; folder.mkdir(exist_ok=True)
    save('summaries/stage6a_acceptance.json', acceptance)
    save('summaries/stage6a_summary_tables.json', tables)
    lines = ['# Stage 6A cohort summary', '', f"Status: **{acceptance['status']}**. Recommended next stage: **{recommendation}**.", '',
        'All acquisition used BF16 Qwen3-VL-4B-Thinking, the fixed official sampling settings, natural EOS and the 40,960-token cap. Existing allocation 109385 on node03 in tmux session 9 supplied four A6000 GPUs; no additional allocation or dataset download was made.', '',
        f"Retained bases: C1={len(c1_keys)}, C2={len(by_cohort['C2'])}, C3={len(by_cohort['C3'])}, C4={len(by_cohort['C4'])}. Native incompletes remain in raw evidence and condition accounting. C1 completion exclusions follow its frozen eligibility rule.", '',
        f"Physical acquisition saved {resource['native_terminal_records']} terminal records and {resource['physical_repeat_generations']} replay generations, totaling {resource['measured_native_device_hours']:.2f} measured GPU device-hours. Reused mechanics records are counted once; this is not elapsed wall time.", '',
        'C4 prevalence uses all 1,000 fixed images. The separate matched atlas does not estimate prevalence. The frozen conservative COCO80 presence protocol is CHAIR-compatible; it is not unmodified official CHAIR and does not exhaustively score attributes, counts, relations or non-COCO objects.', '',
        'Semantic demand/refresh states and anchors are prospective annotations. They do not establish causal grounding, mirage, wandering or fixation. Controlled exact-source roles and natural category-set roles must remain separate. Correct numeric readouts can coexist with wrong geometric bindings or wrong final answers.', '']
    lines += [f"C1 validated evidence-availability conditions average {coverage['mean_available_conditions']:.2f} per base; {coverage['counterfactual_and_mask_available_pairs']} bases have both counterfactual and full-mask assets. Natural EOS averages {coverage['mean_eos_conditions']:.2f} availability conditions per base, with {coverage['counterfactual_and_mask_eos_pairs']} counterfactual/mask pairs both reaching EOS. Construction coverage and native-completion feasibility are distinct; capped variants remain in the release and limit completed-trajectory analyses.", '']
    lower, upper = prevalence['annotation_protocol_uncertainty_interval']
    lines += [f"C4 confirmed object errors occur in {prevalence['confirmed_positive_fraction']:.1%} of the fixed sample. Including unresolved cases gives a {lower:.1%}–{upper:.1%} identification range under this annotation protocol. This is not a statistical confidence interval or a universal upper bound on hallucination. Whole-trace and final-caption labels are distinct; see c4_natural_failure/unbiased_prevalence.json.", '']
    c3_response_review = read('audit/c3_paired_native_response_review.json')
    response_counts = c3_response_review['counts']
    lines += [f"For the fixed 63 present-object C3 families, reviewed yes responses are intact={response_counts['intact'].get('yes',0)}, strong={response_counts['strong'].get('yes',0)}, mask={response_counts['mask'].get('yes',0)}, sham={response_counts['sham'].get('yes',0)}, and sham_strong={response_counts['sham_strong'].get('yes',0)}. These are paired response frequencies, not estimates of causal grounding or hallucination. See audit/c3_paired_native_response_review.json for review scope and sham-shape limits.", '']
    c3_unrelated = read('audit/c3_unrelated_native_response_review.json')
    c3_no_image = read('audit/c3_no_image_native_response_review.json')
    lines += [f"C3 unrelated-image responses are {c3_unrelated['counts'].get('no',0)} no and {c3_unrelated['counts'].get('yes',0)} yes. Reviewed positive cases include one lamp-to-potted-plant error and two unresolved category boundaries. All {c3_no_image['events']} no-image finals answer no with explicit missing-image acknowledgement. They contain {c3_no_image['unique_prompts']} unique prompts; identical prompts yield identical raw responses and are shared controls. These observations do not establish causal prior collapse. See audit/c3_unrelated_native_response_review.json and audit/c3_no_image_native_response_review.json.", '']
    for t in tables:
        lines += [f"## {t['number']}. {t['title']}", '', '| ' + ' | '.join(t['columns']) + ' |', '| ' + ' | '.join(['---'] * len(t['columns'])) + ' |']
        for row in t['rows']:
            values = [json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v) for v in row]
            lines.append('| ' + ' | '.join(v.replace('|', '\\|').replace('\n', ' ') for v in values) + ' |')
        lines.append('')
    lines += ['## Interpretation and limits', '',
        'C1 uses a subset of source-editable diagrams/tables, with all 114 intact candidates reviewed independently of correctness. The target of 120 was attempted using 155 source candidates. Source editability and long-response completion are selection limits; excluded raw evidence is preserved.', '',
        'C2 pairs the same image and reviewed T/X fields. A source-only revalidation during acquisition supersedes the original crop-pass metadata; whole families with prompt/ROI mismatches are excluded while raw traces are retained. Retrieval-only prompts retain spatial/ordinal cues. Task wording and expected answer lengths are not perfectly matched; this is not a claim of zero semantic alignment.', '',
        'C3 opaque polygon masks remove annotated target pixels but may preserve silhouettes, context and boundary fragments. Masked yes responses are not automatically hallucinations. Translated sham shapes can also be described as additional silhouettes: target pixels are preserved, but the sham is not guaranteed neutral for object counts or shape semantics. No-image and unrelated-image final labels distinguish original source-answer consistency from presented-image truth. An explicit no combined with missing-image acknowledgement is recorded separately from verified absence; repeated no-image question text is a shared control, not independent visual evidence.', '',
        'C3 final scoring uses the fixed POPE/COCO category reference. The reviewed truck/van, cup/glass, chair/stool, mattress/bed, and unrelated-image car/pickup and bowl/bucket disagreements retain unresolved local visual truth: benchmark disagreement alone does not establish an objective perception failure. These source families and their raw responses remain included.', '',
        prefix_scope+' Most remaining long trajectories retain unknown local truth/demand. Reviewed local claims are a limited annotation subset, so their correctness counts are not a representative accuracy estimate. Temporal prior access means an earlier reviewed source-linked utterance; it does not prove causal use.', '',
        'C1 numeric regions have mixed granularity: some are coordinate or expression components, others whole expressions or table values. Numeric table keys identify data cells rather than adding separate value regions. Repeated values retain separate source identities, while ambiguous attribution remains unresolved. Region and source-claim counts therefore are not counts of independent facts. The review does not cover every glyph, geometric property or causal dependency.', '',
        'Atlas matching balances count/length/edge-complexity features and dominant object categories approximately. All eligible confirmed cases are retained, including weak matches; imbalance is recorded in matching_diagnostics.json.', '',
        'All matched C4 controls have original-image and complete native-text reviews under the frozen positive COCO80 presence protocol. Known out-of-scope caption errors include calling a sink a bathtub and reading Crisco as Riso. These controls are not globally error-free; see c4_natural_failure/matched_control_review.json.', '',
        'Source/template folds were assigned prospectively and inherited by every condition. Exact/flagged perceptual matches stay grouped, including C3/C4 shared COCO images. Generic task instructions are shared across folds; no unseen-task-template or exhaustive historical semantic-template claim is made.', '',
        'Resource totals count actual generation and replay work once, including failed mechanics and capped responses. Referenced mechanics reuse adds no compute. Device-hours exclude CPU annotation, loading and dependency waits; they are not elapsed wall time or measured utilization.', '',
        'Evidence: [acceptance](stage6a_acceptance.json), [screening](../cohort/screening_accounting.json), [release integrity](../audit/release_integrity.json), [resources](../audit/resource_summary.json), [atlas matching](../c4_natural_failure/matching_diagnostics.json), [annotation integrity](../audit/controlled_annotation_integrity.json).', '',
        'Stage 6A stops here. No PCA, exact causal trajectory scoring, mirage confirmation, rescue or subsequent stage is executed.']
    (folder / 'stage6a_cohort_summary.md').write_text('\n'.join(lines) + '\n')
    reason = 'A specific controlled size/completion gate failed; repair the named construction/availability limitation before internal-state analysis.' if not controlled_pass else 'Controlled gates pass, but the fixed 1,000-image acquisition did not supply 60 matched natural failure/control pairs. Preserve this yield and the frozen labels; any new natural acquisition requires a separately approved plan.' if not gates['C4_atlas'] else 'Controlled gates and the natural atlas size gate pass. Review semantic transition coverage and its stated limits before designing the separate causal retrieval-dynamics analysis.'
    (folder / 'next_analysis_recommendation.md').write_text(f'# {recommendation}\n\n{reason}\n\nThis recommendation does not execute or authorize another stage. See stage6a_acceptance.json for every measured gate.\n')
    print(json.dumps(acceptance, indent=2))


if __name__ == '__main__':
    main()
