import unittest
from scripts.stage12cr.inference import endpoint,transition,infer
class InferenceTests(unittest.TestCase):
 def test_missing_outcome_not_wrong(self):
  r=endpoint([{'c':True},{'c':False},{'c':None}]);self.assertEqual(r['denominator'],2);self.assertEqual(r['missingness_identification_bounds'],[1/3,2/3])
  self.assertEqual(transition(False,None),'UNSCOREABLE_TECHNICAL')
 def test_same_checkpoint_pairing_and_selectivity(self):
  rows=[dict(family_id=str(i),bottleneck='B1' if i<11 else 'B4',c=i<6,n=False,e_has_incorrect_atom=True) for i in range(22)]
  r=infer(rows,draws=100);self.assertEqual(r['decision'],'COT_RESCUE_INFORMATIVE');self.assertEqual(r['primary']['A-P3']['estimate'],6/11)
  self.assertEqual(r['overall_paired']['counts']['RESCUE'],6)
if __name__=='__main__':unittest.main()
