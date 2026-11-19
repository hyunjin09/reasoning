import unittest
import numpy as np
from scripts.stage10c.analysis import summarize,gate
class AnalysisTests(unittest.TestCase):
 def test_constant_paired_effects_and_bonferroni(self):
  rows=[dict(trajectory_id=str(i),dataset='MathVision' if i<8 else 'MathVerse',historical_faithful=True,greedy_faithful=True,
   y=[1,1,0,0,1],nll=[1,2,4,5,3],target_type='numeric') for i in range(16)]
  s=summarize(rows);g=gate(rows,s,True)
  self.assertEqual([s['primary'][k]['point'] for k in ['P1','P2','P3','P4']],[1,2,1,2])
  self.assertEqual(s['primary']['P2']['familywise95_ci'],[2,2]);self.assertTrue(g['main_gate_pass']);self.assertFalse(g['reserve_gate_pass'])
 def test_directional_null_does_not_open_reserve(self):
  rows=[dict(trajectory_id=str(i),dataset='MathVision' if i<8 else 'MathVerse',historical_faithful=True,greedy_faithful=True,
   y=[1,1,1,0,1],nll=[1,2,3,4,2],target_type='numeric') for i in range(16)]
  s=summarize(rows);g=gate(rows,s,True)
  self.assertFalse(g['main_gate_pass']);self.assertFalse(g['reserve_gate_pass']);self.assertEqual(g['outcome'],'C')
 def test_single_case_effect_fails_robustness(self):
  rows=[dict(trajectory_id=str(i),dataset='MathVision' if i<8 else 'MathVerse',historical_faithful=True,greedy_faithful=True,
   y=[1,1,0 if i==0 else 1,0 if i==0 else 1,1],nll=[1,1,2 if i==0 else 1,2 if i==0 else 1,1],target_type='numeric') for i in range(16)]
  self.assertFalse(gate(rows,summarize(rows),True)['main_gate_pass'])
if __name__=='__main__':unittest.main()
