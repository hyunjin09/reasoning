import unittest
from scripts.stage12bs.protocol import authorize_manifest, full_gate, audit_selection, failure_type, persistence
from scripts.stage12bs.inference import infer


class ProtocolTests(unittest.TestCase):
    def test_generation_cannot_replace_reused_or_changed_task(self):
        tasks=[dict(task_id=str(i),item_id=str(i//3)) for i in range(111)]
        frozen=dict(tasks=tasks,config_sha256='fixed')
        shard=dict(frozen=True,phase='remaining',config_sha256='fixed',rows=tasks[:30])
        authorize_manifest(shard,frozen)
        for wrong in [dict(task_id='old',item_id='old'),dict(tasks[0],item_id='changed')]:
            with self.assertRaises(AssertionError):authorize_manifest(dict(shard,rows=[wrong]),frozen)

    def test_full_scale_rates_and_no_repetition_gate(self):
        good=dict(INPUT_VALID=True,SCOREABLE=True,TRUNCATED_BEFORE_OUTCOME=False,R1=True)
        rows={a:[dict(good) for _ in range(61)] for a in 'ENO'}
        for i in range(5):rows['N'][i].update(SCOREABLE=False,TRUNCATED_BEFORE_OUTCOME=True)
        self.assertTrue(full_gate(rows)['pass'])
        rows['N'][5].update(SCOREABLE=False,TRUNCATED_BEFORE_OUTCOME=True)
        self.assertFalse(full_gate(rows)['pass'])

    def test_missing_is_not_a_native_error_or_profile(self):
        rows=[dict(family_id='a',e=True,n=False,o=True),dict(family_id='b',e=False,n=None,o=False),
              dict(family_id='c',e=None,n=False,o=True),dict(family_id='d',e=True,n=True,o=True)]
        result=infer(rows,draws=20)
        self.assertEqual(result['endpoints']['P1']['numerator'],2)
        self.assertEqual(result['native_denominator'],3)
        self.assertEqual(result['endpoints']['P2']['denominator'],1)
        self.assertEqual(result['classes'],dict(B1=0,B2=1,B3=0,B4=0))

    def test_profile_yield_uses_all_scoreable_native_failures(self):
        rows=[dict(family_id=str(i),e=True if i<10 else None,n=False,o=True) for i in range(20)]
        self.assertEqual(infer(rows,draws=20)['decision'],'PROFILE_INFORMATIVE')

    def test_audit_and_pathology_are_deterministic(self):
        order=['a','b','c','d','e','f'];self.assertEqual(audit_selection(order,{'b'}),['a'])
        self.assertEqual(failure_type(dict(R1=True,R2=False,R3=True)),'LOOP_OR_REOPEN')
        self.assertEqual(persistence({'R1'},{'R2'},True),'PERSISTED_DIFFERENT_TYPE')
        self.assertEqual(persistence({'R1'},{'R1','R2'},True),'PERSISTED_SAME_TYPE')
        self.assertEqual(persistence({'R1'},set(),False),'UNSCOREABLE')


if __name__=='__main__':unittest.main()
