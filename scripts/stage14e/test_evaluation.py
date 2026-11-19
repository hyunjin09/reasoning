import unittest
from scripts.stage14e.evaluation_contracts import acquisition_plan, continuation_plan, readout_valid
class Evaluation(unittest.TestCase):
 def test_none_is_explicit_native_alias(self):
  physical,logical=continuation_plan('x',{'S':None,'M':None})
  self.assertEqual(physical,{'x_N':''})
  self.assertEqual(logical['M']['physical_id'],'x_N')
  self.assertEqual(logical['M']['status'],'NO_VALID_READOUT_NATIVE_ALIAS')
 def test_identical_observations_deduplicate_without_success_claim(self):
  r={'target':'cell','read_value':'7','supporting_source':'grid','uncertainty':'certain'}
  physical,logical=continuation_plan('x',{'S':r,'M':dict(r)})
  self.assertEqual(len(physical),2);self.assertEqual(logical['S']['physical_id'],logical['M']['physical_id'])
 def test_structured_unknown_remains_observed_unknown(self):
  r={'status':'UNRESOLVABLE','source_frame':'unknown','observations':[],'unresolved':'unreadable'}
  self.assertTrue(readout_valid(r));p,l=continuation_plan('x',{'S':None,'M':r})
  self.assertEqual(l['M']['status'],'PHYSICAL');self.assertIn('unverified',p['x_M'])
 def test_noimage_control_matched(self):
  r={'question':'Which cell?','prefix':'Perhaps7','image':'source.jpg'}
  t={'status':'QUERY','query':'Read label','target':'cell','property':'printed_label','frame':'grid'}
  p=acquisition_plan(r,{'status':'NONE'},t,'A')
  self.assertEqual(p['M']['prompt'],p['M_noimage']['prompt']);self.assertEqual(p['M_noimage']['images'],[])
  self.assertNotIn('Perhaps7',p['M']['prompt'])
 def test_bad_structured_observation_is_rejected(self):
  self.assertFalse(readout_valid({'status':'OBSERVED','source_frame':'grid','observations':[{'value':'7'}],'unresolved':''}))
if __name__=='__main__':unittest.main()
