"""Validate completed Stage7A evidence before issuing its acceptance certificate.

This reports missing work without creating an acceptance file. Scientific
interpretation and the one next-stage recommendation remain a manual review.
"""
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, sha


def required_paths():
    plan = (ROOT/'plan/stage7a_causal_visual_grounding_states_plan.md').read_text()
    block = plan.split('# 42. Output Structure', 1)[1].split('```text', 1)[1].split('```', 1)[0]
    directory = None
    result = []
    for line in block.splitlines():
        if line.startswith('  ') and not line.startswith('    '):
            directory = line.strip().rstrip('/')
        elif line.startswith('    ') and not line.strip().endswith('/'):
            result.append(directory+'/'+line.strip())
    assert len(result) > 60 and len(result) == len(set(result))
    return result


def validate():
    required = required_paths()
    # Acceptance is written only after this audit and the manual review pass.
    prior = [p for p in required if p != 'summaries/stage7a_acceptance.json']
    extra = ['audit/technical_acceptance_review.json', 'audit/final_figure_review.json',
             'analysis/figures/figure_index.json', 'labels/label_freeze.json',
             'raw/probes_01/run_summary.json', 'audit/fresh_causal_mechanics.json']
    missing = [p for p in prior+extra if not (OUT/p).is_file()]
    if missing:
        return dict(ready_for_acceptance=False, missing=missing, plan_required_paths=required)
    for name in prior:
        path = OUT/name
        if path.suffix == '.json': read_json(path)
        elif path.suffix == '.jsonl': read_jsonl(path)  # Empty rare-state files are valid.
        else: assert path.read_text().strip(), name
    review = read_json(OUT/'audit/technical_acceptance_review.json')
    assert set(review['criteria']) == {str(i) for i in range(1, 21)}
    for key, item in review['criteria'].items():
        assert item['status'] == 'PASS' and item['rationale'] and item['evidence_sha256'], key
        for path, digest in item['evidence_sha256'].items():
            resolved = (ROOT/path).resolve()
            assert resolved.is_relative_to(ROOT)
            assert sha(resolved) == digest, path
    assert review['exactly_one_recommendation']
    assert review['recommendation_sha256'] == sha(OUT/'summaries/next_stage_recommendation.md')
    from scripts.stage7a.export_analysis import load_completed
    entries, metrics, states, frozen = load_completed()
    native = read_jsonl(OUT/'cohort/native_manifest.jsonl')
    generated = read_json(OUT/'native/native_01/run_summary.json')
    assert generated['completed']
    assert {r['event_id'] for r in native} == {r['event_id'] for r in generated['results']}
    for result in generated['results']:
        event_id = result['event_id']
        annotation = read_json(OUT/'annotations/native_reviews'/(event_id+'.json'))
        generation = OUT/'native/native_01/examples'/event_id/'generation.json'
        assert annotation['generation_sha256'] == sha(generation)
        if result['complete']:
            assert annotation['full_native_text_reviewed']
            final = read_json(OUT/'annotations/final_answer_reviews'/(event_id+'.json'))
            assert final['generation_sha256'] == sha(generation) and final['full_native_text_reviewed']
        else:
            assert not annotation['claims'] and annotation['behavior'] == 'incomplete_generation'
    for split in ('discovery', 'confirmation'):
        expected = {e['id'] for e in entries if e['split'] == split}
        run = OUT/'raw'/(split+'_passive_01')
        summary = read_json(run/'run_summary.json')
        assert summary['completed'] and summary['all_native_causal_exact']
        assert {r['id'] for r in summary['results']} == expected
        assert summary['label_freeze_sha256'] == sha(OUT/'labels/label_freeze.json')
    assert read_json(OUT/'raw/probes_01/run_summary.json')['completed']
    assert read_json(OUT/'audit/fresh_causal_mechanics.json')['passed']
    figures = read_json(OUT/'analysis/figures/figure_index.json')
    assert figures['completed'] and set(figures['categories']) == {str(i) for i in range(1, 23)}
    for path, digest in figures['artifacts'].items():
        assert sha(OUT/path) == digest
    for number in range(1, 23):
        suffixes = {(OUT/p).suffix for p in figures['artifacts'] if (OUT/p).name.startswith(f'{number:02d}_')}
        assert {'.svg', '.pdf', '.png'} <= suffixes
    visual_review = read_json(OUT/'audit/final_figure_review.json')
    assert visual_review['passed'] and visual_review['scientific_results_reviewed']
    assert visual_review['figure_index_sha256'] == sha(OUT/'analysis/figures/figure_index.json')
    claims = read_json(OUT/'analysis/paper_claim_assessment.json')
    assert claims['review_complete'] and claims['scope_limitations']
    return dict(ready_for_acceptance=True, plan_required_paths=required,
                native_traces=len(native), causal_events=len(entries),
                technical_criteria=20, figure_categories=22,
                verified_artifacts_sha256={p: sha(OUT/p) for p in prior+extra},
                evidence_audit_only=True, recommendation_selected_by_manual_review=True)


def main():
    result = validate()
    write_json(OUT/'audit/completion_preflight.json', result)
    print('READY_FOR_ACCEPTANCE' if result['ready_for_acceptance'] else 'INCOMPLETE',
          'missing artifacts:', len(result.get('missing', [])))
    if not result['ready_for_acceptance']: raise SystemExit(2)


if __name__ == '__main__':
    main()
