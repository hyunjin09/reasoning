import unittest
from scripts.stage14b.presentation_v2 import labeled_choice

class PresentationTests(unittest.TestCase):
    def test_complete_labeled_choice(self):
        self.assertEqual(labeled_choice('C:25.9',['18.8','23.2','25.9','44.0'],'I','stop'), 'C')
    def test_conflicting_letter_and_text_requires_review(self):
        self.assertIsNone(labeled_choice('C:23.2',['18.8','23.2','25.9','44.0'],'I','stop'))
    def test_no_cap_or_reasoning_mining(self):
        self.assertIsNone(labeled_choice('C:3',['1','2','3'],'I','length'))
        self.assertIsNone(labeled_choice('Maybe C:3, but A:1',['1','2','3'],'I','stop'))
        self.assertIsNone(labeled_choice('C:3',['1','2','3'],'T','stop'))
    def test_only_post_think_scope(self):
        self.assertEqual(labeled_choice('A:1</think>C:3',['1','2','3'],'T','stop'), 'C')

if __name__ == '__main__': unittest.main()
