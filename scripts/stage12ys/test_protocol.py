import unittest
from scripts.stage12ys.protocol import majority, screen, select_candidates, role_signals, seed

class ProtocolTests(unittest.TestCase):
    def test_missing_is_not_failure(self):
        self.assertIsNone(majority([False,None,True],3))
        self.assertFalse(majority([False,False,None],3))
        self.assertTrue(majority([True,True,None],3))
        self.assertIsNone(majority([True,True,None,None,False],5))

    def test_screen_requires_observed_failures(self):
        base=dict(E_I=False,E_T=True,I_img=False,T_img=True,I_E=True,T_E=None)
        self.assertTrue(screen(base)['access_strong'])
        base['I_img']=None
        self.assertFalse(screen(base)['access_weak'])
        self.assertFalse(screen(dict(base,I_E=None,T_E=True))['downstream'])

    def test_candidate_caps_and_supplement_boundary(self):
        rows=[dict(item_id=str(i),family_id=str(i),access_strong=i<7,access_weak=True,downstream=True,native_linked=i>=20) for i in range(35)]
        a,d=select_candidates(rows)
        self.assertEqual(len(a),16)
        self.assertEqual(sum(r['access_strong'] for r in a),7)
        self.assertEqual(len(d),16)
        self.assertEqual(sum(r['native_linked'] for r in d),15)
        rows[7]['access_strong']=True
        self.assertEqual(len(select_candidates(rows)[0]),8)

    def test_frozen_decision_thresholds(self):
        self.assertEqual(role_signals(5,3,5,3,3,2,3)['decision'],'MULTI_ROLE_THINKING_SIGNAL')
        self.assertTrue(role_signals(5,3,5,3,3,2,3)['state'])
        self.assertFalse(role_signals(4,4,4,4,2,2,2)['access'])
        self.assertEqual(role_signals(4,4,4,4,2,2,2)['decision'],'ROLE_DECOMPOSITION_UNRESOLVED')

    def test_seed_domains_are_disjoint(self):
        values=[seed('f','T_E',i,p) for p in ['A','B','C'] for i in range(5)]
        self.assertEqual(len(set(values)),15)

if __name__=='__main__':unittest.main()
