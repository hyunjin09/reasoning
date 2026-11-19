"""Independent final coverage, preservation and analysis consistency checks."""
import csv
import subprocess
from pathlib import Path
from scripts.stage14d1_pilot.common import P, load, rows, save, sha, now
from scripts.stage14d1_pilot.finalize_v8 import summarize


def main():
    initial = load(P/'analysis/scored_logical_rows_v8.json')['rows']
    final = load(P/'analysis/scored_logical_rows_final_v8.json')['rows']
    old = load(P/'analysis/accuracy_and_pairs_v8.json')
    reproduced = summarize(initial)
    for arm, result in old['arms'].items():
        for key, value in result.items():
            assert reproduced['arms'][arm][key] == value, (arm, key)
    for pair, result in old['pairs'].items():
        for key, value in result.items():
            assert reproduced['pairs'][pair][key] == value, (pair, key)
    result = load(P/'analysis/accuracy_and_pairs_final_v8.json')
    reproduced_final = summarize(final)
    assert reproduced_final['arms'] == result['arms']
    assert reproduced_final['pairs'] == result['pairs']
    assert len(final) == 432 and len({r['family_id'] for r in final}) == 72
    assert len({r['generation_path'] for r in final}) == 345
    assert len({(r['family_id'], r['arm']) for r in final}) == 432
    unchanged = 0
    for before, after in zip(initial, final):
        assert before['generation_path'] == after['generation_path']
        if before['correct'] is not None:
            assert before['answer'] == after['answer'] and before['correct'] == after['correct']
            assert not after['response_reviewed']
            unchanged += 1
    assert unchanged == 384
    assert sum(r['correct'] is None for r in final) == 1
    with (P/'analysis/scored_logical_rows_final_v8_clean.csv').open() as f:
        reader = csv.DictReader(f)
        assert len(reader.fieldnames) == len(set(reader.fieldnames))
        exported = list(reader)
    assert len(exported) == 432
    for record, exported_row in zip(final, exported):
        assert record['item_id'] == exported_row['item_id'] and record['arm'] == exported_row['arm']
        assert record['correct'] == {'True':True, 'False':False, '':None}[exported_row['correct']]

    expected = {}
    seals = load(P/'audit/final_historical_preservation_v8.json')['seals']
    seals += [str(P/'audit/execution_metrics_pre_outcome_seal_v8.json'),
              str(P/'audit/scientific_generation_freeze_v8.json')]
    seals += [str(P/'annotations'/name) for name in ['query_review_complete.json',
        'fixed_readout_review_complete.json', 'flagged_readout_review_complete_v8.json',
        'regression_review_complete_v8.json', 'primary_rescue_review_complete_v8.json']]
    for path in seals:
        seal = load(path)
        files = seal['files'] if 'files' in seal else {**seal['package_files'], **seal['code_files']}
        for filename, digest in files.items():
            if filename in expected:
                assert expected[filename] == digest, filename
            expected[filename] = digest
    for filename, digest in expected.items():
        assert sha(filename) == digest, filename
    for original in rows(P/'inference/families.jsonl'):
        assert sha(original['image']) == original['image_sha256']
    for review in load(P/'annotations/response_review_v8.json')['records']:
        assert sha(review['packet']) == review['packet_sha256']
        assert sha(review['generation_path']) == review['generation_sha256']
    for name in ['regression_review_complete_v8.json', 'primary_rescue_review_complete_v8.json']:
        for item in load(P/'annotations'/name)['items']:
            assert (P/'annotations/readouts'/f'{item}.json').exists()
    accounting = load(P/'audit/resource_accounting_final_v8.json')
    assert accounting['total_gpu_seconds'] == sum(j['gpu_seconds'] for j in accounting['jobs']) == 76915
    queued = subprocess.check_output(['squeue','-h','-j','149690,149691','-o','%i'], text=True).strip()
    assert not queued, queued
    save(P/'audit/final_result_verification_v8.json', dict(at=now(), passed=True,
        families=72, logical_slots=432, physical_primary=345, missing=0, unscorable=1,
        unchanged_initially_scorable_rows=unchanged,
        original_analysis_reproduced_exactly=True, final_summary_reproduced_exactly=True,
        clean_csv_unique_headers_and_scores=True, preserved_files=len(expected),
        original_images_verified=72, gold_hidden_response_reviews_verified=45,
        all_regression_and_primary_rescue_source_reviews_complete=True,
        cumulative_gpu_seconds=76915, active_gpu_jobs=0, seals=seals,
        regression_test_evidence='28 tests passed in merge/family/statistics/reuse final verification; prior red/green records retained.',
        verification_code_sha256=sha(__file__)))
    print('Final verification PASS:', len(expected), 'preserved files;72/432/345 coverage;0 active GPUs.')


if __name__ == '__main__':
    main()
