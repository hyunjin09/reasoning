import unittest
from scripts.stage11b.preflight_checks import text_only_fields

class TextOnlyTests(unittest.TestCase):
    def test_auxiliary_zero_modality_tags_are_text(self):
        self.assertTrue(text_only_fields({'input_ids','attention_mask','mm_token_type_ids'},[0]))
    def test_pixels_or_nontext_tags_rejected(self):
        with self.assertRaises(ValueError):text_only_fields({'input_ids','pixel_values'},[0])
        with self.assertRaises(ValueError):text_only_fields({'input_ids','mm_token_type_ids'},[1])
        with self.assertRaises(ValueError):text_only_fields({'input_ids','past_key_values'},[0])

if __name__=='__main__':unittest.main()
