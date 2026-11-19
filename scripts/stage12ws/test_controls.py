import unittest
from scripts.stage12ws.controls import closest, elimination_status
class Tests(unittest.TestCase):
 def test_closest_subset_excludes_support_and_ties_earlier(self):
  b=[dict(block_id=i,token_count=n) for i,n in [(1,40),(2,60),(3,100),(4,100)]]
  self.assertEqual(closest(b,[1,2,3,4],100),[1,2])
  self.assertEqual(closest(b,[4],100),[4])
  self.assertIsNone(closest(b,[],100))
 def test_deletion_gap_stops_inconclusive(self):
  self.assertEqual(elimination_status([1,1]),'ACCEPT')
  self.assertEqual(elimination_status([3,3]),'STOP_LOSS')
  self.assertEqual(elimination_status([2,2]),'STOP_INCONCLUSIVE')
  self.assertEqual(elimination_status([0,3]),'STOP_INCONCLUSIVE')
if __name__=='__main__':unittest.main()
