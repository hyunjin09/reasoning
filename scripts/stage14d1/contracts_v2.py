"""Versioned compact structured helper channel; native solver contract unchanged."""
from scripts.stage14d1.contracts import *
from scripts.stage14d1.contracts import parse_record as parse_thinking_record

def parse_record(raw):
 # Only for requests explicitly sealed as compact structured helpers. Never apply to native solver output.
 return parse_thinking_record('</think>'+raw)

def obj(props,required=None):return {'type':'object','properties':props,'required':list(props) if required is None else required,'additionalProperties':False}
S={'type':'string','maxLength':600}
QPROPS={k:S for k in ['subgoal','entity','entity_id','predicate','spatial_reference','query']}
QPROPS.update(status={'const':'QUERY'},answer_value={'type':'null'},numeric_provenance={'type':'array','maxItems':16,'items':obj({'number':{'type':'string'},'source':{'enum':['question','prefix']},'quote':S})})
SCHEMAS={
 'query':{'anyOf':[obj(QPROPS),obj({'status':{'const':'NONE'},'answer_value':{'type':'null'},'reason':S})]},
 'locate':obj({'mode':{'enum':['LOCAL','MULTI','GLOBAL','UNRESOLVABLE']},'boxes':{'type':'array','maxItems':2,'items':{'type':'array','minItems':4,'maxItems':4,'items':{'type':'number','minimum':0,'maximum':1}}},'source_reference':S,'uncertainty':{'enum':['certain','uncertain']}}),
 'read':obj({'target':S,'read_value':S,'supporting_source':S,'uncertainty':{'enum':['certain','uncertain','unresolvable']}})
}

def compact_prompt(prompt):
 # The native solver remains open-thinking. Helpers are controllers with no second long reasoning rollout.
 return prompt+'\nReturn the requested compact JSON object directly in the final channel. Do not solve the original task or produce another reasoning trace.'
