import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.stage11c.common import save, sha
from scripts.stage11c import calibration_attempts as attempts


class AttemptAccounting(unittest.TestCase):
    def test_interruption_remains_unknown_and_valid_duplicates_are_rejected(self):
        with tempfile.TemporaryDirectory(dir='runs/stage11c/v1/tmp') as directory:
            root = Path(directory)
            save(root/'config.json', {'frozen': True})
            task = dict(task_id='case1', arm='thinking', max_new_tokens=8192)

            def make(name, queue, interrupted):
                path = root/name
                save(path, dict(frozen=True, config_sha256=sha(root/'config.json'), queue=queue,
                                shards=[dict(model_key='thinking', rows=[task])]))
                dest = root/queue/'results/case1'
                save(dest/'generation.json', {'raw': 'partial' if interrupted else 'complete'})
                save(dest/'input.json', {'same_input': True})
                save(dest/'result.json', dict(task_id='case1', arm='thinking', cap=8192,
                    batch_size=1, budget_interrupted=interrupted, manifest_sha256=sha(path),
                    config_sha256=sha(root/'config.json'), generation_sha256=sha(dest/'generation.json'),
                    input_sha256=sha(dest/'input.json')))

            with patch.object(attempts, 'ROOT', root):
                make('calibration_tasks.json', 'calibration', True)
                self.assertEqual(len(attempts.collect()[3]), 0)
                make('calibration_tasks_retry1.json', 'calibration_retry1', False)
                result = attempts.collect()
                self.assertEqual(len(result[3]), 1)
                self.assertEqual(len(result[4]), 2)
                make('calibration_tasks_retry2.json', 'calibration_retry2', False)
                with self.assertRaisesRegex(AssertionError, 'duplicate valid'):
                    attempts.collect()


if __name__ == '__main__':
    unittest.main()
