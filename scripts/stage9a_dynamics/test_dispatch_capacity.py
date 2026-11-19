"""Scheduler boundaries must include pending and unrelated GPU reservations."""
import json
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

import pytest
from scripts.stage9a_dynamics import dispatch


@pytest.mark.parametrize('limit,running,pending,other,node_free,expected', [
    (8, 4, 0, 0, 8, 4),
    (8, 6, 2, 0, 8, 0),
    (8, 4, 0, 4, 8, 0),
    (8, 4, 0, 0, 2, 2),
    (4, 4, 0, 0, 8, 0),
])
def test_one_dispatch_cycle(tmp_path, monkeypatch, limit, running, pending,
                            other, node_free, expected):
    monkeypatch.setenv('SLURM_JOB_ID', 'cpu-test')
    monkeypatch.setattr(dispatch, 'ROOT', tmp_path)
    monkeypatch.setattr(dispatch, 'READOUT_ROOT', tmp_path)
    monkeypatch.setattr(dispatch, 'MAX_GPUS', limit, raising=False)
    monkeypatch.setattr(dispatch, 'WORKER_NODE', 'node02', raising=False)
    (tmp_path/'audit').mkdir()
    (tmp_path/'audit/tasks.json').write_text(json.dumps({'rows': [{'task_id': 'unclaimed'}]}))
    (tmp_path/'audit/readouts_complete.json').write_text('{}')
    count = running + pending
    jobs = [dict(id=f'{dispatch.PREFIX}_worker_{i}', status='running', slurm_job_id=str(i))
            for i in range(count)]
    queue = {'jobs': jobs}
    live = [f'{i}|RUNNING|gres/gpu:1' for i in range(running)]
    live += [f'{i}|PENDING|gres/gpu:1' for i in range(running, count + other)]
    monkeypatch.setattr(dispatch, 'load_gpu_queue', lambda _: queue)
    monkeypatch.setattr(dispatch.subprocess, 'run', lambda *a, **k: SimpleNamespace(stdout='\n'.join(live)))
    def capacity(args, _):
        return dict(warnings=[], remaining_user_slots=max(0, args.max_user_gpus-count-other),
                    available_node_gpus={'node02': {'available': node_free}, 'node07': {'available': 8}})
    monkeypatch.setattr(dispatch.scheduler, 'gpu_status', capacity)
    monkeypatch.setattr(dispatch.scheduler, 'plan_jobs', lambda *a: [])
    added = []
    monkeypatch.setattr(dispatch, 'add_compute', lambda kind, index, node: added.append((kind, node)))
    class CycleFinished(Exception):
        pass
    def stop(_):
        raise CycleFinished()
    monkeypatch.setattr(dispatch.time, 'sleep', stop)
    with pytest.raises(CycleFinished):
        dispatch.run(datetime.now(timezone.utc) + timedelta(minutes=1))
    assert added == [('worker', 'node02')] * expected
    status = json.loads((tmp_path/'audit/dispatcher_status.json').read_text())
    assert status['maximum_gpus'] == limit
