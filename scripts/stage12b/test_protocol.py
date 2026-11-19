import unittest
from scripts.stage12b.protocol import build_prompt, technical_gate, profile, authorize_manifest


class ProtocolTest(unittest.TestCase):
    def test_prompts_preserve_source_and_no_solution_instruction(self):
        row = dict(question='Original?\nOptions:\nA. 1', facts=[dict(probe_request='Which angle?', gold_value='70 degrees')])
        self.assertEqual(build_prompt(row, 'N'), row['question'])
        self.assertIn('Which angle?', build_prompt(row, 'E'))
        self.assertNotIn('70 degrees', build_prompt(row, 'E'))
        oracle = build_prompt(row, 'O')
        self.assertIn('E1: Which angle? 70 degrees', oracle)
        self.assertTrue(oracle.endswith(row['question']))

    def test_gate_exact_boundaries(self):
        rr = {a: [dict(parseable=True, committed_final=True, cap_hit=False, repetition_pathology=False) for _ in range(12)] for a in 'ENO'}
        self.assertTrue(technical_gate(rr)['pass'])
        rr['O'][0]['cap_hit'] = True
        self.assertTrue(technical_gate(rr)['pass'])
        rr['O'][1]['cap_hit'] = True
        self.assertFalse(technical_gate(rr)['pass'])
        rr['O'][1]['cap_hit'] = False
        for i in range(3): rr['E'][i]['parseable'] = False
        self.assertFalse(technical_gate(rr)['pass'])

    def test_taxonomy_and_technical_exclusions(self):
        for e, o, expected in [(False, True, 'B1'), (True, True, 'B2'), (True, False, 'B3'), (False, False, 'B4')]:
            self.assertEqual(profile(e, False, o), expected)
            self.assertIsNone(profile(e, True, o))
        self.assertIsNone(profile(None, False, True))
        self.assertIsNone(profile(False, None, True))

    def test_image_free_oracle_fails_closed(self):
        with self.assertRaises(AssertionError):
            authorize_manifest(dict(phase='technical', rows=[dict(arm='O', image='bad.jpg')]), gate=True, integrity=True)
        with self.assertRaises(AssertionError):
            authorize_manifest(dict(phase='main', rows=[]), gate=False, integrity=True)


if __name__ == '__main__': unittest.main()
