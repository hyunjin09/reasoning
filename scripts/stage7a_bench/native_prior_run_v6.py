"""Fresh native generation for the already frozen three-condition image bank."""
import gc
import time

import torch

from scripts.stage7a.common import write_json, write_jsonl, sha
from scripts.stage7a_bench.bounded_attention_v2 import bounded_native_attention
from scripts.stage7a_bench.image_inputs_v2 import prepare_condition
from scripts.stage7a_bench.prior_controls_v2 import verify_fixed_input
from scripts.stage7a_bench.pilot_freeze_v6 import dependency_hashes
from visual_reasoning.stage0.modeling import generate_once
from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs


def release():
    gc.collect()
    torch.cuda.empty_cache()


def run_native_controls(model, processor, entries, dest, signature, config, started):
    protocol = config['locked_generation_protocol']
    cap = protocol['max_new_tokens']
    parameters = protocol_parameters('official', cap, protocol['seed'])
    kwargs = transformers_generation_kwargs(parameters)
    eos = model.generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else eos
    completed, mechanics = [], []
    for entry in entries:
        for condition in ('mask', 'unrelated', 'no_image'):
            if dependency_hashes() != signature['execution_signature']['dependencies']:
                raise ValueError('Native-control implementation changed during the run')
            variant = signature['control_rows'][entry['id']]['fixed_'+condition]
            example = dest / 'examples' / entry['id'] / condition
            prepared = first = second = generation = tokens = None
            try:
                prepared, meta = prepare_condition(processor, variant, 'cuda:0')
                verify_fixed_input(entry, entry['native_input'], variant, meta)
                # Canonical comparison covers each actual control input. Neither
                # these short mechanics traces nor their content select controls.
                first = generate_once(model, processor, prepared, 128, None,
                    generation_kwargs=kwargs, seed=parameters['seed'], collect_predictive_metrics=False)
                with bounded_native_attention():
                    second = generate_once(model, processor, prepared, 128, None,
                        generation_kwargs=kwargs, seed=parameters['seed'], collect_predictive_metrics=False)
                check = dict(entry_id=entry['id'], condition=condition, cap=128,
                    comparison='Canonical versus bounded eager native generation',
                    exact=first['generated_token_ids'] == second['generated_token_ids'],
                    canonical_token_ids=first['generated_token_ids'],
                    bounded_token_ids=second['generated_token_ids'], scientific_use=False)
                mechanics.append(check)
                write_json(dest / 'native_mechanics.json', dict(checks=mechanics))
                if not check['exact']:
                    raise ValueError('Actual native-control canonical/bounded token parity failed')
                first = second = None
                release()
                write_json(example / 'input.json', meta, freeze=True)
                write_json(example / 'manifest_row.json', variant, freeze=True)
                begin = time.perf_counter()
                torch.cuda.reset_peak_memory_stats()
                with bounded_native_attention():
                    generation = generate_once(model, processor, prepared, cap, None,
                        generation_kwargs=kwargs, seed=parameters['seed'], collect_predictive_metrics=False)
                tokens = generation.pop('token_rows')
                generation.pop('attention_arrays', None)
                write_json(example / 'generation.json', generation, freeze=True)
                write_jsonl(example / 'tokens.jsonl', tokens, freeze=True)
                ids = generation['generated_token_ids']
                ended = bool(ids and ids[-1] in eos)
                result = dict(entry_id=entry['id'], event_id=variant['event_id'], condition=condition,
                    complete=ended and '</think>' in generation['raw_decoded_response'],
                    ended_with_eos=ended, truncated=len(ids) >= cap and not ended, token_count=len(ids),
                    generation_sha256=sha(example / 'generation.json'), tokens_sha256=sha(example / 'tokens.jsonl'),
                    elapsed_seconds=time.perf_counter()-begin,
                    peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
                    native_reasoning_prefix_supplied=False, passive_features_collected=False)
                write_json(example / 'result.json', result, freeze=True)
                completed.append(dict(entry_id=entry['id'], condition=condition,
                    result_sha256=sha(example / 'result.json')))
                print(f'NATIVE_CONTROL {len(completed)}/{3*len(entries)} {entry["id"]} '
                      f'{condition} tokens={len(ids)} eos={ended}', flush=True)
            finally:
                prepared = first = second = generation = tokens = None
                release()
    write_json(dest / 'run_summary.json', dict(completed=True, mode='native_controls',
        results=completed, seconds=time.perf_counter()-started,
        native_convergence_certified=False, full_semantic_review_pending=True))
