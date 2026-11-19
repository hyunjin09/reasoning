"""Wait for fixed C1 acquisition, then run only the authorized Stage6A release.

CPU only, inside the existing allocation. Never submits a new allocation, changes
generation, retries a failed release, rebuilds the frozen atlas or runs Stage6B.
"""
import fcntl
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone

from scripts.stage6a.inventory import OUT, ROOT


def validate_shard(receipt, rank, expected_ids, manifest_sha):
    assert receipt['rank'] == rank, 'Wrong shard rank'
    assert receipt['complete'] is True, 'Shard is not terminal'
    rows = receipt['results']
    assert [r['event_id'] for r in rows] == expected_ids, 'Wrong shard event order or membership'
    assert all(r['manifest_sha256'] == manifest_sha for r in rows), 'Wrong native manifest'
    # Terminal capped records are preserved; EOS is not the readiness criterion.
    return rows


def main():
    assert os.environ.get('SLURM_JOB_ID') == '109385', 'Use the existing allocation'
    log_dir = ROOT / 'runs/stage6a'
    python = str(ROOT / '.venv/bin/python')
    status_path = OUT / 'audit/finalization_status.json'
    lock = (log_dir / 'finalization.lock').open('a+')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def status(state, **details):
        value = dict(status=state, updated_at=datetime.now(timezone.utc).isoformat(),
                     allocation='109385', pid=os.getpid(), **details)
        temporary = status_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(value, indent=2) + '\n')
        temporary.replace(status_path)
        print(json.dumps(value), flush=True)

    def command(args, log_name):
        with (log_dir / log_name).open('w') as stream:
            subprocess.run([python, *args], cwd=ROOT, stdout=stream,
                           stderr=subprocess.STDOUT, check=True)

    def scheduler_done(job, note):
        command(['infra/gpu_scheduler.py', 'update', '--project', '.', '--id', job,
                 '--status', 'succeeded', '--note', note], job + '_completion.log')

    step = 'readiness'
    try:
        assert not (OUT / 'cohort/primary_release_manifest.json').exists(), 'Release already exists; do not overwrite'
        manifest_path = OUT / 'cohort/controlled_stress_manifest.jsonl'
        frozen = json.loads((OUT / 'cohort/c1_membership_freeze.json').read_text())
        raw = manifest_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert digest == frozen['stress_manifest_sha256']
        manifest = [json.loads(line) for line in raw.decode().splitlines()]
        assert len(manifest) == frozen['stress_events'] == 1090
        config = json.loads((OUT / 'config/stage6a_config.json').read_text())
        directories = [OUT / f'native/controlled_stress/shard_{rank:02d}' for rank in range(4)]
        previous = None
        while True:
            ready = [rank for rank, path in enumerate(directories) if (path / 'result.json').exists()]
            if ready != previous:
                status('WAITING_FOR_C1', completed_shards=ready, expected_events=len(manifest))
                previous = ready
            if len(ready) == 4:
                break
            time.sleep(30)
        # A receipt is written last by the worker; any malformed/partial receipt
        # stops safely instead of promoting missing results or retrying work.
        rows = []
        for rank, directory in enumerate(directories):
            signature = json.loads((directory / 'config.json').read_text())
            assert signature['manifest_sha256'] == digest and signature['config'] == config
            assert signature['rank'] == rank and signature['world'] == 4
            assert signature['slurm_job_id'] == '109385' and not signature['replay_baselines']
            receipt = json.loads((directory / 'result.json').read_text())
            shard = validate_shard(receipt, rank, [r['event_id'] for r in manifest[rank::4]], digest)
            for row in shard:
                saved = json.loads((directory / 'examples' / row['event_id'] / 'result.json').read_text())
                assert saved == row, 'Shard receipt differs from terminal example'
            rows.extend(shard)
        assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == digest
        assert json.loads((OUT / 'config/stage6a_config.json').read_text()) == config, 'Config changed while waiting'
        status('C1_ACQUISITION_VERIFIED', terminal_events=len(rows),
               eos_complete=sum(r['complete'] for r in rows), manifest_sha256=digest)
        scheduler_done('stage6a_c1_stress', 'All1090frozen C1stress records terminal; exact shard/config/manifest checks passed. Capped records retained.')
        modules = ['collect_controlled_traces', 'score_controlled_answers',
                   'annotate_controlled_states', 'audit_controlled_annotations',
                   'export_release_manifests', 'audit_release', 'summarize_resources',
                   'summarize_release']
        for step in modules:
            status('FINALIZING', step=step)
            command(['-m', 'scripts.stage6a.' + step] + (['--final'] if step == 'summarize_resources' else []),
                    'final_' + step + '.log')
        scheduler_done('stage6a_annotation_pipeline', 'Stage6Afinal native/semantic/ROI/split audits and18summary tables complete. No subsequent research stage executed.')
        # Refresh resource provenance after scheduler status changes, then render
        # the same deterministic report with the final provenance snapshot.
        for step in ['summarize_resources', 'summarize_release']:
            command(['-m', 'scripts.stage6a.' + step] + (['--final'] if step == 'summarize_resources' else []),
                    'final_' + step + '.log')
        step = 'close_workspace_state'
        status('FINALIZING', step=step)
        command(['-m', 'scripts.stage6a.' + step], 'final_' + step + '.log')
        acceptance = json.loads((OUT / 'summaries/stage6a_acceptance.json').read_text())
        status('RELEASE_ARTIFACTS_COMPLETE', recommendation=acceptance['recommendation'],
               report='summaries/stage6a_cohort_summary.md',
               next_stage_executed=False, final_human_readable_state_review_pending=False,
               workspace_state_closeout='audit/workspace_state_closeout.json',
               review_scope='Pre-reviewed report templates and frozen branch; final artifact/count/hash checks are programmatic.')
    except Exception as error:
        status('FAILED_STOPPED', step=step, error=repr(error))
        raise
    finally:
        lock.close()


if __name__ == '__main__':
    main()
