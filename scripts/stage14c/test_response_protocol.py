import unittest
from scripts.stage14c.response_protocol import extract,repetition
class ResponseTests(unittest.TestCase):
    def test_thinking_requires_boundary_and_ignores_reasoning_option(self):
        self.assertFalse(extract('Answer: A','T','choice','stop')['committed'])
        self.assertEqual(extract('Answer: A</think>Final answer: B','T','choice','stop')['answer'],'B')
    def test_native_formats_and_ambiguous_tail(self):
        for value,kind in [('A','choice'),('{2}','integer'),('{4,3}','ordered_pair'),('{Yes}','yes_no')]:
            self.assertTrue(extract(value,'I',kind,'stop')['committed'])
        self.assertTrue(extract('Answer: A\nActually I should reconsider','I','choice','stop')['needs_review'])
        self.assertTrue(extract('Answer: A','I','choice','length')['needs_review'])
    def test_exact_repetition_threshold(self):
        self.assertTrue(repetition(list(range(8))*128)['flag'])
        self.assertFalse(repetition(list(range(8))*127)['flag'])
        self.assertFalse(repetition(list(range(1200)))['flag'])
if __name__=='__main__':unittest.main()
