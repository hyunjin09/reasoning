"""Balance the unchanged native trace set across exactly two existing devices."""
from collections import defaultdict
from scripts.stage6b.common import OUT,read_json,read_jsonl,write_jsonl,write_json,sha


def main():
    source=OUT/'trajectory/native_endpoint_manifest_v2.jsonl';rows=read_jsonl(source)
    bybase=defaultdict(list);cost={}
    for r in rows:bybase[r['base_id']].append(r)
    for base,entries in bybase.items():
        total=0
        for r in entries:
            ends=[s['token_end'] for s in r['spans']]
            if not ends:continue
            prompt=len(read_json(r['native_input_path'])['prompt_token_ids'])
            total+=sum(((end-8)%2048+8)*(end+prompt) for end in ends)
            maximum=max(ends)-8
            total+=sum(2048*(end+prompt) for end in range(2048,maximum+1,2048))
        cost[base]=total
    assigned=[[],[]];loads=[0,0];caps=[(len(bybase)+1)//2,len(bybase)//2]
    for base in sorted(bybase,key=lambda b:(-cost[b],b)):
        rank=min([r for r in range(2) if len(assigned[r])<caps[r]],key=lambda r:(loads[r],r))
        assigned[rank].append(base);loads[rank]+=cost[base]
    order=[]
    for i in range(caps[0]):
        for rank in range(2):
            if i<len(assigned[rank]):order.append(assigned[rank][i])
    scheduled=[r for base in order for r in bybase[base]]
    assert {r['id']:r for r in rows}=={r['id']:r for r in scheduled}
    target=OUT/'trajectory/native_endpoint_manifest_v3_schedule.jsonl'
    write_jsonl(target,scheduled,freeze=True)
    oldbases=list(bybase)
    write_json(OUT/'audit/native_runtime_schedule.json',{'source_sha256':sha(source),'scheduled_sha256':sha(target),
        'identical_entry_mapping':True,'events':len(rows),'endpoints':sum(len(r['spans']) for r in rows),
        'scheduling_inputs':'Frozen token lengths only; no passive values, causal scores or correctness.',
        'cost_proxy':'Canonical full-chunk queries plus each partial chunk and8singlequeries, weighted by context length; not a runtime guarantee.',
        'old_proxy_loads':[sum(cost[b] for i,b in enumerate(oldbases) if i%2==r) for r in range(2)],
        'balanced_proxy_loads':loads,'bases_per_rank':assigned,'cohort_or_condition_or_split_changed':False,
        'reason':'Restart after validated memory repair; reduce the prior 2.5x prefix-work imbalance without dropping or resampling any trace.'},freeze=True)
    print('Same',len(rows),'traces; balanced proxy loads',loads)


if __name__=='__main__':main()
