"""Independent adversarial checks of the exact final ledger implementation."""
import unittest
from scripts.stage14e.ledger_v2 import compile_ledger
from scripts.stage14e.contracts_v2 import build_catalog

class FinalLedger(unittest.TestCase):
    def setUp(self):
        self.catalog=build_catalog('Inspect the $7$-foot-by-$7$-foot floor.','Perhaps the central cell is shaded. I need to inspect its surroundings.')
        self.entry=dict(source_object='floor',property='layout',source_frame='7-foot-by-7-foot floor',source_refs=['Q000'],coverage='UNKNOWN')
    def run_record(self,e):return compile_ledger({'obligations':[e]},self.catalog)
    def test_real_dimension_serialization(self):self.assertEqual(self.run_record(self.entry)['target']['status'],'QUERY')
    def test_unquoted_numeric_payload_rejected(self):
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_NUMBER'):self.run_record(dict(self.entry,source_frame='99-cell floor'))
    def test_fabricated_source_reference_rejected(self):
        with self.assertRaises(ValueError):self.run_record(dict(self.entry,source_refs=['Q999']))
    def test_assertion_requires_actual_prefix_reference(self):
        with self.assertRaisesRegex(ValueError,'NO_ASSERTION_PROVENANCE'):self.run_record(dict(self.entry,coverage='ASSERTED_IN_PREFIX'))
    def test_abstention_remains_reachable(self):
        self.assertEqual(compile_ledger({'obligations':[]},self.catalog)['target']['status'],'NONE')
    def test_decision_order_preserves_first_unresolved(self):
        given=dict(self.entry,coverage='GIVEN_IN_QUESTION')
        unknown=dict(self.entry,source_object='cell layout')
        r=compile_ledger({'obligations':[given,unknown]},self.catalog)
        self.assertEqual(r['selected_index'],1)
        self.assertFalse(r['semantic_coverage_certified'])
if __name__=='__main__':unittest.main()
