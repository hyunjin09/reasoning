import unittest
from scripts.stage12ws.decision_v2 import select

class DecisionTests(unittest.TestCase):
    def test_local_content_effect_is_not_a_null(self):
        counts=dict(derived_state_support=1,distributed_necessity=0)
        family=dict(eligible=True,derived_state_support=True,order_sensitive=False,
                    derived_contrasts={},block_effects={})
        self.assertEqual(select({'continue':True,'status':'CONTINUE'},counts,{'joint':False},[family]),'UNRESOLVED')

    def test_strong_thresholds_unchanged(self):
        self.assertEqual(select({'continue':True,'status':'CONTINUE'},
            dict(derived_state_support=3,distributed_necessity=2),{'joint':False},[]), 'DISTRIBUTED_DERIVED_STATE_SIGNAL')

    def test_no_certified_content_effect_is_preserved(self):
        self.assertEqual(select({'continue':True,'status':'CONTINUE'},
            dict(derived_state_support=0,distributed_necessity=0),{'joint':False},[]), 'PORTABILITY_CONTENT_UNRESOLVED')

if __name__=='__main__':unittest.main()
