"""Prospective v2: identify obligations before deciding whether to acquire."""
from scripts.stage14e.contracts_v2 import PROPERTIES,validate_demand,compile_target,build_catalog
from scripts.stage14d1_pilot.interface_v5 import object_schema
COVERAGE=['UNKNOWN','TENTATIVE','ASSERTED_IN_PREFIX','GIVEN_IN_QUESTION','NONVISUAL_DERIVATION']
def ledger_schema(catalog):
 entry=object_schema(dict(source_object={'type':'string','minLength':1,'maxLength':240},property={'enum':PROPERTIES},source_frame={'type':'string','minLength':1,'maxLength':320},
  source_refs={'type':'array','minItems':1,'maxItems':8,'items':{'enum':[s['id'] for s in catalog]}},coverage={'enum':COVERAGE}))
 return object_schema(dict(obligations={'type':'array','minItems':0,'maxItems':3,'items':entry}))
def compile_ledger(record,catalog):
 if not isinstance(record,dict) or set(record)!={'obligations'} or not isinstance(record['obligations'],list) or len(record['obligations'])>3:raise ValueError('LEDGER_SCHEMA')
 index={s['id']:s for s in catalog};compiled=[]
 for o in record['obligations']:
  if not isinstance(o,dict) or set(o)!={'source_object','property','source_frame','source_refs','coverage'} or o['coverage'] not in COVERAGE:raise ValueError('OBLIGATION_SCHEMA')
  q={'status':'QUERY','need':'REINSPECT' if o['coverage']=='TENTATIVE' else 'NEW_VISUAL','target':o['source_object'],'property':o['property'],'frame':o['source_frame'],'source_refs':o['source_refs'],'answer_value':None}
  ok,reason=validate_demand(q,catalog)
  if not ok:raise ValueError(reason)
  origins={index[s]['source'] for s in o['source_refs']}
  if o['coverage']=='ASSERTED_IN_PREFIX' and 'prefix' not in origins:raise ValueError('NO_ASSERTION_PROVENANCE')
  if o['coverage']=='GIVEN_IN_QUESTION' and 'question' not in origins:raise ValueError('NO_GIVEN_PROVENANCE')
  compiled.append(compile_target(q,catalog))
 eligible=[j for j,o in enumerate(record['obligations']) if o['coverage'] in ['UNKNOWN','TENTATIVE']]
 selected=eligible[0] if eligible else None
 return {'target':compiled[selected] if selected is not None else {'status':'NONE','reason':'NO_UNRESOLVED_SOURCE_OBLIGATION'},'selected_index':selected,'eligible_indices':eligible,'transport_valid':True,'semantic_coverage_certified':False}
def ledger_prompt(row):
 cat=build_catalog(row['question'],row['prefix'])
 return '''Audit the VISUAL PREMISES of this mathematical problem before deciding whether any image reading is needed. Do not solve the problem.
First identify up to three minimal source-resolvable facts or coherent structures the original question requires. A required fact is a premise needed for calculation, not the unknown answer itself. For a relationship/arrangement, name the relevant entities and the whole frame needed to bind them. Order obligations by what the current reasoning needs next. An empty list is permitted for a wholly text-sufficient question.
For each obligation describe ONLY what to inspect, never what its visual value is. Then compare it against the supplied prefix and assign coverage LAST:
UNKNOWN: the required observed value/relationship has not been explicitly established.
TENTATIVE: the prefix guesses, questions, changes or proposes the visual premise rather than establishing it.
ASSERTED_IN_PREFIX: the prefix explicitly records the needed observed value/binding as a settled source fact. Cite its exact P source refs. Mentioning an object, an intended calculation, a generic template or saying "I need to read" is NOT coverage.
GIVEN_IN_QUESTION: the required value/relation is explicitly supplied by the question; cite Q source refs.
NONVISUAL_DERIVATION: the quantity can only be calculated, not read as a source premise.
Do not classify an entire diagram as covered merely because its object names or some given numbers occur in the prefix. Do not assume the solver's imagined generic arrangement matches the source. Conversely, do not request new acquisition when all required source premises are explicitly settled and only calculation remains. These are judgments of the supplied text, not certifications that the solver is visually correct.
Return JSON {"obligations":[...]}. Each entry has source_object (a visible entity/structure noun phrase), property, source_frame (ordinary visual context), source_refs, coverage, in that order. Keep source_object/source_frame value-free: no guessed counts, coordinates, colors, relations or answers. Source-given structural identifiers may identify a source, but numbers must occur in cited spans. Q000/P000 catalog IDs belong ONLY in source_refs, never in the visual address. Use "the original image" if a more specific frame cannot be named. Do not quote catalog lines into the address. The host will acquire the first UNKNOWN/TENTATIVE obligation or abstain when none exists. Do not force an acquisition.
Properties: '''+', '.join(PROPERTIES)+'.\nExact source catalog:\n'+'\n'.join(f"{s['id']} [{s['source']}] {s['text']}" for s in cat)
