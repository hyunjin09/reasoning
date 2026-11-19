import unittest
from scripts.stage14b.grade_presentation_v4 import normalized_grade
class LatexPresentationTests(unittest.TestCase):
 def test_letter(self):
  self.assertEqual(normalized_grade(r'\text{B}',['x','y'],'B')['status'],'CORRECT')
 def test_spacing_formatting(self):
  self.assertEqual(normalized_grade(r'\text{E. } 50 \mathrm{~cm}^{2}',['x', 'y','z','a',r'$50\text{cm}^2$'],'E')['status'],'CORRECT')
 def test_unit_preserved(self):
  self.assertIsNone(normalized_grade('50 cm',['50 m'],'A'))
 def test_grouped_numbers_not_concatenated(self):
  self.assertIsNone(normalized_grade("2 3",[],"23"))
 def test_degree(self):
  self.assertEqual(normalized_grade(r'45^\circ',['30°','45°'],'B')['status'],'CORRECT')
 def test_mismatch_no_coercion(self):
  self.assertIsNone(normalized_grade(r'A. 10',['20','10'],'A'))
  self.assertIsNone(normalized_grade(r'\text{B or C}',['a','b','c'],'B'))
if __name__=='__main__':unittest.main()
