import unittest
from scripts.stage14d1_pilot.accounting import budget_amounts
class AccountingTests(unittest.TestCase):
    def test_missing_or_delayed_accounting_preserves_full_reservation(self):
        for raw in ['', '\n', 'x|RUNNING|bad|gres/gpu=1']:
            self.assertEqual(budget_amounts(raw,1800),(0,1800))
    def test_pending_cancel_and_completion(self):
        self.assertEqual(budget_amounts('x|PENDING|0|',1800),(0,1800))
        self.assertEqual(budget_amounts('x|CANCELLED by 1|0|',1800),(0,0))
        self.assertEqual(budget_amounts('x|COMPLETED|499|cpu=1,gres/gpu=1',1800),(499,0))
    def test_running_reserves_unspent_maximum(self):
        self.assertEqual(budget_amounts('x|RUNNING|99|gres/gpu=1',1800),(99,1701))
    def test_impossible_charge_does_not_create_budget(self):
        with self.assertRaises(ValueError):budget_amounts('x|RUNNING|1900|gres/gpu=1',1800)
if __name__=='__main__':unittest.main()
