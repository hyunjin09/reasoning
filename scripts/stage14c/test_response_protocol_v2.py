import unittest
from scripts.stage14c.response_protocol_v2 import extract,option_texts
class FormatTests(unittest.TestCase):
    question='Color?\nOptions: A: White, B: Blue, C: Gold, D: Silver'
    def test_committed_label_plus_matching_source_text(self):
        x=extract('Reasoning.\n✅ Final Answer: **A: White**','I','choice','stop',self.question)
        self.assertEqual(x['answer'],'A');self.assertFalse(x['needs_review'])
    def test_label_text_conflict_and_alternatives_remain_review(self):
        for text in ['Final answer: A: Blue','Final answer: A or B','Final answer: A, but B could work']:
            self.assertTrue(extract(text,'I','choice','stop',self.question)['needs_review'])
    def test_option_listing_is_not_final_commitment(self):
        self.assertTrue(extract('A: White\nB: Blue\nC: Gold\nD: Silver','I','choice','stop',self.question)['needs_review'])
    def test_think_boundary_cap_and_source_schema(self):
        self.assertFalse(extract('Final answer: A: White','T','choice','stop',self.question)['committed'])
        self.assertTrue(extract('Answer: A: White','I','choice','length',self.question)['needs_review'])
        self.assertEqual(option_texts('Choices:\n(A) 0\n(B) 1\n(C) 2\n(D) 4'),dict(A='0',B='1',C='2',D='4'))
        self.assertEqual(option_texts('A:White,B:Blue'),{})
if __name__=='__main__':unittest.main()
