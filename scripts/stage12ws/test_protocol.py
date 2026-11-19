import unittest
from scripts.stage12ws.protocol import seed, paired, gate, partition, retain, order_blocks

class ProtocolTests(unittest.TestCase):
    def test_same_seven_seeds_and_family_separation(self):
        self.assertEqual([seed('a',i) for i in range(7)],[seed('a',i) for i in range(7)])
        self.assertEqual(len({seed(f,i) for f in ['a','b'] for i in range(7)}),14)
    def test_paired_threshold_without_majority(self):
        x=paired([True]*5+[False]*2,[True]*2+[False]*5)
        self.assertEqual(x['net_successes'],3); self.assertTrue(x['at_least_3'])
    def test_missing_never_becomes_failure(self):
        x=paired([True]*3+[False]*4,[None]+[False]*6)
        self.assertIsNone(x['at_least_3']); self.assertEqual(x['net_bounds'],[2,3])
    def test_shared_missing_replay_cancels(self):
        self.assertEqual(paired([None]*7,[None]*7,identical=True)['net_bounds'],[0,0])
    def test_gate_distinguishes_weak_and_unresolved(self):
        self.assertEqual(gate([True,True,False,False]),'STOP_WEAK')
        self.assertEqual(gate([True,True,None,False]),'STOP_UNRESOLVED')
        self.assertEqual(gate([True,True,True,None]),'CONTINUE')
    def test_partition_and_deletion_preserve_whitespace(self):
        b=partition(['a\n\n','b ','c\n'],[1,3])
        self.assertEqual(retain(b,[2]),'b c\n')
        with self.assertRaises(AssertionError):partition(['a','b'],[1])
    def test_order_swaps_largest_derived_only(self):
        b=[dict(block_id=i,role=r,token_count=n,text=str(i)) for i,r,n in
           [(1,'RAW_EVIDENCE_AND_BINDING',100),(2,'DERIVED_RELATIONS',2),
            (3,'INTERMEDIATE_COMPUTATION',9),(4,'REPAIR_OR_RESOLUTION',5),(5,'REPRESENTATION_SETUP',90)]]
        self.assertEqual(order_blocks(b),[1,2,4,3,5])

if __name__=='__main__':unittest.main()
