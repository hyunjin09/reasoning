"""Prevent premature automated commitments from contaminating validity gates."""
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.stage13b import review
from visual_reasoning.stage8b.v2_scoring import extract_answer


class ExtractionSafety(unittest.TestCase):
    def automatic_result(self,text,mode='I',cap=False,options=()):
        with tempfile.TemporaryDirectory(dir='runs',prefix='s13b_test_') as temp:
            root=Path(temp);packet=root/'audit/review_packets/toy.json';packet.parent.mkdir(parents=True)
            packet.write_text(json.dumps(dict(task_id='toy',raw=text,cap_hit=cap,checks={'input':True},
                options=list(options),extraction=extract_answer(text,list(options)))))
            with patch.object(review,'ROOT',root),patch.object(review,'packets'),patch.object(review,'tasks',return_value=[dict(task_id='toy',mode=mode)]):
                count=review.automatic('equal','toy');decision=root/'audit/technical_decisions/toy.json'
                return count,json.loads(decision.read_text()) if decision.exists() else None

    def test_terminal_normal_box_is_scoreable(self):
        n,r=self.automatic_result('Thus the result is \\boxed{5}.')
        self.assertEqual(n,1);self.assertEqual(r['outcome'],'5')
        self.assertTrue(r['validity']['TECHNICALLY_VALID'])

    def test_retracted_box_needs_own_response_review(self):
        self.assertEqual(self.automatic_result('I got \\boxed{5}, but this is wrong; reconsidering.'),(0,None))

    def test_capped_box_is_never_auto_accepted_or_auto_rejected(self):
        self.assertEqual(self.automatic_result('Final \\boxed{5}',cap=True),(0,None))

    def test_unclosed_thinking_needs_review(self):
        self.assertEqual(self.automatic_result('Maybe \\boxed{5}',mode='T'),(0,None))

    def test_post_think_final_overrides_reasoning_candidate(self):
        n,r=self.automatic_result('Maybe \\boxed{2}. No.</think>\nFinal \\boxed{5}',mode='T')
        self.assertEqual(n,1);self.assertEqual(r['outcome'],'5')

    def test_inherited_choice_text_prefetch_still_requires_review(self):
        # The inherited extractor prioritizes option-text matches over boxes;
        # only its balanced-box path qualifies for this conservative automation.
        self.assertEqual(self.automatic_result('The value is \\boxed{5}',options=['5','6']),(0,None))


if __name__=='__main__':unittest.main()
