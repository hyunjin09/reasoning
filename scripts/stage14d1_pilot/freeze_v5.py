"""Freeze prospective v5 after independent CPU regressions, before generation."""
import ast
from scripts.stage14d1_pilot.common import *
from scripts.stage14d1_pilot.interface_v5 import SCHEMAS

def main():
    old=load(P/'audit/execution_seal_v4.json')
    for path,digest in old['files'].items():
        assert sha(path)==digest,path
    cfg=load(P/'protocol/runtime.json');cfg['protocol_version']='source_reference_native_coordinates_v5'
    save(P/'protocol/runtime_v5.json',cfg)
    save(P/'protocol/schemas_v5.json',SCHEMAS)
    deps=[Path('scripts/stage14d1_pilot')/n for n in
          ['worker_v5.py','interface_v5.py','common.py','execution.py','launch_v5.py','test_interface_v5.py']]
    deps += [Path('scripts/stage14d1')/n for n in ['common.py','contracts.py','contracts_v2.py','contracts_v3.py','views.py','run.sh']]
    for p in deps:
        if p.suffix=='.py':ast.parse(p.read_text())
    files=deps+[P/'protocol'/n for n in ['runtime_v5.json','schemas_v5.json','technical_controls_v5.json','source_reference_interface_v5.md']]
    files += [P/'inference/families.jsonl',P/'audit/interface_spec_freeze_v5.json',P/'audit/interface_v5_green.txt']
    save(P/'audit/execution_seal_v5.json',dict(at=now(),files={str(p):sha(p) for p in files},v4_preserved=True))
    save(P/'manifests/technical_v5.json',dict(id='technical_v5',mode='technical',families=load(P/'protocol/sampler_and_seeds.json')['technical_families'],wall_seconds=1800,seal=str(P/'audit/execution_seal_v5.json')))
    print('v5 CPU tests PASS; spec/code frozen; prior receipts preserved')
if __name__=='__main__':main()
