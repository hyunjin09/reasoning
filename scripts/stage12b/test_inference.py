import unittest
from scripts.stage12b.inference import infer


class InferenceTest(unittest.TestCase):
    def test_no_native_failures_is_undefined_conditional(self):
        r = infer([dict(family_id=str(i), e=True, n=True, o=True) for i in range(3)], draws=30)
        self.assertEqual(r['endpoints']['P1']['estimate'], 0)
        self.assertIsNone(r['endpoints']['P2']['estimate'])
        self.assertEqual(r['decision'], 'PROFILE_SPARSE')

    def test_four_classes_and_technical_exclusion(self):
        rows = [dict(family_id=str(i), e=i%2==0, n=False, o=i%4<2) for i in range(20)]
        rows.append(dict(family_id='missing', e=None, n=False, o=True))
        r = infer(rows, draws=30)
        self.assertEqual(r['classes'], dict(B1=5, B2=5, B3=5, B4=5))
        self.assertEqual(r['endpoints']['P1']['denominator'], 21)
        self.assertEqual(r['endpoints']['P2']['denominator'], 20)
        self.assertAlmostEqual(sum(r['endpoints'][f'P{i}']['estimate'] for i in range(3,7)), 1)
        self.assertEqual(r['decision'], 'PROFILE_INFORMATIVE')

    def test_reject_duplicate_families(self):
        with self.assertRaises(AssertionError):
            infer([dict(family_id='same', e=True, n=False, o=True)]*2, draws=30)


if __name__ == '__main__': unittest.main()
