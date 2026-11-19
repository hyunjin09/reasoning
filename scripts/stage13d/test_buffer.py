import json,tempfile,unittest
from pathlib import Path
import torch
from vllm import SamplingParams
from vllm.v1.sample.logits_processor.interface import BatchUpdate,MoveDirectionality
from scripts.stage13d.buffer import ImmediateBuffer
class BufferTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir='runs');self.addCleanup(self.temp.cleanup)
        self.p=ImmediateBuffer(None,torch.device('cpu'),False)
    def params(self,name='r',prefix=None):
        return SamplingParams(extra_args={'stage13d_buffer':dict(ids=(prefix or [2,3,8,4])+[5],reasoning_count=2,
            close_id=8,prefix_ids=[4],candidate_ids={'A':[5],'B':[6]},selected_candidate='A',
            receipt=str(Path(self.temp.name)/(name+'.json')))})
    def test_raw_logprobs_exact_force_and_zero_free_steps(self):
        ids=[];self.p.update_state(BatchUpdate(1,[],[(0,self.params(),[1],ids)],[]))
        base=torch.arange(10,dtype=torch.float32).reshape(1,10)
        for x in [2,3,8,4,5]:
            logits=self.p.apply(base.clone());self.assertEqual(logits.argmax().item(),x)
            self.assertEqual(torch.isfinite(logits).sum(),1);ids.append(x)
        receipt=json.loads((Path(self.temp.name)/'r.json').read_text())
        self.assertEqual(receipt['free_generated_tokens'],0)
        self.assertEqual(receipt['forced_decoding_step_count'],5)
        self.assertAlmostEqual(receipt['option_token_logprobs']['A'][0],base.log_softmax(-1)[0,5].item())
        self.assertAlmostEqual(receipt['option_token_logprobs']['B'][0],base.log_softmax(-1)[0,6].item())
        with self.assertRaises(AssertionError):self.p.apply(base.clone())
    def test_rejects_skipped_step(self):
        out=[];self.p.update_state(BatchUpdate(1,[],[(0,self.params(),[1],out)],[]))
        self.p.apply(torch.ones(1,10));out.extend([2,3])
        with self.assertRaises(AssertionError):self.p.apply(torch.ones(1,10))
    def test_batch_swap_and_unforced_semantic_pass_through(self):
        a=[];self.p.update_state(BatchUpdate(2,[],[(0,self.params(),[1],a),(1,SamplingParams(),[1],[])],[]))
        self.p.apply(torch.ones(2,10));a.append(2)
        self.p.update_state(BatchUpdate(2,[],[],[(0,1,MoveDirectionality.SWAP)]))
        out=self.p.apply(torch.ones(2,10));self.assertEqual(out[1].argmax().item(),3)
        self.assertTrue(torch.equal(out[0],torch.ones(10)))
    def test_actual_loader(self):
        from vllm.v1.sample.logits_processor import _load_logitsprocs_by_fqcns
        self.assertEqual(_load_logitsprocs_by_fqcns(['scripts.stage13d.buffer:ImmediateBuffer']),[ImmediateBuffer])
