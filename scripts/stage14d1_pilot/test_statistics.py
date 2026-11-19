import unittest
import numpy as np
from scripts.stage14d1_pilot.statistics import paired_summary, bootstrap_indices
class StatisticsTests(unittest.TestCase):
    def test_pairs_keep_unscorable_out_of_rescue_regression(self):
        x=np.array([1,0,1,0,np.nan]);y=np.array([1,1,0,np.nan,1])
        r=paired_summary(x,y,np.tile(np.arange(5),(20,1)))
        self.assertEqual(r['paired_scorable'],3);self.assertEqual(r['rescue'],1);self.assertEqual(r['regression'],1)
        self.assertEqual(r['paired_accuracy_difference'],0)
        self.assertEqual(r['known_correct_difference_all_assigned'],.2)
        self.assertEqual(r['missingness_difference_bounds'],[0,.4])
    def test_bootstrap_preserves_stratum_counts_and_seed(self):
        a=bootstrap_indices(['a','a','b','c','c'],40,19)
        self.assertTrue(np.array_equal(a,bootstrap_indices(['a','a','b','c','c'],40,19)))
        for row in a:
            self.assertEqual(sum(i<2 for i in row),2);self.assertEqual(sum(i==2 for i in row),1)
    def test_no_scorable_pair_returns_missing_not_zero(self):
        r=paired_summary(np.array([1,np.nan]),np.array([np.nan,0]),np.array([[0,1]]))
        self.assertIsNone(r['paired_accuracy_difference']);self.assertIsNone(r['paired_bootstrap_95ci'])
if __name__=='__main__':unittest.main()
