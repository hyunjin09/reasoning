import unittest
from scripts.stage11b.protocol import discovery_gate, oracle_text, trim_generated

class ProtocolTests(unittest.TestCase):
    def test_gate_requires_all_thresholds_and_twelve_discordances(self):
        good=dict(n=100,eligible=60,t_correct=30,c_correct=18,forward=12)
        self.assertTrue(discovery_gate(**good)['pass'])
        for key,value in [('eligible',39),('forward',11),('t_correct',46),('c_correct',5)]:
            self.assertFalse(discovery_gate(**dict(good,**{key:value}))['pass'])

    def test_oracle_contains_only_fixed_facts_and_question(self):
        text=oracle_text('Find x.', ['AB = 6','Angle ABC = 60 degrees'])
        self.assertIn('Fact 1: AB = 6',text)
        self.assertTrue(text.endswith('Question:\nFind x.'))
        with self.assertRaises(ValueError):oracle_text('Find x.', [])

    def test_batched_padding_does_not_change_eos_or_cap(self):
        self.assertEqual(trim_generated([7,8,2,0,0],{2},5),([7,8,2],True,False))
        self.assertEqual(trim_generated([7,8,9],{2},3),([7,8,9],False,True))

if __name__=='__main__':unittest.main()
