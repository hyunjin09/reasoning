import unittest
from unittest.mock import patch
import scripts.stage14b.coordinator as c

class CoordinatorTests(unittest.TestCase):
    def fixtures(self,missing=False):
        tt=[];meta=[]
        for model in 'IT':
            for branch in ('image','evidence','mathverse'):
                ident='verse:1:Text_Dominant' if branch=='mathverse' else 'mv:1'
                tt.append(dict(task_id=model+branch,model_key=model,condition='native' if branch=='mathverse' else branch,identity=ident))
                meta.append(dict(identity=ident,options=[],gold_answer='DO_NOT_USE_GOLD'))
        def checked(t):
            body='Final answer: 12345'
            if missing and t['task_id']=='Tevidence':body='unfinished'
            if t['model_key']=='T':body='thinking\n</think>\n'+body
            return dict(generation=dict(raw_decoded_response=body,tokens=12,finish_reason='stop'),receipt='outputs/test/result.json')
        return tt,meta,checked
    def exercise(self,missing=False):
        tt,meta,check=self.fixtures(missing);saved=[]
        with patch.object(c,'all_tasks',return_value=tt),patch.object(c,'rows',return_value=meta),patch.object(c,'checked',side_effect=check),patch.object(c,'sha',return_value='hash'),patch.object(c,'save',side_effect=lambda p,v:saved.append(v)):
            c.automated_response_review()
        return saved[0]
    def test_gate_ignores_gold_and_reports_automatic_scope(self):
        r=self.exercise()
        self.assertTrue(r['extraction_and_format_review_pass']);self.assertFalse(r['correctness_used'])
        self.assertIn('Automatic',r['review_scope'])
    def test_missing_branch_holds_instead_of_launching(self):
        with self.assertRaises(AssertionError):self.exercise(missing=True)

if __name__=='__main__':unittest.main()
