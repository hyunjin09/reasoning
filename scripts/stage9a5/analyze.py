"""Analyze sealed stage reviews and apply only frozen sequential decisions."""
import argparse
import os
import pandas as pd
from scripts.stage9a5.common import ROOT, COT, load, save, sha, now
from scripts.stage9a5.review import scored_rows
from scripts.stage9a5.decisions import absolute_decision
from scripts.stage9a5.compare import paired_contrast
from scripts.stage9a4.analyze import summarize


def reference_rows():
    return (load(COT/'stage9a4_qwen3_4b_full_baseline.json')['rows'] +
            load(COT/'audit/r1_scored.json')['rows'] + load(COT/'audit/t128_scored.json')['rows'])


def score(stage):
    assert os.environ.get('SLURM_JOB_ID')
    rows = scored_rows(stage)
    save(ROOT/f'audit/{stage}_scored.json', dict(at=now(), rows=rows, review_sha256=sha(ROOT/f'audit/{stage}_review.json')))
    if stage == 'sink':
        d = load(ROOT/'audit/absolute_final_decision.json')
        result = summarize(rows)
        result.update(at=now(), status='complete', selected_cutoff=d['cutoff'],
                      raw_sensitivity=summarize(rows, True),
                      selected_cutoff_established_sufficient=d['action']=='selected',
                      cot_reference=load(COT/'stage9a4_qwen3_4b_null_sink_control.json'),
                      source_sha256=sha(ROOT/f'audit/{stage}_scored.json'))
        save(ROOT/'stage9a5_null_sink_control.json', result)
        print(result['surface'], flush=True)
        return
    assert stage in ('t1', 't256')
    combined = load(ROOT/'stage9a5_thinking_full_baseline.json')['rows'] + load(ROOT/'audit/t1_scored.json')['rows']
    if stage == 't256':
        combined += rows
    dest = ROOT/('stage9a5_thinking_primary64.parquet' if stage=='t1' else 'stage9a5_thinking_token256.parquet')
    assert not dest.exists()
    pd.DataFrame(combined if stage=='t1' else rows).to_parquet(dest, index=False)
    result = summarize(combined)
    action, cutoff = absolute_decision(result['surface'])
    result.update(at=now(), action=action, cutoff=cutoff, stage=stage, raw_sensitivity=summarize(combined, True),
                  source_sha256=sha(__file__))
    save(ROOT/f'audit/{stage}_decision.json', result)
    comparison = dict(at=now(), status='interim' if action=='run' else 'complete', thinking=result,
                      cot=summarize(reference_rows()),
                      contrasts={p:paired_contrast(combined, reference_rows(), p) for p in ('t0','t64','t128')},
                      primary_contrast='t128', claim_scope='Matched checkpoints; training specialization remains confounded.')
    save(ROOT/f'audit/{stage}_comparison.json', comparison)
    if action != 'run':
        save(ROOT/'audit/absolute_final_decision.json', result)
        save(ROOT/'stage9a5_absolute_access_comparison.json', comparison)
    print({'surface':result['surface'],'action':action,'cutoff':cutoff,'primary':comparison['contrasts']['t128']}, flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage');score(p.parse_args().stage)
