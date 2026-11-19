import unittest
from scripts.stage14b.monitor_main import classify

class MonitorTests(unittest.TestCase):
    def test_pending_is_neither_completed_nor_failed(self):
        self.assertEqual(classify([dict(job_id='1',closed=False,state='PENDING',heartbeat=None,exit=None)]),([],[]))
    def test_expired_slurm_record_with_valid_exit_counts_as_started(self):
        self.assertEqual(classify([dict(job_id='1',closed=True,state='NOT_IN_SLURM',exit={'complete':True})]),([],['1']))
    def test_completed_samples_do_not_hide_worker_failure(self):
        self.assertEqual(classify([dict(job_id='1',closed=True,state='FAILED',heartbeat={'completed':4},exit=None)]),(['1'],[]))

if __name__=='__main__':unittest.main()
