import unittest
from scripts.stage13d.protocol import donor,bootstrap_counts,semantic_decision,buffer_decision
class ProtocolTests(unittest.TestCase):
    def test_donor_excludes_self_and_uses_nearest_length(self):
        rows=[dict(item_id='a',n=10),dict(item_id='b',n=12),dict(item_id='c',n=11)]
        self.assertEqual(donor(rows[0],rows)['item_id'],'c')
    def test_exact_zero_is_not_positive_bootstrap(self):
        self.assertEqual(bootstrap_counts([0]*12)['ci'],[0.,0.])
        self.assertFalse(semantic_decision(12,dict(mean=.05,ci=[0.,.1]),.1,.1))
        self.assertTrue(semantic_decision(12,dict(mean=.05,ci=[.01,.1]),.1,.1))
    def test_buffer_minimum_and_direction(self):
        self.assertFalse(buffer_decision([1.]*7))
        self.assertTrue(buffer_decision([1.]*8))
        self.assertFalse(buffer_decision([0.]*8))
