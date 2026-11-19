import unittest
from scripts.stage12xs.execution_v2 import validate_tasks, native_seed

class ExecutionTests(unittest.TestCase):
    def test_a_requires_every_arm_once_and_never_other_family(self):
        rows=[dict(task_id=a+'_x',item_id='x',arm=a,cap=256 if a=='E' else 32768,image=None if a=='O' else 'image') for a in 'ENO']
        validate_tasks(rows, {'x'}, 'A')
        for bad in [rows[:-1], rows+[rows[0]], [dict(t,item_id='y') for t in rows]]:
            with self.assertRaises(AssertionError):validate_tasks(bad, {'x'}, 'A')
        with self.assertRaises(AssertionError):validate_tasks([dict(t,image='leak') if t['arm']=='O' else t for t in rows],{'x'},'A')

    def test_b_never_includes_non_b4_or_changes_budget(self):
        rows=[dict(task_id=a+'_x',item_id='x',arm=a,cap=32768 if a=='C' else 81920,image='image') for a in ['C','T']]
        validate_tasks(rows,{'x'},'B')
        with self.assertRaises(AssertionError):validate_tasks(rows,{'y'},'B')
        with self.assertRaises(AssertionError):validate_tasks([dict(t,cap=40960) if t['arm']=='T' else t for t in rows],{'x'},'B')

    def test_native_seed_preserves_inherited_family_recipe(self):
        import hashlib
        expected=int(hashlib.sha256(b'stage12a-gen-v1|family').hexdigest()[:8],16)%(2**31)
        self.assertEqual(native_seed('family'),expected)

if __name__=='__main__':unittest.main()
