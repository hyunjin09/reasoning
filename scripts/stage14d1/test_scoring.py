import unittest
from scripts.stage14d1.scoring import score
class ScoringTests(unittest.TestCase):
 def test_unclosed_thought_never_becomes_wrong(self):
  r=score('The answer is 7','length',[],'8');self.assertIsNone(r['correct']);self.assertIn('UNSCORABLE',r['final_status'])
 def test_correct_and_wrong_final_distinct(self):
  self.assertTrue(score('</think>Final answer: 7','stop',[],'7')['correct'])
  self.assertFalse(score('</think>Final answer: 7','stop',[],'8')['correct'])
 def test_choice_not_incidental_letter(self):
  self.assertIsNone(score('</think>Consider A and B, but I am unsure.','length',['first','second'],'A')['correct'])
if __name__=='__main__':unittest.main()
