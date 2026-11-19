import hashlib
import unittest
from scripts.stage14c.common import ROOT,all_tasks,rows,load
from scripts.stage14c.input_adapter import source_image,prepare

class RunContractTests(unittest.TestCase):
    def test_main_pairs_and_source_identity(self):
        cohort={r['family_id']:r for r in rows(ROOT/'source/cohort_manifest.jsonl')}
        evidence={r['family_id']:r for r in rows(ROOT/'source/evidence_atoms.jsonl')}
        tasks=all_tasks('main');self.assertEqual(len(tasks),4588)
        for t in tasks:
            c=cohort[t['family_id']]
            expected=c['question'] if t['condition']=='native' else 'Task-critical visual evidence:\n'+evidence[t['family_id']]['serialized_evidence']+'\n\n'+c['question']
            self.assertEqual(t['prompt'],expected)
            self.assertNotIn('gold',t)
            self.assertEqual(bool(t['image_reference']),t['condition']=='native')
            self.assertEqual(t['cap'],32768 if t['model_key']=='I' else 81920)
            self.assertEqual(t['seed'],int(hashlib.sha256(f'stage14c-v1|{t["benchmark"]}|{t["family_id"]}|r0'.encode()).hexdigest(),16)%2**31)
    def test_preflight_task_coverage_and_reuse(self):
        main={t['task_id']:t for t in all_tasks('main')};pre=all_tasks('preflight')
        self.assertEqual(len(pre),46)
        for t in pre:
            if t['condition']!='seed_replay':self.assertEqual(t,main[t['task_id']])
        self.assertEqual({(t['benchmark'],t['category']) for t in pre if t['condition']=='native'},
                         {(t['benchmark'],t['category']) for t in main.values()})
    def test_exact_external_image_decode_and_text_only_path(self):
        for b in ['MMStar','BlindTest']:
            t=next(t for t in all_tasks('preflight') if t['benchmark']==b and t['condition']=='native')
            im=source_image(t);self.assertGreater(im.width,1)
        class Processor:
            def apply_chat_template(self,messages,**kwargs):
                assert kwargs==dict(tokenize=False,add_generation_prompt=True)
                return messages[0]['content'][0]['text']+'<|im_start|>assistant\n'
        t=next(t for t in all_tasks('preflight') if t['condition']=='equal_evidence')
        inp,msg=prepare(t,Processor(),None,None)
        self.assertNotIn('multi_modal_data',inp);self.assertEqual(msg[0]['content'][0]['text'],t['prompt'])

if __name__=='__main__':unittest.main()
