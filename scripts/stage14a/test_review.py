import copy
import unittest
from scripts.stage14a.review import validate, rendering, FLAGS
from scripts.stage14a.history import identities


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.source=dict(item_id='12',image_hash='image',question_hash='question',question='Original?\n<image1>',options=['a','b'])
        self.receipt=dict(item_id='12',source_image_hash='image',source_question_hash='question',
            primary_review_note='Source checked.',decision='ACCEPT',e_star_atoms=['AB is marked 5 cm.'],
            evidence_request_per_atom=['What length is marked on AB?'],entity_references=['A','B'],units=['cm'],
            task_critical_entities=['AB'],task_critical_relations=['label on AB'],
            direct_image_grounding_rationale=['Segment label.'],final_qc_status='PASS',
            second_review=dict(eligibility='PASS',answer_safety='PASS',sufficiency='PASS',rendering='PASS',atoms=['PASS'],note='Rechecked source.',same_agent=True),
            **{k:False for k in FLAGS})

    def test_qc_required_not_inferred(self):
        validate(self.source,self.receipt)
        for field in ['eligibility','answer_safety','sufficiency','rendering']:
            r=copy.deepcopy(self.receipt);r['second_review'][field]='PENDING'
            with self.assertRaises(AssertionError):validate(self.source,r)
        r=copy.deepcopy(self.receipt);r['source_image_hash']='other'
        with self.assertRaises(AssertionError):validate(self.source,r)

    def test_render_preserves_question_and_options(self):
        s=rendering(self.source,['AB is marked 5 cm.'])
        self.assertEqual(s,'Task-critical visual evidence:\n- AB is marked 5 cm.\n\nOriginal?\n<image1>\n\nOptions:\nA. a\nB. b')

    def test_identity_projection_does_not_use_answer_numbers(self):
        x={'dataset':'MathVerse','problem_index':'20','correct':False,'answer':'12','output_text':'item 50','children':[{'dataset':'MathVision','item_id':'13'}]}
        ids=identities(x,{})
        self.assertEqual(ids,{'mathvision':{'13'},'mathverse':{'20'}})


if __name__=='__main__':unittest.main()
