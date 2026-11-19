import json,unittest
from copy import deepcopy
import xgrammar
from xgrammar.testing import _is_grammar_accept_string as accepts
from scripts.stage14e.contracts import QUERY_SCHEMA,STRUCT_SCHEMA
class Grammar(unittest.TestCase):
 def test_vllm_runtime_validation(self):
  from vllm import SamplingParams
  from vllm.sampling_params import StructuredOutputsParams
  from vllm.v1.structured_output.backend_xgrammar import validate_xgrammar_grammar
  from scripts.stage14e.contracts import READ_SCHEMA
  from scripts.stage14d1_pilot.interface_v6 import SCHEMAS
  for schema in [QUERY_SCHEMA,READ_SCHEMA,STRUCT_SCHEMA,SCHEMAS['locate']]:
   validate_xgrammar_grammar(SamplingParams(structured_outputs=StructuredOutputsParams(json=deepcopy(schema))))
 def test_both_branches(self):
  s=deepcopy(QUERY_SCHEMA);s['anyOf'][0]['properties']['source_refs']['items']={'enum':['Q000','P000']}
  g=xgrammar.Grammar.from_json_schema(json.dumps(s))
  q={'status':'QUERY','need':'REINSPECT','target':'cell','property':'printed_label','frame':'grid','source_refs':['Q000'],'answer_value':None}
  self.assertTrue(accepts(g,json.dumps(q)))
  self.assertTrue(accepts(g,json.dumps({'status':'NONE','reason':'DERIVATION_ONLY','answer_value':None})))
  self.assertFalse(accepts(g,json.dumps(dict(q,source_refs=['Q999']))))
 def test_structured_abstention_and_observation(self):
  g=xgrammar.Grammar.from_json_schema(json.dumps(STRUCT_SCHEMA))
  self.assertTrue(accepts(g,json.dumps({'status':'UNRESOLVABLE','source_frame':'unknown','observations':[],'unresolved':'image unavailable'})))
  self.assertTrue(accepts(g,json.dumps({'status':'OBSERVED','source_frame':'grid','observations':[{'entity':'cell','property':'label','value':'7','visual_support':'printed text'}],'unresolved':''})))
if __name__=='__main__':unittest.main()
