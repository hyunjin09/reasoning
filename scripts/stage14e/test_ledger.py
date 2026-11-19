import unittest
from scripts.stage14e.ledger import compile_ledger,ledger_schema
from scripts.stage14d1_pilot.interface_v5 import build_catalog
class Ledger(unittest.TestCase):
 def setUp(self):
  self.cat=build_catalog('Use the plotted point to compute an area.','Perhaps its coordinate is five. I need to read it.')
  self.o={'source_object':'marked point','property':'spatial_relation','source_frame':'labeled plot axes','source_refs':['Q000','P000'],'coverage':'TENTATIVE'}
 def test_select_unresolved_premise(self):
  r=compile_ledger({'obligations':[self.o]},self.cat);self.assertEqual(r['target']['status'],'QUERY');self.assertEqual(r['selected_index'],0)
 def test_given_and_asserted_allow_none(self):
  o=dict(self.o,coverage='ASSERTED_IN_PREFIX');r=compile_ledger({'obligations':[o]},self.cat);self.assertEqual(r['target']['status'],'NONE')
 def test_empty_none(self):self.assertEqual(compile_ledger({'obligations':[]},self.cat)['target']['status'],'NONE')
 def test_first_eligible_rule(self):
  a=dict(self.o,coverage='GIVEN_IN_QUESTION');b=dict(self.o,source_object='other point');r=compile_ledger({'obligations':[a,b]},self.cat);self.assertEqual(r['selected_index'],1)
 def test_reject_unsupported_value(self):
  o=dict(self.o,source_frame='value equals 99');self.assertRaises(ValueError,compile_ledger,{'obligations':[o]},self.cat)
 def test_asserted_requires_prefix_provenance(self):
  o=dict(self.o,coverage='ASSERTED_IN_PREFIX',source_refs=['Q000']);self.assertRaises(ValueError,compile_ledger,{'obligations':[o]},self.cat)
 def test_reader_target_does_not_contain_prefix_guess(self):
  q=compile_ledger({'obligations':[self.o]},self.cat)['target'];self.assertNotIn('five',str(q));self.assertNotIn('source_refs',str(q))
 def test_malformed(self):self.assertRaises(ValueError,compile_ledger,{'obligations':'bad'},self.cat)
 def test_runtime_grammar_observation_and_abstention(self):
  import json,xgrammar
  from xgrammar.testing import _is_grammar_accept_string
  from vllm import SamplingParams
  from vllm.sampling_params import StructuredOutputsParams
  from vllm.v1.structured_output.backend_xgrammar import validate_xgrammar_grammar
  schema=ledger_schema(self.cat);validate_xgrammar_grammar(SamplingParams(structured_outputs=StructuredOutputsParams(json=schema)))
  g=xgrammar.Grammar.from_json_schema(json.dumps(schema))
  self.assertTrue(_is_grammar_accept_string(g,json.dumps({'obligations':[]})))
  self.assertTrue(_is_grammar_accept_string(g,json.dumps({'obligations':[self.o]})))
if __name__=='__main__':unittest.main()
