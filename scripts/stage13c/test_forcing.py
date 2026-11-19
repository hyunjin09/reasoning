import tempfile,unittest
from pathlib import Path
import torch
from vllm import SamplingParams
from vllm.v1.sample.logits_processor.interface import BatchUpdate,MoveDirectionality
from scripts.stage13c.forcing import ForcedTrace

class ForcingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir='runs');self.addCleanup(self.temp.cleanup)
        self.p=ForcedTrace(None,torch.device('cpu'),False)
    def params(self,name='r',ids=None):
        return SamplingParams(extra_args={'stage13c_forced':dict(ids=ids or [2,3,8],reasoning_count=2,
            close_id=8,open_id=9,receipt=str(Path(self.temp.name)/(name+'.json')))})
    def test_force_each_token_then_normal_final_without_reopening(self):
        ids=[];self.p.update_state(BatchUpdate(1,[],[(0,self.params(),[1],ids)],[]))
        for expected in [2,3,8]:
            logits=self.p.apply(torch.ones(1,10));self.assertEqual(torch.isfinite(logits).sum(),1)
            self.assertEqual(logits.argmax().item(),expected);ids.append(expected)
        logits=self.p.apply(torch.ones(1,10));self.assertEqual(torch.isfinite(logits).sum(),9)
        self.assertEqual(logits[0,9],-float('inf'))
        import json
        receipt=json.loads((Path(self.temp.name)/'r.json').read_text())
        self.assertEqual(receipt['forced_decoding_step_count'],3)
        self.assertEqual(receipt['answer_generation_start_position'],3)
        self.assertTrue(receipt['one_token_per_step'])
    def test_detects_skipped_autoregressive_step(self):
        ids=[];self.p.update_state(BatchUpdate(1,[],[(0,self.params(),[1],ids)],[]))
        self.p.apply(torch.ones(1,10));ids.extend([2,3])
        with self.assertRaises(AssertionError):self.p.apply(torch.ones(1,10))
    def test_reused_index_and_swap_track_live_request(self):
        a=[];b=[]
        self.p.update_state(BatchUpdate(2,[],[(0,self.params('a'),[1],a),(1,self.params('b',[4,5,8]),[1],b)],[]))
        self.p.apply(torch.ones(2,10));a.append(2);b.append(4)
        self.p.update_state(BatchUpdate(2,[],[],[(0,1,MoveDirectionality.SWAP)]))
        out=self.p.apply(torch.ones(2,10));self.assertEqual(out.argmax(1).tolist(),[5,3])
        self.p.update_state(BatchUpdate(1,[0,1],[(0,SamplingParams(),[1],[])],[]))
        self.assertTrue(torch.equal(self.p.apply(torch.ones(1,10)),torch.ones(1,10)))
    def test_worker_class_string_loads_through_actual_vllm_loader(self):
        import ast
        from vllm.v1.sample.logits_processor import _load_logitsprocs_by_fqcns
        tree=ast.parse(Path('scripts/stage13c/worker.py').read_text())
        value=next(k.value.elts[0].value for node in ast.walk(tree) if isinstance(node,ast.Call)
                   for k in node.keywords if k.arg=='logits_processors')
        self.assertEqual(_load_logitsprocs_by_fqcns([value]),[ForcedTrace])

if __name__=='__main__':unittest.main()
