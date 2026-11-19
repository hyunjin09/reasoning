import copy,unittest
from scripts.stage12ts.protocol import authorize_manifest,scientific_decision

class ProtocolTests(unittest.TestCase):
    def test_only_missing_frozen_thinking_calls_allowed(self):
        t=dict(task_id='T_new',arm='T',cap=81920,seed=7)
        m=dict(frozen=True,phase='remaining',arm='T',config_sha256='h',rows=[t])
        authorize_manifest(m,m)
        for change in [dict(task_id='T_reused'),dict(cap=40960),dict(seed=8),dict(arm='C')]:
            altered=copy.deepcopy(m);altered['rows'][0].update(change)
            with self.assertRaises(AssertionError):authorize_manifest(altered,m)
        altered=copy.deepcopy(m);altered['rows']*=2
        with self.assertRaises(AssertionError):authorize_manifest(altered,m)
    def test_frozen_science_thresholds_and_coexisting_states(self):
        self.assertEqual(scientific_decision(4,4,4,4),['THINKING_RESCUE_SPARSE'])
        self.assertEqual(scientific_decision(5,0,3,2),['THINKING_RESCUE_WITHOUT_CLEAR_EVIDENCE_LINK'])
        self.assertEqual(scientific_decision(5,5,3,3),['THINKING_VISUAL_RECOVERY_SIGNAL','THINKING_DOWNSTREAM_SIGNAL'])
        self.assertEqual(scientific_decision(0,5,0,0),['THINKING_DOWNSTREAM_SIGNAL'])
        self.assertEqual(scientific_decision(5,5,3,3,False),['THINKING_TECHNICAL_BREAKDOWN'])

if __name__=='__main__':unittest.main()
