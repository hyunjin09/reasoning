"""Completion-only packets and sealed judgments; no gold or task scoring."""
import argparse
from pathlib import Path
from scripts.stage11cr.common import ROOT,load,save,sha,now
from scripts.stage11cr.protocol import token_comparison,repetition_metrics,completion_gate


def packet(queue):
    manifests={'known_good':'run_known_good_tasks.json','diagnostic':'diagnostic_tasks.json',
        'nonprimary40960':'nonprimary40960_tasks.json'}
    manifest=load(ROOT/manifests[queue]);rows=[]
    for shard in manifest['shards']:
        for task in shard['rows']:
            dest=ROOT/queue/'results'/task['task_id']
            if not (dest/'result.json').exists():continue
            receipt=load(dest/'result.json');g=load(dest/'generation.json');inp=load(dest/'input.json')
            assert receipt['generation_sha256']==sha(dest/'generation.json')
            assert receipt['input_sha256']==sha(dest/'input.json')
            row=dict(task_id=task['task_id'],arm=task['arm'],receipt=receipt,
                generation_path=str(dest/'generation.json'),generation_sha256=receipt['generation_sha256'],
                image_input_valid=inp['image_present'] and inp['visual_token_count']>0,
                repetition=repetition_metrics(g['generated_token_ids']),
                response_head=g['raw_decoded_response'][:900],response_tail=g['raw_decoded_response'][-3000:],
                think_end_present='</think>' in g['raw_decoded_response'])
            if queue=='known_good' or queue.startswith('nonprimary'):
                historical_dir=Path(task['historical_dir']) if queue=='known_good' else Path('outputs/stage9a/v1/native/examples')/f"{task['arm']}_{task['item_id']}"
                old=load(historical_dir/'generation.json');old_inp=load(historical_dir/'input.json')
                if queue=='known_good':assert sha(historical_dir/'generation.json')==task['historical_generation_sha256']
                row.update(token_comparison(old['generated_token_ids'],g['generated_token_ids']))
                row['historical_tokens']=old['tokens']
                row['historical_repetition']=repetition_metrics(old['generated_token_ids'])
                row['historical_input_equal']={k:inp[k]==old_inp[k] for k in
                    ['chat_prompt','prompt_ids_sha256','pixel_values_sha256','image_grid_thw','prompt_token_count']}
            rows.append(row)
    label=now().replace(':','').replace('.','')
    path=ROOT/'audit/technical_packets'/f'{queue}_{label}.json'
    save(path,dict(at=now(),queue=queue,rows=rows,expected=manifest['n_calls'],accuracy_labels_hidden=True))
    print(path)
    for r in rows:
        print(r['task_id'],'tokens',r['receipt']['tokens'],'EOS',r['receipt']['normal_eos'],'cap',r['receipt']['at_length_cap'],
            'exact',r.get('exact_token_identity'),'divergence',r.get('first_divergence_token'),'repeat',r['repetition'])


def seal(packet_path, decisions_path):
    p=load(packet_path);d=load(decisions_path)
    assert len(p['rows'])==p['expected'] and len(d['rows'])==p['expected']
    index={r['task_id']:r for r in d['rows']};assert len(index)==p['expected']
    rows=[]
    for r in p['rows']:
        assert sha(r['generation_path'])==r['generation_sha256']
        j=index[r['task_id']]
        assert isinstance(j['committed_final'],bool) and isinstance(j['pathological_repetition'],bool) and j['reason']
        if j['committed_final']:
            assert j['quote'] and j['quote'] in load(r['generation_path'])['raw_decoded_response']
        rows.append(dict(r['receipt'],image_input_valid=r['image_input_valid'],
            **{k:r[k] for k in ['exact_token_identity','first_divergence_token','length_ratio','historical_tokens','historical_input_equal'] if k in r},
            **{k:v for k,v in j.items() if k!='task_id'}))
    phase='known_good' if p['queue']=='known_good' else 'nonprimary'
    for r in rows:
        if phase=='known_good':
            # Exact tier never silently downgraded; a documented limitation is mandatory for behavioral tier.
            r['replay_tier_pass']=r['exact_token_identity'] or bool(r.get('behavioral_tier_justification') and
                r['normal_eos'] and r['committed_final'] and not r['pathological_repetition'] and not r['at_length_cap'] and .5<=r['length_ratio']<=2)
            r['image_input_valid'] &= all(r['historical_input_equal'].values())
    gate=completion_gate(rows,phase)
    save(ROOT/'annotations'/f"{p['queue']}_technical_review.json",dict(at=now(),frozen=True,
        packet_path=packet_path,packet_sha256=sha(packet_path),decisions_path=decisions_path,decisions_sha256=sha(decisions_path),
        rows=rows,gate=gate,accuracy_used=False))
    print(gate)


if __name__=='__main__':
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('packet');a.add_argument('queue')
    a=sub.add_parser('seal');a.add_argument('packet');a.add_argument('decisions')
    a=p.parse_args();packet(a.queue) if a.cmd=='packet' else seal(a.packet,a.decisions)
