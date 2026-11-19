import unittest
from scripts.stage11a.census_statistics import rate, paired_summary, coarse_state

class StatisticsTests(unittest.TestCase):
    def test_empty_condition_not_zero(self):
        r=rate([]);self.assertEqual(r['n'],0);self.assertIsNone(r['point'])
    def test_paired_independence_and_discordant_exact(self):
        r=paired_summary([1,0],[0,1])
        self.assertEqual(r['n'],2);self.assertEqual(r['point'],0)
        self.assertEqual(r['left_only'],1);self.assertEqual(r['right_only'],1)
        self.assertEqual(r['mcnemar_exact_two_sided_p'],1)
        self.assertEqual(r['ci95'],[-1.,1.])
    def test_not_externalized_is_not_observed_absence(self):
        self.assertNotEqual(coarse_state('N5'),coarse_state('N0'))
        self.assertEqual(coarse_state('N3'),coarse_state('N4'))

if __name__=='__main__':unittest.main()
