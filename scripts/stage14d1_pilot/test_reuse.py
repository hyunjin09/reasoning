"""Reuse cannot silently import stale short continuations or mixed protocols."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts.stage14d1_pilot.common import sha
from scripts.stage14d1_pilot.reuse import load_reusable_state

class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir='runs/stage14d1_pilot')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); (self.root/'states').mkdir()
        self.row=dict(item_id='a',family_id='family_a',seed=7,prefix_sha256='prefix')
        self.put(self.root/'environment.json',dict(runtime_sha256='version5'))
        self.state=dict(item_id='a',family_id='family_a',query_valid=False,
            query_generation=self.receipt('a_query','query'),locator_generation=None,
            readouts={arm:dict(generation_path=None,value=None) for arm in ['G','Q','QI','QIA','QGL']},
            continuation_paths={'N':'old_short_generation'},logical_continuations={'N':'a_N'})
        self.path=self.root/'states/a.json';self.put(self.path,self.state)
    def put(self,p,d):p.write_text(json.dumps(d))
    def receipt(self,rid,kind):
        folder=self.root/rid;folder.mkdir()
        self.put(folder/'input.json',dict(self.row,kind=kind,cap=2048))
        self.put(folder/'generation.json',dict(raw_decoded_response='{}'))
        self.put(folder/'result.json',dict(input_sha256=sha(folder/'input.json'),generation_sha256=sha(folder/'generation.json')))
        return str(folder/'generation.json')
    def test_reuses_bad_queries_without_reselection_but_not_old_solvers(self):
        s=load_reusable_state(self.path,self.row,'version5')
        self.assertFalse(s['query_valid']);self.assertNotIn('continuation_paths',s)
        self.assertEqual(s['reused_acquisition_state'],str(self.path))
        self.assertIn('continuation_paths',json.loads(self.path.read_text()))
    def test_protocol_and_family_mismatch_rejected(self):
        for row,digest in [(self.row,'oldversion'),(dict(self.row,item_id='b'),'version5')]:
            with self.assertRaises(ValueError):load_reusable_state(self.path,row,digest)
    def test_tampered_receipt_rejected(self):
        self.put(self.root/'a_query/generation.json',dict(raw_decoded_response='changed'))
        with self.assertRaises(ValueError):load_reusable_state(self.path,self.row,'version5')
    def test_cross_attempt_reuse_requires_exact_component_allowlist(self):
        child=self.root/'new';(child/'states').mkdir(parents=True)
        self.put(child/'environment.json',dict(runtime_sha256='version6'))
        path=child/'states/a.json';self.put(path,self.state)
        with self.assertRaises(ValueError):load_reusable_state(path,self.row,'version6')
        ref=self.state['query_generation']
        result=load_reusable_state(path,self.row,'version6',helper_allowlist={ref:sha(ref)})
        self.assertEqual(result['query_generation'],ref)
        with self.assertRaises(ValueError):load_reusable_state(path,self.row,'version6',helper_allowlist={ref:'bad_hash'})
    def test_solver_receipt_cannot_masquerade_as_helper(self):
        inp=self.root/'a_query/input.json';d=json.loads(inp.read_text());d['kind']='solver';d['cap']=256;self.put(inp,d)
        result=self.root/'a_query/result.json';d=json.loads(result.read_text());d['input_sha256']=sha(inp);self.put(result,d)
        with self.assertRaises(ValueError):load_reusable_state(self.path,self.row,'version5')
if __name__=='__main__':unittest.main()
