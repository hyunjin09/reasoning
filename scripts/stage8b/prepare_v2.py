"""Freeze the explicitly approved v2 audit without touching historical outputs."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage8b.v2_protocol import generation_parameters, MIN_PIXELS, MAX_PIXELS


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def main():
    root = Path('outputs/stage8b/v2')
    prior = json.loads(Path('outputs/stage8b/config/transfer32_v1.json').read_text())
    original = Path(prior['full_census_manifest'])
    assert sha(original) == prior['full_census_manifest_sha256']
    inventory = json.loads(Path('outputs/stage8b/audit/input_inventory.json').read_text())
    assert Path(inventory['source']).is_file() and Path(prior['model_checkpoint']).is_dir()
    rows = [json.loads(x) for x in original.read_text().splitlines()]
    assert len(rows) == 3040 and len({x['item_id'] for x in rows}) == 3040
    for row in rows:
        assert sha(row['image']) == row['image_sha256']
        # Official Qwen runner adds no custom CoT/boxed suffix by default.
        # Retain local MathVision question + explicit options from the original split.
        row.update(generation_query=row['question'], protocol_id='stage8b_v2_mathvision_t1')
    for name, selected in [('census_manifest_v1.jsonl', rows), ('transfer32_manifest_v1.jsonl', rows[:32])]:
        path = root/'cohort'/name; path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x') as stream:
            for row in selected: stream.write(json.dumps(row, ensure_ascii=False)+'\n')
    (root/'annotations').mkdir(parents=True, exist_ok=True)
    shutil.copyfile('outputs/stage8b/annotations/input_demands_v1.json', root/'annotations/input_demands_v1.json')
    files = set(prior['source_sha256'])
    files.update(['scripts/stage8b/run_native_v2.py', 'scripts/stage8b/finish_batch_v2.py',
        'scripts/stage8b/run_transfer32_v2_batch.sh', 'scripts/stage8b/prepare_v2.py',
        'scripts/stage8b/review_transfer_v2.py', 'scripts/stage8b/score_native_v2.py',
        'code/visual_reasoning/stage8b/v2_protocol.py', 'code/visual_reasoning/stage8b/v2_scoring.py',
        'code/visual_reasoning/stage8b/scoring.py', 'code/visual_reasoning/stage8b/transfer.py',
        'code/visual_reasoning/stage8a/annotations.py', 'plan/stage8b_v2_transfer_annotation_protocol.md'])
    files.update(str(p) for p in (root/'protocol_sources').iterdir() if p.is_file())
    hashes = {p: sha(p) for p in sorted(files)}
    snapshot = root/'source_snapshots/transfer32_t1_v1'
    for name in hashes:
        dest = snapshot/name; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(name, dest)
    cfg = {k: v for k, v in prior.items() if k.startswith('model_') or k.startswith('detector_')}
    cfg.update(at=datetime.now(timezone.utc).isoformat(), stage='8B.0 v2 T=1.0 revalidation',
        protocol_id='stage8b_v2_mathvision_t1', seed=1234, max_new_tokens=40960,
        generation_parameters=generation_parameters(), presence_penalty=0.0,
        min_pixels=MIN_PIXELS, max_pixels=MAX_PIXELS,
        manifest=str(root/'cohort/transfer32_manifest_v1.jsonl'),
        full_census_manifest=str(root/'cohort/census_manifest_v1.jsonl'),
        output_dir=str(root/'native/transfer32_t1_v1'), source_sha256=hashes,
        slurm_request=dict(node='node03', gpus=2, cpus=16, mem='100G', time='1-00:00:00', tmux=False),
        scorer='local cap-independent compatible adapter; unresolved needs blind extraction; no external GPT-4o',
        prompt='local original MathVision question/options, no extra CoT or boxed suffix; official Qwen chat/pixel preprocessing; TSV wording equivalence not asserted')
    cfg['manifest_sha256'] = sha(cfg['manifest'])
    cfg['full_census_manifest_sha256'] = sha(cfg['full_census_manifest'])
    save(root/'config/transfer32_t1_v1.json', cfg)
    save(root/'audit/input_freeze_v1.json', dict(at=cfg['at'], rows=len(rows),
        audit_items=[r['item_id'] for r in rows[:32]], same_pilot_item_ids=True, outcome_selection=False,
        prior_temperature_batch_excluded=True, no_download=True, prior_inventory=inventory,
        all_images_verified=True, source_sha256=hashes,
        historical_results_sha256={str(p): sha(p) for p in Path('outputs/stage8b/native/transfer32_v1/examples').glob('*/result.json')}))
    print(json.dumps(dict(config=str(root/'config/transfer32_t1_v1.json'), rows=len(rows), audit=32,
                         source_files=len(hashes), no_download=True)))


if __name__ == '__main__':
    main()
