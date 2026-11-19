"""CPU grammar acceptance tests using the exact installed xgrammar backend."""
import json
import unittest
import xgrammar
from xgrammar.testing import _is_grammar_accept_string
from scripts.stage14d1.contracts_v2 import SCHEMAS as OLD
from scripts.stage14d1.contracts_v3 import SCHEMAS

QUERY = dict(status='QUERY', subgoal='Determine the needed color', entity='cell',
             entity_id='top cell', predicate='color', spatial_reference='whole grid',
             query='What color is the top cell?', answer_value=None, numeric_provenance=[])
NONE = dict(status='NONE', answer_value=None, reason='No new visual fact needed.')

def accepts(schema, value):
    grammar = xgrammar.Grammar.from_json_schema(json.dumps(schema))
    return _is_grammar_accept_string(grammar, json.dumps(value))

class GrammarTests(unittest.TestCase):
    def test_reproduces_old_prompt_order_bug(self):
        self.assertFalse(accepts(OLD['query'], QUERY))
        self.assertTrue(accepts(OLD['query'], NONE))

    def test_both_status_first_alternatives_reachable(self):
        self.assertTrue(accepts(SCHEMAS['query'], QUERY))
        self.assertTrue(accepts(SCHEMAS['query'], NONE))

    def test_contract_values_not_relaxed(self):
        self.assertFalse(accepts(SCHEMAS['query'], dict(QUERY, answer_value='black')))
        self.assertFalse(accepts(SCHEMAS['query'], dict(QUERY, status='OTHER')))

    def test_existing_read_and_location_examples(self):
        self.assertTrue(accepts(SCHEMAS['locate'], dict(mode='GLOBAL', boxes=[], source_reference='whole configuration', uncertainty='uncertain')))
        self.assertTrue(accepts(SCHEMAS['read'], dict(target='top cell', read_value='unknown', supporting_source='image', uncertainty='unresolvable')))

if __name__ == '__main__':
    unittest.main()
