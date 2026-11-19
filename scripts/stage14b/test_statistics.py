import unittest
from scripts.stage14b.inference_math import paired, rescue, summarize

class StatisticsTests(unittest.TestCase):
    def test_missing_is_not_false(self):
        s=summarize([True,False,None],3)
        self.assertEqual(s['correct'],1);self.assertEqual(s['wrong'],1);self.assertEqual(s['missing_or_unscorable'],1)
        self.assertAlmostEqual(s['resolved_accuracy'],.5)
        self.assertAlmostEqual(s['coverage_lower_accuracy'],1/3)
    def test_pairing_does_not_compare_different_items(self):
        r=paired([{'family_id':'a','I':True,'T':None},{'family_id':'b','I':None,'T':True}],draws=100)
        self.assertEqual(r['paired_n'],0);self.assertIsNone(r['paired_difference_pp'])
    def test_known_alias_weighting_sensitivity(self):
        data=[dict(family_id='a',I=False,T=True)]*3+[dict(family_id='b',I=True,T=False)]
        r=paired(data,draws=100)
        self.assertEqual(r['paired_difference_pp'],50)
        self.assertEqual(r['family_equal']['estimate_pp'],0)
        self.assertEqual(r['cluster']['families'],2)
    def test_rescue_denominator_does_not_drop_unknown_silently(self):
        data=[dict(family_id=str(i),native=x,equal=y) for i,(x,y) in enumerate([(False,True),(False,False),(False,None),(True,True),(None,True)])]
        r=rescue(data,draws=100)
        self.assertEqual(r['native_wrong'],3);self.assertEqual(r['resolved_followups'],2)
        self.assertEqual(r['rescue_fraction_resolved'],.5)
        self.assertEqual(r['all_native_wrong_bounds'],[1/3,2/3])
    def test_complete_known_difference(self):
        r=paired([dict(family_id='a',I=False,T=True),dict(family_id='b',I=True,T=True)],draws=100)
        self.assertEqual(r['paired_difference_pp'],50)
        self.assertEqual(r['missingness_bounds_pp'],[50,50])

if __name__=='__main__':unittest.main()
