import unittest
from scripts.stage14c.common import *
from scripts.stage14c.d1_worker import authorize,prepare
class D1Tests(unittest.TestCase):
    def test_no_launch_before_primary_seal(self):
        with self.assertRaises(FileNotFoundError):
            authorize(dict(mode='D1',config_sha256=sha(ROOT/'spec/model_and_recipe_identity.json')))
    def test_frozen_membership_and_probe_inputs(self):
        ids=load(ROOT/'manifests/D1_source_membership_v1.json')['families'];tasks=all_tasks('D1')
        self.assertEqual(len(tasks),600)
        for b,fs in ids.items():self.assertEqual({t['family_id'] for t in tasks if t['benchmark']==b},set(fs))
        for t in tasks:
            self.assertTrue(t['image_reference']);self.assertNotIn('Task-critical visual evidence:',t['prompt'])
            self.assertTrue(t['prompt'].startswith('Inspect the image for the task below.'))
    def test_math_native_image_integrity_adapter(self):
        task=next(t for t in all_tasks('D1') if t['benchmark']=='math')
        def build(row,image_func,dataset):
            image=image_func(row);self.assertGreater(image.width,1)
            return row
        inp,msg=prepare(task,None,build,lambda messages,processor:dict(prompt=messages['question']))
        self.assertEqual(inp['prompt'],task['prompt'])
        self.assertEqual(msg[0]['content'][0]['sha256'],task['image_sha256'])
if __name__=='__main__':unittest.main()
