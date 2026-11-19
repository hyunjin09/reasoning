"""Run a verified benchmark pilot only inside the existing GPU allocation.

First certify canonical/bounded prefix and source-assay mechanics on the
smallest frozen input. Scientific execution requires that exact certificate.
No allocation, membership selection, automatic retry or classification occurs.
"""
import argparse
import os
import platform
from pathlib import Path
import re
import resource
import time

import numpy as np
import torch
from transformers import AutoTokenizer

from scripts.stage7a.common import ROOT, configure_fresh_processor, read_json, sha, write_json
from scripts.stage7a_bench.causal_execution_v11 import execute_verified_event, release
from scripts.stage7a_bench.causal_mechanics_v11 import compare_prefix_to_canonical, PrefixMechanicsError
from scripts.stage7a_bench.document_inputs_v2 import prepare_document
from scripts.stage7a_bench.image_inputs_v2 import prepare_condition as prepare_image
from scripts.stage7a_bench.pilot_freeze_v11 import load_frozen_pilot, dependency_hashes
from scripts.stage7a_bench.causal_provenance_v2 import object_sha
from scripts.stage7a_bench.prior_controls_v11 import requested_native_banks
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment

OUT = ROOT / 'outputs/stage7a_bench_v2'


def mechanics_entry(entries):
    return min(entries, key=lambda e: (e['native_input']['prompt_token_count'] +
        len(e['event']['history_before_ed_token_ids']), e['id']))


def artifact(reference):
    path = (ROOT / reference['path']).resolve()
    if not path.is_relative_to(OUT / 'causal_pilot/raw') or sha(path) != reference['sha256']:
        raise ValueError('Causal mechanics artifact changed or is outside the active run directory')
    return path


def validate_mechanics(certificate, signature, entries):
    if (certificate.get('status') != 'PASS_ACTUAL_4B_CAUSAL_MECHANICS' or
            certificate.get('execution_signature') != signature):
        raise ValueError('Mechanics does not certify this pilot, runtime and implementation')
    chosen = mechanics_entry(entries)
    if certificate.get('mechanics_entry_id') != chosen['id']:
        raise ValueError('Mechanics entry differs from frozen input-cost selection')
    paths = {k:artifact(v) for k, v in certificate['artifacts'].items()}
    if set(paths) != {'prefix', 'event', 'distributions'}:
        raise ValueError('Mechanics requires prefix, source and distribution evidence')
    prefix, result = read_json(paths['prefix']), read_json(paths['event'])
    required = ('passed', 'actual_gpu_validation', 'all_layer_kv_exact',
                'logits_exact', 'rope_exact', 'prepared_input_unchanged')
    if (any(prefix.get(k) is not True for k in required) or prefix.get('id') != chosen['id'] or
            prefix.get('model_layers') != 36 or prefix.get('model_attention_heads') != 32 or
            prefix.get('model_hidden_size') != 2560 or prefix.get('parameter_dtype') != 'torch.bfloat16'):
        raise ValueError('Exact actual4B GPU prefix mechanics is required')
    expected = {'N'} | {s+'_W2' for s in chosen['w2_sources']} | {s+'_W8' for s in chosen['w8_sources']}
    checks = {'canonical_native_exact', 'unhooked_exact', 'noop_exact',
              'suppression_repeat_exact', 'all_finite'} | {s+'_canonical_exact' for s in expected-{'N'}}
    if (result.get('id') != chosen['id'] or result.get('complete') is not True or
            result.get('source_assay_mechanics') is not True or
            result.get('passive_features_collected') is not False or
            set(result.get('arms', {})) != expected or
            any(result.get('checks', {}).get(k) is not True for k in checks) or
            any(v is not True for v in result['checks'].values()) or
            any(a.get('finite') is not True for a in
                [*result['arms'].values(), *result.get('controls', {}).values()])):
        raise ValueError('Complete canonical, unhooked, repeat and all-window source mechanics is required')
    return chosen['id']


