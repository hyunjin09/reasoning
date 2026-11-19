import unittest
from scripts.stage12c.inference import endpoint, paired, infer


class MissingnessAndPairing(unittest.TestCase):
    def test_missing_is_neither_failure_nor_discordance(self):
        rows=[dict(c=True,t=None),dict(c=False,t=True),dict(c=None,t=False)]
        e=endpoint(rows,'c')
        self.assertEqual((e['numerator'],e['denominator'],e['missing']),(1,2,1))
        self.assertEqual(e['missingness_identification_bounds'],[1/3,2/3])
        p=paired(rows,'c','t')
        self.assertEqual((p['jointly_scoreable'],p['second_only'],p['missing_pairs']),(1,1,2))

    def test_paired_bootstrap_perfect_arm_agreement(self):
        rows=[dict(family_id=str(i),bottleneck='B1' if i<4 else 'B4',
                   c=bool(i%2),t=bool(i%2),n=False,e_has_incorrect_atom=True) for i in range(8)]
        result=infer(rows,draws=100,seed=2)
        self.assertEqual(result['contrasts']['overall_t_minus_c']['percentile95'],[0.0,0.0])
        self.assertEqual(result['contrasts']['t_minus_c_B1']['percentile95'],[0.0,0.0])
        self.assertEqual(result['primary']['P1']['numerator'],2)


if __name__=='__main__': unittest.main()
