import unittest
from scripts.stage13b.inference import effects


class PairedInferenceTests(unittest.TestCase):
    def rows(self):
        return [dict(family_id=str(f),scale=s,condition=c,I=[0,0,0],T=[1,1,1],T_before32k=[True]*3)
                for f in range(48) for s in ['2B','4B','8B'] for c in ['EQ','img']]

    def test_identical_gaps_have_zero_attenuation_and_interaction(self):
        out=effects(self.rows())
        self.assertEqual(out['R_shift']['effect_pp'],0)
        self.assertEqual(out['R_shift']['ci95_pp'],[0,0])
        self.assertIn('SMALL_VLM_POST_EVIDENCE_GAIN',out['states'])
        self.assertNotIn('SCALE_ROLE_SHIFT',out['states'])
        self.assertEqual(out['scales']['2B']['A']['n'],48)

    def test_interaction_uses_same_complete_families_and_missing_bounds(self):
        rows=self.rows()
        for r in rows:
            if r['scale']=='8B' and r['condition']=='img' and int(r['family_id'])<13:r['T'][0]=None
        out=effects(rows)
        self.assertEqual(out['R_shift']['n'],35)
        self.assertEqual(out['scales']['2B']['EQ']['n'],48)
        b=out['missingness']['8B_img']
        self.assertAlmostEqual(b['lower_pp'],100*(144-13)/144)
        self.assertEqual(b['upper_pp'],100)

    def test_thinking_32k_excludes_family_without_changing_primary(self):
        rows=self.rows()
        for r in rows:
            if r['scale']=='2B' and r['condition']=='EQ' and r['family_id']=='0':r['T_before32k'][1]=False
        out=effects(rows)
        self.assertEqual(out['scales']['2B']['EQ']['n'],48)
        self.assertEqual(out['sensitivity']['2B_EQ']['n'],47)


if __name__=='__main__':unittest.main()
