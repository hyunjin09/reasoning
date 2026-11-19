import unittest
from scripts.stage12c.protocol import technical_gate, transition, rescue_decision, authorize_manifest


class ProtocolTest(unittest.TestCase):
    def test_repetition_is_not_a_validity_exclusion(self):
        row = dict(INPUT_VALID=True, SCOREABLE=True, TRUNCATED_BEFORE_OUTCOME=False, R1=True)
        self.assertTrue(technical_gate({a:[dict(row) for _ in range(12)] for a in 'CT'})['pass'])

    def test_two_pre_outcome_caps_stop_sanity(self):
        rows = {a:[dict(INPUT_VALID=True, SCOREABLE=True, TRUNCATED_BEFORE_OUTCOME=False) for _ in range(12)] for a in 'CT'}
        for r in rows['T'][:2]:r.update(SCOREABLE=False, TRUNCATED_BEFORE_OUTCOME=True)
        self.assertFalse(technical_gate(rows)['pass'])

    def test_missing_arm_is_not_a_failure(self):
        self.assertEqual(transition(None, True), 'UNSCOREABLE_TECHNICAL')
        self.assertEqual(transition(False, True), 'T_ONLY')
        self.assertEqual(transition(True, False), 'C_ONLY')

    def test_decision_counts_per_mode_not_union(self):
        rows=[dict(bottleneck='B1',c=i<3,t=3<=i<6) for i in range(11)]
        self.assertEqual(rescue_decision(rows, True), 'RESCUE_SPARSE')
        rows[6]['t']=True
        self.assertEqual(rescue_decision(rows, True), 'RESCUE_INFORMATIVE')
        self.assertEqual(rescue_decision(rows, False), 'TECHNICAL_STOP')

    def test_remaining_queue_requires_passed_sanity(self):
        t=dict(task_id='C_1_v1',arm='C')
        frozen=dict(config_sha256='f',tasks=[t],sanity_ids=[],remaining_ids=['1'])
        m=dict(config_sha256='f',rows=[t],frozen=True,phase='remaining',arm='C')
        with self.assertRaises(AssertionError):authorize_manifest(m,frozen,sanity_pass=False)


if __name__=='__main__':unittest.main()
