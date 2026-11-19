import unittest
from scripts.stage14e2.analyze import summarize, ARMS


class AnalysisTests(unittest.TestCase):
    def records(self):
        return [dict(item_id=f, condition=a, source_stratum='global', label='K',
                     coverage='partial', status='VALID') for f in ['1', '2'] for a in ARMS]

    def test_missing_cap_and_absence_remain_in_denominator(self):
        rows = self.records()
        for r in rows:
            if r['condition'] == 'T_T':
                r['label'] = 'R' if r['item_id'] == '1' else 'X'
            if r['condition'] == 'O_C':
                r['label'] = 'A'
        out = summarize(rows, ['1', '2'])
        self.assertEqual(out['arms']['T_T']['rate'], .5)
        self.assertEqual(out['arms']['O_C']['attempted'], 0)
        self.assertEqual(out['pairs']['T_T-T_C']['gains'], ['1'])
        self.assertEqual(out['pairs']['T_T-T_C']['difference'], .5)

    def test_reject_missing_or_duplicate_assignments(self):
        rows = self.records()
        with self.assertRaises(AssertionError): summarize(rows[:-1], ['1', '2'])
        with self.assertRaises(AssertionError): summarize(rows + rows[:1], ['1', '2'])

    def test_noimage_interpretation_and_repeatable_intervals(self):
        out = summarize(self.records(), ['1', '2'])
        self.assertIn('not visual acquisition', out['arms']['T_N']['interpretation'])
        self.assertEqual(out, summarize(self.records(), ['1', '2']))


if __name__ == '__main__': unittest.main()
