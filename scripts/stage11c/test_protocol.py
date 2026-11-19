import unittest
from scripts.stage11c.protocol import choose_cap, completion_gate, native_gate


class Gates(unittest.TestCase):
    def test_smallest_common_cap_and_strict_ten_percent(self):
        self.assertEqual(choose_cap({4096: (1, 1), 8192: (0, 0)}, 12)['cap'], 4096)
        self.assertEqual(choose_cap({4096: (2, 0), 8192: (1, 0)}, 12)['cap'], 8192)
        self.assertTrue(choose_cap({4096: (2, 0), 8192: (2, 0)}, 12)['completion_limited'])

    def test_completion_requires_matched_sixteen_and_missing_is_unknown(self):
        self.assertEqual(completion_gate([False]*15, [False]*16), 'INCOMPLETE')
        self.assertEqual(completion_gate([True]*4+[False]*12, [False]*16), 'PASS')
        self.assertEqual(completion_gate([True]*5+[False]*11, [False]*16), 'STOP')

    def test_native_gap_and_discordance_are_distinct(self):
        pairs=[(True,False)]*12+[(True,True)]*8+[(False,False)]*60
        self.assertTrue(native_gate(pairs, False)['pass'])
        pairs=[(True,False)]*12+[(False,True)]*8+[(True,True)]*12+[(False,False)]*48
        self.assertFalse(native_gate(pairs, False)['pass'])
        self.assertFalse(native_gate([(True,False)]*80, True)['pass'])


if __name__ == '__main__':
    unittest.main()
