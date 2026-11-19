import unittest
from scripts.stage13a.inference import estimate, bounds, decision, majority, optional_needed

class InferenceTests(unittest.TestCase):
    def test_family_not_replicate_weight(self):
        r=estimate([1/3,-1/3,0]);self.assertAlmostEqual(r['effect_pp'],0)
        self.assertEqual((r['n'],r['positive'],r['zero'],r['negative']),(3,1,1,1))
    def test_bootstrap_constant_and_empty(self):
        self.assertEqual(estimate([1/3]*80)['ci95_pp'],[100/3,100/3])
        self.assertIsNone(estimate([])['effect_pp'])
    def test_missing_bounds(self):
        r=bounds([{'I':[True,None,False],'T':[True,True,None]}])
        self.assertAlmostEqual(r['lower_pp'],0);self.assertAlmostEqual(r['upper_pp'],200/3)
    def test_decision_boundaries(self):
        self.assertEqual(decision(80,5,[.1,9.9],10,False),'EQUAL_EVIDENCE_THINKING_ADVANTAGE_CONFIRMED')
        self.assertEqual(decision(79,30,[20,40],0,True),'EQUAL_EVIDENCE_TECHNICALLY_UNRESOLVED')
        self.assertEqual(decision(96,4.9,[1,9],0,False),'EQUAL_EVIDENCE_SIGNAL_PARTIAL')
        self.assertEqual(decision(96,5,[0,10],0,False),'EQUAL_EVIDENCE_SIGNAL_PARTIAL')
        self.assertEqual(decision(80,10,[1,20],11,False),'EQUAL_EVIDENCE_TECHNICALLY_UNRESOLVED')
        self.assertEqual(decision(80,10,[1,20],11,True),'EQUAL_EVIDENCE_THINKING_ADVANTAGE_CONFIRMED')
        self.assertEqual(decision(96,0,[-2,2],0,False),'EQUAL_EVIDENCE_NO_ADVANTAGE')
    def test_missing_majorities(self):
        self.assertIsNone(majority([True,False,None]))
        self.assertTrue(majority([True,True,None]))
        self.assertFalse(majority([False,False,None]))
    def test_optional_only_after_confirmed(self):
        self.assertFalse(optional_needed(False,estimate([1/3]*10)))
        self.assertTrue(optional_needed(True,estimate([1/3]*79)))
        self.assertFalse(optional_needed(True,estimate([1/3]*80)))

if __name__=='__main__':unittest.main()
