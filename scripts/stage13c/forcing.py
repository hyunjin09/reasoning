"""V1 batch processor: one prescribed token per ordinary autoregressive step."""
import json
from pathlib import Path
from vllm.v1.sample.logits_processor.interface import LogitsProcessor,MoveDirectionality

class ForcedTrace(LogitsProcessor):
    def __init__(self,vllm_config,device,is_pin_memory):
        self.entries={};self.requests={}
    def is_argmax_invariant(self):return False
    def update_state(self,batch_update):
        if batch_update is None:return
        # Follow the V1 interface order, including same-index replacement.
        for i in batch_update.removed:self.entries.pop(i,None)
        for i,params,prompt,output in batch_update.added:
            self.entries.pop(i,None)
            spec=(params.extra_args or {}).get('stage13c_forced')
            if spec is None:continue
            key=spec['receipt']
            if key not in self.requests:
                assert spec['ids'][-1]==spec['close_id']
                assert len(spec['ids'])==spec['reasoning_count']+1
                self.requests[key]=dict(spec=spec,steps=0,last=-1,receipt_saved=False,resumptions=0)
            else:self.requests[key]['resumptions']+=1
            state=self.requests[key];state['output']=output
            self.entries[i]=state
        for a,b,direction in batch_update.moved:
            sa=self.entries.pop(a,None);sb=self.entries.pop(b,None)
            if sa is not None:self.entries[b]=sa
            if sb is not None and direction==MoveDirectionality.SWAP:self.entries[a]=sb
    def apply(self,logits):
        for i,state in self.entries.items():
            spec=state['spec'];ids=spec['ids'];output=state['output'];p=len(output)
            if p<=len(ids):
                assert p==state['last']+1,('Not a single autoregressive step',p,state['last'])
                if p:assert output[-1]==ids[p-1],('Forced token mismatch',p)
                state['last']=p
            if p<len(ids):
                logits[i].fill_(-float('inf'));logits[i,ids[p]]=0
                state['steps']+=1
            else:
                # Closing the native reasoning channel is mandatory. No reopening.
                logits[i,spec['open_id']]=-float('inf')
                if not state['receipt_saved']:
                    assert output[:len(ids)]==ids and state['steps']==len(ids)
                    path=Path(spec['receipt']);path.parent.mkdir(parents=True,exist_ok=True)
                    with path.open('x') as f:
                        json.dump(dict(forced_token_ids=ids,reasoning_token_count=spec['reasoning_count'],
                            forced_decoding_step_count=state['steps'],close_marker_position=len(ids)-1,
                            answer_generation_start_position=len(ids),one_token_per_step=True,
                            kv_request_continuation=True,persistent_batch_resumptions=state['resumptions'],
                            implementation='One masked-logit token per V1 autoregressive forward; no forced-prefix prefill.'),f,indent=2)
                    state['receipt_saved']=True
        return logits
