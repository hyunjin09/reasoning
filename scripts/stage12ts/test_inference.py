import unittest
from scripts.stage12ts.inference import infer,endpoint,paired

class InferenceTests(unittest.TestCase):
    def test_missingness_is_not_wrong(self):
        rr=[dict(t=True,c=False),dict(t=False,c=True),dict(t=None,c=False)]
        p=endpoint(rr);self.assertEqual((p['numerator'],p['denominator'],p['frozen_total'],p['missing']),(1,2,3,1))
        self.assertEqual(p['missingness_identification_bounds'],[1/3,2/3])
        self.assertEqual(paired(rr)['counts'],dict(BOTH_WRONG=0,FIRST_ONLY=1,THINKING_ONLY=1,BOTH_CORRECT=0,UNSCOREABLE_TECHNICAL=1))
    def test_empty_sensitivity_is_undefined(self):
        r=infer([],draws=20)
        self.assertIsNone(r['primary']['T-P1']['estimate']);self.assertIsNone(r['primary']['T-P3']['percentile95'])
    def test_full_trace_alone_is_not_thinking_only_rescue(self):
        rr=[dict(family_id=str(i),bottleneck='B1' if i<3 else 'B4',t=True,c=[False,True,None,False][i],n=False,T_trace='TRACE_E_FULL',C_trace='TRACE_E_WRONG_OR_CONFLICTING',e_has_incorrect_atom=True) for i in range(4)]
        r=infer(rr,draws=20)
        self.assertEqual(r['evidence_B1']['evidence_linked_rescues'],3)
        self.assertEqual(r['evidence_B1']['thinking_only_evidence_recovery_rescues'],1)
        self.assertEqual(r['overall']['common_joint_n'],3)

if __name__=='__main__':unittest.main()
