"""Value-separated demand/reader contracts. Source references are not truth labels."""
import hashlib,re
from scripts.stage14d1_pilot.interface_v5 import build_catalog,numeric_lexemes as legacy_numeric_lexemes,object_schema
from scripts.stage14d1.contracts import READ_INSTRUCTION
def numeric_lexemes(text):
 # A prose dimension separator is not an arithmetic negative sign.
 text=re.sub(r'(?i)\b(\d+(?:\.\d+)?(?:-(?:foot|feet|inch|inches|cm|mm|m))?)-by-(?=\d)',r'\1 by ',text)
 return legacy_numeric_lexemes(text)
PROPERTIES=['printed_label','count','spatial_relation','layout','connectivity','color','shape','ordering','marked_measurement','entity_binding']
NONE_REASONS=['GIVEN_IN_QUESTION','SOURCE_FACTS_ALREADY_ASSERTED','DERIVATION_ONLY','NO_IDENTIFIABLE_VISUAL_PREMISE']
QUERY_SCHEMA={'anyOf':[
 object_schema(dict(status={'const':'QUERY'},need={'enum':['NEW_VISUAL','REINSPECT']},target={'type':'string','minLength':1,'maxLength':240},
  property={'enum':PROPERTIES},frame={'type':'string','minLength':1,'maxLength':320},
  source_refs={'type':'array','minItems':1,'maxItems':8,'items':{'type':'string'}},answer_value={'type':'null'})),
 object_schema(dict(status={'const':'NONE'},reason={'enum':NONE_REASONS},answer_value={'type':'null'}))]}
READ_SCHEMA=object_schema(dict(target={'type':'string'},read_value={'type':'string'},supporting_source={'type':'string'},uncertainty={'enum':['certain','uncertain','unresolvable']}))
STRUCT_SCHEMA=object_schema(dict(status={'enum':['OBSERVED','PARTIAL','UNRESOLVABLE']},source_frame={'type':'string'},
 observations={'type':'array','maxItems':12,'items':object_schema(dict(entity={'type':'string'},property={'type':'string'},value={'type':'string'},visual_support={'type':'string'}))},
 unresolved={'type':'string'}))
FORBIDDEN=re.compile(r'\b(equals|equal to|the answer|correct option|must be|ignore|disregard|override|instructions?)\b|[=<>]|\n|\r',re.I)
def validate_demand(q,catalog):
 if not isinstance(q,dict) or q.get('answer_value','missing') is not None:return False,'ANSWER_OR_TYPE'
 if q.get('status')=='NONE':return (set(q)=={'status','reason','answer_value'} and q['reason'] in NONE_REASONS),'NONE'
 if set(q)!={'status','need','target','property','frame','source_refs','answer_value'} or q['status']!='QUERY':return False,'SCHEMA'
 if q['need'] not in ['NEW_VISUAL','REINSPECT'] or q['property'] not in PROPERTIES:return False,'SCHEMA'
 for k,lim in [('target',240),('frame',320)]:
  if not isinstance(q[k],str) or not 1<=len(q[k].strip())<=lim:return False,'TEXT'
  if re.search(r'\b[QP]\d{3}\b|\[(?:question|prefix)\]',q[k]):return False,'CATALOG_TAG_IN_VISUAL_ADDRESS'
  if FORBIDDEN.search(re.sub(r'<image\d+>','',q[k])):return False,'ASSERTION_OR_INSTRUCTION'
 refs=q['source_refs'];index={s['id']:s for s in catalog}
 if not isinstance(refs,list) or not 1<=len(refs)<=8 or not all(isinstance(s,str) for s in refs) or len(set(refs))!=len(refs):return False,'REFERENCES'
 if not all(s in index for s in refs):return False,'UNKNOWN_REFERENCE'
 selected=[index[s] for s in refs]
 if any(hashlib.sha256(s['text'].encode()).hexdigest()!=s['sha256'] for s in selected):return False,'CATALOG_HASH'
 text=' '.join(s['text'] for s in selected)
 if not numeric_lexemes(q['target']+' '+q['frame'])<=numeric_lexemes(text):return False,'UNSUPPORTED_NUMBER'
 # This certifies transport and guards obvious value injection, not semantic truth.
 return True,'VALID_TRANSPORT_SEMANTICS_UNCERTIFIED'
