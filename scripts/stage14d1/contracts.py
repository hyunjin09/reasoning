"""No-oracle SAVA input contracts and deterministic source-coordinate transforms."""
import json,re,math,hashlib
RUNTIME_KEYS={'item_id','family_id','question','image','image_sha256','prefix','prefix_sha256','seed','eligible','original_chat_prompt','original_messages','original_image_pixels','original_image_sizes'}
ARMS=('N','G','Q','QI','QIA','QGL')
def fingerprint(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def safe_payload(row):
 if set(row)!=RUNTIME_KEYS:raise ValueError('Unexpected/missing runtime fields: '+repr(set(row)^RUNTIME_KEYS))
 if not all(isinstance(row[k],str) for k in ['question','image','prefix']):raise ValueError('Invalid text inputs')
 return row

def parse_record(raw):
 # Native Thinking JSON is accepted only after its official reasoning boundary.
 if '</think>' not in raw:return None
 body=raw.rsplit('</think>',1)[-1].strip().removesuffix('<|im_end|>').strip()
 body=re.sub(r'^```(?:json)?\s*','',body);body=re.sub(r'\s*```$','',body)
 def unique(pairs):
  d={}
  for k,v in pairs:
   if k in d:raise ValueError('Duplicate key')
   d[k]=v
  return d
 try:
  value=json.loads(body,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
  return value if isinstance(value,dict) else None
 except (ValueError,TypeError):return None

def validate_query(q,question,prefix):
 if not isinstance(q,dict):return False,'NOT_COMMITTED_JSON'
 if q.get('answer_value','MISSING') is not None:return False,'VALUE_SLOT_NOT_NULL'
 if q.get('status')=='NONE':return (set(q)<={'status','answer_value','reason'},'NONE')
 fields={'status','subgoal','entity','entity_id','predicate','spatial_reference','query','answer_value','numeric_provenance'}
 if set(q)!=fields or q.get('status')!='QUERY':return False,'SCHEMA'
 if any(not isinstance(q[k],str) or not q[k].strip() or len(q[k])>1000 for k in fields-{'status','answer_value','numeric_provenance'}):return False,'TEXT_FIELDS'
 needed=set(re.findall(r'\d+(?:\.\d+)?',' '.join(q[k] for k in ['subgoal','entity','entity_id','predicate','spatial_reference','query'])))
 proven=set()
 if not isinstance(q['numeric_provenance'],list):return False,'NUMERIC_PROVENANCE'
 for p in q['numeric_provenance']:
  if not isinstance(p,dict) or set(p)!={'number','source','quote'} or p['source'] not in ['question','prefix']:return False,'NUMERIC_PROVENANCE'
  if not all(isinstance(p[k],str) for k in p):return False,'NUMERIC_PROVENANCE'
  source=question if p['source']=='question' else prefix
  if not p['quote'] or p['quote'] not in source or p['number'] not in re.findall(r'\d+(?:\.\d+)?',p['quote']):return False,'UNSUPPORTED_NUMBER'
  proven.add(p['number'])
 if not needed<=proven:return False,'UNSUPPORTED_NUMBER'
 return True,'SCHEMA_VALID_NOT_SEMANTICALLY_CERTIFIED'

def box_pixels(box,w,h):
 if not isinstance(box,list) or len(box)!=4 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in box):raise ValueError('Invalid normalized ROI')
 x0,y0,x1,y1=box
 if not 0<=x0<x1<=1 or not 0<=y0<y1<=1:raise ValueError('Invalid normalized ROI')
 return (math.floor(x0*w),math.floor(y0*h),math.ceil(x1*w),math.ceil(y1*h))
def pixel_to_normalized(box,w,h):return [box[0]/w,box[1]/h,box[2]/w,box[3]/h]
def validate_address(a,w,h):
 if not isinstance(a,dict) or set(a)!={'mode','boxes','source_reference','uncertainty'}:return False
 if a['mode'] not in ['LOCAL','MULTI','GLOBAL','UNRESOLVABLE'] or not isinstance(a['boxes'],list):return False
 if a['mode'] in ['GLOBAL','UNRESOLVABLE']:return len(a['boxes'])==0
 if not (len(a['boxes'])==1 if a['mode']=='LOCAL' else 1<len(a['boxes'])<=2):return False
 try:
  for b in a['boxes']:box_pixels(b,w,h)
 except ValueError:return False
 return True

def valid_readout(r):
 return isinstance(r,dict) and set(r)=={'target','read_value','supporting_source','uncertainty'} and all(isinstance(r[k],str) for k in r) and r['uncertainty'] in ['certain','uncertain','unresolvable']
def solver_suffix(readout):
 if readout is None:return ''
 return '\n\n[Visual lookup record; this is an unverified model observation and may be wrong.]\n'+json.dumps(readout,ensure_ascii=False)+'\n[Continue the same problem from the reasoning above. Check consistency; do not assume the lookup is correct.]\n'
def choose_checkpoint(text,max_chars):
 prefix=text[:max_chars]
 for marker in ['</think>','<|im_end|>','\\boxed','Final answer:','final answer:']:
  prefix=prefix.split(marker,1)[0]
 return prefix

QUERY_INSTRUCTION='''You are pausing a solver at its current reasoning prefix. Identify exactly ONE new visual fact needed by its next reasoning step. Use only the supplied question and prefix. Do not solve the problem. Do not guess or include the requested value. The target may be an entity, label binding, coordinate, count, relation or global structure. Return NONE if no new image fact is needed; do not force a query.
End with exactly one JSON object, no markdown. QUERY schema:
{"status":"QUERY","subgoal":"...","entity":"...","entity_id":"...","predicate":"...","spatial_reference":"...","query":"...","answer_value":null,"numeric_provenance":[{"number":"3","source":"question or prefix","quote":"exact quoted span containing that coordinate or identifier"}]}
Use numeric_provenance only for numbers actually in your query fields; all must be supported by exact question/prefix spans. Numbers are permitted as source addresses, not guessed answer values. Omit unneeded numbers. NONE schema: {"status":"NONE","answer_value":null,"reason":"..."}. Your final JSON must follow your normal completed reasoning boundary.'''
LOCATE_INSTRUCTION='''Locate the requested entity/property in the full original image. Do not read or propose its value and do not solve the task. Return exactly one final JSON object with keys mode, boxes, source_reference, uncertainty. mode is LOCAL (one coherent region), MULTI (two referenced regions), GLOBAL (whole configuration), or UNRESOLVABLE. boxes are normalized [xmin,ymin,xmax,ymax] in the original full image; use [] for GLOBAL/UNRESOLVABLE. Keep source_reference value-free. Do not invent a crop for a global relationship. uncertainty is certain or uncertain. Include no ground-truth guesses.'''
READ_INSTRUCTION='''Recover only the visual fact needed at this checkpoint. Do not solve the full problem. Preserve entity, coordinate and relationship identity using the original scene context. If unavailable or ambiguous say so, without guessing. End with exactly one JSON object: {"target":"source entity/property","read_value":"observed value or unknown","supporting_source":"where in the image; no full solution","uncertainty":"certain or uncertain or unresolvable"}.'''
def helper_prompt(row,kind,query=None,address=None):
 safe_payload(row)
 context='Original question:\n'+row['question']+'\n\nCurrent reasoning prefix (possibly mistaken):\n'+row['prefix']
 if kind=='query':return QUERY_INSTRUCTION+'\n\n'+context
 if kind=='locate':return LOCATE_INSTRUCTION+'\n\n'+context+'\n\nRequested visual query:\n'+json.dumps(query,ensure_ascii=False)
 if kind=='G':return READ_INSTRUCTION+'\nCheck the original image again for the next visual fact needed by the current reasoning.\n\n'+context
 out=READ_INSTRUCTION+'\n\n'+context+'\n\nRequested visual query:\n'+json.dumps(query,ensure_ascii=False)
 if address is not None:out+='\n\nPredicted source address (not verified):\n'+json.dumps(address,ensure_ascii=False)
 return out
