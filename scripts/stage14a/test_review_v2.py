import copy
import unittest
from scripts.stage14a.test_review import ReviewTests
from scripts.stage14a.review_v2 import validate

class StructuredAtomTests(unittest.TestCase):
    def test_structured_size_and_rationale_required(self):
        fixture=ReviewTests();fixture.setUp()
        r=copy.deepcopy(fixture.receipt)
        r['atom_metadata']=[dict(atom_type='structured_layout',structured_subfact_count=16,
            size_unit='cell states',coherent_source_object='single grid',minimality_note='All cells define symmetry constraints.')]
        validate(fixture.source,r)
        r['atom_metadata'][0]['structured_subfact_count']=0
        with self.assertRaises(AssertionError):validate(fixture.source,r)
        r['atom_metadata']=[dict(atom_type='scalar_relation',structured_subfact_count=None)]
        validate(fixture.source,r)
        r['atom_metadata']=[]
        with self.assertRaises(AssertionError):validate(fixture.source,r)

if __name__=='__main__':unittest.main()
