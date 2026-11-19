"""CPU-only reporting after successful completion of the frozen MMLong pilot.

This script cannot launch experiments, choose a recommendation, or bypass an
incomplete wrapper. Every exporter revalidates its input provenance.
"""
import argparse
from pathlib import Path
from transformers import AutoTokenizer
from scripts.stage7a.common import ROOT,read_json,write_json,sha
from scripts.stage7a_bench.compile_causal_v15 import compile_run
from scripts.stage7a_bench.pilot_yield_v12 import export as export_yield
from scripts.stage7a_bench.compare_benchmarks_v2 import export as export_comparison
from scripts.stage7a_bench.render_causal_v4 import render
from scripts.stage7a_bench.assemble_reduced_sweep_accounting_v20 import assemble

O=ROOT/'outputs/stage7a_bench_v2'

def ref(path):return dict(path=str(path.relative_to(ROOT)),sha256=sha(path))

def main(run_id):
    if run_id!='mmlong_causal_v15_20260915':raise ValueError('Only the currently authorized frozen pilot')
    wrapper=read_json(O/'causal_pilot/wrappers'/f'{run_id}.json')
    if wrapper.get('completed') is not True or wrapper.get('exit_code')!=0:
        raise ValueError('Complete successful scientific wrapper required')
    config=read_json(O/'config/runtime_node02_two_gpu_v15.json')
    tokenizer=AutoTokenizer.from_pretrained(config['model_checkpoint'],local_files_only=True)
    result=compile_run(run_id,tokenizer)
    assert result['events']==42 and result['native_bases']==36 and result['source_families']==29
    compilation=O/'causal_pilot/compiled/mmlongbench_doc'/run_id/'compilation.json'
    native=O/'native_screen/reports/mmlong_pilot_bound_native_v18/report.json'
    request=O/'causal_pilot/report_requests'/f'{run_id}_v20.json'
    write_json(request,dict(compilation=ref(compilation),native_report=ref(native)),freeze=True)
    directory=export_yield(str(request.relative_to(ROOT)))
    pair=dict(native_report=ref(native),pilot_yield=ref(directory/'yield.json'),native_condition='image_present')
    source=read_json(O/'analysis/comparison_requests/reduced_sweep_pre_mmlong_causal_v16.json')
    source['comparison_id']='reduced_sweep_complete_v20'
    assert 'mmlong' in source['reports'][-1]['native_report']['path']
    source['reports'][-1]=pair
    request=O/'analysis/comparison_requests/reduced_sweep_complete_v20.json'
    write_json(request,source,freeze=True)
    comparison=export_comparison(str(request.relative_to(ROOT)))
    assemble(str((comparison/'benchmark_comparison.json').relative_to(ROOT)))
    figures=read_json(O/'analysis/causal_figure_requests/completed_retained_pilots_pre_mmlong_v17.json')
    figures['figure_batch_id']='reduced_sweep_complete_causal_v20';figures['reports'].append(pair)
    request=O/'analysis/causal_figure_requests/reduced_sweep_complete_causal_v20.json'
    write_json(request,figures,freeze=True)
    render(str(request.relative_to(ROOT)))
    print('Completed raw reporting and figure exports; visual review, interpretation, acceptance and exactly one recommendation remain.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True)
    main(parser.parse_args().run_id)
