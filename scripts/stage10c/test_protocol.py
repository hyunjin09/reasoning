import unittest
import numpy as np
from scripts.stage10c.protocol import matched_windows,selected_queries,contrasts,choose_control
class ProtocolTests(unittest.TestCase):
 def test_prediction_alignment_and_restoration(self):
  pre,post=matched_windows(100)
  self.assertEqual(pre,[76,100]);self.assertEqual(post,[100,124])
  self.assertEqual(selected_queries(10,85,26,[pre]),list(range(24)))
  self.assertEqual(selected_queries(10,109,26,[post]),list(range(24)))
  self.assertEqual(selected_queries(10,133,2,[post]),[])
  self.assertEqual(selected_queries(10,0,10,[[0,24]]),[])
 def test_paired_signs_and_nll(self):
  y=np.array([[1,1,0,0,1],[0,0,1,1,0]])
  n=np.array([[2,3,5,6,4],[2,2,1,1,2]])
  np.testing.assert_equal(contrasts(y,n),[[1,2,1,2],[-1,-1,-1,-1]])
 def test_matched_control_disjoint_compact(self):
  target=[5,6,9,10];control=choose_control(target,[],[1,4,4],set())
  self.assertEqual(len(control),len(target));self.assertFalse(set(control)&set(target))
  self.assertEqual(control,choose_control(target,[],[1,4,4],set()))
 def test_impossible_control_rejected(self):
  with self.assertRaises(ValueError):choose_control(list(range(12)),[],[1,4,4],set())
if __name__=='__main__':unittest.main()
