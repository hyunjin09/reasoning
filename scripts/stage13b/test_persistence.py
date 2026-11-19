import unittest
from scripts.stage13b.inference import effects


class LiteralPersistenceGate(unittest.TestCase):
    def test_section20_does_not_add_section17_five_point_threshold(self):
        rows=[dict(family_id=str(f),scale=s,condition='EQ',I=[0,0,0],
                   T=[int(f<6),0,0] if s=='2B' else [1,1,1],T_before32k=[True]*3)
              for f in range(48) for s in ['2B','4B','8B']]
        out=effects(rows)
        self.assertNotIn('SMALL_VLM_POST_EVIDENCE_GAIN',out['states'])
        self.assertGreater(out['scales']['2B']['EQ']['ci95_pp'][0],0)
        self.assertIn('POST_EVIDENCE_GAIN_ACROSS_SCALES',out['states'])


if __name__=='__main__':unittest.main()
