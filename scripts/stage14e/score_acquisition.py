"""Seal manual source comparisons independently of downstream answer scoring."""
import argparse
import csv
import json
from scripts.stage14e.common import P, load, rows, save, sha, now
from scripts.stage14e.analysis_metrics import acquisition


def main(attempt):
    root = P / 'raw' / attempt
    states = load(root / 'acquisition_states.json')
    selected = load(P / 'manifests/evaluation_family_selection_v1.json')['rows']
    source = {r['item_id']: r for r in selected}
    families = {r['item_id']: r for r in rows(P / 'inference/evaluation_families.jsonl')}
    label_path = P / 'annotations/evaluation_labels_v1.tsv'
    with label_path.open() as f:
        labels = list(csv.DictReader(f, delimiter='\t'))
    assert len(labels) == 32 and {r['item_id'] for r in labels} == set(source)
    records = []
    for label in labels:
        i = label['item_id']
        for arm in ['S', 'M', 'M_noimage']:
            read = states[i]['read_plan'].get(arm)
            code = label[arm]
            assert (code == 'A') == (read is None)
            path = read['generation_path'] if read else None
            g = load(path) if path else None
            parsed = states[i]['readouts'][arm]
            if code == 'X':
                assert g and parsed is None
            records.append(dict(item_id=i, family_id=source[i]['family_id'], condition=arm, label=code,
                notes=label['notes'], target_relevance=label['target_' + ('M' if arm == 'M_noimage' else arm)],
                generation_path=path, generation_sha256=sha(path) if path else None,
                raw_exact_output=g['raw_decoded_response'] if g else None, parsed=parsed,
                image=families[i]['image'], image_sha256=families[i]['image_sha256'],
                prefix_sha256=families[i]['prefix_sha256'], stratum=source[i]['stratum'],
                physical_execution=read is not None, no_fresh_helper_image=arm == 'M_noimage'))
    save(P / 'annotations/evaluation_source_review_v1.json', dict(at=now(), records=records,
        labels_sha256=sha(label_path), reviewer='single AI; condition visible; source reference uncertainty retained',
        new_solver_final_outcomes_inspected=False, original_SAVA_outcome_exposure=True))
    summary = acquisition(records, [r['family_id'] for r in selected], [r['stratum'] for r in selected],
                          ['S', 'M', 'M_noimage'])
    save(P / 'analysis/evaluation_acquisition_results_v1.json', dict(at=now(), **summary,
         primary_contrast='M-S', noimage_contrast='M-M_noimage (reverse sign of stored pair)',
         selected_method=load(P / 'protocol/final_method_selection_v1.json')['selected']))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('attempt')
    main(parser.parse_args().attempt)
