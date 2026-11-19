import unittest

from scripts.stage14cv.resume_longer import validate_checkpoint


class ResumeCheckpointTests(unittest.TestCase):
    def test_finished_wave_is_reused_and_future_wave_remains(self):
        self.assertEqual(validate_checkpoint(
            [(0, 'a'), (0, 'b'), (1, 'c')], {'a', 'b'}, {'a', 'b'}), ['c'])

    def test_unfinished_active_call_blocks_restart(self):
        with self.assertRaises(ValueError):
            validate_checkpoint([(0, 'a'), (0, 'b')], {'a', 'b'}, {'a'})

    def test_partial_wave_cannot_change_matched_batch_context(self):
        with self.assertRaises(ValueError):
            validate_checkpoint([(0, 'a'), (0, 'b')], {'a'}, {'a'})

    def test_completed_queue_has_no_new_calls(self):
        self.assertEqual(validate_checkpoint([(0, 'a')], {'a'}, {'a'}), [])


if __name__ == '__main__':
    unittest.main()
