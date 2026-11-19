import unittest
from scripts.stage14b.accounting_v2 import elapsed_accounting


class ResourceTests(unittest.TestCase):
    def test_cpu_time_is_never_gpu_time(self):
        self.assertEqual(elapsed_accounting(0,'RUNNING',0,None,None,7200)['gpu_hours'],0)

    def test_gpu_multiplier_and_closed_interval(self):
        r=elapsed_accounting(2,'COMPLETED',100,3700,None,100000)
        self.assertEqual(r['gpu_hours'],2)
        self.assertEqual(r['basis'],'Slurm start/end interval')

    def test_purged_job_stops_at_worker_exit(self):
        r=elapsed_accounting(1,'NOT_IN_SLURM',100,None,{'at':'1970-01-01T01:01:40+00:00','seconds':3500},100000)
        self.assertEqual(r['gpu_hours'],1)
        self.assertIn('proxy',r['basis'])

    def test_unobserved_terminal_time_not_invented(self):
        r=elapsed_accounting(1,'NOT_IN_SLURM',100,None,None,100000)
        self.assertIsNone(r['gpu_hours'])

    def test_pending_time_zero(self):
        self.assertEqual(elapsed_accounting(4,'PENDING',None,None,None,100000)['gpu_hours'],0)

if __name__=='__main__':unittest.main()
