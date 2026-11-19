import unittest
from scripts.stage12ar.decision import decide


class DecisionTests(unittest.TestCase):
    def test_failed_d_stops_without_c_or_validation(self):
        self.assertEqual(decide({'pass': False}, None, None), 'D_INVALID')

    def test_no_passing_c_stops_without_validation(self):
        self.assertEqual(decide({'pass': True}, {'C0': {'pass': False}, 'C1': {'pass': False}}, None), 'C_INVALID')

    def test_development_success_does_not_imply_validation(self):
        with self.assertRaises(AssertionError):
            decide({'pass': True}, {'C0': {'pass': True}}, None)

    def test_fresh_failure_is_contract_unstable(self):
        self.assertEqual(decide({'pass': True}, {'C0': {'pass': True}}, {'D': {'pass': False}, 'C0': {'pass': True}}), 'CONTRACT_UNSTABLE')

    def test_both_validation_arms_required(self):
        self.assertEqual(decide({'pass': True}, {'C1': {'pass': True}}, {'D': {'pass': True}, 'C1': {'pass': True}}), 'CONTRACT_VALID')


if __name__ == '__main__': unittest.main()
