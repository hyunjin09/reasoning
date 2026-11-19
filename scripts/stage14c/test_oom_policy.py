import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.stage14c import common
from scripts.stage14c import oom_policy as policy


class OOMPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='runs')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for mod in (common, policy):
            p = patch.object(mod, 'ROOT', self.root)
            p.start(); self.addCleanup(p.stop)
        self.tasks = [dict(task_id=x, collection='test') for x in ('a', 'b', 'c')]

    def test_only_explicit_gpu_oom_triggers_recovery(self):
        self.assertTrue(policy.is_gpu_oom('torch.OutOfMemoryError: CUDA out of memory.'))
        self.assertTrue(policy.is_gpu_oom('CUDA error: out of memory'))
        for text in ('EngineDeadError', 'CUDA illegal memory access', 'MemoryError',
                     'slurmstepd: oom-kill event', 'not enough KV cache space'):
            self.assertFalse(policy.is_gpu_oom(text))

    def test_completed_receipts_are_never_recomputed(self):
        t = self.tasks[0]; folder = common.result_dir(t)
        common.save(folder/'input.json', {})
        common.save(folder/'generation.json', {})
        common.save(folder/'result.json', dict(task_sha256=common.fingerprint(t),
            input_sha256=common.sha(folder/'input.json'),
            generation_sha256=common.sha(folder/'generation.json')))
        pending, attempts = policy.remaining(self.tasks)
        self.assertEqual([t['task_id'] for t in pending], ['b', 'c'])

    def test_attributable_oom_is_skipped_and_next_task_remains(self):
        t = self.tasks[0]
        policy.mark_missing(t, 'OOM_SKIP', {'job': '1'})
        policy.mark_missing(t, 'OOM_SKIP', {'job': '1'})  # restart-safe
        pending, _ = policy.remaining(self.tasks)
        self.assertEqual([t['task_id'] for t in pending], ['b', 'c'])
        receipt = common.load(policy.missing_path(t))
        self.assertTrue(receipt['final_technical_failure'])
        self.assertEqual(receipt['status'], 'TECHNICAL_MISSING')

    def test_ambiguous_batch_oom_does_not_blame_arbitrary_sample(self):
        failure = dict(active_ids=['a', 'b'], pending_id=None, phase='step')
        self.assertEqual(policy.identified_sample(failure), None)
        self.assertEqual(policy.identified_sample(dict(failure, active_ids=['a'])), 'a')
        self.assertEqual(policy.identified_sample(dict(failure, pending_id='c', phase='prepare')), 'c')
        self.assertIsNone(policy.identified_sample(dict(failure, pending_id='c', phase='add_request')))

    def test_interrupted_sample_gets_one_versioned_attempt(self):
        common.save(common.result_dir(self.tasks[0])/'input.json', {})
        _, attempts = policy.remaining(self.tasks)
        self.assertEqual(attempts, {'a': 1, 'b': 0, 'c': 0})
        common.save(common.result_dir(self.tasks[0], 1)/'input.json', {})
        pending, attempts = policy.remaining(self.tasks)
        self.assertNotIn('a', attempts)
        self.assertEqual(common.load(policy.missing_path(self.tasks[0]))['reason'], 'INFRASTRUCTURE_RETRY_EXHAUSTED')

    def test_timeout_is_not_relabelled_as_oom(self):
        common.save(common.result_dir(self.tasks[0])/'technical_failure.json', {'reason':'REQUEST_TIMEOUT'})
        with self.assertRaisesRegex(RuntimeError, 'non-OOM'):
            policy.remaining(self.tasks)

    def test_startup_oom_does_not_skip_any_sample(self):
        with self.assertRaisesRegex(RuntimeError, 'before a sample'):
            policy.resolve_oom(self.tasks, {}, 'CUDA out of memory', {})
        self.assertFalse(any(policy.missing_path(t).exists() for t in self.tasks))



if __name__ == '__main__':
    unittest.main()