def compile_target(q,catalog):
 ok,why=validate_demand(q,catalog)
 if not ok:raise ValueError(why)
 if q['status']=='NONE':return {'status':'NONE','reason':q['reason']}
 return {'status':'QUERY','target':q['target'],'property':q['property'],'frame':q['frame'],
         'query':f"Read the {q['property'].replace('_',' ')} of {q['target']}. Source frame: {q['frame']}. Report only observed source information, not a solved quantity."}
def query_prompt(row):
 cat=build_catalog(row['question'],row['prefix'])
 return '''Identify the task-critical VISUAL PREMISE needed by this solver's current reasoning. First distinguish a source fact that can be read from the supplied image from a mathematical unknown that must be calculated. A word or number mentioned tentatively by the solver is not a verified observation. Reinspect a specific doubtful visual premise when needed. Do not ask for an unknown answer, computed length, future state, or the label of an already named label. If source facts are already explicitly established and the next operation is mathematical, choose NONE. NONE is permitted and must not be avoided.
For QUERY identify a coherent source object AND the relation/attribute needed, with enough frame to distinguish panels, rows, connected edges, sectors or corresponding entities. Prefer the minimum complete visual structure needed over an unnamed single point. The frame identifies what to inspect; it must not state the evidence value or assert a relation as true. Use question/prefix source_refs only to identify the premise. Do not include guessed counts, colors, measured values or proposed answers in target/frame. Structural identifiers may be used when present in cited spans. Do not solve the original problem.
The target is a visible object noun phrase, not the name of a property. The frame is an ordinary-language VISUAL coordinate/context description (for example, the labeled axes of the original plot), not a source-catalog address. Catalog identifiers such as Q000/P000 and tags such as [prefix] are permitted ONLY in source_refs; never copy them into target or frame. Do not quote a catalog line into frame. If no more specific visual frame can be named, use "the original image".
Return one compact JSON with fields in this order:
QUERY: status, need (NEW_VISUAL or REINSPECT), target, property, frame, source_refs, answer_value (null).
NONE: status, reason, answer_value (null).
Properties: '''+', '.join(PROPERTIES)+'.\nNONE reasons: '+', '.join(NONE_REASONS)+'.\n\nExact source catalog:\n'+'\n'.join(f"{s['id']} [{s['source']}] {s['text']}" for s in cat)
def reader_prompt(row,target,with_prefix=False,structured=False):
 if target.get('status')!='QUERY':raise ValueError('No target to read')
 instruction=READ_INSTRUCTION if not structured else '''Inspect the original image to supply only the requested visual evidence. Do not solve the mathematical problem or infer unprinted numerical values. First establish a source coordinate/frame using visible labels, rows, panels or boundaries. Then record the minimal observed entity-property-value bindings that jointly answer the request. For layouts/counts/connectivity, enumerate the actual visible components or connections in a consistent frame; do not replace them with a generic template. Separate unreadable/occluded/ambiguous facts into unresolved. A source structure may require several bindings. State only directly observed content or direct counting of visible components, not algebraic deductions. Return status (OBSERVED, PARTIAL, UNRESOLVABLE), source_frame, observations [{entity,property,value,visual_support}], unresolved. A confident statement is not a certificate of correctness.'''
 text=instruction+'\n\nOriginal question:\n'+row['question']
 if with_prefix:text+='\n\nSolver prefix (not verified):\n'+row['prefix']
 # Deliberately never serialize source_refs, quoted prefix spans, need rationale or candidate values.
 text+='\n\nVisual evidence request:\n'+target['query']
 return text

def budget_admissible(charged,reserved,ceiling=86400):
 return min(charged,reserved,ceiling)>=0 and charged+reserved<=ceiling