def reference(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--pilot', required=True)
    parser.add_argument('--pilot-sha256', required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--mechanics', action='store_true')
    mode.add_argument('--native-controls', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch('[a-z0-9_]+', args.run_id):
        raise ValueError('Unsafe run identity')
    config = read_json(OUT / 'config/runtime_node02_v3.json')
    allocation = config['runtime']
    if (os.environ.get('SLURM_JOB_ID') != allocation['slurm_allocation'] or
            platform.node().split('.')[0] != allocation['node']):
        raise RuntimeError('Use the existing registered Slurm/tmux allocation')
    if torch.cuda.device_count() != 1 or 'A6000' not in torch.cuda.get_device_name(0):
        raise RuntimeError('Expected the existing single A6000')
    tokenizer = AutoTokenizer.from_pretrained(config['model_checkpoint'], local_files_only=True)
    pilot_ref = dict(path=args.pilot, sha256=args.pilot_sha256)
    pilot = load_frozen_pilot(pilot_ref, tokenizer)
    entries = pilot['selected_entries']
    if not entries:
        raise ValueError('Empty frozen pilot')
    signature = dict(pilot=pilot_ref, dependencies=dependency_hashes(),
        runtime_sha256=sha(OUT / 'config/runtime_node02_v3.json'))
    certificate_path = OUT / 'causal_pilot/mechanics' / (pilot['benchmark']+'.json')
    if args.mechanics:
        if certificate_path.exists():
            raise FileExistsError('Existing mechanics certificate cannot be replaced')
        selected = [mechanics_entry(entries)]
        cert_ref = None
    else:
        validate_mechanics(read_json(certificate_path), signature, entries)
        cert_ref = reference(certificate_path)
        selected = entries
    native_banks = {}
    if args.native_controls:
        native_banks = requested_native_banks(selected)
        selected = [entry for entry in selected if entry['id'] in native_banks]
        if not selected:
            raise ValueError('Frozen pilot has no reviewed native control bank')
    directory = 'causal_pilot/native_controls' if args.native_controls else 'causal_pilot/raw'
    dest = OUT / directory / args.run_id
    dest.mkdir(parents=True, exist_ok=False)
    run_signature = dict(execution_signature=signature,
        mechanics=args.mechanics, mechanics_certificate=cert_ref,
        event_ids=[e['id'] for e in selected], passive_features_collected=False)
    if args.native_controls:
        run_signature.update(mode='native_controls',
            generation_protocol=config['locked_generation_protocol'],
            entry_sha256={e['id']:object_sha(e) for e in selected},
            control_rows={eid:bank[0] for eid, bank in native_banks.items()},
            control_provenance={eid:bank[1] for eid, bank in native_banks.items()})
    write_json(dest / 'signature.json', run_signature, freeze=True)
    for name, digest in signature['dependencies'].items():
        source = ROOT / name
        if sha(source) != digest:
            raise ValueError('Dependency changed before source snapshot')
        target = dest / 'source_snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    started = time.perf_counter()
    completed = []
    try:
        checkpoint = Path(config['model_checkpoint'])
        processor, model = load_runtime(checkpoint, device='cuda:0')
        configure_fresh_processor(processor)
        if next(model.parameters()).dtype != torch.bfloat16:
            raise RuntimeError('The frozen BF16 model dtype changed')
        write_json(dest / 'environment.json', dict(
            **runtime_environment(checkpoint, model, 40960),
            slurm_job_id=os.environ['SLURM_JOB_ID'], node=platform.node(),
            parameter_dtype=str(next(model.parameters()).dtype)))
        if args.native_controls:
            from scripts.stage7a_bench.native_prior_run_v11 import run_native_controls
            run_native_controls(model, processor, selected, dest, run_signature, config, started)
            return
        for index, entry in enumerate(selected):
            if dependency_hashes() != signature['dependencies']:
                raise ValueError('Implementation changed during the run')
            torch.cuda.reset_peak_memory_stats()
            if args.mechanics:
                prepare = prepare_document if entry['row'].get('document_path') else prepare_image
                prepared, meta = prepare(processor, entry['row'], 'cuda:0')
                try:
                    if meta != entry['native_input']:
                        raise ValueError('Mechanics input differs from frozen native input')
                    prefix = compare_prefix_to_canonical(model, prepared, entry)
                    write_json(dest / 'prefix_mechanics.json', prefix, freeze=True)
                except PrefixMechanicsError as error:
                    write_json(dest / 'prefix_mechanics_failed.json', error.evidence, freeze=True)
                    raise
                finally:
                    del prepared
                    release('cuda:0')
            result, distributions = execute_verified_event(model, processor, entry, 'cuda:0',
                                                            mechanics=args.mechanics)
            result.update(pilot_sha256=args.pilot_sha256,
                peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
                peak_host_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            path = dest / 'events' / (entry['id']+'.json')
            path.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(path.with_suffix('.npz'), **distributions)
            write_json(path, result, freeze=True)
            completed.append(dict(event=reference(path), distributions=reference(path.with_suffix('.npz'))))
            print(f'{index+1}/{len(selected)} {entry["id"]} seconds={result["seconds"]:.1f}', flush=True)
        if args.mechanics:
            certificate = dict(status='PASS_ACTUAL_4B_CAUSAL_MECHANICS', execution_signature=signature,
                mechanics_entry_id=selected[0]['id'], artifacts=dict(
                    prefix=reference(dest / 'prefix_mechanics.json'), **completed[0]),
                selection_rule='Minimum frozen prompt plus native-history token count, then event ID; no scores')
            validate_mechanics(certificate, signature, entries)
            certificate_path.parent.mkdir(parents=True, exist_ok=True)
            with certificate_path.open('x') as stream:
                import json
                json.dump(certificate, stream, indent=2)
                stream.write('\n')
        write_json(dest / 'run_summary.json', dict(completed=True, events=completed,
            mechanics=args.mechanics, seconds=time.perf_counter()-started, passive_features_collected=False))
    except BaseException as error:
        write_json(dest / 'run_summary.json', dict(completed=False, events=completed,
            mechanics=args.mechanics, seconds=time.perf_counter()-started,
            error_type=type(error).__name__, error=str(error), automatic_retry=False))
        raise


if __name__ == '__main__':
    main()
