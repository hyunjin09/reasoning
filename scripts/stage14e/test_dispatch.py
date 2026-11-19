import unittest
from unittest.mock import patch
from scripts.stage14e.dispatch_after_acquisition import pending_manifests

class Dispatch(unittest.TestCase):
    def setUp(self):
        self.r=dict(solver_manifests=['a','b','c','d'],families=list(range(32)),logical_count=96)
    def test_existing_receipts_never_relaunched(self):
        with patch('scripts.stage14e.dispatch_after_acquisition.load',side_effect=lambda p:{'id':p}):
            self.assertEqual(pending_manifests(self.r,lambda i:i in ['stage14e_a','stage14e_c']),['b','d'])
    def test_duplicate_or_missing_shards_rejected(self):
        with self.assertRaises(AssertionError):
            pending_manifests(dict(self.r,solver_manifests=['a','a','b','c']),lambda _:False)
    def test_wrong_family_count_rejected(self):
        with self.assertRaises(AssertionError):
            pending_manifests(dict(self.r,families=list(range(31))),lambda _:False)
if __name__=='__main__':unittest.main()
