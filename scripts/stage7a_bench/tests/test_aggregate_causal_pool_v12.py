"""Reject partial/swapped pool evidence; preserve exact events on a valid merge."""
import json
from pathlib import Path
import pytest
from scripts.stage7a_bench import aggregate_causal_pool_v12 as agg
from scripts.stage7a_bench.causal_pool_v12 import partition_entries


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))


@pytest.fixture
def pool(tmp_path,monkeypatch):
    monkeypatch.setattr(agg,'ROOT',tmp_path);out=tmp_path/'outputs/stage7a_bench_v2';monkeypatch.setattr(agg,'OUT',out)
    entries=[dict(id='a',native_input={'prompt_token_count':5},event={'history_before_ed_token_ids':[]}),dict(id='b',native_input={'prompt_token_count':6},event={'history_before_ed_token_ids':[]})]
    monkeypatch.setattr(agg,'load_frozen_pilot',lambda *_:dict(selected_entries=entries))
    monkeypatch.setattr(agg,'dependency_hashes',lambda:{})
    monkeypatch.setattr(agg,'validate_mechanics',lambda *_:None)
    dump(out/'config/runtime_node02_two_gpu_v12.json',{'runtime':{'slurm_allocation':'114451'},'assigned_gpu_uuids':['gpu0','gpu1']})
    cert=out/'causal_pilot/mechanics/mmlongbench_doc.json';dump(cert,{'test_only':True})
    signature=dict(execution_signature={'pilot':{},'dependencies':{}},mechanics=False,mechanics_certificate=agg.reference(cert),passive_features_collected=False)
    for i in range(2):
        run=out/'causal_pilot/raw'/('test__worker'+str(i));ids=[e['id'] for e in partition_entries(entries,i)]
        dump(run/'signature.json',dict(signature,event_ids=ids))
        dump(run/'environment.json',dict(slurm_job_id='114451',parameter_dtype='torch.bfloat16',node='node02',gpu_uuid='gpu'+str(i)))
        dump(run/'device_mechanics_certificate.json',{'gpu_uuid':'gpu'+str(i)})
        events=[]
        for eid in ids:
            ep=run/'events'/(eid+'.json');dp=ep.with_suffix('.npz');dump(ep,dict(id=eid,complete=True,source_assay_mechanics=False));dp.write_bytes(b'test-distribution')
            events.append(dict(event=agg.reference(ep),distributions=agg.reference(dp)))
        dump(run/'run_summary.json',dict(completed=True,seconds=2+i,events=events))
        dump(out/'causal_pilot/wrappers'/(run.name+'.json'),dict(completed=True,exit_code=0,slurm_job_id='114451'))
    return out,entries


def test_valid_pool_preserves_complete_membership_and_sums_gpu_time(pool):
    out,entries=pool;dest=agg.aggregate('test',None);d=json.loads((dest/'run_summary.json').read_text())
    assert d['seconds']==5 and d['pool_workers']==2
    assert [json.loads((agg.ROOT/e['event']['path']).read_text())['id'] for e in d['events']]==['a','b']
    assert (out/'causal_pilot/raw/test__worker0/run_summary.json').exists()


@pytest.mark.parametrize('fault',['failed','missing_event','wrong_allocation','changed_artifact','same_gpu'])
def test_invalid_pool_cannot_write_complete_run(pool,fault):
    out,_=pool;p=out/'causal_pilot/raw/test__worker0'
    if fault=='failed':
        path=out/'causal_pilot/wrappers/test__worker0.json';d=json.loads(path.read_text());d['completed']=False;dump(path,d)
    if fault=='missing_event':
        path=p/'run_summary.json';d=json.loads(path.read_text());d['events']=[];dump(path,d)
    if fault=='wrong_allocation':
        path=p/'environment.json';d=json.loads(path.read_text());d['slurm_job_id']='old';dump(path,d)
    if fault=='same_gpu':
        path=p/'environment.json';d=json.loads(path.read_text());d['gpu_uuid']='gpu1';dump(path,d)
    if fault=='changed_artifact':
        path=next((p/'events').glob('*.json'));path.write_text('{}')
    with pytest.raises(ValueError):agg.aggregate('test',None)
    assert not (out/'causal_pilot/raw/test').exists()
