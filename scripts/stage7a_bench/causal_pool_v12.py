"""Two-worker cost partition; longest caches run after worker1 exits."""
import time
from pathlib import Path
import json


def token_cost(entry):
    return entry['native_input']['prompt_token_count']+len(entry['event']['history_before_ed_token_ids'])


def partition_entries(entries,index):
    if index not in (0,1):
        raise ValueError('Exactly two worker indices are supported')
    heavy=[e for e in entries if token_cost(e)>=100000]
    ordinary=[e for e in entries if token_cost(e)<100000]
    bins=[set(),set()];costs=[0,0]
    for e in sorted(ordinary,key=lambda e:(-token_cost(e),e['id'])):
        owner=min(range(2),key=lambda i:(costs[i],i));bins[owner].add(e['id']);costs[owner]+=token_cost(e)**2
    selected=[e for e in entries if e['id'] in bins[index]]
    return selected+(heavy if index==0 else [])


def wait_for_peer_before_large_event(entry,worker_index,run_id,out):
    if token_cost(entry)<100000:return
    if worker_index!=0 or not run_id.endswith('__worker0'):
        raise ValueError('Large-cache work must execute last on worker0')
    peer=Path(out)/'causal_pilot/wrappers'/(run_id.removesuffix('__worker0')+'__worker1.json')
    print('Waiting for peer process exit before large-cache event',entry['id'],flush=True)
    while not peer.exists():time.sleep(1)
    record=json.loads(peer.read_text())
    if record.get('completed') is not True or record.get('exit_code')!=0:
        raise RuntimeError('Peer failed; do not proceed with partial pilot')
