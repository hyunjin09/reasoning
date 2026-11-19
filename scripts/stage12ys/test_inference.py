import unittest
from scripts.stage12ys.inference import descriptive, confirm_families, transfer

class InferenceTests(unittest.TestCase):
    def test_attenuation_uses_four_arm_common_denominator(self):
        rows=[dict(I_img=False,T_img=True,I_E=False,T_E=True,E_I=False,E_T=True),
              dict(I_img=False,T_img=True,I_E=None,T_E=False,E_I=None,E_T=True)]
        d=descriptive(rows)
        self.assertEqual(d['G_img']['n'],2)
        self.assertEqual(d['A_evidence']['n'],1)
        self.assertEqual(d['A_evidence']['estimate'],0)

    def test_missing_majority_not_downstream_failure(self):
        rows=[dict(item_id='x',arm=a,replicate=k,correct=v) for a,vs in [('I_E',[False,False,None]),('T_E',[True,None,False])] for k,v in enumerate(vs)]
        r=confirm_families(['x'],rows)[0]
        self.assertIsNone(r['downstream'])
        self.assertIs(r['I_E'],False)

    def test_transfer_needs_baseline_and_shuffle_failure(self):
        rows=[dict(item_id='x',arm=a,replicate=k,correct=v) for a,vs in [('RT_T',[True]*5),('RT_I',[True]*5),('Q_I',[False]*5),('SH_I',[False,False,None,None,None])] for k,v in enumerate(vs)]
        r=transfer(['x'],rows)[0]
        self.assertIsNone(r['state_support'])
        self.assertFalse(r['controls_resolved'])

if __name__=='__main__':unittest.main()
