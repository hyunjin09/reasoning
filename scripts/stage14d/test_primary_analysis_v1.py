import unittest

from scripts.stage14d.primary_analysis_v1 import summarize, validate_rows


class PrimaryAnalysisTest(unittest.TestCase):
    def test_missing_member_retains_known_outcome_and_planned_denominator(self):
        families = ['a', 'b', 'c']
        rows = [dict(family_id='a', model='T', arm='LOOK_TARGET', answer='CORRECT', evidence='EXPLICIT_CORRECT'),
                dict(family_id='a', model='T', arm='LOOK_GENERIC', answer='WRONG', evidence='NOT_DEMONSTRATED'),
                dict(family_id='b', model='T', arm='LOOK_TARGET', answer='TECHNICAL_MISSING', evidence='TECHNICAL_MISSING'),
                dict(family_id='b', model='T', arm='LOOK_GENERIC', answer='CORRECT', evidence='EXPLICIT_CORRECT')]
        r = summarize(rows, families, 'T', 'S1', 'P1', 'answer', 'LOOK_TARGET', 'LOOK_GENERIC')
        self.assertEqual(r['complete_pairs'], 1)
        self.assertEqual(r['bounds'], [-1/3, 2/3])
        self.assertEqual(r['effect'], 1)
        self.assertEqual(r['transitions']['CORRECT->WRONG'], 0)
        self.assertEqual(r['transitions']['WRONG->CORRECT'], 1)

    def test_wrong_rate_direction_is_preserved(self):
        rows = [dict(family_id='a', model='T', arm='LOOK_TARGET', answer='WRONG', evidence='NOT_DEMONSTRATED'),
                dict(family_id='a', model='T', arm='B0', answer='CORRECT', evidence='EXPLICIT_CORRECT')]
        r = summarize(rows, ['a'], 'T', 'S3', 'P3', 'answer', 'LOOK_TARGET', 'B0', wrong_rate=True)
        self.assertEqual(r['effect'], 1)
        self.assertEqual(r['transitions']['CORRECT->WRONG'], 1)

    def test_duplicate_family_arm_and_unknown_labels_fail(self):
        row = dict(family_id='a', model='T', arm='B0', answer='WRONG', evidence='NOT_DEMONSTRATED')
        with self.assertRaises(ValueError):
            validate_rows([row, row])
        with self.assertRaises(ValueError):
            validate_rows([dict(row, answer='CAP_HIT_IS_WRONG')])

    def test_evidence_absence_is_observed_zero_not_missing(self):
        rows = [dict(family_id='a', model='T', arm='LOOK_TARGET', answer='WRONG', evidence='NOT_DEMONSTRATED'),
                dict(family_id='a', model='T', arm='LOOK_GENERIC', answer='WRONG', evidence='PARTIAL_OR_APPROXIMATE')]
        r = summarize(rows, ['a'], 'T', 'S1', 'P2', 'evidence', 'LOOK_TARGET', 'LOOK_GENERIC')
        self.assertEqual(r['complete_pairs'], 1)
        self.assertEqual(r['effect'], 0)


if __name__ == '__main__':
    unittest.main()
