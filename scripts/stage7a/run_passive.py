"""Single-GPU passive extraction, gated by immutable causal labels."""
import argparse
import gc
import os
import platform
import resource
import time
from pathlib import Path
import numpy as np
import torch
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, sha, configure_fresh_processor
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage6a.runtime import prepare_condition
from visual_reasoning.stage6b.text_interface import prefill_condition
from visual_reasoning.stage4a.runtime import make_event_root
from visual_reasoning.stage6b.runtime import score_equal
from visual_reasoning.stage7a.passive import collect_state, collect_prior_sink, sink_release
from visual_reasoning.stage7a.metrics import passive_control_distances


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--causal-run', required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    config = read_json(OUT / 'config/stage7a_config.json')
    assert os.environ['SLURM_JOB_ID'] == config['runtime']['slurm_allocation']
    assert platform.node().split('.')[0] == config['runtime']['node']
    assert torch.cuda.device_count() == 1
    freeze_path = OUT / 'labels/label_freeze.json'
    frozen = read_json(freeze_path)
    assert frozen['frozen'] and frozen['passive_features_used_for_labels'] is False
    manifest = ROOT / args.manifest
    assert sha(manifest) in frozen['events_manifest_sha256'].values()
    for path, digest in frozen['labels_sha256'].items():
        assert sha(ROOT / path) == digest
    causal = OUT / 'raw' / args.causal_run
    assert read_json(causal / 'signature.json')['manifest_sha256'] == sha(manifest)
    assert read_json(causal / 'run_summary.json')['completed']
    dest = OUT / 'raw' / args.run_id
    if (dest / 'signature.json').exists() and not args.resume:
        raise RuntimeError('Existing passive run requires --resume')
    sources = ['scripts/stage7a/run_passive.py', 'code/visual_reasoning/stage7a/passive.py',
               'code/visual_reasoning/stage6b/runtime.py', 'code/visual_reasoning/stage5a/passive.py',
               'scripts/stage7a/common.py', 'code/visual_reasoning/stage7a/metrics.py', 'code/visual_reasoning/stage6a/runtime.py',
               'code/visual_reasoning/stage6b/text_interface.py', 'code/visual_reasoning/stage4a/runtime.py']
    signature = dict(manifest_sha256=sha(manifest), labels_freeze_sha256=sha(freeze_path),
                     causal_run=args.causal_run, config_sha256=sha(OUT / 'config/stage7a_config.json'),
                     dependency_sha256={p: sha(ROOT / p) for p in sources})
    write_json(dest / 'signature.json', signature, freeze=True)
    for source in sources:
        target = dest / 'source_snapshot' / source
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists(): assert target.read_bytes() == (ROOT / source).read_bytes()
        else: target.write_bytes((ROOT / source).read_bytes())
    processor, model = load_runtime(Path(config['model_checkpoint']), device='cuda:0')
    configure_fresh_processor(processor)
    assert next(model.parameters()).dtype == torch.bfloat16
    write_json(dest / 'environment.json', dict(**runtime_environment(Path(config['model_checkpoint']), model, 40960),
               slurm_job_id=os.environ['SLURM_JOB_ID'], node=platform.node(), parameter_dtype='torch.bfloat16'))
    results = []
    entries = read_jsonl(manifest)
    for index, entry in enumerate(entries):
        path = dest / 'events' / (entry['id']+'.json')
        if path.exists():
            existing = read_json(path)
            assert existing['complete'] and existing['manifest_sha256'] == signature['manifest_sha256']
            results.append(dict(id=entry['id'], seconds=existing['seconds']))
            continue
        start = time.perf_counter()
        torch.cuda.reset_peak_memory_stats()
        row = entry['row']
        if row.get('image_path'): assert sha(row['image_path']) == row['image_sha256']
        prepared, meta = prepare_condition(processor, row, 'cuda:0')
        native = read_json(entry['native_input_path'])
        assert all(meta[k] == native[k] for k in ('prompt_token_ids', 'visual_token_indices', 'image_grid_thw', 'decoded_image_sha256'))
        prefill, audit = prefill_condition(model, prepared, row.get('no_image', False))
        del prepared
        prior = collect_prior_sink(model, prefill, entry['event'])
        root = make_event_root(model, prefill, entry['event'])
        report, vectors = collect_state(model, root, entry, meta)
        reference = read_json(causal / 'events' / (entry['id']+'.json'))['arms']['N']
        assert score_equal(report, reference), 'Passive instrumentation changed canonical native readout'
        report.update(prior_t_minus8=prior, sink_release=sink_release(prior, report['telemetry']))
        with np.load(causal/'events'/(entry['id']+'.npz')) as distributions:
            report['offline_control_distances'] = passive_control_distances(entry['condition'], distributions)
        result = dict(id=entry['id'], base_id=entry['base_id'], split=entry['split'],
                      manifest_sha256=signature['manifest_sha256'], label_freeze_sha256=sha(freeze_path),
                      native_causal_exact=True, complete=True, report=report, prefill_audit=audit,
                      seconds=time.perf_counter()-start, peak_gpu_bytes=torch.cuda.max_memory_allocated(),
                      peak_host_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path.with_suffix('.npz'), **vectors)
        write_json(path, result)
        results.append(dict(id=entry['id'], seconds=result['seconds']))
        print(f'{index+1}/{len(entries)} {entry["id"]} passive native exact, seconds={result["seconds"]:.1f}', flush=True)
        del root, prefill
        gc.collect()
        torch.cuda.empty_cache()
    assert sha(freeze_path) == signature['labels_freeze_sha256']
    write_json(dest / 'run_summary.json', dict(completed=True, all_native_causal_exact=True, results=results,
               label_freeze_sha256=signature['labels_freeze_sha256']))


if __name__ == '__main__':
    main()
