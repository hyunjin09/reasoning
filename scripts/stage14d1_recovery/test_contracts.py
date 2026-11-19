import unittest
from scripts.stage14d1_recovery.contracts import replay_comparison, require_replay, remaining_seconds

class RecoveryContracts(unittest.TestCase):
    def test_first_divergence_is_zero_based(self):
        a = {'tokens':[1,2,3], 'prompt':[7], 'seed':9, 'pixels':['p']}
        b = dict(a, tokens=[1,4,3])
        self.assertEqual(replay_comparison(a,b)['first_divergence'],1)

    def test_matching_outputs_do_not_hide_wrong_reconstruction(self):
        a = {'tokens':[1], 'prompt':[7], 'seed':9, 'pixels':['p']}
        b = dict(a,prompt=[8])
        self.assertFalse(replay_comparison(a,b)['pass'])

    def test_all_eight_are_required_before_helpers_are_admitted(self):
        with self.assertRaises(ValueError):
            require_replay([{'pass':True}]*7)
        with self.assertRaises(ValueError):
            require_replay([{'pass':True}]*7+[{'pass':False}])
        require_replay([{'pass':True}]*8)

    def test_pending_jobs_do_not_consume_allocated_budget(self):
        self.assertEqual(remaining_seconds(1421,[0,0]),5779)
        with self.assertRaises(ValueError):
            remaining_seconds(1421,[5800])

if __name__=='__main__':
    unittest.main()
