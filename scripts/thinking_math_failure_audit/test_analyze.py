import unittest

from scripts.thinking_math_failure_audit.analyze import (
    status_counts, pair_transitions, literal_flags, question_tags, evidence_state,
    cluster_arrays,
)


class AuditTests(unittest.TestCase):
    def test_unscorable_is_not_wrong(self):
        result = status_counts([{'status': s} for s in ['CORRECT', 'WRONG', 'UNSCORABLE']])
        self.assertEqual(result['wrong'], 1)
        self.assertEqual(result['scored'], 2)
        self.assertEqual(result['wrong_rate'], .5)

    def test_seed_and_family_pairing(self):
        rows = [dict(item_id='a', family_id='f', replicate=r, version=v, status=s)
                for r, v, s in [(0, 'Text Only', 'CORRECT'), (0, 'Vision Only', 'WRONG'),
                                 (1, 'Text Only', 'WRONG'), (1, 'Vision Only', 'CORRECT')]]
        result = pair_transitions(rows, 'Text Only', 'Vision Only')
        self.assertEqual(result['counts']['CORRECT__WRONG'], 1)
        self.assertEqual(result['counts']['WRONG__CORRECT'], 1)
        self.assertEqual(len(result['pairs']), 2)

    def test_quote_offsets_and_no_causal_label(self):
        text = "α. Since I can't see the image, let's assume a square."
        flags = literal_flags(text)
        self.assertTrue(flags['image_unavailable_statement'])
        self.assertTrue(flags['assumption_language'])
        for matches in flags.values():
            for match in matches:
                self.assertEqual(text[match['start']:match['end']], match['quote'])
        self.assertNotIn('ignored_image', flags)

    def test_question_tags_do_not_read_answers(self):
        self.assertIn('counting', question_tags('How many cubes are shown?'))
        self.assertIn('area', question_tags('Find the shaded area.'))
        self.assertEqual(question_tags('What is x?'), ['unspecified_in_question_text'])

    def test_incomplete_evidence_is_not_explicit_error(self):
        self.assertEqual(evidence_state('3'), 'INCOMPLETE_OR_AMBIGUOUS')
        self.assertEqual(evidence_state('2'), 'EXPLICIT_REQUIRED_SOURCE_ERROR')

    def test_family_counts_keep_aliases_together(self):
        rows = [dict(family_id=f, status=s) for f, s in [('a', 'WRONG'), ('a', 'CORRECT'), ('b', 'WRONG')]]
        arrays = cluster_arrays(rows)
        self.assertEqual(len(arrays['families']), 2)
        self.assertEqual(sorted(arrays['wrong'].tolist()), [1, 1])
        self.assertEqual(sorted(arrays['scored'].tolist()), [1, 2])


if __name__ == '__main__':
    unittest.main()
