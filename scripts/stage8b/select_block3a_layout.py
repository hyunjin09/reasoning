"""Freeze the operational layout from exact-parity and throughput measurements."""
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage8b.shared_execution import choose_layout


def select(cfg):
    root = Path(cfg['output_dir'])
    measurements = {}; samples = {}; memory = []
    for mode, workers in [('single', 2), ('double', 4)]:
        phase = root/f'benchmark_{mode}'
        env = [json.loads((phase/f'worker{i}'/'environment.json').read_text()) for i in range(workers)]
        uuids = Counter(e['gpu_uuid'] for e in env)
        assert len(uuids) == 2 and set(uuids.values()) == {workers//2}
        assert all(e['hostname'].split('.')[0] == 'node02' for e in env)
        for i in range(workers):
            assert json.loads((phase/f'worker{i}'/'checks.json').read_text())['pass_checks']
            assert json.loads((phase/f'worker{i}'/'completed.json').read_text())['completed']
        rows = [json.loads(p.read_text()) for p in phase.glob('worker*/item_*.json')]
        assert len(rows) == 4 and {r['item_id'] for r in rows} == set(cfg['performance_probe_ids'])
        samples[mode] = {r['item_id']: r for r in rows}
        wall = max(r['finished'] for r in rows)-min(r['started'] for r in rows)
        measurements[mode] = dict(wall_seconds=wall, tokens=sum(r['tokens'] for r in rows),
                                  tokens_per_second=sum(r['tokens'] for r in rows)/wall,
                                  gpu_uuids=sorted(uuids))
        memory.extend(e['gpu_total_memory_bytes']/2**30 for e in env)
    assert measurements['single']['gpu_uuids'] == measurements['double']['gpu_uuids']
    exact = all(samples['single'][item][key] == samples['double'][item][key]
                for item in cfg['performance_probe_ids']
                for key in ['token_ids', 'raw_logit_sha256', 'passive_sha256'])
    ratio = measurements['double']['tokens_per_second']/measurements['single']['tokens_per_second']
    estimated_double_memory = 2*max(cfg['historical_peak_reserved_bytes'],
        max(r['runtime']['peak_gpu_reserved_bytes'] for r in samples['double'].values()))/2**30
    per_gpu = choose_layout(speedup=ratio, exact_parity=exact, double_memory_gib=estimated_double_memory, device_memory_gib=min(memory))
    return dict(at=datetime.now(timezone.utc).isoformat(), workers_per_gpu=per_gpu, worker_count=2*per_gpu,
                selected_benchmark_phase='benchmark_double' if per_gpu == 2 else 'benchmark_single',
                exact_parity=exact, measurements=measurements, aggregate_speedup=ratio,
                conservative_double_reserved_gib=estimated_double_memory, gpu_memory_gib=min(memory),
                rule='Use2/processes per GPU if exact parity, >=1.05x measured throughput and <=90% projected reserved memory; otherwise use1. No scientific protocol changes.',
                limitation='2048-token startup performance probe; long-context throughput may differ. Memory projection includes historical40960-token runs.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True)
    cfg = json.loads(Path(ap.parse_args().config).read_text())
    result = select(cfg)
    with Path(cfg['layout_decision']).open('x') as stream:
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(result, indent=2), flush=True)
