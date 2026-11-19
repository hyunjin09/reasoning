import copy
import unittest
from scripts.stage13b.protocol import select, bootstrap_units, missing_gate, primary_gate


class FrozenDesignTests(unittest.TestCase):
    def rows(self):
        return [dict(family_id=f'f{i:03}', answer_type='multiple_choice' if i % 2 else 'open_ended',
                     level=1+i % 5, facts=[{}]*(1+i % 3)) for i in range(96)]

    def test_exact_disjoint_deterministic_source_only_selection(self):
        rows=self.rows(); a=select(rows)
        changed=copy.deepcopy(rows[::-1])
        for i,r in enumerate(changed):
            r.update(correct=i % 2, pathology=True, response_length=i, B_label='B4')
        b=select(changed)
        self.assertEqual(a,b)
        self.assertEqual(len(set(a['scientific'])),48)
        self.assertEqual(len(set(a['technical'])),4)
        self.assertFalse(set(a['scientific']) & set(a['technical']))
        self.assertEqual(len(set(a['initial8'])),8)
        self.assertTrue(set(a['initial8']) <= set(a['scientific']))
        self.assertEqual(sum(x['selected'] for x in a['strata']),48)

    def test_integer_zero_interval_boundary(self):
        self.assertEqual(bootstrap_units([0]*48)['ci95_pp'],[0.0,0.0])
        self.assertEqual(bootstrap_units([1]*48)['effect_pp'],100/3)
        self.assertEqual(bootstrap_units([3,-3]*24)['effect_pp'],0)

    def test_tranche_missingness_strict_boundary(self):
        self.assertTrue(missing_gate(4,24))
        self.assertFalse(missing_gate(5,24))
        with self.assertRaises(AssertionError):missing_gate(1,23)

    def test_primary_coverage_and_zero_are_not_positive_evidence(self):
        self.assertFalse(primary_gate(dict(n=39,effect_pp=10,ci95_pp=[1,20])))
        self.assertFalse(primary_gate(dict(n=48,effect_pp=10,ci95_pp=[0,20])))
        self.assertFalse(primary_gate(dict(n=48,effect_pp=4.99,ci95_pp=[1,20])))
        self.assertTrue(primary_gate(dict(n=40,effect_pp=5,ci95_pp=[.01,20])))


if __name__=='__main__':unittest.main()
