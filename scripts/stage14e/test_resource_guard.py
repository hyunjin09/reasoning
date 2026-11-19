import unittest
from scripts.stage14e.resource_guard import exhausted,allowance
class Guard(unittest.TestCase):
 def test_allocation_not_request_latency(self):
  self.assertTrue(exhausted(970,1,1000));self.assertFalse(exhausted(969,1,1000))
 def test_no_invalid_allowance(self):
  for value in [-1,0,86401,'12']:
   with self.assertRaises(ValueError):allowance({'budget_reservation_seconds':value})
 def test_explicit_reservation(self):self.assertEqual(allowance({'budget_reservation_seconds':18000}),18000)
 def test_two_gpus_charge_twice(self):self.assertTrue(exhausted(485,2,1000))
if __name__=='__main__':unittest.main()
