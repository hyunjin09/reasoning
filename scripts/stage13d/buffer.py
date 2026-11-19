"""Score raw model logits at a forced boundary; never allow a free token.

For singleton canonical MC letters, all candidate teacher-forced likelihoods
share the same history and are read from the same next-token distribution.
Only the first canonical letter is physically appended, then max_tokens stops
the request. Technical open-ended probes score one frozen multi-token sequence.
"""
import json
from pathlib import Path
from vllm.v1.sample.logits_processor.interface import LogitsProcessor,MoveDirectionality
class ImmediateBuffer(LogitsProcessor):
    def __init__(self,vllm_config,device,is_pin_memory):self.entries={};self.requests={}
    def is_argmax_invariant(self):return False
    def update_state(self,batch_update):
        if batch_update is None:return
        for i in batch_update.removed:self.entries.pop(i,None)
        for i,params,prompt,output in batch_update.added:
            self.entries.pop(i,None);spec=(params.extra_args or {}).get('stage13d_buffer')
            if spec is None:continue
            key=spec['receipt']
            if key not in self.requests:
                n=spec['reasoning_count'];assert spec['ids'][n]==spec['close_id']
                candidates=spec['candidate_ids'];lengths={len(x) for x in candidates.values()}
                assert lengths=={1} or len(candidates)==1
                assert spec['ids'][n+1:]==spec['prefix_ids']+candidates[spec['selected_candidate']]
                self.requests[key]=dict(spec=spec,steps=0,last=-1,logps={a:[] for a in candidates},resumptions=0)
            else:self.requests[key]['resumptions']+=1
            state=self.requests[key];state['output']=output;self.entries[i]=state
        for a,b,d in batch_update.moved:
            sa=self.entries.pop(a,None);sb=self.entries.pop(b,None)
            if sa is not None:self.entries[b]=sa
            if sb is not None and d==MoveDirectionality.SWAP:self.entries[a]=sb
    def apply(self,logits):
        for i,s in self.entries.items():
            spec=s['spec'];ids=spec['ids'];out=s['output'];p=len(out)
            assert p<len(ids),'No free token is permitted after candidate scoring'
            assert p==s['last']+1,('Skipped autoregressive step',p,s['last'])
            if p:assert out[-1]==ids[p-1]
            s['last']=p;s['steps']+=1
            candidate_start=spec['reasoning_count']+1+len(spec['prefix_ids'])
            if p>=candidate_start:
                position=p-candidate_start
                # V1 invokes this before temperature/top-p/top-k/penalties.
                # No allowed-token masks or other custom processors are installed.
                raw=logits[i].float().log_softmax(-1)
                for label,tokens in spec['candidate_ids'].items():
                    s['logps'][label].append(float(raw[tokens[position]].item()))
            logits[i].fill_(-float('inf'));logits[i,ids[p]]=0
            if p==len(ids)-1:
                assert out==ids[:-1] and s['steps']==len(ids)
                path=Path(spec['receipt']);path.parent.mkdir(parents=True,exist_ok=True)
                with path.open('x') as f:json.dump(dict(
                    forced_token_ids=ids,reasoning_token_count=spec['reasoning_count'],
                    forced_decoding_step_count=s['steps'],close_marker_position=spec['reasoning_count'],
                    prefix_ids=spec['prefix_ids'],candidate_start_position=candidate_start,
                    candidate_ids=spec['candidate_ids'],selected_candidate=spec['selected_candidate'],
                    option_token_logprobs=s['logps'],free_generated_tokens=0,
                    one_token_per_step=True,kv_request_continuation=True,
                    persistent_batch_resumptions=s['resumptions'],
                    logprob_definition='Raw-model full-vocabulary fp32 log_softmax, before sampling transformations',
                    receipt_boundary='Last candidate token selected deterministically; final worker verifies emitted IDs.'),f,indent=2)
        return logits
