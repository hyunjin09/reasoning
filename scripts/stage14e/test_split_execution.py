import hashlib
import unittest
from scripts.stage14e.evaluation_contracts import continuation_plan
from scripts.stage14e.split_execution import frozen_plan, physical_order


class Split(unittest.TestCase):
    def setup_records(self):
        read = dict(target='cell', read_value='7', supporting_source='visible glyph', uncertainty='certain')
        acquisition = {'readouts': {'S': None, 'M': read, 'M_noimage': None}}
        physical, assignments = continuation_plan('x', acquisition['readouts'])
        logical = [dict(item_id='x', arm=arm, **value,
                       suffix_sha256=hashlib.sha256(physical[value['physical_id']].encode()).hexdigest())
                   for arm, value in assignments.items()]
        return acquisition, physical, assignments, logical

    def test_exact_suffix_and_native_alias_survive_split(self):
        acquisition, physical, assignments, logical = self.setup_records()
        self.assertEqual(frozen_plan('x', acquisition, logical), (physical, assignments))
        self.assertEqual(assignments['S']['physical_id'], 'x_N')

    def test_readout_mutation_rejected(self):
        acquisition, _, _, logical = self.setup_records()
        acquisition['readouts']['M']['read_value'] = '8'
        with self.assertRaises(AssertionError):
            frozen_plan('x', acquisition, logical)

    def test_missing_assignment_rejected(self):
        acquisition, _, _, logical = self.setup_records()
        with self.assertRaises(AssertionError):
            frozen_plan('x', acquisition, logical[:-1])

    def test_order_does_not_depend_on_dict_insertion(self):
        self.assertEqual(physical_order({'x_N': '', 'x_M': 'a'}), physical_order({'x_M': 'a', 'x_N': ''}))


if __name__ == '__main__':
    unittest.main()
