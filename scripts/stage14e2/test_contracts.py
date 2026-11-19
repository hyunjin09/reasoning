import unittest
from scripts.stage14e2.contracts import helper_boundary, parse_readout

VALID = '{"target":"grid","read_value":"unknown","supporting_source":"unreadable","uncertainty":"unresolvable"}'


class ReadoutContracts(unittest.TestCase):
    def test_only_declared_boundary_changes(self):
        prompt = 'original image and prefix<assistant><think>\n'
        self.assertEqual(helper_boundary(prompt, 'thinking'), prompt)
        self.assertEqual(helper_boundary(prompt, 'compact'), prompt + '</think>\n\n')

    def test_unknown_mode_or_wrong_template_rejected(self):
        for prompt, mode in [('text', 'thinking'), ('<think>\n', 'typo')]:
            with self.assertRaises(ValueError):
                helper_boundary(prompt, mode)

    def test_only_committed_thinking_final_is_read(self):
        raw = VALID + '\n</think>\n' + VALID
        self.assertEqual(parse_readout(raw, 'thinking', False)['status'], 'VALID')
        self.assertEqual(parse_readout(VALID, 'thinking', False)['status'], 'NO_COMMITTED_FINAL')

    def test_compact_final_is_direct_json(self):
        self.assertEqual(parse_readout(VALID, 'compact', False)['parsed']['uncertainty'], 'unresolvable')

    def test_code_fence_allowed_only_for_one_final_object(self):
        self.assertEqual(parse_readout('```json\n' + VALID + '\n```', 'compact', False)['status'], 'VALID')
        self.assertEqual(parse_readout(VALID + '\n' + VALID, 'compact', False)['status'], 'INVALID_JSON')

    def test_cap_hit_not_mined_for_success(self):
        result = parse_readout('thinking</think>' + VALID, 'thinking', True)
        self.assertEqual(result['status'], 'CAPPED')
        self.assertIsNone(result['parsed'])

    def test_duplicate_keys_rejected(self):
        raw = VALID.replace('"target":"grid"', '"target":"grid","target":"invented"')
        self.assertEqual(parse_readout(raw, 'compact', False)['status'], 'INVALID_JSON')

    def test_unexpected_fields_not_silently_discarded(self):
        raw = VALID[:-1] + ',"final_answer":"A"}'
        self.assertEqual(parse_readout(raw, 'compact', False)['status'], 'INVALID_SCHEMA')

    def test_wrong_types_and_uncertainty_rejected(self):
        for raw in [VALID.replace('"unknown"', 'null'), VALID.replace('"unresolvable"', '"guaranteed"')]:
            self.assertEqual(parse_readout(raw, 'compact', False)['status'], 'INVALID_SCHEMA')

    def test_reasoning_text_never_promoted_to_final(self):
        self.assertEqual(parse_readout(VALID + '</think> No readable evidence.', 'thinking', False)['status'], 'INVALID_JSON')


if __name__ == '__main__':
    unittest.main()
