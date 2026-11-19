"""Release source-validated C3 stress conditions independently of C1 eligibility."""
import hashlib
import json
from collections import Counter
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write


def main():
    target=OUT/'cohort/c3_stress_manifest.jsonl';assert not target.exists()
    source=OUT/'cohort/c3_primary_v2_manifest.jsonl'
    rows=[json.loads(s) for s in source.read_text().splitlines()]
    assert len(rows)==660 and len({r['base_id'] for r in rows})==136
    assert json.loads((OUT/'audit/primary_asset_preflight.json').read_text())['status']=='PASS'
    donor_checks=[json.loads(s) for s in (OUT/'audit/c3_unrelated_v2_preflight.jsonl').read_text().splitlines()]
    assert len(donor_checks)==136 and all(r['status']=='PASS' for r in donor_checks)
    splits=json.loads((OUT/'cohort/prospective_source_split.json').read_text())['assignments']
    selected=[r for r in rows if r['condition']!='intact']
    assert len(selected)==524
    for r in selected:assert r['split']==splits[r['base_id']]['split'] and r['group_id']==splits[r['base_id']]['group_id']
    assert not list((OUT/'native/c3_stress').glob('shard_*/examples/*/generation.json'))
    write(target,selected)
    report=dict(status='C3_STRESS_FROZEN',events=len(selected),base_families=136,
        condition_counts=dict(Counter(r['condition'] for r in selected)),
        source_manifest_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        stress_manifest_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        scheduling='Each existing GPU starts after its C4extension shard releases memory; C1 native eligibility does not govern source-selected C3 membership.',
        source_conditions_or_protocol_changed=False,model_outcomes_used_for_membership=False)
    (OUT/'cohort/c3_stress_freeze.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
