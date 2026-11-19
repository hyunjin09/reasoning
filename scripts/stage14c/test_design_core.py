import unittest
import numpy as np
from scripts.stage14c.design_core import (
    select_families, score_final, panel, contrast, ratio_draws,
)


class SelectionTests(unittest.TestCase):
    def test_strata_and_input_order_do_not_change_cohort(self):
        rows = [dict(family_id=str(i), stratum='a' if i < 8 else 'b') for i in range(12)]
        a = select_families(rows, 6, 3, 'seed')
        self.assertEqual(a, select_families(rows[::-1], 6, 3, 'seed'))
        self.assertEqual(sum(r['stratum'] == 'a' for r in a['main']), 4)
        self.assertEqual(len(a['reserve']), 3)
        self.assertFalse({r['family_id'] for r in a['main']} & {r['family_id'] for r in a['reserve']})

    def test_duplicate_family_is_rejected_not_double_counted(self):
        with self.assertRaises(ValueError):
            select_families([dict(family_id='x', stratum='a')] * 2, 2, 0, 's')

    def test_smaller_population_is_not_padded(self):
        rows = [dict(family_id=str(i), stratum='a') for i in range(3)]
        result = select_families(rows, 1000, 250, 's')
        self.assertEqual(len(result['main']), 3)
        self.assertEqual(result['reserve'], [])


class AdapterTests(unittest.TestCase):
    def test_semantic_final_not_initial_reasoning_letter(self):
        self.assertEqual(score_final('C', 'C', 'choice', ['A', 'B', 'C']), 'CORRECT')
        self.assertEqual(score_final('At first A, finally C', 'C', 'choice', ['A', 'B', 'C']), 'REVIEW')
        self.assertEqual(score_final('D', 'C', 'choice', ['A', 'B', 'C']), 'REVIEW')

    def test_native_answer_types_and_missingness(self):
        self.assertEqual(score_final('{3}', '3', 'integer'), 'CORRECT')
        self.assertEqual(score_final('3.0', '3', 'integer'), 'REVIEW')
        self.assertEqual(score_final('False', 'no', 'yes_no'), 'CORRECT')
        self.assertEqual(score_final('a', 'A', 'letter'), 'CORRECT')
        self.assertEqual(score_final('(3, 4)', '(4, 3)', 'ordered_pair'), 'WRONG')
        self.assertEqual(score_final(None, '3', 'integer'), 'UNSCORABLE')
        self.assertEqual(score_final('(3, 4', '(3, 4)', 'ordered_pair'), 'REVIEW')

    def test_bad_gold_is_source_issue(self):
        self.assertEqual(score_final('3', 'banana', 'integer'), 'SOURCE_REVIEW')


def row(family, native, equal):
    return dict(family_id=family, item_id=family, native=native, equal=equal)


class EstimandTests(unittest.TestCase):
    def test_rescue_regression_and_missing_bounds(self):
        rows = [row('a', 'WRONG', 'CORRECT'), row('b', 'CORRECT', 'WRONG'),
                row('c', 'WRONG', 'WRONG'), row('d', 'WRONG', 'UNSCORABLE'),
                row('e', 'TECHNICAL_MISSING', 'CORRECT')]
        p = panel(rows, 'native', 'equal', draws=200, stream='fixture')
        self.assertEqual(p['paired_n'], 3)
        self.assertAlmostEqual(p['difference_pp'], 0)
        self.assertEqual(p['difference_bounds_pp'], [0, 40])
        self.assertEqual(p['rescue']['numerator'], 1)
        self.assertEqual(p['rescue']['scored_denominator'], 2)
        self.assertEqual(p['rescue']['unresolved_followups'], 1)
        np.testing.assert_allclose(p['rescue']['bounds_pp'], [100/3, 200/3])
        self.assertEqual(p['counts_left']['TECHNICAL_MISSING'], 1)
        self.assertEqual(p['counts_right']['UNSCORABLE'], 1)
        self.assertEqual(sum(p['transitions'].values()), 5)
        self.assertEqual(p['marginal_left']['accuracy_pp'], 25)
        self.assertEqual(p['marginal_right']['accuracy_pp'], 50)
        self.assertEqual(p['marginal_right']['residual_error_pp'], 50)
        self.assertEqual(p['marginal_right']['residual_error_bounds_pp'], [40, 60])
        cells = p['paired_transition_fraction_family_equal']
        self.assertAlmostEqual(p['difference_pp'], 100 * (cells['WRONG__CORRECT'] - cells['CORRECT__WRONG']))

    def test_family_equal_weighting_prevents_large_family_domination(self):
        rows = [dict(family_id='large', item_id=str(i), native='WRONG', equal='CORRECT') for i in range(9)]
        rows += [row('small', 'CORRECT', 'WRONG')]
        p = panel(rows, 'native', 'equal', draws=100, stream='weights')
        self.assertAlmostEqual(p['difference_pp'], 0)
        self.assertAlmostEqual(p['item_difference_pp'], 80)
        self.assertEqual(p['independent_units'], 2)

    def test_unsupported_labels_and_duplicate_items_fail_closed(self):
        with self.assertRaises(ValueError):
            panel([row('x', 'MISSING', 'WRONG')], 'native', 'equal')
        with self.assertRaises(ValueError):
            panel([row('x', 'CORRECT', 'WRONG')] * 2, 'native', 'equal')

    def test_no_scored_native_wrong_is_not_zero_rescue(self):
        p = panel([row('x', 'CORRECT', 'CORRECT')], 'native', 'equal', draws=20)
        self.assertIsNone(p['rescue']['estimate_pp'])
        self.assertIsNone(p['rescue']['bounds_pp'])
        self.assertIsNone(p['rescue']['ci95_pp'])

    def test_opposite_constant_tasks_have_known_contrast(self):
        a = panel([row('a', 'WRONG', 'CORRECT')], 'native', 'equal', draws=30, stream='math')
        b = panel([row('b', 'CORRECT', 'WRONG')], 'native', 'equal', draws=30, stream='vqa')
        c = contrast(a, b, 'difference')
        self.assertEqual(c['estimate_pp'], 200)
        self.assertEqual(c['ci95_pp'], [200, 200])
        self.assertEqual(c['bounds_pp'], [200, 200])

    def test_bootstrap_is_repeatable_and_task_streams_are_independent(self):
        a = ratio_draws([0, 1, 1], [1, 1, 1], 100, 'math')
        np.testing.assert_array_equal(a, ratio_draws([0, 1, 1], [1, 1, 1], 100, 'math'))
        self.assertFalse(np.array_equal(a, ratio_draws([0, 1, 1], [1, 1, 1], 100, 'vqa')))

    def test_tiny_wrong_denominator_is_flagged_without_adding_cases(self):
        rows = [row('failed', 'WRONG', 'CORRECT')]
        rows += [row(str(i), 'CORRECT', 'CORRECT') for i in range(99)]
        a = panel(rows, 'native', 'equal', draws=400, stream='math')
        b = panel(rows, 'native', 'equal', draws=400, stream='vqa')
        self.assertEqual(contrast(a, b, 'rescue')['status'], 'UNSTABLE_BOOTSTRAP')


if __name__ == '__main__':
    unittest.main()
