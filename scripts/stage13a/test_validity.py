import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.stage13a import review
from scripts.stage13a.execution import save,load

class ReviewValidityTests(unittest.TestCase):
    def test_normal_stop_no_answer_differs_from_cap_missing(self):
        with tempfile.TemporaryDirectory(dir='runs/stage13a/v1') as tmp,patch.object(review,'ROOT',Path(tmp)):
            for tid,cap in [('normal',False),('cap',True),('cap_final',True)]:
                save(Path(tmp)/'audit/review_packets'/f'{tid}.json',dict(arm='I_EQ',cap_hit=cap,checks={'input':True}))
                review.record(tid,'7' if tid=='cap_final' else None,'Synthetic response-only validity check.')
            normal=load(Path(tmp)/'audit/technical_decisions/normal.json')
            cap=load(Path(tmp)/'audit/technical_decisions/cap.json')
            final=load(Path(tmp)/'audit/technical_decisions/cap_final.json')
            self.assertEqual(normal['outcome'],'__NO_ANSWER__')
            self.assertTrue(normal['validity']['TECHNICALLY_VALID'])
            self.assertTrue(cap['validity']['TRUNCATED_BEFORE_OUTCOME'])
            self.assertFalse(cap['validity']['TECHNICALLY_VALID'])
            self.assertTrue(final['validity']['TECHNICALLY_VALID'])
    def test_thinking_guard_requires_instruct_qc_closed(self):
        with tempfile.TemporaryDirectory(dir='runs/stage13a/v1') as tmp,patch.object(review,'ROOT',Path(tmp)):
            with self.assertRaises(AssertionError):review.blind_guard('T_EQ')
            review.blind_guard('I_EQ')
            save(Path(tmp)/'audit/I_EQ_scoring_closed.json',dict(test=True))
            review.blind_guard('T_EQ')

if __name__=='__main__':unittest.main()
