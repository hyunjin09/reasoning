"""Freeze a resource-only continuation after terminal cancellation."""
import json
from datetime import datetime,timezone
from pathlib import Path
from visual_reasoning.stage8b.block1_data import digest,save
from visual_reasoning.stage8b.block3a_resume import balanced_remaining
ROOT=Path('outputs/stage8b_block3a/v1');AUDIT=ROOT/'audit/resume_four_v1'


def main():
    terminal=(AUDIT/'previous_job_terminal.txt').read_text();assert 'JobState=CANCELLED' in terminal
    old_path=ROOT/'audit/native_config.json';old=json.loads(old_path.read_text())
    for p,h in old['source_sha256'].items():assert digest(p)==h,p
    assert digest(old['manifest'])==old['manifest_sha256']
    tasks=[json.loads(s) for s in Path(old['manifest']).read_text().splitlines()];expected={r['task_id']:r for r in tasks}
    reused={};done=set();partial={};native=Path(old['output_dir'])
    for directory in sorted((native/'examples').iterdir()):
        assert directory.name in expected
        receipt=directory/'result.json'
        if receipt.exists():
            r=json.loads(receipt.read_text());task=expected[directory.name]
            assert r['task_id']==task['task_id'] and r['seed']==task['seed'] and str(r['item_id'])==str(task['item_id'])
            for p,h in r['provenance_sha256'].items():assert digest(p)==h,p
            reused[str(receipt)]=digest(receipt);done.add(directory.name)
        else:partial[directory.name]={str(p):digest(p) for p in directory.iterdir() if p.is_file()}
    base=json.loads((ROOT/'audit/base_cohort.json').read_text())['anchors']
    costs={str(a['original']['item_id']):json.loads((Path(a['native_dir'])/'result.json').read_text())['tokens'] for a in base}
    remaining,loads=balanced_remaining(tasks,done,costs)
    assert len(done)==14 and len(remaining)==114
    manifest=AUDIT/'remaining_manifest.jsonl'
    with manifest.open('x') as f:
        for row in remaining:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    save(AUDIT/'inventory.json',dict(at=datetime.now(timezone.utc).isoformat(),previous_job='118099',reused=14,remaining=114,
        reused_receipt_sha256=reused,completed_tasks=sorted(done),partial_attempts_preserved=partial,estimated_queries_by_worker=loads,
        full_manifest_sha256=old['manifest_sha256'],complete_artifacts_verified=True))
    cfg=dict(old);cfg.update(at=datetime.now(timezone.utc).isoformat(),stage='Block3A remaining114 on four node02 GPUs',
        gpus=4,worker_count=8,workers_per_gpu=2,manifest=str(manifest),manifest_sha256=digest(manifest),
        full_manifest=old['manifest'],full_manifest_sha256=old['manifest_sha256'],output_dir=str(ROOT/'native_resume_four_v1'),
        log_dir='runs/stage8b_block3a/native_resume_four_v1',reused_receipt_sha256=reused,
        technical_reference=str(native/'benchmark_single/worker0/checks.json'),
        technical_probe_row=next(r for r in tasks if r['item_id']=='2299' and r['seed']==1235),
        completion_index=str(ROOT/'audit/native_completion.json'),expected_remaining=114)
    paths=['scripts/stage8b/run_block3a_four_native.py','scripts/stage8b/run_block3a_four_parent.py','scripts/stage8b/run_block3a_four.sh',
        'scripts/stage8b/finish_block3a_four.py','scripts/stage8b/prepare_block3a_four.py','code/visual_reasoning/stage8b/block3a_resume.py',
        'scripts/stage8b/run_native_v2_shared.py','code/visual_reasoning/stage8b/single_execution.py',
        'code/visual_reasoning/stage8b/v2_protocol.py','code/visual_reasoning/stage8b/passive.py','code/visual_reasoning/stage0/modeling.py',
        'code/visual_reasoning/stage8a/protocol.py','plan/stage8b_block3a_four_gpu_resume_v1.md',
        str(ROOT/'annotations/anchor_seal.json'),str(ROOT/'annotations/image_crosscheck.json'),
        cfg['technical_reference'],cfg['layout_decision'],str(AUDIT/'inventory.json')]
    cfg['source_sha256']={p:digest(p) for p in paths};save(AUDIT/'config.json',cfg)
    save(ROOT/'audit/active_native_run.json',dict(config=str(AUDIT/'config.json'),config_sha256=digest(AUDIT/'config.json'),
        example_roots=[str(native/'examples'),str(Path(cfg['output_dir'])/'examples')],completion_index=cfg['completion_index']))
    print(json.dumps(dict(reused=len(done),remaining=len(remaining),interrupted=list(partial),expected_tokens_by_worker=loads),indent=2))

if __name__=='__main__':main()
