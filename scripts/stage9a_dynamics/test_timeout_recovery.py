"""A walltime resume must preserve completed results and interrupted evidence."""
import json
from scripts.stage9a_dynamics import dispatch


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data))


def test_timeout_releases_only_incomplete_owned_task(tmp_path,monkeypatch):
    monkeypatch.setattr(dispatch,'ROOT',tmp_path)
    write(tmp_path/'rollouts/workers/slurm_7/progress.jsonl',{'completed':'a'})
    for task,owner in [('done','slurm_7'),('partial','slurm_7'),('other','slurm_8')]:
        write(tmp_path/'rollouts/claims'/task/'owner.json',{'worker':owner})
    write(tmp_path/'rollouts/tasks/done/complete.json',{'complete':True})
    rows=[dict(task_id='partial',execution='run',result_key=k) for k in ['valid','unfinished','absent']]
    write(tmp_path/'audit/interventions.json',{'rows':rows})
    write(tmp_path/'rollouts/results/valid/result.json',{'tokens':3})
    write(tmp_path/'rollouts/results/unfinished/generation.json',{'partial':True})
    (tmp_path/'rollouts/results/unfinished/result.json').write_text('{')
    dispatch.release_timeout_claims('7')
    assert (tmp_path/'rollouts/claims/done/owner.json').exists()
    assert (tmp_path/'rollouts/claims/other/owner.json').exists()
    assert not (tmp_path/'rollouts/claims/partial').exists()
    assert json.loads((tmp_path/'rollouts/results/valid/result.json').read_text())=={'tokens':3}
    archive=tmp_path/'audit/timeout_continuations/slurm_7'
    assert (archive/'partial_owner.json').exists()
    assert (archive/'unfinished/generation.json').exists()
    assert not (tmp_path/'rollouts/results/unfinished').exists()
