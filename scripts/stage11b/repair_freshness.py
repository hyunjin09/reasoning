"""Prospective source-only alias repair after a visually confirmed prior alias."""
import re,hashlib
from collections import defaultdict
from scripts.stage11b.common import ROOT,SEED,load,save,sha,now
from scripts.stage11b.protocol import hash_order

initial=load(ROOT/'stage11b_discovery_manifest.json')
reserve=load(ROOT/'audit/heldout_reserve.json')
old=load('outputs/stage9a/v1/stage9a_cohort_manifest.json')['rows']
pool=initial['rows']+reserve['rows'];allrows=old+pool
parent={r['family_id']:r['family_id'] for r in allrows}
def root(k):
    while parent[k]!=k:parent[k]=parent[parent[k]];k=parent[k]
    return k
tokens={r['item_id']:set(re.findall(r'[a-z0-9]+',r['question'].lower())) for r in allrows}
edges=[]
for i,a in enumerate(allrows):
    x=tokens[a['item_id']]
    for b in allrows[:i]:
        y=tokens[b['item_id']]
        if min(len(x),len(y))<20:continue
        overlap=len(x&y)/len(x|y)
        if overlap>=.45:
            parent[root(a['family_id'])]=root(b['family_id'])
            edges.append(dict(a=a['item_id'],b=b['item_id'],question_token_jaccard=overlap))
oldroots={root(r['family_id']) for r in old}
groups=defaultdict(list)
for r in pool:groups[root(r['family_id'])].append(r)
initial_order={r['item_id']:i for i,r in enumerate(initial['rows'])}
usable=[];excluded=[]
for group,rows in groups.items():
    if group in oldroots:excluded.extend(r['item_id'] for r in rows);continue
    rows.sort(key=lambda r:(initial_order.get(r['item_id'],10000),hash_order(r,SEED,'discovery')))
    r=dict(rows[0]);r['inherited_family_id']=r['family_id']
    members=sorted(x['family_id'] for x in rows)
    if len(members)>1:r['family_id']='stage11b_family_'+hashlib.sha256('|'.join(members).encode()).hexdigest()[:20]
    r['source_only_alias_item_ids']=sorted(x['item_id'] for x in rows)
    usable.append(r)
by={r['item_id']:r for r in usable};chosen=[];replacements=[]
used=set(initial_order)&set(by)
for original in initial['rows']:
    if original['item_id'] in by:r=by[original['item_id']]
    else:
        options=[r for r in usable if r['item_id'] not in used and all(r[k]==original[k] for k in ['subject','level','answer_format'])]
        assert options,'No silent sampling-stratum change'
        r=min(options,key=lambda r:hash_order(r,SEED,'discovery'))
        used.add(r['item_id']);replacements.append(dict(old_item_id=original['item_id'],new_item_id=r['item_id'],same_sampling_stratum=True))
    chosen.append(dict(r,discovery_order=len(chosen)))
assert len(chosen)==len({r['family_id'] for r in chosen})==128
save(ROOT/'stage11b_discovery_manifest_v2.json',dict(initial,at=now(),rows=chosen,
    supersedes=str(ROOT/'stage11b_discovery_manifest.json'),supersedes_sha256=sha(ROOT/'stage11b_discovery_manifest.json'),
    input_only_repair=True,repair_audit=str(ROOT/'audit/freshness_repair_v2.json')))
save(ROOT/'audit/heldout_reserve_v2.json',dict(at=now(),unopened=True,rows=[r for r in usable if r['item_id'] not in used]))
import pyarrow as pa
inventory=load('outputs/stage8b/audit/input_inventory.json')
with pa.memory_map(inventory['source'],'r') as f:
    metadata=pa.ipc.open_stream(f).read_all().select(['solution']).to_pylist()
packets=[dict(r,source_solution=metadata[r['row_index']]['solution']) for r in chosen]
save(ROOT/'packets/discovery_evidence_v2.json',dict(at=now(),rows=packets,model_outcomes_opened=False,
    supersedes=str(ROOT/'packets/discovery_evidence.json')))
save(ROOT/'audit/freshness_repair_v2.json',dict(at=now(),prior_alias=dict(a='1699',b='1237',visually_confirmed=True),
    reason='Inherited image/question family map missed a redrawn paraphrase before inference; source-only conservative repair',
    rule='Union question-token Jaccard>=0.45 where both have>=20 distinct lowercase alphanumeric tokens; conservative screening includes options; may overmerge unrelated items',
    old_manifest_preserved=True,scientific_model_outcomes_opened=False,edges=edges,excluded_prior_alias_item_ids=excluded,
    replacements=replacements,remaining_families=len(usable)-128,
    per_item_repair='Retain unaffected initial rows; replace only merged/prior-linked rows with next same-stratum fixed-hash representative'))
print(dict(replacements=replacements,excluded_prior=len(excluded),edges=len(edges),reserve=len(usable)-128))
