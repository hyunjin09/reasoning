import unittest
from scripts.stage14cv.operational_v2 import admit_wave, check_amended_budget


class DeadlineTests(unittest.TestCase):
    def test_drain_before_thinking_r_deadline(self):
        self.assertFalse(admit_wave(2699, 'T', 'R', []))
        self.assertTrue(admit_wave(7200, 'T', 'R', []))

    def test_observed_slow_wave_increases_drain_margin(self):
        self.assertFalse(admit_wave(3000, 'T', 'R', [2400]))

    def test_preflight_and_c_have_their_own_operational_margin(self):
        self.assertTrue(admit_wave(1500, 'T', 'technical', []))
        self.assertFalse(admit_wave(1000, 'T', 'C', []))
        self.assertTrue(admit_wave(1500, 'I', 'C', []))

    def test_new_limit_is_still_a_hard_limit(self):
        self.assertEqual(check_amended_budget([23.5283], [3, 4, 1]),31.5283)
        with self.assertRaises(ValueError):
            check_amended_budget([31], [2])


if __name__ == '__main__':
    unittest.main()
