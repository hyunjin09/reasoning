import copy
import unittest
from scripts.stage13c.protocol import select, dummy_ids, donor, bootstrap_units, signals


class ProtocolTest(unittest.TestCase):
    def test_selection_is_source_only_and_disjoint(self):
        rows=[dict(family_id=str(i),answer_type='MC' if i%3 else 'open',level=i%5,facts=[1]*(1+i%2)) for i in range(96)]
        a=select(rows)
        perturbed=copy.deepcopy(rows)
        for r in perturbed:r.update(correct=True,pathology=True,length=9999)
        self.assertEqual(a,select(list(reversed(perturbed))))
        self.assertEqual(len(set(a['scientific'])),24)
        self.assertEqual(len(set(a['technical'])),4)
        self.assertFalse(set(a['technical']) & set(a['scientific']))
        self.assertEqual(len(a['initial8']),8)
        self.assertTrue(set(a['initial8']) <= set(a['scientific']))

    def test_dummy_exact_counts_and_donor(self):
        self.assertEqual(dummy_ids([2,5,7],8),[2,5,7,2,5,7,2,5])
        self.assertEqual(dummy_ids([2],0),[])
        with self.assertRaises(AssertionError):dummy_ids([],2)
        self.assertEqual(donor('a',{'a':4,'b':5,'c':9}),'b')

    def test_integer_bootstrap_zero_and_gate_minima(self):
        e=bootstrap_units([0]*24)
        self.assertEqual(e['ci95_pp'],[0.,0.])
        self.assertFalse(signals(e,e,e,e,e,e)['COMPUTATIONAL_BUFFER_SIGNAL'])
        positive=bootstrap_units([1]*24)
        s=signals(positive,positive,positive,positive,positive,positive)
        self.assertTrue(s['COMPUTATIONAL_BUFFER_SIGNAL'])
        self.assertTrue(s['PORTABLE_DERIVED_PRIMING_SIGNAL'])
        self.assertEqual(s['decision'],'COMPLEMENTARY_COMPUTE_AND_SEMANTICS')
        small=bootstrap_units([5]*11)
        self.assertFalse(signals(small,small,small,small,small,small)['DERIVED_SEMANTIC_SIGNAL'])


if __name__=='__main__':unittest.main()
