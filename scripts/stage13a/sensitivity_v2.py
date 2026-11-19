"""Prospectively frozen conditional cap sensitivity; no automatic job launch."""
import argparse
from scripts.stage13a.execution import ROOT,load,save,sha,now,shards
from scripts.stage13a.analyze_v2 import results,parquet
from scripts.stage13a.inference_v2 import estimate,bounds

def prepare():
    main=load(ROOT/'stage13a_primary_inference.json')
    assert (ROOT/'audit/primary_inference_seal.json').exists()
    if not main['optional_capmatched_triggered']:
        save(ROOT/'audit/capmatched_status.json',dict(at=now(),executed=False,reason='Frozen primary/comparable gate did not authorize the optional assay.'))
        print('Optional cap-matched assay not triggered.');return
    frozen=load(ROOT/'stage13a_capmatched24_manifest.json');tasks=frozen['tasks']
    assert len(tasks)==72 and len({t['family_id'] for t in tasks})==24
    path=ROOT/'audit/phaseS_execution.json';save(path,dict(at=now(),phase='S',tasks=tasks))
    save(ROOT/'audit/capmatched_authorization.json',dict(at=now(),authorized=True,execution_sha256=sha(path),
        primary_sha256=sha(ROOT/'stage13a_primary_inference.json'),selection_sha256=sha(ROOT/'stage13a_capmatched24_manifest.json')))
    paths=shards('S',tasks,4)
    save(ROOT/'audit/capmatched_launch_plan.json',dict(at=now(),manifests=paths,minutes=30,reservation_gpu_hours=2))
    print('Optional gate passed; four18-call shards frozen for separately checked2GPUh reservation.')

def close():
    import pandas as pd
    assert load(ROOT/'stage13a_primary_inference.json')['optional_capmatched_triggered']
    optional=results('S','T_32K');assert len(optional)==72
    ins=pd.read_parquet(ROOT/'stage13a_instruct_equal_evidence_results.parquet').to_dict('records')
    families=[]
    for item in load(ROOT/'stage13a_capmatched24_manifest.json')['selected_ids']:
        ii=sorted([r for r in ins if r['item_id']==item],key=lambda r:r['replicate']);tt=sorted([r for r in optional if r['item_id']==item],key=lambda r:r['replicate'])
        assert len(ii)==len(tt)==3
        i=[None if pd.isna(r['correct']) else bool(r['correct']) for r in ii];t=[r['correct'] for r in tt]
        families.append(dict(item_id=item,I=i,T=t,complete=None not in i+t))
    effect=estimate([(r['T'].count(True)-r['I'].count(True))/3 for r in families if r['complete']])
    parquet(ROOT/'stage13a_capmatched24_results.parquet',optional)
    save(ROOT/'audit/capmatched_status.json',dict(at=now(),executed=True,calls=72,estimate=effect,
        missingness_bounds=bounds(families),families=families,primary_gate_unchanged=True,
        scope='Budget sensitivity only; same Thinking sampling, not checkpoint/decoding isolation.'))
    print('Optional cap-matched sensitivity closed:',effect)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','close']);a=p.parse_args()
    (prepare if a.action=='prepare' else close)()
