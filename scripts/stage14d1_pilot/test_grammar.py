import json
import unittest
from copy import deepcopy
import xgrammar
from xgrammar.testing import _is_grammar_accept_string
from scripts.stage14d1_pilot.provenance import QUERY_SCHEMA


class PointerGrammar(unittest.TestCase):
    def test_both_status_first_branches_and_dynamic_source_ids(self):
        schema = deepcopy(QUERY_SCHEMA)
        schema["anyOf"][0]["properties"]["source_refs"]["items"] = {"enum": ["Q000", "P001"]}
        grammar = xgrammar.Grammar.from_json_schema(json.dumps(schema))
        q = dict(status="QUERY", target="marked vertex", property="count", scope="local",
                 source_refs=["Q000"], answer_value=None)
        n = dict(status="NONE", reason="no_visual_need", answer_value=None)
        self.assertTrue(_is_grammar_accept_string(grammar, json.dumps(q)))
        self.assertTrue(_is_grammar_accept_string(grammar, json.dumps(n)))
        self.assertFalse(_is_grammar_accept_string(grammar, json.dumps(dict(q, source_refs=["Q999"]))))
        self.assertFalse(_is_grammar_accept_string(grammar, json.dumps(dict(q, answer_value=5))))


if __name__ == "__main__":
    unittest.main()
