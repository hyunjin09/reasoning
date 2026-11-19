"""Exact saved-token offsets, including split UTF-8 and skipped special tokens."""
import json
import unittest
from pathlib import Path
from tokenizers import Tokenizer
from scripts.stage14d.token_offsets_v1 import valid_boundaries_for_offsets


class OffsetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg = json.loads(Path('outputs/stage14d/spec/pinned_model_revisions_and_recipes.json').read_text())
        cls.tok = Tokenizer.from_file(cfg['models']['T']['model']['checkpoint'] + '/tokenizer.json')

    def check_offsets(self, ids, points, stride):
        raw = self.tok.decode(ids, skip_special_tokens=True)
        brute = []
        for n in range(len(ids) + 1):
            prefix = self.tok.decode(ids[:n], skip_special_tokens=True)
            if raw.startswith(prefix):
                brute.append((n, len(prefix)))
        actual = valid_boundaries_for_offsets(self.tok, ids, raw, points, stride=stride)
        for p in points:
            self.assertEqual(max(n for n, c in actual if c <= p), max(n for n, c in brute if c <= p))
            self.assertEqual(min(n for n, c in actual if c >= p), min(n for n, c in brute if c >= p))

    def test_unicode_and_special_token_plateaus(self):
        ids = self.tok.encode('가나다 中文 ∠ABC = 90° 😃 👩🏽‍🔬\n\nDone.', add_special_tokens=False).ids
        special = self.tok.token_to_id('<|im_end|>')
        ids = [special] * 4 + ids[:8] + [special] * 9 + ids[8:] + [special] * 5
        raw = self.tok.decode(ids, skip_special_tokens=True)
        self.check_offsets(ids, range(len(raw) + 1), stride=3)

    def test_long_text_sparse_queries_match_exhaustive(self):
        ids = self.tok.encode(('First, read the source. ∠ABC. 가나다.\n' * 70), add_special_tokens=False).ids
        raw = self.tok.decode(ids, skip_special_tokens=True)
        self.check_offsets(ids, [0, 1, 80, len(raw)//2, len(raw)-1, len(raw)], stride=64)

    def test_saved_native_generation(self):
        review = json.loads(Path('outputs/stage14d/annotation/native_review_v1/mv_82_image_T_r0.json').read_text())
        g = json.loads(Path(review['original_receipts']['generation']).read_text())
        points = [review['anchor_char_index']]
        for e in list(review['events'].values()) + review['observed_repeats_or_contradictions']:
            if e:
                points.extend([e['char_start'], e['char_end']])
        self.check_offsets(g['generated_token_ids'], points, stride=256)

    def test_mismatched_transcript_is_rejected(self):
        with self.assertRaises(AssertionError):
            valid_boundaries_for_offsets(self.tok, [42], 'invented transcript', [0])


if __name__ == '__main__':
    unittest.main()
