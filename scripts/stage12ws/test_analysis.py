import unittest
from scripts.stage12ws.analysis import signature, distributed
class Tests(unittest.TestCase):
 def test_derived_requires_both_and_family_eligibility(self):
  t=[True]*7;f=[False]*7
  self.assertTrue(signature(t,f,t,f,True))
  self.assertFalse(signature(t,f,t,t,True))
  self.assertFalse(signature(t,f,t,f,False))
 def test_missing_cannot_certify_distributed(self):
  self.assertIsNone(distributed([[0,4]],[4,4],[0,0],1.0))
 def test_length_matched_and_no_large_single_drop(self):
  self.assertTrue(distributed([[1,1],[2,2]],[4,4],[0,1],.9))
  self.assertFalse(distributed([[4,4]],[4,4],[0,0],1))
  self.assertIsNone(distributed([[0,0]],[4,4],[0,0],.1))
if __name__=='__main__':unittest.main()
