"""CPU contracts for the bounded technical adapter (no CUDA import)."""
import unittest
from scripts.stage14d.technical_core_v1 import kept_positions, block_decode, admit_call, exact_prefix


class TechnicalContracts(unittest.TestCase):
    def test_only_image_keys_removed(self):
        self.assertEqual(kept_positions(8, [1, 2, 5]), [0, 3, 4, 6, 7])

    def test_prefill_and_first_output_remain_image_enabled(self):
        self.assertFalse(block_decode(1, 100, 100, True))
        self.assertFalse(block_decode(40, 100, 100, True))
        self.assertTrue(block_decode(1, 101, 100, True))
        self.assertFalse(block_decode(1, 101, 100, False))

    def test_unsupported_multiquery_decode_fails_closed(self):
        with self.assertRaises(ValueError): block_decode(2, 102, 100, True)

    def test_mask_cannot_remove_current_generated_token(self):
        with self.assertRaises(ValueError): kept_positions(4, [4])

    def test_no_call_retries_and_fixed_call_ceiling(self):
        self.assertTrue(admit_call('b', {'a'}, {'a','b'}, 24, 500))
        for key,done,allowed,remaining in [('a',{'a'},{'a'},500), ('c',set(),{'a'},500), ('a',set(),{'a'},100)]:
            with self.assertRaises(ValueError): admit_call(key, done, allowed,24,remaining)

    def test_original_prefix_ids_are_not_retokenized(self):
        self.assertEqual(exact_prefix([1,2,3], [8,9,10], 2, [50]), [1,2,3,8,9,50])
        with self.assertRaises(ValueError): exact_prefix([1],[2],2,[])


if __name__ == '__main__': unittest.main()
