import json
import unittest
import xgrammar
from xgrammar.testing import _is_grammar_accept_string as accepts
from scripts.stage14d1_pilot.interface_v6 import SCHEMAS
class LocatorModes(unittest.TestCase):
    def test_exact_mode_cardinality_without_forcing_local(self):
        grammar=xgrammar.Grammar.from_json_schema(json.dumps(SCHEMAS['locate']))
        for mode,n in [('LOCAL',1),('MULTI',2),('GLOBAL',0),('UNRESOLVABLE',0)]:
            for count in range(3):
                d=dict(mode=mode,boxes=[[100,200,800,900]]*count,source_reference='source',uncertainty='uncertain')
                with self.subTest(mode=mode,count=count):self.assertEqual(accepts(grammar,json.dumps(d)),count==n)
if __name__=='__main__':unittest.main()
