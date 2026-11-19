import unittest
from scripts.stage12vs.protocol import segment,anchors,majority,localization,seed


class ProtocolTests(unittest.TestCase):
    def test_causal_step_needs_specificity_and_paraphrase(self):
        from scripts.stage12vs.inference import causal_step
        self.assertTrue(causal_step(True,False,False,True,True))
        self.assertFalse(causal_step(True,False,False,False,True))
        self.assertFalse(causal_step(True,False,False,True,False))
        self.assertIsNone(causal_step(True,False,None,True,True))

    def test_evidence_failure_must_be_in_the_causal_families(self):
        from scripts.stage12vs.inference import decision
        rows=[dict(stable=True,causal=True,oracle=False)]*2+[dict(stable=True,causal=True,oracle=True),dict(stable=True,causal=False,oracle=False)]
        self.assertEqual(decision(rows,0)['decision'],'UNRESOLVED')
        rows[2]['oracle']=False
        self.assertEqual(decision(rows,0)['decision'],'DERIVED_STATE_CAUSAL_SIGNAL')

    def test_segmentation_preserves_every_character_and_equation(self):
        text='Let x be a length.\n\n\\[\nx=2\n\n+y\n\\]\n\nThus the relation holds.  '
        parts=segment(text)
        self.assertEqual(''.join(parts),text)
        self.assertTrue(any('x=2\n\n+y' in s for s in parts))

    def test_coarse_anchors_include_endpoints(self):
        self.assertEqual(anchors(10),[0,2,4,6,8,10])
        self.assertEqual(anchors(3),[0,1,2,3])

    def test_missingness_is_not_incorrect(self):
        self.assertIsNone(majority([True,None,None]))
        self.assertIs(majority([False,False,None]),False)

    def test_adjacent_transition_needs_later_support(self):
        self.assertEqual(localization({0:False,3:False,4:True,8:True})['status'],'STABLE')
        self.assertEqual(localization({0:False,3:False,4:True})['status'],'NO_LATER_SUPPORT')

    def test_oscillation_is_not_sharp_transition(self):
        self.assertEqual(localization({0:False,2:True,4:False,6:True})['status'],'NONMONOTONIC_PORTABILITY')

    def test_unknown_midpoint_cannot_be_treated_as_failure(self):
        self.assertEqual(localization({0:False,2:None,4:True})['status'],'MISSING_BOUNDARY')

    def test_seed_identity_includes_phase_and_step(self):
        vals=[seed('family','phaseA',k,r) for k in range(3) for r in range(3)]
        self.assertEqual(len(set(vals)),9)
        self.assertNotEqual(vals[0],seed('family','phaseB',0,0))


if __name__=='__main__':unittest.main()
