"""Freeze fresh discovery and unopened reserve using source metadata only."""
import math
from collections import defaultdict, Counter
from pathlib import Path
import pyarrow as pa
from scripts.stage11b.common import ROOT,SEED,load,save,sha,now
from scripts.stage11b.protocol import CANDIDATES,hash_order

def stratified(rows,n,purpose):
    groups=defaultdict(list)
    for r in rows:groups[(r['subject'],r['level'],r['answer_format'])].append(r)
    counts={k:math.floor(n*len(v)/len(rows)) for k,v in groups.items()}
    order=sorted(groups,key=lambda k:(-(n*len(groups[k])/len(rows)-counts[k]),str(k)))
    for k in order[:n-sum(counts.values())]:counts[k]+=1
    selected=[r for k,v in sorted(groups.items()) for r in sorted(v,key=lambda r:hash_order(r,SEED,purpose))[:counts[k]]]
    return sorted(selected,key=lambda r:hash_order(r,SEED,purpose+'-order'))

def main():
    source=Path('outputs/stage8c_v2/v1/audit/remaining_family_representatives.json')
    old=Path('outputs/stage9a/v1/stage9a_cohort_manifest.json')
    excluded={r['family_id'] for r in load(old)['rows']}
    pool=[r for r in load(source)['rows'] if r['family_id'] not in excluded and r['level']>=3]
    assert len(pool)==len({r['family_id'] for r in pool})
    rows=stratified(pool,128,'discovery');selected={r['family_id'] for r in rows}
    reserve=[r for r in pool if r['family_id'] not in selected]
    inventory=load('outputs/stage8b/audit/input_inventory.json')
    assert sha(inventory['source'])==inventory['source_sha256']
    with pa.memory_map(inventory['source'],'r') as f:
        table=pa.ipc.open_stream(f).read_all()
        cols=[c for c in table.column_names if c not in ('image','decoded_image')]
        metadata=table.select(cols).to_pylist()
    packets=[]
    for i,r in enumerate(rows):
        assert sha(r['image'])==r['image_sha256']
        r['discovery_order']=i
        original=metadata[r['row_index']]
        packets.append(dict(r,source_solution=original.get('solution'),
            source_metadata={k:v for k,v in original.items() if k in ['solution','answer','subject','level']}))
    save(ROOT/'stage11b_discovery_manifest.json',dict(at=now(),frozen=True,seed=SEED,rows=rows,n=128,
        source=str(source),source_sha256=sha(source),excluded_manifest=str(old),excluded_sha256=sha(old),
        prior_outcomes_opened=False,candidate_strata=CANDIDATES,
        selection='Largest remainder subject/level/format; SHA256 stage11b:seed:purpose:family_id order within strata',
        distributions={k:dict(Counter(str(r[k]) for r in rows)) for k in ['subject','level','answer_format']}))
    save(ROOT/'audit/heldout_reserve.json',dict(at=now(),rows=reserve,unopened=True,eligible_harder_pool=len(pool),
        exclude_families=sorted(excluded|selected)))
    save(ROOT/'packets/discovery_evidence.json',dict(at=now(),rows=packets,model_outcomes_opened=False,
        note='Original image/question/options/gold only; no model text or scores. Source release has no solution where null.'))
    save(ROOT/'audit/input_provenance.json',dict(at=now(),source_inventory=inventory,source_columns=cols,
        image_sha256={r['image']:r['image_sha256'] for r in rows},model_source='outputs/stage11a/v1/probe_config.json',
        no_download=True,overlap_stage11a=0,discovery_reserve_overlap=0))
    print(dict(discovery=len(rows),untouched_harder_reserve=len(reserve),metadata_columns=cols))

if __name__=='__main__':main()
