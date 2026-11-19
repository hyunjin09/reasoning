import unittest
from scripts.stage11c.inference_core import paired_estimates


class FamilyInference(unittest.TestCase):
    def test_gap_closure_preserves_pairing_and_rejects_pseudoreplication(self):
        rows = [dict(family_id=str(i), native_thinking=True, native_direct=False,
                     oracle_thinking=True, oracle_direct=True) for i in range(80)]
        result = paired_estimates(rows)
        self.assertEqual(result['endpoints']['P1_native_gap']['ci95'], [1., 1.])
        self.assertEqual(result['endpoints']['P2_oracle_gap']['ci95'], [0., 0.])
        self.assertEqual(result['endpoints']['P3_gap_closure']['ci95'], [1., 1.])
        self.assertEqual(result['closure_fraction'], 1.)
        with self.assertRaises(AssertionError):
            paired_estimates(rows+[rows[0]])
        rows[0]['oracle_thinking'] = None
        with self.assertRaisesRegex(AssertionError, 'imputation'):
            paired_estimates(rows)

    def test_identical_condition_gaps_have_zero_paired_closure_uncertainty(self):
        rows = [dict(family_id=str(i), native_thinking=i%2 == 0, native_direct=i%2 != 0,
                     oracle_thinking=i%2 == 0, oracle_direct=i%2 != 0) for i in range(80)]
        result = paired_estimates(rows)
        self.assertEqual(result['endpoints']['P3_gap_closure']['ci95'], [0., 0.])
        self.assertLess(result['endpoints']['P1_native_gap']['ci95'][0], 0)
        self.assertGreater(result['endpoints']['P1_native_gap']['ci95'][1], 0)
        self.assertIsNone(result['closure_fraction'])


if __name__ == '__main__':
    unittest.main()
