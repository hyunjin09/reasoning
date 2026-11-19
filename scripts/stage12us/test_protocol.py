import unittest
from scripts.stage12us.protocol import canonical,seed,majority
from scripts.stage12us.inference import interpret,decision


class ProtocolTests(unittest.TestCase):
    def test_preserve_characters(self):
        self.assertEqual(canonical('<think>  a\n\\frac{1}{2} </think>\n'),'  a\n\\frac{1}{2} \n')

    def test_seed_condition_specific(self):
        self.assertEqual(seed('f','RT_I',0),seed('f','RT_I',0))
        self.assertNotEqual(seed('f','RT_I',0),seed('f','RT_T',0))
        self.assertNotEqual(seed('f','RT_I',0),seed('f','RT_I',1))

    def test_missingness_bounds(self):
        self.assertTrue(majority([True,None,True]))
        self.assertFalse(majority([False,None,False]))
        self.assertIsNone(majority([True,False,None]))

    def test_repair_is_not_utilization(self):
        outcomes={k:[False]*3 for k in ['RT_T','RT_I','RC_I','RC_T','Q_I','Q_T']}
        outcomes['RC_T']=[True,True,False]
        r=interpret(outcomes,'E_FULL','DERIVATION_FLAWED')
        self.assertTrue(r['REPAIR_SUPPORT']);self.assertFalse(r['UTILIZATION_SUPPORT'])
        outcomes['Q_T']=[True]*3
        self.assertFalse(interpret(outcomes,'E_FULL','DERIVATION_FLAWED')['REPAIR_SUPPORT'])

    def test_same_model_gate_and_question_control(self):
        out={k:[False]*3 for k in ['RT_T','RT_I','RC_I','RC_T','Q_I','Q_T']};out['RT_I']=[True]*3
        self.assertFalse(interpret(out,'E_FULL','DERIVATION_VALID')['PRODUCTION_SUPPORT'])
        out['RT_T']=[True]*3
        r=interpret(out,'E_FULL','DERIVATION_VALID');self.assertTrue(r['PRODUCTION_SUPPORT'])
        self.assertEqual(decision([r]*5)['decision'],'STATE_PRODUCTION_SIGNAL')
        out['Q_I']=[True]*3
        self.assertFalse(interpret(out,'E_FULL','DERIVATION_VALID')['PRODUCTION_SUPPORT'])


if __name__=='__main__':unittest.main()
