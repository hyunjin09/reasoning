import json
from pathlib import Path
import pytest
from scripts.stage8b.finish_resume125 import digest, verify
from scripts.stage8b.select_shared_layout import select


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


@pytest.fixture
def batch(tmp_path):
    rows = [dict(item_id=str(i), family_id=f'f{i}') for i in range(256)]
    index = []
    for i, row in enumerate(rows):
        root = tmp_path/('old' if i < 131 else 'new')/'examples'/str(i)
        artifact = write(root/'manifest_row.json', row)
        receipt = write(root/'result.json', dict(row, provenance_sha256={str(artifact): digest(artifact)}))
        index.append(dict(row, receipt=str(receipt), receipt_sha256=digest(receipt) if i < 131 else None))
    cfg = dict(output_dir=str(tmp_path/'new'))
    for key, data in [('manifest', rows[131:]), ('bounded_cohort_manifest', rows)]:
        p = tmp_path/f'{key}.jsonl'; p.write_text(''.join(json.dumps(r)+'\n' for r in data))
        cfg[key] = str(p); cfg[key+'_sha256'] = digest(p)
    p = write(tmp_path/'index.json', dict(rows=index))
    cfg.update(cohort_artifact_index=str(p), cohort_artifact_index_sha256=digest(p))
    cfg['layout_decision'] = str(write(tmp_path/'layout.json', dict(worker_count=4, workers_per_gpu=2, exact_parity=True)))
    for rank in range(4):
        root = tmp_path/'new/census'/f'worker{rank}'
        write(root/'environment.json', dict(rank=rank, slurm_parent_rank=rank//2, workers_per_gpu=2,
                                           gpu_uuid=f'gpu{rank//2}', hostname='node06'))
        write(root/'completed.json', dict(completed=True, items=[r['item_id'] for r in rows[131+rank::4]]))
    return cfg


def test_accepts_preserved131_plus_new125(batch):
    assert len(verify(batch)) == 125


@pytest.mark.parametrize('damage', ['prior', 'missing', 'shard', 'gpu'])
def test_rejects_broken_continuation(batch, damage):
    root = Path(batch['output_dir'])
    if damage == 'prior':
        (root.parent/'old/examples/0/manifest_row.json').write_text('{}')
    elif damage == 'missing':
        (root/'examples/131/result.json').unlink()
    elif damage == 'shard':
        write(root/'census/worker0/completed.json', dict(completed=True, items=[]))
    else:
        p = root/'census/worker0/environment.json'; r = json.loads(p.read_text()); r['gpu_uuid'] = 'other'; write(p, r)
    with pytest.raises(AssertionError):
        verify(batch)


@pytest.fixture
def benchmarks(tmp_path):
    cfg = dict(output_dir=str(tmp_path), performance_probe_ids=['0','1','2','3'], historical_peak_reserved_bytes=20*2**30)
    for mode, n in [('single', 2), ('double', 4)]:
        for i in range(n):
            root = tmp_path/f'benchmark_{mode}'/f'worker{i}'
            write(root/'environment.json', dict(gpu_uuid=f'gpu{i//(n//2)}', hostname='node06', gpu_total_memory_bytes=48*2**30))
            write(root/'checks.json', dict(pass_checks=True)); write(root/'completed.json', dict(completed=True))
        for item in range(4):
            worker = item//2 if mode == 'single' else item
            start = item%2*10 if mode == 'single' else 0
            finish = start+10 if mode == 'single' else 15
            write(tmp_path/f'benchmark_{mode}'/f'worker{worker}'/f'item_{item}.json',
                  dict(item_id=str(item), tokens=100, token_ids=[1,2], raw_logit_sha256=['a','b'], passive_sha256={'features':'c'},
                       started=start, finished=finish, runtime=dict(peak_gpu_reserved_bytes=8*2**30)))
    return cfg


def test_benchmark_gate_compares_same_work(benchmarks):
    r = select(benchmarks)
    assert r['exact_parity'] and r['workers_per_gpu'] == 2
    assert r['aggregate_speedup'] == pytest.approx(4/3)


def test_benchmark_gate_rejects_numerical_change(benchmarks):
    p = Path(benchmarks['output_dir'])/'benchmark_double/worker0/item_0.json'
    row = json.loads(p.read_text()); row['raw_logit_sha256'] = ['changed']; write(p, row)
    with pytest.raises(ValueError):
        select(benchmarks)
