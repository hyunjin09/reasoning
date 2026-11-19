import unittest
from scripts.stage11b.futility import forward_upper_bound


class FutilityTests(unittest.TestCase):
    def test_incomplete_arm_is_not_assumed_failed(self):
        self.assertEqual(forward_upper_bound([(None, None), (True, None), (None, False)]), 3)

    def test_only_observed_impossibility_removes_family(self):
        self.assertEqual(forward_upper_bound([(False, None), (None, True), (True, False), (False, False)]), 1)


if __name__ == '__main__':
    unittest.main()
