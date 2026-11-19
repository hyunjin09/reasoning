import unittest
from scripts.stage12a.protocol import build_prompt, parse_task, parse_evidence, technical_gate, phenotype

class Contracts(unittest.TestCase):
    def test_evidence_request_excludes_question_and_gold(self):
        row=dict(question='PRIVATE TASK',facts=[dict(probe_request='Read left label.',gold_value='SECRET')])
        text=build_prompt(row,'E')
        self.assertIn('Read left label.',text)
        self.assertNotIn('PRIVATE TASK',text);self.assertNotIn('SECRET',text)

    def test_native_formats_preserve_question(self):
        for kind in ['multiple_choice','open_ended']:
            r=dict(question='EXACT question\nOptions remain.',answer_type=kind)
            for arm in ['D','C']:self.assertTrue(build_prompt(r,arm).startswith(r['question']+'\n\n'))

    def test_option_only_d_rejects_reasoning(self):
        self.assertEqual(parse_task(' (B). ','D','multiple_choice')['answer'],'B')
        self.assertFalse(parse_task('Because x is positive, B.','D','multiple_choice')['format_valid'])
        self.assertFalse(parse_task('Final answer: B','D','multiple_choice')['format_valid'])

    def test_open_d_value_vs_working(self):
        self.assertTrue(parse_task(r'$\frac{5\sqrt{3}}{6}$','D','open_ended')['format_valid'])
        for s in ['2+2=4','First compute 2+2. 4','4\nSo answer is4']:
            self.assertFalse(parse_task(s,'D','open_ended')['format_valid'])

    def test_c_requires_terminal_answer(self):
        self.assertEqual(parse_task('Reasoning.\nFinal answer: B','C','multiple_choice')['answer'],'B')
        self.assertFalse(parse_task('Final answer: B\nBut that is wrong.','C','multiple_choice')['format_valid'])
        self.assertTrue(parse_task('Reasoning\nFinal answer: $4\\pi$','C','open_ended')['format_valid'])

    def test_e_schema_all_required_unique(self):
        self.assertTrue(parse_evidence('E1: 3\nE2: AB is parallel to CD',2)['format_valid'])
        for s in ['E1: 3','E1: 3\nE1: 4','First count them.\nE1: 3\nE2: 4','E1: [value]\nE2: 4']:
            self.assertFalse(parse_evidence(s,2)['format_valid'])

    def test_gates_preserve_boundaries(self):
        good={a:[dict(format_valid=True,severe_reasoning=False,intermediate_reasoning=False,
            repetition_pathology=False,committed_final=True,cap_hit=False) for _ in range(12)] for a in 'EDC'}
        self.assertTrue(technical_gate(good)['pass'])
        for r in good['C'][:3]:r['cap_hit']=True
        self.assertFalse(technical_gate(good)['pass'])

    def test_lost_key_not_defined_by_c_and_not_atoms(self):
        self.assertEqual(phenotype(True,False,True),dict(L=True,F1=False,F2=True,F3=True,F4=False))
        self.assertEqual(phenotype(False,False,True),dict(L=False,F1=True,F2=False,F3=False,F4=False))

if __name__=='__main__':unittest.main()
