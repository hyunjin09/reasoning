import unittest
from scripts.stage14d1_pilot.family_recovery_v8 import family_policy
class FamilyPolicyTests(unittest.TestCase):
    def test_complete_family_keeps_all_valid_receipts(self):
        self.assertEqual(family_policy({'N','G'},{'N':'oldN','G':'oldG'}),({'N':'oldN','G':'oldG'},set()))
    def test_partial_family_never_mixes_batch_schedules(self):
        self.assertEqual(family_policy({'N','G','QI'},{'QI':'oldQI'}),({}, {'N','G','QI'}))
    def test_empty_family_gets_all_conditions(self):
        self.assertEqual(family_policy({'N','G'},{}),({}, {'N','G'}))
    def test_foreign_receipt_rejected(self):
        with self.assertRaises(ValueError):family_policy({'N'},{'other':'wrong'})
