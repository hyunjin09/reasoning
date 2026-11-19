import copy,json,unittest
from scripts.stage14e.contracts import validate_demand,reader_prompt,compile_target,QUERY_SCHEMA,READ_SCHEMA,STRUCT_SCHEMA,budget_admissible
from scripts.stage14d1_pilot.interface_v5 import build_catalog
class Contracts(unittest.TestCase):
 def setUp(self):
  self.r={'question':'A grid contains labeled cells. Find the required total.','prefix':'Perhaps the shaded cell is 999. I need its printed label.'}
  self.cat=build_catalog(self.r['question'],self.r['prefix'])
  self.q={'status':'QUERY','need':'REINSPECT','target':'shaded cell','property':'printed_label','frame':'grid in the original image','source_refs':['P000'],'answer_value':None}
 def test_valid_reference_not_truth(self):self.assertTrue(validate_demand(self.q,self.cat)[0])
 def test_none(self):self.assertTrue(validate_demand({'status':'NONE','reason':'DERIVATION_ONLY','answer_value':None},self.cat)[0])
 def test_invented_reference(self):
  q=dict(self.q,source_refs=['P999']);self.assertFalse(validate_demand(q,self.cat)[0])
 def test_duplicate_reference_rejected_after_decoding(self):
  q=dict(self.q,source_refs=['P000','P000']);self.assertFalse(validate_demand(q,self.cat)[0])
 def test_catalog_tag_is_not_visual_address(self):
  q=dict(self.q,frame='P000');self.assertEqual(validate_demand(q,self.cat),(False,'CATALOG_TAG_IN_VISUAL_ADDRESS'))
 def test_answer_slot(self):
  q=dict(self.q,answer_value='99');self.assertFalse(validate_demand(q,self.cat)[0])
 def test_asserted_value(self):
  q=dict(self.q,target='cell equals 999');self.assertFalse(validate_demand(q,self.cat)[0])
 def test_unsupported_number(self):
  q=dict(self.q,frame='row 32');self.assertFalse(validate_demand(q,self.cat)[0])
 def test_supported_structural_number(self):
  cat=build_catalog('Read the label in row 3.','')
  q=dict(self.q,target='cell',frame='row 3',source_refs=['Q000']);self.assertTrue(validate_demand(q,cat)[0])
 def test_reader_has_no_solver_values_or_reference_spans(self):
  target=compile_target(self.q,self.cat)
  p=reader_prompt(self.r,target,with_prefix=False)
  self.assertNotIn('999',p);self.assertNotIn('source_refs',p);self.assertNotIn('P000',p)
 def test_matched_prefix_toggle(self):
  target=compile_target(self.q,self.cat)
  p=reader_prompt(self.r,target,with_prefix=True);self.assertIn(self.r['prefix'],p)
  self.assertEqual(p.replace('\n\nSolver prefix (not verified):\n'+self.r['prefix'],''),reader_prompt(self.r,target,with_prefix=False))
 def test_corrupt_catalog(self):
  cat=copy.deepcopy(self.cat);cat[-1]['text']='invented';self.assertFalse(validate_demand(self.q,cat)[0])
 def test_wrong_type(self):self.assertFalse(validate_demand([],self.cat)[0])
 def test_budget(self):
  self.assertTrue(budget_admissible(100,200,300));self.assertFalse(budget_admissible(100,201,300))
  self.assertFalse(budget_admissible(-1,200,300))
 def test_grammar_literals(self):
  import jsonschema
  jsonschema.validate(self.q,QUERY_SCHEMA)
  jsonschema.validate({'status':'NONE','reason':'DERIVATION_ONLY','answer_value':None},QUERY_SCHEMA)
if __name__=='__main__':unittest.main()
