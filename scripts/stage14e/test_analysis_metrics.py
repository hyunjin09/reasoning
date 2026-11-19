import unittest
from scripts.stage14e.analysis_metrics import accuracy, acquisition


class Metrics(unittest.TestCase):
    def records(self):
        return [dict(family_id=f, item_id=f, arm=a, stratum='x', correct=value)
                for f, values in [('1', [True, True, False]), ('2', [False, True, True]),
                                  ('3', [None, None, True]), ('4', [False, False, None])]
                for a, value in zip(['N', 'S', 'M'], values)]

    def test_missingness_not_recast_as_wrong(self):
        result = accuracy(self.records(), ['1', '2', '3', '4'])
        self.assertEqual(result['arms']['M']['wrong'], 1)
        self.assertEqual(result['arms']['M']['unscorable'], 1)
        self.assertEqual(result['arms']['M']['accuracy_missingness_bounds'], [.5, .75])
        pair = result['pairs']['M-N']
        self.assertEqual(pair['paired_scorable'], 2)
        self.assertEqual(pair['rescue'], 1)
        self.assertEqual(pair['regression'], 1)
        self.assertEqual(pair['paired_accuracy_difference'], 0)

    def test_duplicate_rejected(self):
        records = self.records()
        with self.assertRaises(AssertionError):
            accuracy(records + [records[0]], ['1', '2', '3', '4'])

    def test_missing_assignment_rejected(self):
        with self.assertRaises(AssertionError):
            accuracy(self.records()[:-1], ['1', '2', '3', '4'])

    def test_abstention_and_known_evidence_not_success(self):
        rows = [dict(family_id=str(i), condition='M', label=label)
                for i, label in enumerate(['U', 'R', 'K', 'W', '?', 'I', 'A', 'X'])]
        result = acquisition(rows, [str(i) for i in range(8)], ['x']*8, ['M'])['arms']['M']
        self.assertEqual(result['assigned'], 8)
        self.assertEqual(result['attempted'], 7)
        self.assertEqual(result['useful_correct'], 2)
        self.assertEqual(result['useful_correct_fraction'], .25)

    def test_noimage_not_called_visual_success(self):
        result = acquisition([dict(family_id='1', condition='M_noimage', label='U')],
                             ['1'], ['x'], ['M_noimage'])
        self.assertIn('not visual acquisition', result['arms']['M_noimage']['interpretation'])


if __name__ == '__main__':
    unittest.main()
