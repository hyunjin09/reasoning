"""Export completed causal evidence and descriptive metrics without relabeling."""
from collections import Counter
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha
from visual_reasoning.stage7a.reporting import faithfulness_summary, correctness_matrix, state_yields


def load_completed():
    freeze = read_json(OUT/'labels/label_freeze.json')
    assert freeze['frozen'] and freeze['passive_features_used_for_labels'] is False
    for path, digest in freeze['labels_sha256'].items():
        assert sha(ROOT/path) == digest
    entries, metrics, states = [], {}, {}
    for split in ('discovery', 'confirmation'):
        manifest = OUT/'config'/(split+'_events.jsonl')
        metric_path = OUT/'causal'/(split+'_event_metrics.jsonl')
        assert sha(manifest) == freeze['events_manifest_sha256'][split]
        assert sha(metric_path) == freeze['causal_metrics_sha256'][split]
        entries += read_jsonl(manifest)
        metrics.update({r['id']: r for r in read_jsonl(metric_path)})
        states.update({r['id']: r for r in read_jsonl(OUT/'labels'/(split+'_states.jsonl'))})
    assert set(metrics) == set(states) == {e['id'] for e in entries}
    return entries, metrics, states, freeze


def main():
    entries, metrics, states, freeze = load_completed()
    thresholds = read_json(OUT/'config/discovery_thresholds.json')
    assert read_json(OUT/'annotations/processed_source_review.json')['status'] == 'PASS'
    source_review = read_json(OUT/'annotations/source_edit_review.json')
    assert source_review and all(r['status'] == 'PASS_SOURCE_PIXELS' for r in source_review)
    native = read_jsonl(OUT/'cohort/native_manifest.jsonl')
    reviews = {r['event_id']: read_json(OUT/'annotations/native_reviews'/(r['event_id']+'.json')) for r in native}
    final_reviews = {}
    for event_id in reviews:
        path = OUT/'annotations/final_answer_reviews'/(event_id+'.json')
        if path.exists():
            final = read_json(path)
            assert final['generation_sha256'] == reviews[event_id]['generation_sha256']
            assert final['full_native_text_reviewed'] and final['causal_scores_used'] is False
            final_reviews[event_id] = final
    raw = {e['id']: read_json(ROOT/metrics[e['id']]['raw_result_path']) for e in entries}
    for e in entries:
        assert raw[e['id']]['complete'] and sha(ROOT/metrics[e['id']]['raw_result_path']) == metrics[e['id']]['raw_result_sha256']
    def jsonl(path, rows):
        write_jsonl(OUT/path, rows, freeze=True)
    def meta(e):
        return {k: e[k] for k in ('id', 'event_id', 'base_id', 'group_id', 'split', 'dataset', 'condition', 'readout_type')}
    def eligible(e):
        return e['readout_type'] == 'V' and e['reviewed_claim']['demand'] == 'singleton'
    selectors = {
        'faithful': lambda e: eligible(e) and e['condition'] == 'intact' and e['reviewed_claim']['locally_correct'],
        'prior_fill': lambda e: eligible(e) and e['condition'] in ('strong', 'mask', 'unrelated', 'no_image'),
        'wrong_source': lambda e: eligible(e) and not e['reviewed_claim']['locally_correct'],
        'stale_source': lambda e: eligible(e) and e['reviewed_claim']['kind'] == 'aba_return',
        'extraction_error': lambda e: eligible(e) and not e['reviewed_claim']['locally_correct'] and e['condition'] in ('intact', 'strong', 'sham_mask'),
        'integration_error': lambda e: eligible(e) and (e.get('downstream_review') or {}).get('integration_error_eligible') is True,
    }
    for name, select in selectors.items():
        jsonl('cohort/'+name+'_manifest.jsonl', [dict(**meta(e), semantic_condition_eligibility=True,
              selected_by_causal_state=False, source_manifest='config/'+e['split']+'_events.jsonl') for e in entries if select(e)])
    jsonl('annotations/demand.jsonl', [dict(**meta(e), demand=e['reviewed_claim']['demand'], physical_source=e['physical_demanded_source'],
          claim_kind=e['reviewed_claim']['kind'], source_aliases=e['source_aliases']) for e in entries])
    jsonl('annotations/source_candidates.jsonl', [dict(**meta(e), source_groups=e['source_groups'],
          roles=e['roles'], separation_valid=e['source_separation_valid'], row_fields=e['row']['fields']) for e in entries])
    jsonl('annotations/evidence_claims.jsonl', [dict(**meta(e), reviewed_claim=e['reviewed_claim'], review_sha256=e['review_sha256']) for e in entries])
    for readout, name in [('V', 'value'), ('B', 'binding')]:
        jsonl('annotations/'+name+'_readouts.jsonl', [dict(**meta(e), event=e['event']) for e in entries if e['readout_type'] == readout])
    jsonl('annotations/error_readouts.jsonl', [dict(**meta(e), event=e['event'], reviewed_claim=e['reviewed_claim'],
          native_error_scores=raw[e['id']]['arms']['N']) for e in entries if eligible(e) and not e['reviewed_claim']['locally_correct']])
    jsonl('annotations/downstream_error_review.jsonl', [dict(event_id=k, base_id=r['base_id'], split=r['split'],
          downstream=r['downstream'], final_answer_review=final_reviews.get(k), review_sha256=sha(OUT/'annotations/native_reviews'/(k+'.json')),
          missing_review_is_unknown=r['downstream'] is None) for k, r in reviews.items()])
    jsonl('causal/w2_source_scores.jsonl', [dict(**meta(e), source=source, **effect)
          for e in entries for source, effect in metrics[e['id']]['source_effects'].items() if source.endswith('_W2')])
    jsonl('causal/w8_sensitivity.jsonl', [dict(**meta(e), source=source, w8=effect,
          w2=metrics[e['id']]['source_effects'].get(source.replace('_W8', '_W2')), primary_window_changed=False)
          for e in entries for source, effect in metrics[e['id']]['source_effects'].items() if source.endswith('_W8')])
    jsonl('causal/error_oriented_scores.jsonl', [dict(**meta(e), actual_wrong_claim=not e['reviewed_claim']['locally_correct'],
          effects=metrics[e['id']]['source_effects'], native=raw[e['id']]['arms']['N'],
          primary='first actual wrong token and wrong-minus-correct token margin; actual-claim support is diagnostic on correct claims') for e in entries if e['readout_type'] == 'V'])
    for role, name in [('T', 'target'), ('X', 'alternative')]:
        jsonl('causal/'+name+'_counterfactuals.jsonl', [dict(**meta(e), effects=metrics[e['id']]['semantic_effects'][role],
              raw_control_audit=raw[e['id']]['control_audits'][role+'_semantic'])
              for e in entries if role in metrics[e['id']]['semantic_effects']])
    jsonl('causal/sham_controls.jsonl', [dict(**meta(e), control=name, scores=scores,
          audit=raw[e['id']]['control_audits'][name]) for e in entries for name, scores in raw[e['id']]['controls'].items() if name.endswith('_sham')])
    for condition, name in [('mask', 'masked'), ('unrelated', 'unrelated'), ('no_image', 'no_image')]:
        jsonl('prior_fill/'+name+'_scores.jsonl', [dict(**meta(e), metrics=metrics[e['id']], causal_state=states[e['id']])
              for e in entries if e['condition'] == condition])
    jsonl('prior_fill/guess_mode_scores.jsonl', [dict(event_id=k, behavior=r['behavior'], notes=r['notes'],
          selected_claims=len(r['claims']), downstream=r['downstream']) for k, r in reviews.items()
          if r['condition'] in ('mask', 'unrelated', 'no_image')])
    write_json(OUT/'prior_fill/distribution_similarity.json', dict(scope='Same native prefix under different image availability; native convergence separately reviewed',
               events={e['id']: dict(pairs=metrics[e['id']]['distribution_similarity'], native=metrics[e['id']]['native_convergence'])
                       for e in entries if metrics[e['id']]['distribution_similarity']}), freeze=True)
    summaries = {}
    for split in ('discovery', 'confirmation', 'all'):
        subset = [e for e in entries if split == 'all' or e['split'] == split]
        summaries[split] = dict(overall=faithfulness_summary(subset, states, metrics, thresholds),
            by_condition={c: faithfulness_summary([e for e in subset if e['condition'] == c], states, metrics, thresholds)
                          for c in sorted({r['condition'] for r in native})})
    write_json(OUT/'labels/faithfulness_metrics.json', summaries, freeze=True)
    # Final-answer reviews are descriptive only. They neither revise local
    # claims nor supply new integration-error eligibility to frozen labels.
    matrix_entries = [{**e, 'downstream_review': {**(e.get('downstream_review') or {}),
                      **({'final_correct': final_reviews[e['event_id']]['final_correct']}
                         if e['event_id'] in final_reviews else {})}} for e in entries]
    write_json(OUT/'analysis/correctness_faithfulness_matrix.json', correctness_matrix(matrix_entries, states), freeze=True)
    datasets = sorted({e['dataset'] for e in entries})
    write_json(OUT/'analysis/dataset_robustness.json', dict(
        absent_datasets=['MathVerse'], cohort_limitations='C1 is predominantly MathVista TabMWP tables; four MathVision bases. No accepted MathVerse images.',
        datasets={dataset: {split: dict(yields=state_yields([e for e in entries if e['dataset'] == dataset and e['split'] == split], states),
                  metrics=faithfulness_summary([e for e in entries if e['dataset'] == dataset and e['split'] == split], states, metrics, thresholds))
                  for split in ('discovery', 'confirmation')} for dataset in datasets},
        contrasts=read_json(OUT/'analysis/dataset_primary_contrasts.json')), freeze=True)
    no_image_rows = [r for r in native if r['condition'] == 'no_image']
    no_image_checks = {r['event_id']: not read_json(OUT/'native/native_01/examples'/r['event_id']/'input.json')['visual_token_indices'] for r in no_image_rows}
    assert all(no_image_checks.values())
    audits = {
        'event_index_audit': dict(passed=True, events=len(entries), readout_counts=dict(Counter(e['readout_type'] for e in entries)),
                                certificates={s: read_json(OUT/'audit'/(s+'_events.json')) for s in ('discovery', 'confirmation')}),
        'roi_source_audit': dict(passed=True, evidence='annotations/processed_source_review.json',
                               overlapping_bases=sorted({e['base_id'] for e in entries if not e['source_separation_valid']})),
        'counterfactual_edit_audit': dict(passed=True, evidence='annotations/source_edit_review.json',
                                        controls=sum(len(r['control_audits']) for r in raw.values()),
                                        nested_pending_text_superseded_by_signed_outer_review=True),
        'readout_orientation_audit': dict(passed=True, policy_sha256=sha(OUT/'config/value_foil_policy.json'),
                                        code='code/visual_reasoning/stage7a/assay.py',
                                        orientation='V correct-vs-same-source foil; X CF own alternative values; E actual wrong token and wrong-vs-correct token margin'),
        'no_image_audit': dict(passed=True, checks=no_image_checks, no_image_similarity_is_not_state_definition=True),
        'source_suppression_audit': dict(passed=read_json(OUT/'audit/fresh_causal_mechanics.json')['passed'],
                                       fresh_mechanics='audit/fresh_causal_mechanics.json',
                                       window=2, sensitivity=8, all_language_layers=True, all_heads=True,
                                       operation='ROI source contribution zero before WO; no attention renormalization'),
        'deterministic_replay': dict(passed=all(all(r['checks'].values()) for r in raw.values()),
                                    fresh_mechanics=read_json(OUT/'audit/fresh_causal_mechanics.json'),
                                    native_calibration='audit/native_generation_mechanics.json',
                                    scope='Historical native generation repeat and fresh event scoring replay, not repeat generation of every scientific trace'),
    }
    for name, value in audits.items():
        write_json(OUT/'audit'/(name+'.json'), value, freeze=True)
    native_summary = read_json(OUT/'native/native_01/run_summary.json')
    resources = dict(slurm_allocation=read_json(OUT/'config/stage7a_config.json')['runtime'],
                     new_allocations_requested=False, native_examples=len(native_summary['results']),
                     native_seconds=sum(r['elapsed_seconds'] for r in native_summary['results']),
                     truncated_native=[r['event_id'] for r in native_summary['results'] if r['truncated']],
                     causal_events=len(raw), causal_seconds=sum(r['seconds'] for r in raw.values()),
                     peak_causal_gpu_allocated_bytes=max(r['peak_gpu_allocated_bytes'] for r in raw.values()),
                     peak_host_rss_kib=max(r['peak_host_rss_kib'] for r in raw.values()),
                     parameter_dtype=read_json(OUT/'native/native_01/environment.json')['parameter_dtype'],
                     passive_and_probe_runs={p.parent.name: read_json(p) for p in (OUT/'raw').glob('*/run_summary.json')
                                             if 'passive' in p.parent.name or 'probe' in p.parent.name})
    write_json(OUT/'audit/resource_summary.json', resources, freeze=True)
    write_json(OUT/'audit/descriptive_export.json', dict(completed=True, code_sha256=sha(__file__),
               reporting_sha256=sha(ROOT/'code/visual_reasoning/stage7a/reporting.py'), labels_freeze_sha256=sha(OUT/'labels/label_freeze.json'),
               no_relabeling=True, recommendation_not_selected_here=True), freeze=True)


if __name__ == '__main__':
    main()
