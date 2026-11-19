"""Score-blind same-subgoal packets and explicit main-agent review storage."""
import json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from visual_reasoning.stage8b.block0 import episodes
from visual_reasoning.stage8b.block1_data import digest,save
from visual_reasoning.stage8b.block3a_review import align_read
from visual_reasoning.stage8b.transfer import reasoning_length
ROOT=Path('outputs/stage8b_block3a/v1')


def prepare():
    anchors=json.loads((ROOT/'annotations/anchor_seal.json').read_text())['anchors']
    crosscheck=json.loads((ROOT/'annotations/image_crosscheck.json').read_text())
    byitem={str(r['item_id']):r for r in anchors};done=0
    active_path=ROOT/'audit/active_native_run.json'
    roots=json.loads(active_path.read_text())['example_roots'] if active_path.exists() else [str(ROOT/'native/examples')]
    results=sorted(p for root in roots for p in Path(root).glob('*/result.json'))
    assert len({p.parent.name for p in results})==len(results), 'Duplicate completed task across runs'
    for result in results:
        native=result.parent;receipt=json.loads(result.read_text());task=receipt['task_id'];dest=ROOT/'annotations/packets'/f'{task}.json'
        if dest.exists():continue
        for path,sha in receipt['provenance_sha256'].items():assert digest(path)==sha,path
        pieces=[json.loads(s)['decoded_token'] for s in (native/'tokens.jsonl').read_text().splitlines()]
        length=reasoning_length(pieces);pieces=pieces[:length]
        with np.load(native/'passive.npz') as arrays:bounds=episodes(arrays['retrieval_score'][:length],4)
        safe=[{k:e[k] for k in ['episode_index','start_token','end_token']} for e in bounds]
        anchor=dict(byitem[str(receipt['item_id'])])
        anchor['analysis_family_id']=crosscheck['analysis_family_by_item'][str(receipt['item_id'])]
        anchor['terminology_clarification']=crosscheck['terminology_clarification'].get(str(receipt['item_id']))
        save(dest,dict(task_id=task,item_id=str(receipt['item_id']),family_id=receipt['family_id'],seed=receipt['seed'],anchor=anchor,
            native_dir=str(native),receipt_sha256=digest(result),token_file=str(native/'tokens.jsonl'),token_sha256=digest(native/'tokens.jsonl'),
            reasoning_tokens=length,episodes=safe))
        lines=[f'# {task}: {anchor["subgoal"]}',anchor['demand'],f'Correct interpretation: {anchor["correct_interpretation"]}',
            'Review native text without source-routing values. Character offsets in brackets.',anchor.get('terminology_clarification') or '']
        cursor=0
        for start in range(0,length,128):
            chunk=''.join(pieces[start:start+128]);lines.append(f'[{cursor}:{cursor+len(chunk)}] tokens {start}:{min(start+128,length)}\n{chunk}');cursor+=len(chunk)
        dest.with_suffix('.md').write_text('\n\n'.join(lines));done+=1
    print(json.dumps(dict(new_packets=done,total_packets=len(list((ROOT/'annotations/packets').glob('*.json'))))))


def record(task, judgment):
    p=ROOT/'annotations/packets'/f'{task}.json';packet=json.loads(p.read_text());anchor=packet['anchor']
    assert judgment['local'] in ['L+','L-','L?',None] and len(judgment['rationale'])>20
    assert judgment['prior_context_check'] and judgment['subgoal_checked']
    row=dict(judgment,task_id=task,event_id=task+'_'+anchor['subgoal'],item_id=packet['item_id'],family_id=packet['family_id'],
        seed=packet['seed'],subgoal=anchor['subgoal'],category=anchor['category'],sources=anchor['sources'],analysis_family_id=anchor['analysis_family_id'],
        source_identity=anchor['demand'],native_dir=packet['native_dir'],packet_sha256=digest(p),reviewer='main agent; single annotator',
        source_routing_opened=False,at=datetime.now(timezone.utc).isoformat())
    if judgment['local'] is not None:
        assert digest(packet['token_file'])==packet['token_sha256']
        pieces=[json.loads(s)['decoded_token'] for s in Path(packet['token_file']).read_text().splitlines()][:packet['reasoning_tokens']]
        row.update(align_read(pieces,judgment,packet['episodes']))
        row['eligible']=row['retrieval_eligible'] and row['local'] in ['L+','L-']
    else:
        row.update(eligible=False,retrieval_eligible=False)
    save(ROOT/'annotations/reviews'/f'{task}.json',row)
    return row

if __name__=='__main__':prepare()
