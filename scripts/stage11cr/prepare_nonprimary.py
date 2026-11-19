"""Freeze one original-case validation wave after the known-good gate."""
import argparse
from scripts.stage11cr.common import ROOT,ARMS,load,save,sha,now


def main(cap):
    assert cap==load(ROOT/'audit/cap_protocol_correction.json')['selected_cap']==40960
    protocol=load(ROOT/'stage11cr_repaired_protocol.json');assert protocol['pass']
    rows=load(ROOT/'nonprimary_cases.json')['rows'];assert len(rows)==12
    shards=[]
    for arm in ARMS:
        bins=[[],[],[],[]];costs=[0.,0.,0.,0.]
        timings={(r['item_id'],r['arm']):r['seconds'] for r in load(ROOT/'audit/nonprimary_historical_resource_forecast.json')['rows']}
        for r in sorted(rows,key=lambda r:-timings[r['item_id'],arm]):
            k=min(range(4),key=lambda j:costs[j]);bins[k].append(r);costs[k]+=timings[r['item_id'],arm]
        for part in range(4):
            tasks=[]
            for r in bins[part]:
                tasks.append(dict(r,task_id=f'cap{cap}_{arm}_{r["item_id"]}',arm=arm,
                    condition='native',max_new_tokens=cap))
            shards.append(dict(id=f'{arm}_{part}',model_key='thinking' if arm=='thinking' else 'instruct',rows=tasks))
    save(ROOT/f'nonprimary{cap}_tasks.json',dict(at=now(),frozen=True,queue=f'nonprimary{cap}',
        protocol=protocol['worker_protocol'],config_sha256=sha(ROOT/'config.json'),
        repaired_protocol_sha256=sha(ROOT/'stage11cr_repaired_protocol.json'),
        nonprimary_cases_sha256=sha(ROOT/'nonprimary_cases.json'),n_calls=24,shards=shards,
        cap_amendment_sha256=sha(ROOT/'audit/cap_protocol_correction.json'),
        source_sha256=load(ROOT/'run_known_good_tasks.json')['source_sha256']))
    print('FROZEN_NONPRIMARY',cap,24)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('cap',type=int);main(p.parse_args().cap)
