import unittest
from unittest.mock import patch
from scripts.stage14e.accounting_retry import refresh

class AccountingRetry(unittest.TestCase):
    def test_newly_submitted_job_becomes_visible(self):
        with patch('scripts.stage14e.accounting_retry.refresh_once',side_effect=[RuntimeError('Missing Slurm accounting'),{'new_actual_gpu_seconds':90,'new_reserved_gpu_seconds':14310}]) as query, patch('scripts.stage14e.accounting_retry.time.sleep') as wait:
            self.assertEqual(refresh()['new_reserved_gpu_seconds'],14310)
            self.assertEqual(query.call_count,2);wait.assert_called_once_with(1)
    def test_persistent_missing_blocks_admission(self):
        with patch('scripts.stage14e.accounting_retry.refresh_once',side_effect=RuntimeError('Missing Slurm accounting')) as query, patch('scripts.stage14e.accounting_retry.time.sleep'):
            with self.assertRaisesRegex(RuntimeError,'Missing Slurm accounting'):refresh()
            self.assertEqual(query.call_count,6)
    def test_unrelated_failure_not_hidden(self):
        with patch('scripts.stage14e.accounting_retry.refresh_once',side_effect=RuntimeError('Invalid TRES')), patch('scripts.stage14e.accounting_retry.time.sleep') as wait:
            with self.assertRaisesRegex(RuntimeError,'Invalid TRES'):refresh()
            wait.assert_not_called()
if __name__=='__main__':unittest.main()
