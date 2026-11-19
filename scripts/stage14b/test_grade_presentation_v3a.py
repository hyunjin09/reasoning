import unittest
from scripts.stage14b.grade_presentation_v3a import normalized_grade
class GradePresentationTests(unittest.TestCase):
    def test_markdown_number(self):
        self.assertEqual(normalized_grade('60**',[], '60')['status'],'CORRECT')
        self.assertEqual(normalized_grade('**12**',[], '11')['status'],'WRONG')
    def test_letter_text_agrees(self):
        self.assertEqual(normalized_grade('**A. Wednesday**',['Wednesday','Tuesday'],'A')['status'],'CORRECT')
        self.assertEqual(normalized_grade('B. Tuesday**',['Wednesday','Tuesday'],'A')['status'],'WRONG')
        self.assertIsNone(normalized_grade('A. Tuesday',['Wednesday','Tuesday'],'A'))
    def test_whole_answer_only(self):
        for text in ['Maybe 60, or 70','60 is my first guess','(E) — because the tower used','A and B']:
            self.assertIsNone(normalized_grade(text,['Monday','Tuesday'],'A'))
    def test_math_wrappers(self):
        self.assertEqual(normalized_grade('**C. $2 \\cdot 4 \\cdot 3$**',['1','2','$2 \\cdot 4 \\cdot 3$'],'C')['status'],'CORRECT')
    def test_no_unbounded_simplification(self):
        self.assertIsNone(normalized_grade('x² + 2x + 1',[],'(x+1)^2'))
if __name__=='__main__':unittest.main()
