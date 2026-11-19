"""Seal all bounded native semantic judgments before any new source capture."""
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
from visual_reasoning.stage8b.block1_data import digest,save
from visual_reasoning.stage8b.block3a import pair_reads
ROOT=Path('outputs/stage8b_block3a/v1')


def main():
    manifest=[json.loads(s) for s in (ROOT/'audit/rollout_manifest.jsonl').read_text().splitlines()]
    anchors={str(a['item_id']):a for a in json.loads((ROOT/'annotations/anchor_seal.json').read_text())['anchors']}
    crosscheck=json.loads((ROOT/'annotations/image_crosscheck.json').read_text())
    active_path=ROOT/'audit/active_native_run.json'
    completion=Path(json.loads(active_path.read_text())['completion_index']) if active_path.exists() else ROOT/'native/completed.json'
    assert len(manifest)==128 and json.loads(completion.read_text())['complete']
    records=[];hashes={}
    for task in manifest:
        p=ROOT/'annotations/reviews'/f'{task["task_id"]}.json';r=json.loads(p.read_text());a=anchors[str(task['item_id'])]
        assert r['task_id']==task['task_id'] and r['seed']==task['seed'] and r['subgoal']==task['subgoal']
        assert r['analysis_family_id']==crosscheck['analysis_family_by_item'][str(task['item_id'])]
        assert r['sources']==a['sources'] and r['category']==a['category'] and not r['source_routing_opened']
        packet=ROOT/'annotations/packets'/f'{task["task_id"]}.json';assert digest(packet)==r['packet_sha256']
        records.append(r);hashes[str(p)]=digest(p)
    assert len(list((ROOT/'annotations/reviews').glob('*.json')))==128
    pairs=pair_reads([r for r in records if r['eligible']])
    crosscheck=json.loads((ROOT/'annotations/image_crosscheck.json').read_text())
    for pair in pairs:pair['analysis_family_id']=crosscheck['analysis_family_by_item'][pair['item_id']]
    families={p['analysis_family_id'] for p in pairs}
    gate=dict(pairs=len(pairs),items=len({p['item_id'] for p in pairs}),families=len(families),minimum_pairs=20,minimum_families=16,
        pass_gate=len(pairs)>=20 and len(families)>=16,preferred_pairs=32,preferred_families=24,
        finite_cohort_complete=True,expansion_authorized=False)
    save(ROOT/'annotations/semantic_seal.json',dict(at=datetime.now(timezone.utc).isoformat(),annotation_complete=True,
        protocol_sha256=digest('plan/stage8b_block3a_execution_protocol_v1.md'),anchor_seal_sha256=digest(ROOT/'annotations/anchor_seal.json'),
        review_sha256=hashes,image_crosscheck_sha256=digest(ROOT/'annotations/image_crosscheck.json'),
        family_protocol_sha256=digest('plan/stage8b_block3a_family_clarification_v1.md'),source_measurements_opened=False,records=records,
        counts=Counter(str(r['local']) for r in records),eligible_counts=Counter(r['local'] for r in records if r['eligible']),pairs=pairs))
    pd.DataFrame(pairs,columns=['item_id','subgoal','family_id','analysis_family_id','category','success','failure']).to_parquet(ROOT/'audit/semantic_pairs.parquet',index=False)
    save(ROOT/'audit/yield_gate.json',gate);print(json.dumps(gate,indent=2))

if __name__=='__main__':main()
