"""Materialize only the pre-outcome frozen null-sink inventory after main analysis."""
import copy,json,shutil
from pathlib import Path
from scripts.stage9a_dynamics.prepare_answers import MAIN,save,sha


def main():
    ready=json.loads((MAIN/'audit/main_analysis_ready.json').read_text())
    assert sha(MAIN/'stage9a_primary_inference.json')==ready['main_analysis_sha256']
    old=json.loads((MAIN/'audit/interventions.json').read_text());rows=old['deferred_control_rows'];assert len(rows)==87 and len({r['result_key'] for r in rows})==87
    assert all(r['mode']=='null_sink' and r['execution']=='run' for r in rows)
    selected={r['task_id'] for r in rows};tasks=[r for r in json.loads((MAIN/'audit/tasks.json').read_text())['rows'] if r['task_id'] in selected]
    assert len(tasks)==24 and len({r['family_id'] for r in tasks})==8
    root=MAIN/'controls_v1';root.mkdir(exist_ok=False)
    save(root/'audit/tasks.json',dict(rows=tasks))
    save(root/'audit/interventions.json',dict(rows=rows,frozen=True,parent_sha256=sha(MAIN/'audit/interventions.json'),selection='Exact87 deferred_control_rows frozen before main execution; no outcome-dependent selection'))
    shutil.copyfile(MAIN/'stage9a_mask_backend_validation.json',root/'stage9a_mask_backend_validation.json')
    cfg=copy.deepcopy(json.loads((MAIN/'config.json').read_text()));cfg.update(root=str(root),manifest_sha256=sha(root/'audit/interventions.json'),tasks_sha256=sha(root/'audit/tasks.json'),reused_results=[],main_families=8,main_tasks=24,main_unique=87,max_total_gpus=8,control_launch_gate='Passed: main inference sealed, exact originally frozen null-sink queue only')
    cfg['source_sha256'].update({str(MAIN/'audit/main_analysis_ready.json'):sha(MAIN/'audit/main_analysis_ready.json')})
    save(root/'config.json',cfg)
    save(root/'audit/launch_authorization.json',dict(main_analysis_ready=ready,conditions=87,families=8,tasks=24,expected_max_gpus=8,allowed_nodes=cfg['allowed_nodes'],parent_condition_sha256=sha(MAIN/'audit/interventions.json'),source_sha256={p:sha(p) for p in ['scripts/stage9a_dynamics/run_worker.py','code/visual_reasoning/stage9a_dynamics/access.py','code/visual_reasoning/stage9a_dynamics/generation.py']}))
    print(root)

if __name__=='__main__':main()
