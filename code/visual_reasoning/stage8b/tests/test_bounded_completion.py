"""Completion must reject missing, altered, or misassigned native evidence."""
import json
from pathlib import Path

import pytest

from scripts.stage8b.finish_census224 import digest, verify_batch


@pytest.fixture
def batch(tmp_path):
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return path

    rows = [dict(item_id=str(i), family_id=f'family{i}') for i in range(256)]
    index = []
    for i, row in enumerate(rows):
        root = tmp_path/('prior' if i < 32 else 'new')/'examples'/row['item_id']
        artifact = write(root/'manifest_row.json', row)
        receipt = write(root/'result.json', dict(row, provenance_sha256={str(artifact): digest(artifact)}))
        index.append(dict(row, receipt=str(receipt), receipt_sha256=digest(receipt) if i < 32 else None))
    manifest = tmp_path/'new.jsonl'
    manifest.write_text(''.join(json.dumps(r)+'\n' for r in rows[32:]))
    combined = tmp_path/'combined.jsonl'
    combined.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    ix = write(tmp_path/'index.json', dict(rows=index))
    for rank in range(4):
        root = tmp_path/'new'/'census'/f'worker{rank}'
        write(root/'environment.json', dict(gpu_uuid=f'gpu{rank}'))
        write(root/'completed.json', dict(completed=True, items=[r['item_id'] for r in rows[32+rank::4]]))
    return dict(output_dir=str(tmp_path/'new'), manifest=str(manifest), manifest_sha256=digest(manifest),
                cohort_artifact_index=str(ix), cohort_artifact_index_sha256=digest(ix),
                bounded_cohort_manifest=str(combined), bounded_cohort_manifest_sha256=digest(combined))


def test_accepts_exact_continuation(batch):
    assert len(verify_batch(batch)) == 224


@pytest.mark.parametrize('damage', ['missing', 'old_tampered', 'new_tampered', 'duplicate_gpu', 'wrong_worker'])
def test_rejects_broken_evidence(batch, damage):
    root = Path(batch['output_dir'])
    if damage == 'missing':
        (root/'examples/32/result.json').unlink()
    elif damage == 'old_tampered':
        (root.parent/'prior/examples/0/manifest_row.json').write_text('{}')
    elif damage == 'new_tampered':
        (root/'examples/32/manifest_row.json').write_text('{}')
    elif damage == 'duplicate_gpu':
        (root/'census/worker1/environment.json').write_text('{"gpu_uuid": "gpu0"}')
    else:
        p = root/'census/worker0/completed.json'
        value = json.loads(p.read_text())
        value['items'][0] = '33'
        p.write_text(json.dumps(value))
    with pytest.raises(AssertionError):
        verify_batch(batch)
