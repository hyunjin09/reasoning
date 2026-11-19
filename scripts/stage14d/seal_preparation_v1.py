"""CPU-only G1/G2 and main-input freeze. Never submits work or reads new outcomes."""
import datetime as dt
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer

from scripts.stage14d.design import fingerprint, render_directive
from scripts.stage14d.prepare_technical_v1 import ROOT, lines, save, sha
from scripts.stage14d.review_qc_v1 import records


def jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as out:
        for row in rows:
            out.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def run():
    at = dt.datetime.now(dt.timezone.utc).isoformat()
    out = ROOT / 'spec/main_condition_manifest_v1.jsonl'
    if out.exists():
        raise FileExistsError('Freeze already exists; preserve it and version any repair')
    files = {}

    def pin(path):
        files[str(path)] = sha(path)
        return files[str(path)]

    def read(path):
        pin(path)
        return json.loads(Path(path).read_text())

    cfg = read(ROOT / 'spec/pinned_model_revisions_and_recipes.json')
    read(ROOT / 'audit/native_second_pass_checkpoint_414_v1.json')
    read(ROOT / 'audit/native_review_adjudication_index_v68.json')
    source_index = read(ROOT / 'audit/source_review_adjudication_index_v1.json')['active_overrides']
    sources = {}
    for p in sorted((ROOT / 'annotation/source_review_v1').glob('*.json')):
        if p.stem in source_index:
            entry = source_index[p.stem]
            p = Path(entry['path'])
            assert sha(p) == entry['sha256']
        s = read(p)
        s['active_review_path'] = str(p)
        s['active_review_sha256'] = sha(p)
        sources[s['item_id']] = s
    cohorts = lines(ROOT / 'cohorts/thinking_strata_300.jsonl')
    overlap = lines(ROOT / 'cohorts/instruct_overlap_120.jsonl')
    assert len(sources) == 300 and set(sources) == {r['item_id'] for r in cohorts}
    assert len({r['family_id'] for r in cohorts}) == 300
    source_rows, exclusions = [], []
    for row in cohorts:
        s = sources[row['item_id']]
        assert row['family_id'] == s['family_id']
        original = s['original_source']
        assert original['source_image'] == row['original_image']
        assert original['source_image_sha256'] == row['original_image_sha256']
        assert pin(original['source_image']) == original['source_image_sha256']
        assert pin(original['source_receipt']) == s['source_receipt_sha256']
        if s['status'] == 'SOURCE_VALID_VALUE_FREE':
            assert render_directive('LOOK_TARGET', s['model_visible_target']) == s['target_directive']
            x0, y0, x1, y1 = s['ROI_pixels']
            w, h = s['source_image_dimensions']
            assert 0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h
        else:
            exclusions.append(dict(item_id=s['item_id'], family_id=s['family_id'],
                                   scope='all models and arms', status=s['status'], reason=s['reason']))
        source_rows.append(s)

    active = {}
    anchors, events, states, changes = [], [], [], []
    for path, r in records():
        pin(path)
        tid = r['task_id']
        s = sources[r['item_id']]
        assert r['source_review'] == s['active_review_path']
        assert r['source_review_sha256'] == s['active_review_sha256']
        qcpath = ROOT / 'annotation/native_qc_v1' / f'{tid}.json'
        qc = read(qcpath)
        assert qc['reviewed_record_sha256'] == sha(path)
        assert qc['source_neutral_prefix_qc'] == qc['event_timing_qc'] == qc['target_label_qc'] == 'PASS'
        assert r['entire_native_trace_manually_reviewed'] and not qc['scientific_intervention_outcomes_seen']
        native = read(r['original_receipts']['generation'])
        assert sha(r['original_receipts']['generation']) == r['original_receipts']['generation_sha256']
        n = r['anchor_token_index']
        assert native['generated_token_ids'][:n] == r['prefix_generated_token_ids']
        assert native['raw_decoded_response'][:r['anchor_char_index']] == r['prefix_text']
        assert fingerprint(r['prefix_generated_token_ids']) == r['prefix_ids_sha256']
        for event in r['events'].values():
            if event is not None:
                assert native['raw_decoded_response'][event['char_start']:event['char_end']] == event['quote']
        if r['events']['earliest']:
            assert r['anchor_char_index'] <= r['events']['earliest']['char_start']
        else:
            assert n == 0 and r['fallback']
        for name in ('input', 'result'):
            assert pin(r['original_receipts'][name]) == r['original_receipts'][f'{name}_sha256']
        ref = dict(task_id=tid, item_id=r['item_id'], family_id=r['family_id'], model=r['model'],
                   native_review=str(path), native_review_sha256=sha(path),
                   second_pass_QC=str(qcpath), second_pass_QC_sha256=sha(qcpath))
        anchors.append(dict(ref, **{k: r[k] for k in ['anchor_token_index', 'anchor_char_index',
            'prefix_text', 'prefix_generated_token_ids', 'prefix_text_sha256', 'prefix_ids_sha256',
            'fallback', 'fallback_reason', 'source_neutral_prefix_review']},
            original_receipts=r['original_receipts']))
        events.append(dict(ref, events=r['events'], repeats_or_contradictions=r['observed_repeats_or_contradictions'], note=r['note']))
        states.append(dict(ref, evidence_state=r['evidence_state'], source_review=r['source_review'],
                           source_review_sha256=r['source_review_sha256'], native_context_only=True))
        original = json.loads((ROOT / 'annotation/native_review_v1' / f'{tid}.json').read_text())
        if path != ROOT / 'annotation/native_review_v1' / f'{tid}.json':
            changes.append(dict(task_id=tid, fields_changed=[k for k in ['evidence_state','E0','E1','E2','earliest','boundary','fallback'] if original[k] != r[k]],
                                original_state=original['evidence_state'], final_state=r['evidence_state'], active_review=str(path)))
        active[tid] = (path, r, native)
    assert len(active) == 414

    tokenizers = {m: Tokenizer.from_file(str(Path(cfg['models'][m]['model']['checkpoint'])/'tokenizer.json')) for m in 'IT'}
    slots = lines(ROOT / 'spec/main_condition_slots_proposed_v1.jsonl')
    manifest = []
    for slot in slots:
        item, model, arm = slot['item_id'], slot['model'], slot['arm']
        s = sources[item]
        r = dict(slot)
        r.update(state='READY_REQUIRES_MAIN_RELEASE', scientific=True, image_access='ON',
                 source_review=s['active_review_path'], source_review_sha256=s['active_review_sha256'])
        r.pop('prefix_identity', None)
        r.pop('source_request', None)
        if s['status'] != 'SOURCE_VALID_VALUE_FREE':
            r.update(state=s['status'], executable=False, reason=s['reason'])
        elif arm == 'LOOK_IRRELEVANT' and s['irrelevant_status'] != 'SOURCE_VALID_VALUE_FREE':
            r.update(state='IRRELEVANT_CONTROL_INAPPLICABLE', executable=False, reason=s['irrelevant_reason'])
        else:
            path, nr, native = active[f'mv_{item}_image_{model}_r0']
            inp = read(nr['original_receipts']['input'])
            assert inp['task']['prompt'] == s['original_source']['native_question']
            target = s['irrelevant_model_visible_target'] if arm == 'LOOK_IRRELEVANT' else s['model_visible_target']
            directive = render_directive(arm, target)
            directive_ids = tokenizers[model].encode(directive, add_special_tokens=False).ids
            cap = cfg['models'][model]['cap']
            prompt_tokens = len(native['prompt_token_ids']) + nr['anchor_token_index'] + len(directive_ids)
            r.update(executable=prompt_tokens+cap<=128000,
                     native_review=str(path), native_review_sha256=sha(path),
                     parent_input=nr['original_receipts']['input'], parent_input_sha256=nr['original_receipts']['input_sha256'],
                     parent_generation=nr['original_receipts']['generation'], parent_generation_sha256=nr['original_receipts']['generation_sha256'],
                     image=s['original_source']['source_image'], image_sha256=s['original_source']['source_image_sha256'],
                     prefix_ids_sha256=nr['prefix_ids_sha256'], prefix_text_sha256=nr['prefix_text_sha256'],
                     prefix_tokens=nr['anchor_token_index'], directive=directive, directive_ids=directive_ids,
                     directive_tokens=len(directive_ids), processed_prompt_tokens=prompt_tokens,
                     max_tokens=cap, recipe=cfg['models'][model]['recipe'],
                     model_revision=cfg['models'][model]['model']['revision'],
                     full_historical_native_tokens=native['tokens'],
                     remaining_native_tokens_proxy=max(0,native['tokens']-nr['anchor_token_index']),
                     model_payload_rule='Only original chat/image, saved prefix IDs and directive IDs; no stratum/gold/reference metadata.')
            if not r['executable']:
                r.update(state='CONTEXT_BUDGET_INAPPLICABLE', reason='Unchanged prefix plus inherited cap exceeds128000; no truncation or cap change.')
        manifest.append(r)
    assert len(manifest) == 2100 and len({r['task_id'] for r in manifest}) == 2100
    runnable = [r for r in manifest if r['executable']]
    for r in manifest:
        if not r['executable']:
            exclusions.append({k:r[k] for k in ['task_id','family_id','item_id','model','arm','state','reason']})
    for r in runnable:
        assert r['seed'] == int(hashlib.sha256(('stage14d-g0-v1-20261011|generation|'+r['family_id']).encode()).hexdigest(),16)%(2**31)
        assert (r['arm'] == 'B0') == (r['directive_ids'] == [])

    # No preexisting matched image-edit inventory is certified in the approved
    # source protocol or Stage14A/B files. No new image edits are manufactured.
    mechanism = []
    for row in lines(ROOT / 'cohorts/mechanism_source_review_order_v1.jsonl'):
        s = sources[row['item_id']]
        mechanism.append(dict(row, included=False, source_validity=s['status'],
            source_review=s['active_review_path'], source_review_sha256=s['active_review_sha256'],
            state='NOT_EXECUTED_INVALID_CF',
            reason='No preexisting certified single-target same-layout semantic edit and matched local readout in approved reused source inventory.',
            new_image_edit_created=False, model_outcomes_used=False))
    assert len(mechanism) == 300

    calibration = read(ROOT / 'audit/technical_resource_reestimate_v1.json')
    cost = {}
    for model in 'IT':
        mr = [r for r in runnable if r['model']==model]
        rate = calibration['per_model'][model]['observed_serial_tokens_per_second']
        total = sum(r['full_historical_native_tokens'] for r in mr)
        cost[model] = dict(calls=len(mr), observed_512_token_serial_tokens_per_second=rate,
            full_native_length_proxy_tokens=total, full_native_length_linear_GPUh=total/rate/3600,
            remaining_native_length_proxy_tokens=sum(r['remaining_native_tokens_proxy'] for r in mr),
            all_calls_at_cap_tokens=sum(r['max_tokens'] for r in mr),
            all_calls_at_cap_linear_GPUh=sum(r['max_tokens'] for r in mr)/rate/3600,
            maximum_processed_prompt_tokens=max(r['processed_prompt_tokens'] for r in mr))
    point = sum(x['full_native_length_linear_GPUh'] for x in cost.values())
    stress = 2*point+6+calibration['measured_technical_allocated_GPUh']
    proposed = math.ceil(stress/25)*25
    estimate = dict(at=at,per_model=cost,executable_main_calls=len(runnable),nested_continuations=0,
        short_readouts=0,total_scientific_call_ceiling=len(runnable),technical_calls_completed=24,
        total_physical_continuation_ceiling=len(runnable)+24,
        spent_allocated_GPUh=calibration['measured_technical_allocated_GPUh'],
        linear_main_GPUh_proxy=point,double_output_length_plus6h_and_spent_GPUh=stress,
        proposed_total_stage_GPUh_hard_ceiling=proposed,approved_main_GPUh_ceiling=None,
        max_concurrency_proposed=8,linear_compute_wall_hours_at8=point/8,
        limitations=['512-token throughput cannot bound81920-token long tails or large prefills.',
                    'One active request perGPU; no18-way throughput assumption.',
                    'Full native length per arm is a planning proxy; prefixes are not subtracted in headline estimate.',
                    'Budget is allocated GPU time, including startup/idle/failure; no guarantee entire panel fits.',
                    'If remaining budget cannot reserve safe completion, hold before next request; no outcome-dependent dropping.'])

    outputs = {
        'cohorts/target_source_annotations.jsonl':source_rows,
        'cohorts/exclusion_and_inapplicability_log.jsonl':exclusions,
        'cohorts/mechanism_source_screen_v1.jsonl':mechanism,
        'cohorts/mechanism_source_valid_48.jsonl':[],
        'anchors/evidence_events_E0_E1_E2.jsonl':events,
        'anchors/prefix_identity_and_timing.jsonl':anchors,
        'anchors/source_ROI_identity.jsonl':[{k:s.get(k) for k in ['item_id','family_id','status','ROI_pixels','normalized_ROI','source_image_dimensions','active_review_path','active_review_sha256']} for s in source_rows],
        'annotation/native_evidence_state_reviews_sealed_v1.jsonl':states,
        'annotation/source_fidelity_QC.jsonl':[dict(item_id=s['item_id'],family_id=s['family_id'],
            status=s['status'],source_review=s['active_review_path'],source_review_sha256=s['active_review_sha256'],
            scope='target-local original-image/source review; references rechecked in applicable native QC',
            independent_interrater=False,whole_E_star_certification=False) for s in source_rows],
        'spec/main_condition_manifest_v1.jsonl':manifest,
    }
    for rel, rs in outputs.items():
        jsonl(ROOT/rel,rs);pin(ROOT/rel)
    save(ROOT/'audit/main_resource_estimate_v2.json',estimate);pin(ROOT/'audit/main_resource_estimate_v2.json')
    counts = dict(at=at,source_families=300,source_status=dict(Counter(s['status'] for s in source_rows)),
        irrelevant_source_status=dict(Counter(s['irrelevant_status'] for s in source_rows)),
        native_slots=420,applicable_full_trace_and_whole_prefix_QC=414,source_inapplicable_native_slots=6,
        same_agent_two_passes=True,independent_interrater_reliability=False,
        active_adjudication_index='outputs/stage14d/audit/native_review_adjudication_index_v68.json',
        all_versioned_changes=changes,native_evidence_states_by_model={m:dict(Counter(r['evidence_state'] for r in states if r['model']==m)) for m in 'IT'},
        fallback_by_model={m:sum(r['fallback'] for r in anchors if r['model']==m) for m in 'IT'},
        anchor_tokens_quantiles={m:np.quantile([r['anchor_token_index'] for r in anchors if r['model']==m],[0,.25,.5,.75,1]).tolist() for m in 'IT'},
        main_slots=2100,executable_main_calls=len(runnable),slot_status=dict(Counter(r['state'] for r in manifest)),
        executable_by_model_arm={m:dict(Counter(r['arm'] for r in runnable if r['model']==m)) for m in 'IT'},
        executable_by_model_stratum={m:dict(Counter(r['stratum'] for r in runnable if r['model']==m)) for m in 'IT'},
        valid_semantic_counterfactual_families=0,nested_calls=0,short_readouts=0,
        new_scientific_generations=0,main_release=False)
    save(ROOT/'audit/source_anchor_inventory_sealed_v1.json',counts);pin(ROOT/'audit/source_anchor_inventory_sealed_v1.json')
    for p in ['spec/statistical_analysis_spec.md','spec/scoring_and_evidence_annotation_protocol.md',
              'spec/source_target_and_anchor_protocol.md','spec/condition_templates_frozen.json',
              'cohorts/thinking_strata_300.jsonl','cohorts/instruct_overlap_120.jsonl',
              'spec/main_condition_slots_proposed_v1.jsonl','audit/technical_preflight_validation_v1.json',
              'audit/technical_execution_seal_v2.json']:
        pin(ROOT/p)
    for p in ['scripts/stage14d/design.py','scripts/stage14d/primary_analysis_v1.py',
              'scripts/stage14d/seal_preparation_v1.py','scripts/stage14d/token_offsets_v1.py']:
        pin(p)
    save(ROOT/'audit/source_anchor_preparation_seal_v1.json',dict(at=at,files=files,
        G1='COMPLETE_WITH_EXPLICIT_INAPPLICABILITY',G2='414_APPLICABLE_COMPLETE',
        G3='24_TECHNICAL_CALLS_PASS',G4='MAIN_RELEASE_PENDING',
        all_main_outcomes_unseen=True,new_scientific_calls=0))
    print(json.dumps({k:v for k,v in counts.items() if k!='all_versioned_changes'},indent=2))
    print(json.dumps(estimate,indent=2))


if __name__ == '__main__':
    run()
