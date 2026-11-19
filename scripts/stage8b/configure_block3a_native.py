"""Seal rollout configuration after the item and semantic anchor freeze."""
import json
from datetime import datetime,timezone
from pathlib import Path
from visual_reasoning.stage8b.block1_data import digest,save
ROOT=Path('outputs/stage8b_block3a/v1')

def main():
    old=json.loads(Path('outputs/stage8b1a/config/resume125_node06_v1.json').read_text())
    base=json.loads((ROOT/'audit/base_cohort.json').read_text());anchors=json.loads((ROOT/'annotations/anchor_seal.json').read_text())
    assert anchors['complete'] and len(anchors['anchors'])==32
    cfg={key:old[key] for key in ['model_checkpoint','model_revision','detector_freeze','detector_freeze_sha256','protocol_id',
        'max_new_tokens','generation_parameters','presence_penalty','min_pixels','max_pixels','worker_count_options','historical_peak_reserved_bytes']}
    cfg.update(at=datetime.now(timezone.utc).isoformat(),stage='Block3A fixed same-item native replication',seed=1235,seeds=base['seeds'],
        manifest=str(ROOT/'audit/rollout_manifest.jsonl'),output_dir=str(ROOT/'native'),layout_decision=str(ROOT/'native/layout_decision.json'),
        log_dir='runs/stage8b_block3a/native_v1',performance_probe_ids=[r['item_id'] for r in base['selected'][:4]],performance_probe_tokens=2048,
        reused_receipt_sha256={},node='node02',gpus=2,maximum_trajectories=128,maximum_wall_hours=36)
    cfg['manifest_sha256']=digest(cfg['manifest'])
    paths=['scripts/stage8b/run_block3a_native.py','scripts/stage8b/run_block3a_native.sh','scripts/stage8b/run_block3a_parent.py',
        'scripts/stage8b/benchmark_block3a.py','scripts/stage8b/select_block3a_layout.py','scripts/stage8b/finish_block3a_native.py',
        'scripts/stage8b/run_native_v2_shared.py','code/visual_reasoning/stage8b/block3a_tasks.py',
        'code/visual_reasoning/stage8b/shared_execution.py','code/visual_reasoning/stage8b/single_execution.py',
        'code/visual_reasoning/stage8b/v2_protocol.py','code/visual_reasoning/stage8b/passive.py','code/visual_reasoning/stage0/modeling.py',
        'code/visual_reasoning/stage8a/protocol.py','plan/stage8b_block3a_execution_protocol_v1.md',
        str(ROOT/'annotations/anchor_seal.json'),str(ROOT/'audit/base_cohort.json')]
    cfg['source_sha256']={p:digest(p) for p in paths}
    save(ROOT/'audit/native_config.json',cfg)
    print(json.dumps({k:cfg[k] for k in ['stage','node','gpus','seeds','manifest_sha256','maximum_trajectories']}))

if __name__=='__main__':main()
