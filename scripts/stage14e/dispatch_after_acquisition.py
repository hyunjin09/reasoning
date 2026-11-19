"""Finite CPU handoff: freeze acquisition, submit four authorized solver shards, exit.

No annotations, model selection, scoring, or follow-on experiments are performed.
This can run afterok under Slurm while the agent is not attached.
"""
import os
from scripts.stage14e.common import P, load, save, sha, now
from scripts.stage14e.evaluation_packets import main as packets
from scripts.stage14e.prepare_final_solvers import main as prepare
from scripts.stage14e.launch_flexible import launch


def pending_manifests(registry, receipt_exists):
    paths = registry['solver_manifests']
    assert len(paths) == len(set(paths)) == 4
    assert len(registry['families']) == len(set(registry['families'])) == 32
    assert registry['logical_count'] == 96
    return [path for path in paths if not receipt_exists('stage14e_' + load(path)['id'])]


def main():
    assert os.environ.get('SLURM_JOB_ID'), 'Run the finite automatic dispatcher under Slurm'
    attempt = 'evaluation_acquisition_a6000_v2'
    result_path = P / 'raw' / attempt / 'result.json'
    assert load(result_path)['status'] == 'ACQUISITION_COMPLETED'
    if not (P/'audit/evaluation_acquisition_freeze_v1.json').exists():
        packets(attempt)
    registry_path=P/'manifests/final_execution_registry_v1.json'
    if not registry_path.exists():
        prepare()
    for path, digest in load(P/'audit/final_solver_seal_v1.json')['files'].items():
        assert sha(path) == digest, path
    registry=load(registry_path)
    # afterok has already been satisfied; do not propagate CPU dispatch dependency.
    os.environ.pop('SBATCH_DEPENDENCY',None)
    paths=pending_manifests(registry, lambda i:(P/'audit/launches'/f'{i}.json').exists())
    for path in paths:
        launch(path,module='split_entry')
    save(P/'audit/automatic_dispatch_v1.json',dict(at=now(),cpu_job=os.environ['SLURM_JOB_ID'],
        acquisition_sha256=sha(result_path),registry_sha256=sha(registry_path),
        submitted_manifests=paths,scientific_outcomes_inspected=False,
        scope='four frozen N/S/M solver queues only; no new stage or analysis'))


if __name__=='__main__':main()
