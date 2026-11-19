import unittest
from scripts.stage12xs.inference_v2 import infer_transfer,exact

class InferenceTests(unittest.TestCase):
    def rows(self,n):
        return [dict(item_id=str(i),arm=a,replicate=k,correct=a in ['RT_T','RT_I']) for i in range(n) for a in ['RT_T','RT_I','Q_I','Q_T','SH_I'] for k in range(5)]
    def test_exact_gate_uses_family_not_seed_denominator(self):
        result=infer_transfer([str(i) for i in range(5)],self.rows(5))
        self.assertEqual(result['decision'],'HELDOUT_STATE_PRODUCTION_REPLICATED')
        self.assertEqual(result['endpoints']['RT_I']['exact']['denominator'],5)
        self.assertAlmostEqual(exact(0,5)['exact95'][0],0)
    def test_missing_control_never_becomes_failure(self):
        rows=self.rows(5)
        for r in rows:
            if r['arm']=='SH_I':r['correct']=None
        result=infer_transfer([str(i) for i in range(5)],rows)
        self.assertEqual(result['decision'],'UNRESOLVED_TECHNICAL')
        self.assertEqual(result['endpoints']['production_support']['unknown'],5)
        self.assertEqual(result['endpoints']['production_support']['exact']['denominator'],0)
        self.assertEqual(result['endpoints']['production_support']['missingness_bounds'],[0,1])
    def test_small_yield_is_not_null(self):
        rows=self.rows(3)
        for r in rows:r['correct']=False
        self.assertEqual(infer_transfer(['0','1','2'],rows)['decision'],'UNRESOLVED_LOW_YIELD')

if __name__=='__main__':unittest.main()
