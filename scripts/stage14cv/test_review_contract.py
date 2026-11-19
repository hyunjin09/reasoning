"""Frozen source granularity, literal provenance and missingness safeguards."""
import copy
import unittest
from scripts.stage14cv.c_review import validate_decision
from scripts.stage14c.d1_scoring_v2 import metrics


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.target = dict(atoms=[dict(subfact_count=5, subfact_keys=list('abcde'))])
        self.review = dict(status='SCORED', reason='Response reviewed against source.',
            atoms=[dict(exact=False, recovered_units=['a'], evidence_quotes=['blue above red'])],
            claims=[dict(text='blue above red', binding='left', classification='required',
                         target_atom=0, target_unit=0)])

    def test_partial_recovery_does_not_become_full_atom(self):
        validate_decision(self.target, self.review, 'At left: blue above red.')
        result = metrics(self.target, self.review)
        self.assertEqual(result['subfact_recall'], .2)
        self.assertFalse(result['full_E_star_recovery'])

    def test_unmatched_true_fact_counts_in_precision_denominator(self):
        self.review['claims'].append(dict(text='white background', classification='accurate_irrelevant'))
        validate_decision(self.target, self.review, 'blue above red; white background')
        self.assertEqual(metrics(self.target, self.review)['targeted_precision'], .5)

    def test_invented_quote_or_source_unit_rejected(self):
        with self.assertRaises(AssertionError):
            validate_decision(self.target, self.review, 'no matching quote')
        self.review['atoms'][0]['recovered_units'] = ['unfrozen fact']
        with self.assertRaises(AssertionError):
            validate_decision(self.target, self.review, 'blue above red')

    def test_unresolved_has_no_zero_recovery_imputation(self):
        result = metrics(self.target, dict(status='UNRESOLVED', reason='Unclosed Thinking.'))
        self.assertEqual(result, {'status': 'UNRESOLVED'})

    def test_duplicate_bound_fact_rejected(self):
        self.review['claims'].append(copy.deepcopy(self.review['claims'][0]))
        with self.assertRaises(AssertionError):
            validate_decision(self.target, self.review, 'blue above red')


if __name__ == '__main__':
    unittest.main()
