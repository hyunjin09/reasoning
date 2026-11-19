"""Reconcile the released primary events with immutable construction evidence.

Run only after primary export. Reports distinguish mechanical integrity from
semantic yield; they do not classify causal states or change cohort membership.
"""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image

from scripts.stage6a.inventory import OUT, ROOT, allowed
from scripts.stage6a.prepare_candidates import write


def load(name):
    return [json.loads(line) for line in (OUT / name).read_text().splitlines()]


def report(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')


def main():
    release = json.loads((OUT / 'cohort/primary_release_manifest.json').read_text())
    events = load('cohort/primary_release_events.jsonl')
    by_event = {r['event_id']: r for r in events}
    assert len(events) == len(by_event) == release['events']
    assert hashlib.sha256((OUT / 'cohort/primary_release_events.jsonl').read_bytes()).hexdigest() == release['release_events_sha256']
    bases = {r['base_id']: r for r in events}
    controlled = {k: r for k, r in by_event.items() if r['cohort'] != 'C4'}
    native_rows = load('traces/controlled_native_index.jsonl') + load('c4_natural_failure/generations.jsonl')
    native = {r['event_id']: r for r in native_rows if r['event_id'] in by_event}
    assert set(native) == set(by_event)
    checks = {r['event_id']: r for r in load('audit/controlled_native_checks.jsonl')}
    assert all(checks[eid]['status'] == 'PASS' for eid in controlled)
    errors = []

    # Native metadata proves which image, prompt and no-image route were used.
    inputs = {}
    for eid, row in by_event.items():
        result = native[eid]
        directory = Path(result['input_metadata_artifact']).parent if 'input_metadata_artifact' in result else ROOT / result['artifact_dir']
        data = json.loads((directory / 'input.json').read_text())
        inputs[eid] = data
        if data['prompt'] != row['prompt'] or data['condition'] != row['condition'] or data['image_path'] != row.get('image_path'):
            errors.append([eid, 'native input differs from release stimulus'])
        if result['membership_used_attention'] is not False or result['membership_used_causal_scores'] is not False:
            errors.append([eid, 'selection blindness flag'])
        if row['cohort'] == 'C4':
            generation = json.loads((directory / 'generation.json').read_text())
            tokens = [json.loads(line) for line in (directory / 'tokens.jsonl').read_text().splitlines()]
            if generation['generated_token_ids'] != [t['token_id'] for t in tokens] or generation['raw_decoded_response'] != ''.join(t['decoded_token'] for t in tokens):
                errors.append([eid, 'natural native token identity'])
            image = Image.open(allowed(Path(data['image_path']))).convert('RGB')
            if hashlib.sha256(image.tobytes()).hexdigest() != data['decoded_image_sha256']:
                errors.append([eid, 'natural native image hash'])
            _, height, width = data['visual_mapping']['merged_grid_shape']
            if len(set(data['visual_token_indices'])) != height * width or len(data['visual_token_indices']) != height * width:
                errors.append([eid, 'natural visual grid'])
    prospective_assignments = json.loads((OUT / 'cohort/prospective_source_split.json').read_text())['assignments']
    no_image = []
    unrelated = []
    for eid, row in controlled.items():
        data = inputs[eid]
        if row['condition'] == 'no_image':
            valid = data['no_image'] and data['image_path'] is None and data['image_grid_thw'] is None and data['visual_token_indices'] == []
            no_image.append(dict(event_id=eid, status='PASS' if valid else 'FAIL',
                complete=native[eid]['complete'], visual_tokens=0 if valid else len(data['visual_token_indices']),
                final_truth_scope='Source-answer consistency and abstention; source image is not presented.'))
            if not valid: errors.append([eid, 'no-image route'])
        elif row['condition'] == 'unrelated':
            intact = inputs[row['base_id'] + '__intact']
            donor = row['unrelated_donor']
            valid = (data['decoded_image_sha256'] != intact['decoded_image_sha256']
                and data['image_grid_thw'] == intact['image_grid_thw']
                and prospective_assignments[donor]['split'] == row['split']
                and 'fresh prepare' in data['image_state_policy'])
            unrelated.append(dict(event_id=eid, donor=donor, status='PASS' if valid else 'FAIL',
                distinct_image_matched_grid_same_fold=valid, source_answer=row['source_answer'],
                presented_condition_answer=row['answer'], original_roi_is_coordinate_placebo=True,
                semantic_truth_scope='Reviewed donor category absence' if row['cohort'] == 'C3' else 'Original mathematical truth not promoted to unrelated-image truth'))
            if not valid: errors.append([eid, 'unrelated control'])
    report('audit/no_image_audit.json', dict(status='PASS' if all(r['status'] == 'PASS' for r in no_image) else 'FAIL',
        events=len(no_image), records=no_image, cache_scope='Fresh text-only preparation; no visual prompt positions or donor cache supplied.'))
    report('audit/unrelated_image_audit.json', dict(status='PASS' if all(r['status'] == 'PASS' for r in unrelated) else 'FAIL',
        events=len(unrelated), records=unrelated, semantic_evidence='audit/c3_unrelated_semantic_review.jsonl; audit/c3_unrelated_v2_preflight.jsonl'))

    # Initial pixel audit covers every construction condition. Revised C3 donor
    # pixels have their own explicit second-version audit before inference.
    pixels = {r['event_id']: r for r in load('audit/primary_saved_pixel_checks.jsonl')}
    donors = {r['event_id']: r for r in load('audit/c3_unrelated_v2_preflight.jsonl')}
    assert set(controlled) <= set(pixels)
    assert all(donors[eid]['status'] == 'PASS' for eid, r in controlled.items() if r['cohort'] == 'C3' and r['condition'] == 'unrelated')
    manipulation = []
    for eid, row in controlled.items():
        check = pixels[eid]
        if 'changed_pixels' in check:
            valid = check['changed_pixels'] > 0 and check['outside_mask_exact'] and check['matched_target_sham_area'] and check['sham_disjoint']
            if 'opaque_mask_gray_127' in check: valid = valid and check['opaque_mask_gray_127']
            manipulation.append(dict(**check, cohort=row['cohort'], status='PASS' if valid else 'FAIL'))
            if not valid: errors.append([eid, 'saved-pixel manipulation'])
    report('audit/manipulation_audit.json', dict(status='PASS' if all(r['status'] == 'PASS' for r in manipulation) else 'FAIL',
        events=len(manipulation), records=manipulation,
        semantic_review=['config/primary_c1_authored_semantics.json', 'config/primary_c2_authored_semantics.json',
            'audit/c3_present_source_mask_review.jsonl', 'audit/c3_absent_source_review.jsonl'],
        limitations=['Old construction crop packets retain pending-review metadata; the authored semantic records are authoritative.',
            'Opaque annotated pixels preserve possible silhouette/context/category cues; zero causal information is not established.']))

    roi_maps = [r for r in load('regions/controlled_roi_maps.jsonl') if r['event_id'] in controlled]
    regions = [r for r in load('regions/ground_truth_rois.jsonl') if r['base_id'] in bases]
    present = [r for r in bases.values() if r['cohort'] == 'C3' and r['present']]
    absent = [r for r in bases.values() if r['cohort'] == 'C3' and not r['present']]
    no_image_ids = {r['event_id'] for r in no_image}
    assert not any(r['event_id'] in no_image_ids for r in roi_maps)
    absent_ids = {r['base_id'] for r in absent}
    assert not any(r['base_id'] in absent_ids and r.get('source_id') == 'T' for r in regions)
    report('audit/roi_audit.json', dict(status='PASS', primary_source_regions=len(regions), native_controlled_maps=len(roi_maps),
        geometry_counts=dict(Counter((r['cohort'] + ':' + r['geometry_type']) for r in regions)),
        present_object_families=len(present), absent_object_families=len(absent), absent_targets_have_no_fabricated_roi=True,
        native_mapping='Each controlled map independently checked against original-pixel enumeration by collect_controlled_traces.',
        provenance='regions/region_provenance.json',
        scope='Source catalog includes excluded construction candidates; these counts join retained primary base IDs.'))

    assignments = json.loads((OUT / 'cohort/discovery_confirmation_split.json').read_text())['assignments']
    original = json.loads((OUT / 'cohort/prospective_source_split.json').read_text())
    extension = json.loads((OUT / 'cohort/c4_extension_preparation/split_preparation.json').read_text())
    assert hashlib.sha256((OUT / 'cohort/prospective_source_split.json').read_bytes()).hexdigest() == extension['original_split_sha256']
    prospective = {**original['assignments'], **extension['assignments']}
    assert all(assignments[key] == prospective[key] for key in assignments)
    identities = {r['base_id']: r for r in load('audit/source_identity_catalog.jsonl') + load('cohort/c4_extension_preparation/source_identity_catalog.jsonl')}
    links = load('audit/perceptual_duplicate_candidates.jsonl') + load('cohort/c4_extension_preparation/duplicate_candidates.jsonl')
    split_errors = []
    buckets = defaultdict(list)
    for key, row in bases.items():
        assert key in identities
        if row['split'] not in ['discovery', 'confirmation']: continue
        buckets['group:' + row['group_id']].append(key)
        buckets['pixels:' + identities[key]['decoded_stimulus_sha256']].append(key)
    for bucket, keys in buckets.items():
        if len({bases[key]['split'] for key in keys}) > 1: split_errors.append([bucket, keys])
    for pair in links:
        left, right = pair['left'], pair['right']
        retained = [key for key in [left, right] if key in bases and bases[key]['split'] in ['discovery', 'confirmation']]
        if len(retained) == 2 and bases[left]['split'] != bases[right]['split']:
            split_errors.append(['flagged near-image pair crosses folds', pair])
        if retained and any(identities.get(key, {}).get('phase') in ['historical', 'mechanics', 'pilot'] for key in [left, right]):
            split_errors.append(['historical/validation near-image overlap', pair])
    metadata = [r for r in load('cohort/source_template_groups.jsonl') if r['base_id'] in bases]
    family_folds = defaultdict(set)
    for row in metadata:
        if row['split'] in ['discovery', 'confirmation']: family_folds[row['template_geometry_family']].add(row['split'])
    for family, folds in family_folds.items():
        if len(folds) > 1: split_errors.append(['template crosses folds', family])
    duplicate = dict(status='PASS' if not split_errors else 'FAIL', errors=split_errors,
        reviewed_identity_records=len(identities), flagged_perceptual_pairs=len(links),
        primary_exact_pixel_groups=sum(len(v) > 1 for k, v in buckets.items() if k.startswith('pixels:')),
        declared_template_families=len(family_folds), known_limits=original['known_limits'],
        control_donors='Within the recipient fold; condition variants stay with their base.',
        no_unseen_task_template_claim=True)
    report('audit/stimulus_duplicate_audit.json', duplicate)
    report('audit/split_integrity.json', dict(**duplicate, original_assignments_unchanged=True,
        per_cohort_split_bases=dict(Counter(r['cohort'] + ':' + r['split'] for r in bases.values()))))
    errors.extend(split_errors)

    c1_reviews = load('c1_diagram_stress/intact_local_claim_review.jsonl')
    assert all(r['membership_selected_by_correctness'] is False and r['attention_or_causal_data_used'] is False for r in c1_reviews)
    report('audit/cohort_selection_blindness.json', dict(status='PASS', primary_native_events=len(native),
        attention_and_causal_selection_flags_all_false=True, c1_terminal_reviews=len(c1_reviews),
        construction_rules='Frozen semantic/editability/source-order criteria; correctness-independent C1 completion/readout eligibility.',
        allowed_outcome_use=['C1 intact completion and local readout interpretability', 'Prespecified C4 600-to-1000 low-yield branch',
            'Object-error labels for the separate outcome-balanced natural atlas'],
        observations_not_used=['attention', 'hidden-state/PCA features', 'causal effects', 'rescue outcomes'],
        evidence=['cohort/c1_membership_freeze.json', 'cohort/c4_extension_activation.json',
            'cohort/prospective_source_split.json', 'c4_natural_failure/matching_diagnostics.json']))
    mechanics = json.loads((OUT / 'audit/mechanics_v2_validation.json').read_text())
    assert mechanics['status'] == 'PASS' and all(mechanics['checks'].values())
    report('audit/mechanical_validation.json', dict(**{**mechanics, 'status': 'FAIL' if errors else 'PASS'}, authoritative_version='mechanics_v2',
        superseded_failure='audit/mechanical_validation_v1_failed.json', primary_audit_errors=errors,
        primary_native_complete=sum(r['complete'] for r in native.values()), primary_terminal_records=len(native)))
    report('audit/deterministic_replay.json', dict(status='PASS', accepted_mechanics_baselines=mechanics['native_replays'],
        exact_token_ids_and_raw_text=True, physical_replay_accounting='audit/resource_summary.json',
        evidence=['audit/mechanics_v2_validation.json', 'cohort/mechanics_v2_reused_results.jsonl'],
        scope='Same cached native generation shape/configuration. No BF16 equality claim across different replay shapes.'))
    report('audit/release_integrity.json', dict(status='PASS' if not errors else 'FAIL', errors=errors,
        events=len(events), bases=len(bases), release_sha256=release['release_events_sha256'],
        cohort_yield_acceptance='Separate report; integrity does not imply every scientific size gate passed.'))
    assert not errors, errors
    print(json.dumps(dict(status='PASS', events=len(events), bases=len(bases)), indent=2))


if __name__ == '__main__':
    main()
