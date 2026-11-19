"""Finite historical-only replay audit on the allocated single GPU."""
import argparse
import gc
import os
import platform
import resource
import time
from pathlib import Path
import torch
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, sha
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage6a.runtime import prepare_condition
from visual_reasoning.stage6b.text_interface import prefill_condition, validate_text_replay
from visual_reasoning.stage6b.runtime import score_equal
from visual_reasoning.stage4a.runtime import make_event_root, score_event_arm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    config = read_json(OUT / 'config/stage7a_config.json')
    assert os.environ['SLURM_JOB_ID'] == config['runtime']['slurm_allocation']
    assert platform.node().split('.')[0] == config['runtime']['node']
    assert torch.cuda.device_count() == 1
    assert 'A6000' in torch.cuda.get_device_name(0)
    dest = OUT / 'raw' / args.run_id
    manifest = OUT / 'cohort/historical_mechanics_manifest.jsonl'
    write_json(dest / 'signature.json', dict(config_sha256=sha(OUT / 'config/stage7a_config.json'),
               manifest_sha256=sha(manifest), code_sha256=sha(Path(__file__)),
               scientific_role='historical mechanics only; never fresh confirmation'), freeze=True)
    processor, model = load_runtime(Path(config['model_checkpoint']), device='cuda:0')
    assert next(model.parameters()).dtype == torch.bfloat16
    write_json(dest / 'environment.json', {
        **runtime_environment(Path(config['model_checkpoint']), model, 40960),
        'slurm_job_id': os.environ['SLURM_JOB_ID'], 'node': platform.node(),
        'parameter_dtype': str(next(model.parameters()).dtype)})
    results = []
    for entry in read_jsonl(manifest):
        start = time.perf_counter()
        torch.cuda.reset_peak_memory_stats()
        prepared, meta = prepare_condition(processor, entry['row'], 'cuda:0')
        native = read_json(entry['native_input_path'])
        assert all(meta[k] == native[k] for k in [
            'prompt_token_ids', 'visual_token_indices', 'image_grid_thw', 'decoded_image_sha256'])
        prefill, audit = prefill_condition(model, prepared, entry['row'].get('no_image', False))
        del prepared
        if entry['row'].get('no_image'):
            audit['text_replay'] = validate_text_replay(model, prefill, entry['event'])
        root = make_event_root(model, prefill, entry['event'])
        settings = {'source_groups': entry['source_groups'], 'irrelevant_controls_validated': False}
        arms = {'N': score_event_arm(model, root, settings, entry['event'], validate=True),
                'unhooked': score_event_arm(model, root, settings, entry['event'], hooked=False)}
        checks = {'unhooked_exact': score_equal(arms['N'], arms['unhooked']),
                  'native_input_exact': True}
        for source in entry['w2_sources']:
            for window in [2, 8]:
                arms[f'{source}_W{window}'] = score_event_arm(
                    model, root, settings, entry['event'], roi=source, window=window, validate=True)
        if entry['w2_sources']:
            source = entry['w2_sources'][0]
            arms['noop'] = score_event_arm(model, root, settings, entry['event'],
                                           roi=source, window=8, gain=1., validate=True)
            repeated = score_event_arm(model, root, settings, entry['event'],
                                      roi=source, window=2, validate=True)
            checks['noop_exact'] = score_equal(arms['N'], arms['noop'])
            checks['suppression_replay_exact'] = repeated == arms[source + '_W2']
        result = dict(id=entry['id'], checks=checks, arms=arms, prefill_audit=audit,
                      seconds=time.perf_counter() - start,
                      peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
                      peak_host_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        write_json(dest / (entry['id'] + '.json'), result)
        assert all(checks.values()), checks
        results.append({k: v for k, v in result.items() if k not in ['arms', 'prefill_audit']})
        print(entry['id'], result['seconds'], checks, flush=True)
        del root, prefill, arms
        gc.collect()
        torch.cuda.empty_cache()
    write_json(dest / 'run_summary.json', dict(completed=True, historical_only=True, results=results))
    write_json(OUT / 'audit/canonical_path_audit.json', dict(passed=True,
        evidence=str(dest.relative_to(ROOT)), results=results, passive_extraction_run=False,
        assay='W2 primary, W8 sensitivity; all 36 layers and 32 heads; pre-W_O ROI contribution zero, no renormalization'))


if __name__ == '__main__':
    main()
