"""Preserve Block2 evidence and freeze missing native-only routing requests."""
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from visual_reasoning.stage8b.block1_data import digest,save
from visual_reasoning.stage8b.block2_data import source_positions

ROOT=Path('outputs/stage8b_block3a/v1'); B2=Path('outputs/stage8b_block2/v1')

def main():
    freeze_path=B2/'stage8b_block2_freeze.json';freeze=json.loads(freeze_path.read_text())
    assert digest(freeze_path)=='b12c4588fadd08bb13253b7e4bc96aaf3437a84563ed0f783d86073691f2893e'
    for p,h in {**freeze['artifacts_sha256'],**freeze['supporting_sha256']}.items():assert digest(p)==h,p
    seal_path=B2/'annotations/semantic_seal.json';seal=json.loads(seal_path.read_text())
    assert seal['annotation_complete'] and digest(seal_path)=='47bebb11bae2d14aedc7e4df8d6b431c45b520bc91a54b7aae10f449f12bf08a'
    prep=json.loads((B2/'audit/preparation_freeze.json').read_text())
    previous=json.loads((B2/'stage8b_block2_replay_manifest.json').read_text())
    old={}
    for path in sorted((B2/'replay').glob('worker*/events/*.json')):
        obj=json.loads(path.read_text());assert obj['capture_logits_exact'] and obj['native_features_match']
        old[obj['event_id']]=dict(path=str(path),sha256=digest(path))
    manifest={str(r['item_id']):r for r in map(json.loads,Path('outputs/stage8b1a/cohort/census256_manifest_v1.jsonl').read_text().splitlines())}
    records=[r for r in seal['records'] if r.get('source_localizable')]
    assert len(records)==117 and Counter(r['local'] for r in records)=={'L+':101,'L-':12,'L?':4}
    requests=[];inventory=[];verified=set()
    for event in records:
        item=str(event['item_id']);native=Path(prep['native_paths'][item]);row=manifest[item]
        assert digest(row['image'])==row['image_sha256']
        metadata=json.loads((native/'input.json').read_text())
        positions,geometry=source_positions(event['sources'],metadata)
        entry=dict(original=event,native_dir=str(native),source_positions=positions,geometry=geometry,existing_replay=old.get(event['event_id']))
        eligible=event['local'] in ('L+','L-') and bool(positions.get('T')) and bool(positions.get('X'))
        entry['resolved_TX']=eligible;inventory.append(entry)
        if not eligible or event['event_id'] in old:continue
        receipt=json.loads((native/'result.json').read_text())
        if item not in verified:
            for p,h in receipt['provenance_sha256'].items():assert digest(p)==h,p
            verified.add(item)
        requests.append(dict(event_id=event['event_id'],item_id=item,family_id=event['family_id'],local=event['local'],
            native_dir=str(native),row=row,native_sha256=receipt['provenance_sha256'],source_positions=positions,geometry=geometry,
            source_identity=event['source_identity'],sources=event['sources'],query=event['predicting_generated_query'],claim_start=event['claim_start_token']))
    costs={}
    for r in requests:costs[r['item_id']]=max(costs.get(r['item_id'],0),r['query']+1)
    loads=[0,0];ranks={}
    for item in sorted(costs,key=lambda k:(-costs[k],k)):
        rank=min(range(2),key=lambda r:(loads[r],r));loads[rank]+=costs[item];ranks[item]=rank
    for r in requests:r['rank']=ranks[r['item_id']]
    save(ROOT/'audit/native_inventory.json',dict(at=datetime.now(timezone.utc).isoformat(),block2_freeze_sha256=digest(freeze_path),annotation_seal_sha256=digest(seal_path),records=inventory,existing_replays=old))
    paths=['scripts/stage8b/run_block3a_replay.py','scripts/stage8b/run_block3a_replay.sh','scripts/stage8b/prepare_block3a.py',
        'plan/stage8b_block3a_execution_protocol_v1.md','code/visual_reasoning/stage8b/block3a.py',
        'code/visual_reasoning/stage8b/block2_capture.py','code/visual_reasoning/stage8b/block2_data.py','code/visual_reasoning/stage8b/v2_protocol.py',
        'code/visual_reasoning/stage8b/passive.py','code/visual_reasoning/stage0/modeling.py','code/visual_reasoning/stage3c9/streaming.py',
        'code/visual_reasoning/stage3b0/cache.py','code/visual_reasoning/stage3b0/runtime.py']
    output=dict(at=datetime.now(timezone.utc).isoformat(),stage='Block3A missing native observational routing',
        annotation_seal_path=str(seal_path),annotation_seal_sha256=digest(seal_path),model_checkpoint=previous['model_checkpoint'],
        model_revision=previous['model_revision'],seed=1234,layers=[19,20,21,22],heads=list(range(16)),dtype='bfloat16',node='node02',gpus=2,
        destination=str(ROOT/'native_replay'),requests=requests,estimated_queries_by_rank=loads,
        source_sha256={p:digest(p) for p in paths},global_feature_parity=dict(atol=1e-5,rtol=1e-5),interventions=False,generation=False)
    save(ROOT/'audit/native_replay_manifest.json',output)
    print(json.dumps(dict(inventory=len(inventory),reused=len(old),new_events=len(requests),new_items=len(costs),queries_by_rank=loads)))

if __name__=='__main__':main()
