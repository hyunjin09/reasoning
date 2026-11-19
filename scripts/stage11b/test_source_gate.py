import unittest
from scripts.stage11b.source_gate import source_possible

class NecessaryGateTests(unittest.TestCase):
    def test_twelve_forward_and_75_percent_ceiling_need_sixteen(self):
        self.assertFalse(source_possible(20,15,True)['possible'])
        self.assertTrue(source_possible(20,16,True)['possible'])
    def test_eligibility_or_diversity_failure_is_decisive(self):
        self.assertFalse(source_possible(128,51,True)['possible'])
        self.assertTrue(source_possible(128,52,True)['possible'])
        self.assertFalse(source_possible(128,60,False)['possible'])

if __name__=='__main__':unittest.main()
