"""Bounded CPU integrity/independent arithmetic checks for the sealed main panel."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import pandas as pd
import numpy as np
from scripts.stage9a_dynamics.prepare_answers import MAIN, save, sha
from scripts.stage9a_dynamics.analyze_main import load


def main():
    config=load(MAIN/'config.json');inference=load(MAIN/'stage9a_primary_inference.json')
    assert all(sha(p)==expected for p,expected in config['source_sha256'].items())
    technical=load(MAIN/'stage9a_mask_backend_validation.json')
    assert technical['pass_all'] and technical['examples']==12
    assert all(sha(p)==expected for p,expected in technical['source_sha256'].items())
    review=load(MAIN/'annotations/answer_extraction_review_frozen.json')
    packets=load(MAIN/'annotations/answer_packets.json')['rows']
    idx=load(MAIN/'annotations/answer_packet_index.json')
    assert review['frozen'] and not review['gold_or_accuracy_accessed']
    assert sha(MAIN/'annotations/answer_packets.json')==review['packets_sha256']
    assert sha(MAIN/'annotations/answer_decisions.json')==review['ledger_sha256']
    assert len(review['rows'])==len(packets)==1717
    assert {r['packet_id'] for r in review['rows']}=={r['packet_id'] for r in packets}
    assert datetime.fromisoformat(review['at'])<datetime.fromisoformat(inference['at'])
    main=load(MAIN/'audit/interventions.json');controls=load(MAIN/'controls_v1/audit/interventions.json')
    assert controls['rows']==main['deferred_control_rows'] and len(controls['rows'])==87
    assert controls['parent_sha256']==sha(MAIN/'audit/interventions.json')
    assert len({r['result_key'] for r in idx['rows']+idx['exact_native_reuse']})==1904
    frame=pd.DataFrame(load(MAIN/'audit/scored_conditions.json')['rows'])
    assert len(frame)==2138 and frame.family_id.nunique()==64
    assert not frame.duplicated(['task_id','condition_id']).any()
    assert len(set(frame.loc[frame.execution=='run','result_key']))==1904
    counts={}
    for assay,filename,n in [('cumulative','cumulative_cutoff_results',960),('local','local_window_results',960),('demand','demand_aligned_knockout',218)]:
        table=pd.read_parquet(MAIN/f'stage9a_{filename}.parquet')
        assert len(table)==n and (table.assay==assay).all()
        expected=frame[frame.assay==assay].sort_values(['task_id','condition_id'])
        actual=table.sort_values(['task_id','condition_id'])
        assert list(zip(actual.task_id,actual.condition_id))==list(zip(expected.task_id,expected.condition_id))
        assert np.array_equal(actual.accuracy_no_credit.to_numpy(),expected.accuracy_no_credit.to_numpy())
        counts[assay]=n
    # Independent wide-table arithmetic rather than invoking the estimator implementation.
    wide=frame.pivot(index=['family_id','arm'],columns='condition_id',values='accuracy_no_credit')
    values={}
    for key,condition in [('P1_512','cutoff_512'),('P1_2048','cutoff_2048')]:
        damage=wide.cutoff_full-wide[condition]
        values[key]=damage.unstack('arm')['thinking']-damage.unstack('arm')['instruct_cot']
    damage=wide.cutoff_full-(wide.local20_3+wide.local20_4)/2
    values['P2']=damage.unstack('arm')['thinking']-damage.unstack('arm')['instruct_cot']
    demand=frame[frame.assay=='demand'].pivot(index=['family_id','arm'],columns='role',values='accuracy_no_credit')
    effect=(demand.control-demand.demand).unstack('arm')
    values['P3']=effect.thinking-effect.instruct_cot
    verified={}
    for key,series in values.items():
        series=series.dropna();reference=inference['primary'][key]['simultaneous']
        assert len(series)==reference['n_families']
        assert np.isclose(series.mean(),reference['mean'],atol=1e-15)
        assert set(series.index)==set(reference['paired_families'])
        verified[key]=dict(n=len(series),mean=float(series.mean()))
    figures=list((MAIN/'figures').glob('figure*.*'))
    assert len(figures)==10 and sum(p.suffix=='.png' for p in figures)==5 and sum(p.suffix=='.pdf' for p in figures)==5
    for path in figures:
        header=path.read_bytes()[:8]
        assert header.startswith(b'%PDF') if path.suffix=='.pdf' else header==b'\x89PNG\r\n\x1a\n'
    summary=(MAIN/'stage9a_summary.md').read_text()
    assert all((MAIN/url).exists() for url in re.findall(r'\]\(([^)]+)\)',summary))
    result=dict(at=datetime.now(timezone.utc).isoformat(),pass_all=True,scope='Main/secondary postprocessing; control execution still separately required',
        parquet_rows=counts,independent_primary_arithmetic=verified,review_packets=1717,
        review_preceded_scoring=True,frozen_sources_unchanged=True,controls_exact_original_inventory=True,
        figure_files=10,visual_review='All5 PNGs inspected; overlap repaired in figures2/3 and rechecked',
        script_hashes={str(p):sha(p) for p in [Path(__file__),Path('scripts/stage9a_dynamics/analyze_main.py'),Path('scripts/stage9a_dynamics/secondary_analysis.py'),Path('scripts/stage9a_dynamics/figures.py')]})
    save(MAIN/'audit/main_postprocess_validation.json',result)
    print(json.dumps(result['independent_primary_arithmetic']))


if __name__=='__main__':main()
