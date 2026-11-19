"""Freeze the next224 entries of the existing order without outcome selection."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def external(path):
    resolved = Path(path).resolve()
    assert resolved.is_relative_to('/data/dataset'), resolved
    return resolved


def main():
    root = Path('outputs/stage8b1a')
    parent = Path('outputs/stage8b/v2/config/transfer32_t1_node02_four_v1.json')
    cfg = json.loads(parent.read_text())
    assert not Path('datasets').exists() and not Path('datasets').is_symlink(), 'Review the project dataset link before reuse'
    inventory = json.loads(Path('outputs/stage8b/audit/input_inventory.json').read_text())
    assert digest(external(inventory['source'])) == inventory['source_sha256']
    for path, sha in cfg['source_sha256'].items():
        assert digest(path) == sha, path
    assert digest(cfg['full_census_manifest']) == cfg['full_census_manifest_sha256']
    assert digest(cfg['manifest']) == cfg['manifest_sha256']
    full = [json.loads(x) for x in Path(cfg['full_census_manifest']).read_text().splitlines()]
    prior = [json.loads(x) for x in Path(cfg['manifest']).read_text().splitlines()]
    assert len(full) == 3040 and len(prior) == 32 and full[:32] == prior
    combined, selected = full[:256], full[32:256]
    assert len({r['item_id'] for r in combined}) == 256
    for row in combined:
        assert digest(external(row['image'])) == row['image_sha256'], row['item_id']
    checkpoint = external(cfg['model_checkpoint'])
    weights = {}
    for name in ['model.safetensors']:
        path = external(checkpoint/name)
        sha = digest(path)
        assert len(path.name) == 64 and path.name == sha, path
        weights[name] = sha
    assert digest(cfg['detector_freeze']) == cfg['detector_freeze_sha256']
    rule = json.loads(Path(cfg['detector_freeze']).read_text())
    assert digest(rule['retrieval']['models']) == rule['retrieval']['models_sha256']
    old_root = Path(cfg['output_dir'])
    new_root = root/'native/census224_node02_v1'
    rows = []
    for i, row in enumerate(combined):
        receipt = (old_root if i < 32 else new_root)/'examples'/row['item_id']/'result.json'
        if i < 32:
            result = json.loads(receipt.read_text())
            assert result['item_id'] == row['item_id'] and result['family_id'] == row['family_id']
            for artifact, sha in result['provenance_sha256'].items():
                assert digest(artifact) == sha, artifact
        else:
            assert not receipt.parent.exists(), receipt
        rows.append(dict(order=row['order'], item_id=row['item_id'], family_id=row['family_id'],
                         origin='existing32' if i < 32 else 'new224', receipt=str(receipt),
                         receipt_sha256=digest(receipt) if i < 32 else None))
    manifests = {}
    for size, content in [(224, selected), (256, combined)]:
        path = root/'cohort'/f'census{size}_manifest_v1.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as stream:
            for row in content:
                stream.write(json.dumps(row, ensure_ascii=False)+'\n')
        manifests[size] = path
    index = root/'cohort/census256_artifact_index_v1.json'
    save(index, dict(rows=rows, selection='Original census order [:256]; new [32:256], no outcome filtering'))
    cfg.update(at=datetime.now(timezone.utc).isoformat(), stage='8B.1a bounded224 native continuation',
               manifest=str(manifests[224]), manifest_sha256=digest(manifests[224]), output_dir=str(new_root),
               parent_config=str(parent), parent_config_sha256=digest(parent),
               scheduler_id='stage8b1a_census224_node02_v1', reused_items={}, reused_receipt_sha256={},
               cohort_artifact_index=str(index), cohort_artifact_index_sha256=digest(index),
               bounded_cohort_manifest=str(manifests[256]), bounded_cohort_manifest_sha256=digest(manifests[256]),
               slurm_request=dict(node='node02', gpus=4, cpus=32, mem='120G', time='2-00:00:00', tmux=False))
    extra = ['scripts/stage8b/prepare_census224.py', 'scripts/stage8b/run_census224_batch.sh',
             'scripts/stage8b/finish_census224.py', 'code/visual_reasoning/stage8b/tests/test_bounded_completion.py',
             'plan/stage8b1a_224_mathvision_bounded_census_plan.md', 'plan/stage8b1a_execution_checklist.md']
    cfg['source_sha256'].update({p: digest(p) for p in extra})
    for path in cfg['source_sha256']:
        copy = root/'source_snapshots/census224_node02_v1'/path
        copy.parent.mkdir(parents=True, exist_ok=True)
        assert not copy.exists(), copy
        shutil.copyfile(path, copy)
    config = root/'config/census224_node02_v1.json'
    save(config, cfg)
    freeze = dict(at=cfg['at'], config=str(config), config_sha256=digest(config),
                  existing_examples=32, new_examples=224, total_examples=256,
                  unique_families=len({r['family_id'] for r in combined}),
                  new_ids=[r['item_id'] for r in selected],
                  worker_ids={str(i): [r['item_id'] for r in selected[i::4]] for i in range(4)},
                  lookup_order=['Project datasets link absent', 'Exact existing allowed external Arrow/images/model verified'],
                  dataset=inventory, model_weights_sha256=weights,
                  preserved_reviewed_scores_sha256=digest('outputs/stage8b/v2/analysis/census_snapshot_reviewed_v2.json'),
                  source_files=len(cfg['source_sha256']), no_download=True, gpu_work_started=False,
                  gpu_hours_estimate=224*0.281607432299,
                  four_gpu_wall_hours_estimate=[15.8, 21.9], requested_hours=48)
    save(root/'audit/input_freeze_v1.json', freeze)
    for directory in ['runs/stage8b1a/node02', 'runs/stage8b1a/tmp', str(root/'audit/matplotlib_cache')]:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print(json.dumps({k: v for k, v in freeze.items() if k not in ['new_ids', 'worker_ids', 'dataset', 'model_weights_sha256']}, indent=2))


if __name__ == '__main__':
    main()
