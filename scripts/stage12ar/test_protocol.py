import unittest
from scripts.stage12ar.protocol import select_validation, gate, select_candidate, build_prompt


class ProtocolTests(unittest.TestCase):
    def test_validation_ignores_outcomes_and_is_disjoint_and_order_invariant(self):
        rows = [dict(item_id=str(i), family_id=f'family_{i}', answer_type='multiple_choice' if i % 3 == 0 else 'open_ended') for i in range(61)]
        a = select_validation(rows, [str(i) for i in range(12)])
        b = select_validation([dict(r, answer='changed', difficulty=99, subject='changed') for r in reversed(rows)], [str(i) for i in range(12)])
        self.assertEqual(a, b)
        self.assertEqual(len(set(a)), 12)
        self.assertFalse(set(a) & set(str(i) for i in range(12)))
        self.assertTrue(4 <= sum(rows[int(i)]['answer_type'] == 'multiple_choice' for i in a) <= 6)

    def test_d_must_fail_even_with_twelve_finals_if_two_show_reasoning(self):
        rows = [dict(format_valid=True, visible_reasoning=False, committed_final=True, cap_hit=False, severe_repetition=False, tokens=2) for _ in range(12)]
        self.assertTrue(gate('D', rows)['pass'])
        rows[0]['visible_reasoning'] = rows[1]['visible_reasoning'] = True
        self.assertFalse(gate('D', rows)['pass'])

    def test_c_requires_visible_reasoning_and_bounded_caps(self):
        rows = [dict(format_valid=True, visible_reasoning=True, committed_final=True, cap_hit=False, severe_repetition=False, tokens=200) for _ in range(12)]
        self.assertTrue(gate('C0', rows)['pass'])
        for r in rows: r['visible_reasoning'] = False
        self.assertFalse(gate('C0', rows)['pass'])

    def test_selection_is_lexicographic_without_correctness(self):
        base = dict(n=12, format_valid=12, visible_reasoning=12, committed_final=12, cap_hit=0, severe_repetition=0, median_tokens=500)
        candidates = {'C0': {'pass': True, 'summary': dict(base)}, 'C1': {'pass': True, 'summary': dict(base, median_tokens=100)}}
        self.assertEqual(select_candidate(candidates), 'C1')
        candidates['C1']['summary']['severe_repetition'] = 1
        self.assertEqual(select_candidate(candidates), 'C0')
        candidates['C1']['summary'] = dict(base)
        self.assertEqual(select_candidate(candidates), 'C0')
        for r in candidates.values(): r['pass'] = False
        self.assertIsNone(select_candidate(candidates))

    def test_prompts_preserve_original_question_and_native_types(self):
        q = 'Original question\nwith untouched formatting.'
        mc = dict(question=q, answer_type='multiple_choice')
        op = dict(question=q, answer_type='open_ended')
        self.assertEqual(build_prompt(mc, 'C0'), q + "\n\nLet's think step by step.")
        self.assertIn('exactly one option letter: A, B, C, D, or E.', build_prompt(mc, 'D'))
        self.assertIn('exactly one final value or mathematical expression.', build_prompt(op, 'D'))
        self.assertTrue(build_prompt(op, 'C1').startswith(q + '\n\n'))


if __name__ == '__main__':
    unittest.main()
