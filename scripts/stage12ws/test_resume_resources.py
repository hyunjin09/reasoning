import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from scripts.stage12ws.common import sha
from scripts.stage12ws.resume_resources import cost, enforce, account

class ResourceTests(unittest.TestCase):
    def test_cleanup_counts_after_reported_runtime(self):
        fields = dict(JobState='COMPLETING', RunTime='00:40:00',
                      TimeLimit='00:40:00', StartTime='2026-10-02T10:00:00')
        result = cost(fields, '2026-10-02T11:30:00+09:00')
        self.assertAlmostEqual(result['upper'], 1.5)
        self.assertFalse(result['released'])

    def test_pending_commits_limit_without_spending_it(self):
        result = cost(dict(JobState='PENDING', RunTime='00:00:00',
                           TimeLimit='00:20:00', StartTime='Unknown'), '2026-10-02T11:30:00+09:00')
        self.assertEqual(result['lower'], 0)
        self.assertAlmostEqual(result['upper'], 1/3)

    def test_both_authorized_limits_apply(self):
        enforce(10.1283, 2.5, .5)
        with self.assertRaises(AssertionError): enforce(10.1283, 2.9, .2)
        with self.assertRaises(AssertionError): enforce(13.0, .5, .6)

    def test_purged_job_uses_explicit_verified_bounds(self):
        with tempfile.TemporaryDirectory(dir='runs/stage12ws/v1') as folder:
            root = Path(folder)
            def write(name, value):
                p = root/name; p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(value)); return p
            write('audit/resource_amendment_approved_v1.json', dict(approved=True, additional_gpu_hours=3, total_ceiling_gpu_hours=14))
            write('audit/resume_resource_reconciliation_v1.json', dict(conservative_allocation_hours_bounds=[7,10]))
            worker = write('workers/1/exit.json', dict(complete=True))
            write('audit/resume_missing_terminal_bounds/1.json', dict(released=True, lower=.1, upper=.3,
                worker_exit_sha256=sha(worker), status='PURGED_RELEASED_WORKER_COMPLETE', node='node07',
                interpretation='Worker and queue bounds; not exact Slurm runtime.'))
            queue = dict(jobs=[dict(id='stage12ws_resume_test', slurm_job_id='1', gpus=1, command='frozen', log_path='log')])
            with patch('scripts.stage12ws.resume_resources.ROOT', root), patch('scripts.stage12ws.resume_resources.scheduler.load_gpu_queue', return_value=queue), patch('scripts.stage12ws.resume_resources.subprocess.run') as shell:
                result = account('test')
                self.assertEqual(result['new_gpu_hours_lower'], .1)
                self.assertEqual(result['new_gpu_hours_upper'], .3)
                self.assertTrue(result['all_released'])
                shell.assert_not_called()
                worker.write_text('{}')
                with self.assertRaises(AssertionError): account('changed_receipt')

if __name__ == '__main__': unittest.main()
