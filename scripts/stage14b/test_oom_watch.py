import unittest
from unittest.mock import patch
from types import SimpleNamespace
from scripts.stage14b import oom_watch


class OOMWatchTests(unittest.TestCase):
    def test_user_cancellation_timeout_and_host_oom_do_not_restart(self):
        for state in ('CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY'):
            self.assertEqual(oom_watch.inspect_closed('1', {}, {'JobState':state})['action'], 'HOLD')

    def test_healthy_completion_does_not_launch_another_job(self):
        self.assertEqual(oom_watch.inspect_closed('1', {}, {'JobState':'COMPLETED'})['action'], 'DONE')

    def test_existing_replacement_is_reused_without_new_submission(self):
        existing=dict(id='vr_stage14b_oom_recovery_1',slurm_job_id='2')
        with patch.object(oom_watch.scheduler,'load_gpu_queue',return_value={'jobs':[existing]}), \
             patch.object(oom_watch.scheduler,'execute_launch') as launch:
            self.assertEqual(oom_watch.submit_replacement('1',None,1),existing)
            launch.assert_not_called()

    def test_eight_gpu_ceiling_prevents_submission(self):
        with patch.object(oom_watch.scheduler,'load_gpu_queue',return_value={'jobs':[]}), \
             patch.object(oom_watch.scheduler,'gpu_status',return_value={'warnings':[], 'remaining_user_slots':0}), \
             patch.object(oom_watch.scheduler,'execute_launch') as launch:
            self.assertIsNone(oom_watch.submit_replacement('1',None,1))
            launch.assert_not_called()


if __name__=='__main__':unittest.main()
