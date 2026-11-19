"""Freeze exactly the first16 matched native cases after source and cap sealing."""
from scripts.stage11c.common import ROOT, ARMS, load, save, sha, now


def main():
    split = load(ROOT/'stage11c_primary_split.json')
    cap = load(ROOT/'stage11c_cap_validation.json')
    assert split['frozen'] and split['status'] == 'READY' and split['primary_n'] >= 64
    assert split['model_outcomes_opened'] is False and cap['frozen'] and cap['status'] == 'COMPLETE'
    assert split['e_star_sha256'] == sha(ROOT/'stage11c_e_star_gold.parquet')
    assert split['review_sha256'] == sha(ROOT/'stage11c_e_star_sufficiency_review.json')
    assert split['original_source_manifest_sha256'] == sha(ROOT/'stage11c_heldout_source_manifest.json')
    for path, digest in split['source_exclusion_sha256'].items():
        assert sha(path) == digest
    families = split['primary'][:16]
    shards = []
    for arm in ARMS:
        model_key = 'thinking' if arm == 'thinking' else 'instruct'
        for part in range(2):
            tasks = []
            for index, family in enumerate(families):
                if index % 2 != part:
                    continue
                row = {k: family[k] for k in ['item_id', 'family_id', 'image', 'image_sha256', 'generation_query']}
                row.update(task_id=f'native_{arm}_{family["item_id"]}', arm=arm,
                    condition='native', max_new_tokens=cap['cap'], primary_order=index)
                tasks.append(row)
            shards.append(dict(id=f'{model_key}_{part}', model_key=model_key, rows=tasks))
    manifest = dict(at=now(), frozen=True, queue='native_early', shards=shards,
        config_sha256=sha(ROOT/'config.json'), primary_split_sha256=sha(ROOT/'stage11c_primary_split.json'),
        cap_validation_sha256=sha(ROOT/'stage11c_cap_validation.json'),
        common_cap=cap['cap'], n_families=16, n_calls=32,
        early_completion_gate='All32 calls must finish; >4/16 cap hits in either arm stops before further native/oracle.')
    save(ROOT/'native_early_tasks.json', manifest)
    (ROOT/'native_early/claims').mkdir(parents=True, exist_ok=False)
    print('EARLY_NATIVE_FROZEN', 32, 'CALLS', 'CAP', cap['cap'])


if __name__ == '__main__':
    main()
