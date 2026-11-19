import unittest
from scripts.stage12a.inference import endpoints,estimate

class FamilyInference(unittest.TestCase):
    def test_conditional_denominators_and_nested_counts(self):
        rows=[dict(e=True,d=False,c=True),dict(e=True,d=False,c=False),
              dict(e=False,d=False,c=True),dict(e=False,d=False,c=False),
              dict(e=False,d=False,c=False),dict(e=False,d=False,c=False),dict(e=True,d=True,c=True)]
        p=endpoints(rows)
        self.assertEqual(p['n'],7);self.assertEqual(p['L'],2);self.assertEqual(p['rescued'],1)
        self.assertEqual(p['R_avail'],.5);self.assertEqual(p['R_unavail'],.25);self.assertEqual(p['delta'],.25)
        self.assertEqual(p['F2'],p['F3']+p['F4'])

    def test_absent_comparator_is_not_zero_rescue(self):
        p=endpoints([dict(e=True,d=False,c=True)])
        self.assertIsNone(p['R_unavail']);self.assertIsNone(p['delta'])

    def test_bootstrap_is_family_level_and_reproducible(self):
        rows=[dict(e=bool(i%2),d=False,c=bool(i%3)) for i in range(12)]
        a=estimate(rows,seed=15,draws=4000);b=estimate(rows,seed=15,draws=4000)
        self.assertEqual(a,b);self.assertEqual(a['bootstrap']['draws'],4000)
        self.assertLessEqual(a['P1_wilson95'][0],a['point']['P1'])
        self.assertGreaterEqual(a['P1_wilson95'][1],a['point']['P1'])

if __name__=='__main__':unittest.main()
