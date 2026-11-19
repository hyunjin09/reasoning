"""Verify historical seals without exposing model text."""
from scripts.stage14d1_pilot.common import P,load,save,sha,now


def main():
    seals=['outputs/stage14d1_sava/audit/final_package_seal.json',
        'outputs/stage14d1_sava_recovery/v1/audit/recovery_closure_seal.json']
    seals += [str(P/'audit'/n) for n in ['execution_seal_v4.json','execution_seal_v5.json',
        'execution_seal_v6.json','main_execution_seal.json','resumption_v8_execution_seal.json',
        'analysis_pre_outcome_seal_v8.json']]
    expected={};origins={}
    for seal in seals:
        record=load(seal)
        sealed_files=record['files'] if 'files' in record else {**record['package_files'],**record['code_files']}
        for path,digest in sealed_files.items():
            if path in expected:assert expected[path]==digest, ('conflicting_seals',path)
            expected[path]=digest;origins.setdefault(path,[]).append(seal)
    failures=[]
    for path,digest in expected.items():
        if sha(path)!=digest:failures.append(dict(path=path,seals=origins[path]))
    save(P/'audit/final_historical_preservation_v8.json',dict(at=now(),seals=seals,
        unique_files=len(expected),failures=failures,passed=not failures))
    assert not failures,failures
    print('Verified historical and analysis files:',len(expected))

if __name__=='__main__':main()
