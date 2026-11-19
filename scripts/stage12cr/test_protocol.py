import unittest
from scripts.stage12cr.protocol import select_fresh, thinking_gate, authorize_manifest

class ProtocolTests(unittest.TestCase):
    def test_fresh_identity_only_balanced_and_disjoint(self):
        rows=[dict(item_id=str(i),family_id=f'f{i}',answer_type='multiple_choice' if i<20 else 'open_ended',answer='secret') for i in range(61)]
        chosen=select_fresh(rows,[str(i) for i in range(12)])
        self.assertEqual(len(chosen),12)
        self.assertEqual(sum(rows[int(i)]['answer_type']=='multiple_choice' for i in chosen),5)
        self.assertFalse(set(chosen)&set(map(str,range(12))))
        self.assertEqual(chosen,select_fresh(list(reversed(rows)),[str(i) for i in range(12)]))
    def test_phase_specific_gates_and_repetition_not_excluded(self):
        rows=[dict(INPUT_VALID=True,SCOREABLE=i<10,TRUNCATED_BEFORE_OUTCOME=i==11,R1=True) for i in range(12)]
        self.assertFalse(thinking_gate(rows,'same12')['pass'])
        self.assertTrue(thinking_gate(rows,'fresh12')['pass'])
        rows[10]['SCOREABLE']=True
        self.assertTrue(thinking_gate(rows,'same12')['pass'])
        rows[10]['TRUNCATED_BEFORE_OUTCOME']=True
        self.assertFalse(thinking_gate(rows,'same12')['pass'])
    def test_fresh_launch_is_gated_but_cot_independent(self):
        frozen={'config_sha256':'hash','tasks':[{'task_id':'T_1','arm':'T','item_id':'1'}], 'fresh12_ids':['1']}
        m={'frozen':True,'phase':'fresh12','arm':'T','config_sha256':'hash','rows':frozen['tasks']}
        with self.assertRaises(AssertionError):authorize_manifest(m,frozen,False)
        authorize_manifest(m,frozen,True)
        frozen['tasks']=[{'task_id':'C_2','arm':'C','item_id':'2'}];frozen['cot_ids']=['2']
        m.update(phase='cot',arm='C',rows=frozen['tasks'])
        authorize_manifest(m,frozen,False)

if __name__=='__main__':unittest.main()
