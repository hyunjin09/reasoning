"""Seal source review and choose once by the predeclared development rule."""
import argparse
import csv
import json
from scripts.stage14e.common import P, load, rows, save, sha, now
from scripts.stage14e.analysis_metrics import acquisition


def main(attempt):
    root = P / 'raw' / attempt
    assert load(root / 'result.json')['status'] == 'COMPLETED'
    manifest = load(P / 'manifests' / (attempt + '.json'))
    logical = {(r['item_id'], r['condition']): r
               for r in load(root / 'read_execution_manifest.json')['logical']}
    families = {r['item_id']: r for r in rows(P / 'inference/diagnostic_families.jsonl')}
    source = {r['item_id']: r for r in rows('outputs/stage14d1_sava_pilot/v1/data/offline_source_manifest.jsonl')}
    label_path = P / 'annotations/development_labels_v2.tsv'
    with label_path.open() as f:
        labels = list(csv.DictReader(f, delimiter='\t'))
    assert len(labels) == 24 and {r['item_id'] for r in labels} == set(manifest['families'])
    result = []
    for label in labels:
        i = label['item_id']
        for arm in ['A_blind', 'R_context', 'R_blind', 'R_noimage']:
            row = logical[i, arm]
            code = label[arm]
            path = row['generation_path']
            generation = load(path) if path else None
            assert (code == 'A') == (generation is None)
            try:
                parsed = json.loads(generation['raw_decoded_response']) if generation else None
            except (ValueError, TypeError):
                parsed = None
            if code == 'X':
                assert generation and parsed is None
            result.append(dict(item_id=i, family_id=families[i]['family_id'], condition=arm, label=code,
                notes=label['notes'], execution_status=row['status'], generation_path=path,
                generation_sha256=sha(path) if path else None, raw_exact_output=generation['raw_decoded_response'] if generation else None,
                image=families[i]['image'], image_sha256=families[i]['image_sha256'],
                prefix_sha256=families[i]['prefix_sha256'], parsed=parsed,
                source_stratum=source[i]['audit_context_stratum']))
    review = P / 'annotations/development_source_review_v2.json'
    save(review, dict(at=now(), records=result, reviewer='single AI, condition visible, development data',
                     labels_sha256=sha(label_path), final_evaluation_outcomes_inspected=False))
    family_ids = [families[r['item_id']]['family_id'] for r in labels]
    strata = [source[r['item_id']]['audit_context_stratum'] for r in labels]
    summary = acquisition(result, family_ids, strata, ['A_blind', 'R_context', 'R_blind', 'R_noimage'])
    arms = {'A': summary['arms']['A_blind'], 'R': summary['arms']['R_context']}
    selected = sorted(arms, key=lambda a: (-arms[a]['useful_correct'], arms[a]['label_counts'].get('W', 0), a))[0]
    save(P / 'analysis/development_results_v2.json', dict(at=now(), **summary, selected=selected))
    save(P / 'protocol/final_method_selection_v1.json', dict(at=now(), selected=selected,
        rule='Maximum useful-correct family count; tie fewer explicitly wrong readouts; final tie A',
        development_attempt=attempt, matched_runtime=True, source_review_sha256=sha(review),
        no_final_evaluation_outcomes_exist=True, no_further_method_revision=True,
        scientific_revision='outputs/stage14e_acquisition_development/v1/protocol/development_revision_v2.md'))
    print(json.dumps(dict(selected=selected, **summary), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('attempt')
    main(parser.parse_args().attempt)
