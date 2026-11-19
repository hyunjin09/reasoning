import unittest
from scripts.stage14cv.parallel_recovery import split_waves, validate_shards


class ParallelRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(task_id=f'{w}_{i}',wave=w) for w,n in [(14,18),(15,18),(16,12)] for i in range(n)]

    def test_two_queues_preserve_all_frozen_waves(self):
        shards=split_waves(self.rows,2)
        self.assertEqual([len(s) for s in shards],[30,18])
        self.assertEqual([[r['wave'] for r in s][::18] for s in shards],[[14,16],[15]])
        validate_shards(self.rows,shards)

    def test_duplicate_task_rejected(self):
        shards=split_waves(self.rows,2)
        shards[1].append(shards[0][0])
        with self.assertRaises(ValueError):validate_shards(self.rows,shards)

    def test_split_wave_rejected_even_if_coverage_complete(self):
        with self.assertRaises(ValueError):validate_shards(self.rows,[self.rows[::2],self.rows[1::2]])

    def test_reordered_wave_rejected(self):
        shards=split_waves(self.rows,2);shards[0][:18]=reversed(shards[0][:18])
        with self.assertRaises(ValueError):validate_shards(self.rows,shards)

    def test_no_empty_or_missing_queue(self):
        with self.assertRaises(ValueError):validate_shards(self.rows,[self.rows,[]])
        with self.assertRaises(ValueError):validate_shards(self.rows,[self.rows[:-1]])


if __name__=='__main__':unittest.main()
