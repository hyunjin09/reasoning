import unittest
from scripts.stage14b.protocol import native_prompt, clean_verse, seed, extract, grade

class ProtocolTests(unittest.TestCase):
    def test_native_question_and_options_preserved(self):
        self.assertEqual(native_prompt({'question':'Q\n<image1>','options':['a','b']}),'Q\n<image1>\n\nOptions:\nA. a\nB. b')
    def test_clean_layer_rejects_ambiguity(self):
        checks=dict.fromkeys(['same_task','gold_consistency','text_only_sufficient','visual_versions_sufficient','answer_safe'],'PASS')
        self.assertTrue(clean_verse({'consistency_checks':checks}))
        checks['same_task']='UNRESOLVED'
        self.assertFalse(clean_verse({'consistency_checks':checks}))
    def test_seed_pairing_and_distinct_replicates(self):
        self.assertEqual(seed('mv:5',0),seed('mv:5',0))
        self.assertNotEqual(seed('mv:5',0),seed('mv:5',1))
    def test_thinking_without_final_is_unscorable(self):
        self.assertIsNone(extract('Maybe \\boxed{3}, but let me reconsider.',[],'T','length')['answer'])
    def test_terminal_answer_over_reasoning_letters(self):
        self.assertEqual(extract('A could work, B fails. Final answer: C',['1','2','3'],'I','stop')['answer'],'C')
    def test_completed_box(self):
        self.assertEqual(extract('Reason\n</think>\n\\boxed{\\frac{1}{2}}',[],'T','stop')['answer'],r'\frac{1}{2}')
    def test_unscorable_not_wrong(self):
        self.assertIsNone(grade(None,{'options':[],'gold_answer':'3'})['correct'])
    def test_exact_and_numeric_equivalence(self):
        self.assertTrue(grade(r'\frac{1}{2}',{'options':[],'gold_answer':'0.5'})['correct'])
        self.assertFalse(grade('3',{'options':[],'gold_answer':'2'})['correct'])
    def test_unsupported_expression_needs_review(self):
        self.assertIsNone(grade('x+1',{'options':[],'gold_answer':'1+x'})['correct'])

if __name__=='__main__':unittest.main()

class VerseChoicesTests(unittest.TestCase):
    def test_vision_only_missing_text_choices_is_not_source_failure(self):
        from scripts.stage14b.protocol import verse_options
        row={'question':'','answer_type':'multi-choice'}
        reference={'question':'Question\nChoices:\nA: 1\nB: 2\nC: 3\nD: 4'}
        self.assertEqual(verse_options(row,reference),['1','2','3','4'])
        self.assertEqual(row['question'],'')
