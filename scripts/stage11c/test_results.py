import unittest
from scripts.stage11c.results import grade_literal

class LiteralScoring(unittest.TestCase):
    def test_literal_scores_and_unknowns_are_distinct(self):
        source = dict(options=['3', '4', '6'], answer='B')
        self.assertTrue(grade_literal('4', source)['correct'])
        self.assertTrue(grade_literal('(B)', source)['correct'])
        self.assertFalse(grade_literal('A', source)['correct'])
        self.assertIsNone(grade_literal('not a committed option', source)['correct'])
        self.assertEqual(grade_literal(None, source), dict(correct=False, answer_status='NO_COMMITTED_FINAL'))
        self.assertTrue(grade_literal('0.5', dict(options=[], answer='1/2'))['correct'])
        self.assertIsNone(grade_literal('x', dict(options=[], answer='1/2'))['correct'])

if __name__ == '__main__':
    unittest.main()
