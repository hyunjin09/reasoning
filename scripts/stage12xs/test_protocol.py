import unittest
from scripts.stage12xs.protocol import majority, support, decision, seed, prompt

class ProtocolTests(unittest.TestCase):
    def test_missing_outcomes_cannot_be_failures(self):
        self.assertIsNone(majority([True,True,None,False,False]))
        self.assertTrue(majority([True,True,True,None,None]))
        self.assertFalse(majority([True,False,False,False,None]))
        self.assertIsNone(support({'RT_T':[True]*5,'RT_I':[True]*5,'Q_I':[False,False,None,None,None],'SH_I':[False]*5}))

    def test_exact_family_gates_and_low_yield_boundary(self):
        self.assertEqual(decision(2,[True,True],[True,True]),'HELDOUT_CANDIDATE_SPARSE')
        self.assertEqual(decision(5,[True]*4+[False],[True]*3+[False]*2),'HELDOUT_STATE_PRODUCTION_REPLICATED')
        self.assertEqual(decision(5,[True]*5,[True,False,False,False,False]),'HELDOUT_STATE_PRODUCTION_NOT_REPLICATED')
        self.assertEqual(decision(3,[True]*3,[True,True,False]),'HELDOUT_PORTABILITY_PARTIAL')
        self.assertEqual(decision(4,[True]*4,[True,False,False,False]),'UNRESOLVED_LOW_YIELD')
        self.assertEqual(decision(5,[True]*5,[True,False,None,None,None]),'UNRESOLVED_TECHNICAL')

    def test_fixed_prompt_contract_and_condition_specific_seeds(self):
        row=dict(question='Original question\nA. 1\nB. 2',facts=[dict(probe_request='What is labeled AB?',gold_value='3 cm')])
        self.assertEqual(prompt(row,'N'),row['question'])
        self.assertEqual(prompt(row,'C'),row['question']+" Let's think step by step.")
        self.assertNotIn('3 cm',prompt(row,'E'))
        self.assertIn('3 cm',prompt(row,'O'))
        self.assertNotEqual(seed('f','RT_I',0),seed('f','Q_I',0))
        self.assertEqual(seed('f','RT_I',0),seed('f','RT_I',0))

if __name__=='__main__':unittest.main()
