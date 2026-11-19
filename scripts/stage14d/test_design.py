import unittest
from scripts.stage14d.design import select_panel, classify, pair_effect, render_directive, enforce_release, arm_order

class DesignTest(unittest.TestCase):
    def examples(self,n=80):
        return [dict(family_id=f'f{i}',alias_member_item_ids=[str(i)],answer_type='MC' if i%2 else 'open',has_structured_atom=i%3==0,subject=['algebra','geometry'][i%2],difficulty=i%5+1,num_e_star_atoms=i%4+1,evidence_types={'quantity':i%2==0}) for i in range(n)]
    def test_selection_is_input_order_invariant(self):
        x=self.examples();self.assertEqual(select_panel(x,30,'fixed'),select_panel(list(reversed(x)),30,'fixed'))
    def test_selection_enforces_exact_unique_size(self):
        self.assertEqual(len({r['family_id'] for r in select_panel(self.examples(),30,'fixed')}),30)
    def test_aliases_cannot_be_independent(self):
        x=self.examples();x[1]['alias_member_item_ids']=x[0]['alias_member_item_ids']
        with self.assertRaises(ValueError):select_panel(x,30,'fixed')
    def test_no_silent_source_shortfall(self):
        with self.assertRaises(ValueError):select_panel(self.examples(3),4,'fixed')
    def test_missing_is_not_failure(self):
        self.assertIsNone(classify('UNSCORABLE','CORRECT'));self.assertIsNone(classify('WRONG','UNSCORABLE'));self.assertEqual(classify('CORRECT','UNSCORABLE'),'S3')
    def test_correct_evidence_uses_thinking_joint_stratum(self):
        self.assertEqual(classify('WRONG','CORRECT'),'S1');self.assertEqual(classify('WRONG','WRONG'),'S2')
    def test_missingness_bounds_keep_planned_families(self):
        e=pair_effect([('CORRECT','WRONG'),('UNSCORABLE','CORRECT')],draws=100,seed=5)
        self.assertEqual(e['complete_pairs'],1);self.assertEqual(e['effect'],1);self.assertEqual(e['bounds'],[0,0.5])
    def test_unapproved_or_unclosed_stage_cannot_launch(self):
        with self.assertRaises(ValueError):enforce_release(dict(user_approved=False,gpu_hours=50,cv_closed=True,calibration_pass=True))
        with self.assertRaises(ValueError):enforce_release(dict(user_approved=True,gpu_hours=50,cv_closed=False,calibration_pass=True))
        with self.assertRaises(ValueError):enforce_release(dict(user_approved=True,gpu_hours=50,cv_closed=True,calibration_pass=False))
    def test_target_value_may_not_be_injected(self):
        with self.assertRaises(ValueError):render_directive('LOOK_TARGET',{'request':'Read AB=3','value':'3'})
    def test_unreviewed_target_is_not_executable(self):
        with self.assertRaises(ValueError):render_directive('LOOK_TARGET',{'request':'Read the marked length of AB','review_status':'PENDING'})
    def test_b0_is_exact_empty_and_order_balanced(self):
        self.assertEqual(render_directive('B0',{}),'')
        orders=[arm_order(i) for i in range(5)];self.assertTrue(all(len({o[j] for o in orders})==5 for j in range(5)))
    def test_target_request_does_not_change_literal(self):
        x={'request':'Read the marked length of AB.','review_status':'SOURCE_VALID_VALUE_FREE','source_request_sha256':__import__('hashlib').sha256(b'Read the marked length of AB.').hexdigest(),'value':None}
        self.assertIn(x['request'],render_directive('LOOK_TARGET',x))


class InferenceTest(unittest.TestCase):
    def test_no_discordance_is_not_positive(self):
        from scripts.stage14d.design import paired_exact_p
        self.assertEqual(paired_exact_p([('CORRECT','CORRECT')]*10)['p_two_sided'],1)
    def test_exact_discordance_probability(self):
        from scripts.stage14d.design import paired_exact_p
        r=paired_exact_p([('CORRECT','WRONG')]*10)
        self.assertAlmostEqual(r['p_two_sided'],2/1024)
        self.assertEqual(r['target_only'],10)
    def test_two_claim_holm_keeps_both_claims(self):
        from scripts.stage14d.design import holm_two
        self.assertEqual(holm_two({'P1':.02,'P2':.049}),{'P1':.04,'P2':.049})
    def test_missing_second_endpoint_prevents_joint_claim(self):
        from scripts.stage14d.design import holm_two
        self.assertEqual(holm_two({'P1':.001,'P2':None}),{'P1':None,'P2':None})

class RequestSealTest(unittest.TestCase):
    def test_changed_request_is_rejected(self):
        x={'request':'Read a different source.','review_status':'SOURCE_VALID_VALUE_FREE','source_request_sha256':'0'*64}
        with self.assertRaises(ValueError):render_directive('LOOK_TARGET',x)

if __name__=='__main__':unittest.main()
