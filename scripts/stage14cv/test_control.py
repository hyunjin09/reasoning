import unittest
from scripts.stage14cv.control import budget_check, pending_ids, wave_groups, oom_action


class ControlTests(unittest.TestCase):
    def test_budget_reserves_whole_future_wall_time(self):
        self.assertEqual(budget_check([2, 4, 5], [6, 7]), 24)
        with self.assertRaises(ValueError): budget_check([2,4,5], [6,7.01])
        with self.assertRaises(ValueError): budget_check([-1], [1])

    def test_resume_never_recomputes_valid_or_missing_rows(self):
        self.assertEqual(pending_ids(['a','b','c'], {'a'}, {'b'}), ['c'])
        self.assertEqual(pending_ids(['a'], {'a'}, set()), [])
        with self.assertRaises(ValueError): pending_ids(['a'], {'a'}, {'a'})
        with self.assertRaises(ValueError): pending_ids(['a'], {'x'}, set())

    def test_partial_resume_keeps_original_wave_boundaries(self):
        rows=[dict(task_id=str(i),wave=i//18) for i in range(37)]
        done={str(i) for i in range(17)}|{'20'}
        groups=wave_groups(rows,done,set())
        self.assertEqual([[t['task_id'] for t in g] for g in groups],
                         [['17'],['18','19']+[str(i) for i in range(21,36)],['36']])

    def test_injected_singleton_oom_skips_only_attributable_sample(self):
        failure=dict(error='CUDA out of memory',phase='step',active_ids=['b'])
        self.assertEqual(oom_action(failure,set()), ('SKIP','b'))
        self.assertEqual(pending_ids(['a','b','c'],{'a'},{'b'}),['c'])

    def test_injected_unknown_batch_oom_never_guesses(self):
        failure=dict(error='torch.OutOfMemoryError: CUDA out of memory',phase='step',active_ids=['a','b'])
        self.assertEqual(oom_action(failure,set()),('SINGLETON_RECOVERY',None))
        with self.assertRaises(RuntimeError): oom_action(failure,set(),recovery_used=True)

    def test_completed_request_and_startup_oom_are_not_skipped(self):
        for failure in [dict(error='CUDA out of memory',phase='step',active_ids=['a']),
                        dict(error='CUDA out of memory',phase='startup',active_ids=[])]:
            with self.assertRaises(RuntimeError): oom_action(failure,{'a'})
        with self.assertRaises(RuntimeError):oom_action(dict(error='permission denied',active_ids=['a']),set())

    def test_preparation_oom_is_attributable_with_other_active_rows(self):
        self.assertEqual(oom_action(dict(error='CUDA out of memory',phase='prepare',active_ids=['a'],pending_id='b'),set()),('SKIP','b'))


if __name__=='__main__':unittest.main()
