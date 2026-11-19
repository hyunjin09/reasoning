"""Freeze original routing taxonomy and fixed base items before new rollouts."""
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from visual_reasoning.stage8b.block1_data import digest,save
from visual_reasoning.stage8b.block3a import routing_subtype,select_anchors

ROOT=Path('outputs/stage8b_block3a/v1')

def main():
    inv=json.loads((ROOT/'audit/native_inventory.json').read_text())
    replay={k:v for k,v in inv['existing_replays'].items()}
    for rank in (0,1):
        p=ROOT/'native_replay'/f'worker{rank}'/'completed.json';assert json.loads(p.read_text())['completed']
    for p in sorted((ROOT/'native_replay').glob('worker*/events/*.json')):
        row=json.loads(p.read_text());assert row['capture_logits_exact'] and row['native_features_match']
        assert row['event_id'] not in replay
        replay[row['event_id']]=dict(path=str(p),sha256=digest(p))
    taxonomy=[];candidates=[]
    for entry in inv['records']:
        original=entry['original'];ref=replay.get(original['event_id']);routing={}
        if ref:
            assert digest(ref['path'])==ref['sha256'];routing=json.loads(Path(ref['path']).read_text())['routing']
        subtype=routing_subtype(original['local'],routing)
        row=dict(original=original,native_routing=routing,routing_subtype=subtype,measurement=ref,
            source_positions=entry['source_positions'],geometry=entry['geometry'],native_dir=entry['native_dir'])
        taxonomy.append(row)
        if entry['resolved_TX'] and subtype!='R4':
            candidates.append(dict(event_id=original['event_id'],item_id=str(original['item_id']),family_id=original['family_id'],
                local=original['local'],review_order=original['review_order'],qk_T_X=routing['qk_T_X']))
    selected=select_anchors(candidates,32)
    lookup={r['original']['event_id']:r for r in taxonomy}
    anchors=[lookup[r['event_id']] for r in selected]
    rows={str(r['item_id']):r for r in map(json.loads,Path('outputs/stage8b1a/cohort/census256_manifest_v1.jsonl').read_text().splitlines())}
    tasks=[]
    for seed in (1235,1236,1237,1238):
        for anchor in anchors:
            item=str(anchor['original']['item_id']);native=Path(anchor['native_dir'])
            tasks.append(dict(rows[item],seed=seed,task_id=f'{item}_s{seed}',subgoal=anchor['original']['event_id'],
                reference_input=str(native/'input.json'),reference_input_sha256=digest(native/'input.json')))
    save(ROOT/'stage8b_block3a_routing_subtypes.json',dict(at=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=digest('plan/stage8b_block3a_execution_protocol_v1.md'),scope='Block2 original native inventory; new rollouts separate',
        counts=Counter(r['routing_subtype'] for r in taxonomy),counts_by_local={label:Counter(r['routing_subtype'] for r in taxonomy if r['original']['local']==label) for label in ['L+','L-','L?']},records=taxonomy))
    save(ROOT/'audit/base_cohort.json',dict(at=datetime.now(timezone.utc).isoformat(),selected=selected,anchors=anchors,
        protocol_sha256=digest('plan/stage8b_block3a_execution_protocol_v1.md'),seeds=[1235,1236,1237,1238],
        items=32,trajectories=128,primary_pairing='new-new only; disjoint seed-sorted pairs per frozen subgoal'))
    with (ROOT/'audit/rollout_manifest.jsonl').open('x') as f:
        for row in tasks:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    display=[dict(item_id=str(r['original']['item_id']),event_id=r['original']['event_id'],subtype=r['routing_subtype'],
        local=r['original']['local'],qk=r['native_routing']['qk_T_X'],source=r['original']['source_identity'],
        original_subtype=r['original'].get('subtype'),roi_type=r['original'].get('roi_type'),rationale=r['original']['rationale'],
        quote=r['original']['quote']) for r in anchors]
    save(ROOT/'audit/anchor_review_packet.json',display)
    print(json.dumps(dict(counts=Counter(r['routing_subtype'] for r in taxonomy),selected=selected),indent=2))

if __name__=='__main__':main()
