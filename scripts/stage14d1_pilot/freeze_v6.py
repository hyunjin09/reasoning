import ast
from pathlib import Path
from scripts.stage14d1_pilot.common import *
from scripts.stage14d1_pilot.interface_v6 import SCHEMAS

def main():
    previous=load(P/'audit/execution_seal_v5.json')
    for path,digest in previous['files'].items():assert sha(path)==digest,path
    assert load(P/'raw/technical_v5/exit.json')['status']=='COMPLETE'
    allowed={};evidence=[]
    for p in sorted((P/'raw/technical_v5/states').glob('*.json')):
        s=load(p)
        for path in [s['query_generation']]+[s['readouts'][a]['generation_path'] for a in ('G','Q','QI')]:
            if path:
                allowed[path]=sha(path)
                evidence += [Path(path),Path(path).parent/'input.json',Path(path).parent/'result.json']
    save(P/'protocol/helper_reuse_v6.json',dict(at=now(),files=allowed,query_interface_sha256=sha('scripts/stage14d1_pilot/interface_v5.py'),
         from_version='v5',to_version='v6',compatible_components=['QUERY','G_READ','Q_READ','QI_READ'],
         reason='Only LOCATE mode/cardinality changed; preserve every unchanged helper regardless of success'))
    cfg=load(P/'protocol/runtime_v5.json');cfg['protocol_version']='source_reference_native_coordinates_mode_cardinality_v6'
    save(P/'protocol/runtime_v6.json',cfg);save(P/'protocol/schemas_v6.json',SCHEMAS)
    deps=[Path('scripts/stage14d1_pilot')/n for n in ['worker_v6.py','interface_v6.py','launch_v6.py','test_locator_v6.py']]
    files=deps+[P/'protocol'/n for n in ['runtime_v6.json','schemas_v6.json','helper_reuse_v6.json','locator_cardinality_v6.md']]+[P/'audit/spec_freeze_v6.json',P/'audit/locator_v6_green.txt']+evidence
    for p in deps:ast.parse(p.read_text())
    save(P/'audit/execution_seal_v6.json',dict(at=now(),files=dict(previous['files'],**{str(p):sha(p) for p in files})))
    save(P/'manifests/technical_v6.json',dict(id='technical_v6',mode='technical',families=load(P/'protocol/sampler_and_seeds.json')['technical_families'],wall_seconds=1800,seal=str(P/'audit/execution_seal_v6.json')))
    print('v6 frozen; unchangedhelperreceipts',len(allowed))
if __name__=='__main__':main()
