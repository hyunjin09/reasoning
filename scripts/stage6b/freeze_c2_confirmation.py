"""Apply the predeclared discovery quantile without inspecting confirmation."""
import argparse
from datetime import datetime, timezone
import numpy as np

from scripts.stage6b.common import OUT, read_json, sha, write_json
from scripts.stage6b.c2_results import load_complete_run, flatten


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
    manifest,results=load_complete_run(args.run_id,'discovery')
    rows=[flatten(manifest[eid],r) for eid,r in results.items()]
    assert len(rows)==48 and len({r['base_id'] for r in rows})==12
    rules=read_json(OUT/'config/c2_factorial_rules.json')
    densities=np.asarray([r['focal_features']['attention_density'] for r in rows])
    assert np.isfinite(densities).all() and (densities>0).all()
    report={'status':'FROZEN_BEFORE_CONFIRMATION','discovery_run_id':args.run_id,
        'discovery_events':48,'discovery_families':12,
        'high_attention_density_threshold':float(np.quantile(densities,.75)),
        'criterion':'focal ROI mean attention density across layers28-29/all32 heads >= discovery pooled 75th percentile',
        'matching':rules['matching'],'rules_sha256':sha(OUT/'config/c2_factorial_rules.json'),
        'manifest_sha256':sha(OUT/'config/phase_a_events.jsonl'),
        'statistical_families_sha256':sha(OUT/'config/statistical_families.json'),
        'confirmation_effects_inspected':False,
        'frozen_at':datetime.now(timezone.utc).isoformat()}
    write_json(OUT/'config/c2_confirmation_freeze.json',report,freeze=True)
    write_json(OUT/'c2_alignment_retrieval/discovery_features.json',rows,freeze=True)
    print('C2 confirmation criterion frozen from 48 discovery events; threshold='+str(report['high_attention_density_threshold']))


if __name__=='__main__':main()
