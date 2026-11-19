"""Fresh frozen-event source suppression and semantic controls; no passive features."""
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
from scripts.stage7a.causal_variants import semantic_variant, fixed_prefix_variants
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage6a.runtime import prepare_condition
from visual_reasoning.stage6b.text_interface import prefill_condition, validate_text_replay
from visual_reasoning.stage6b.runtime import score_equal
from visual_reasoning.stage4a.runtime import make_event_root, score_event_arm
from visual_reasoning.stage7a.assay import score_bundle


def remap_groups(entry, meta):
    visual = meta['visual_token_indices']
    if not visual:
        return {}
    roles = {'T': entry['physical_demanded_source'], 'X': entry['physical_alternative_source'], 'I': 'I'}
    groups = {r: [visual[i] for i in entry['row']['local_source_groups'].get(p, [])]
              for r, p in roles.items() if r != 'I' or entry['physical_demanded_source'] == 'T'}
    return {**{r: g for r, g in groups.items() if g}, 'G': visual}


def release():
    gc.collect()
    torch.cuda.empty_cache()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--mechanics', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    config = read_json(OUT / 'config/stage7a_config.json')
    assert os.environ['SLURM_JOB_ID'] == config['runtime']['slurm_allocation']
    assert platform.node().split('.')[0] == config['runtime']['node']
    assert torch.cuda.device_count() == 1 and 'A6000' in torch.cuda.get_device_name(0)
    manifest = ROOT / args.manifest
    entries = read_jsonl(manifest)
    assert entries and len({e['split'] for e in entries}) == 1
    split = entries[0]['split']
    certificate = read_json(OUT / 'audit' / (manifest.stem + '.json'))
    assert certificate['status'] == 'FROZEN' and certificate['manifest_sha256'] == sha(manifest)
    if args.mechanics:
        assert split == 'discovery' and certificate['role'] == 'discovery mechanics only'
    else:
        assert read_json(OUT / 'audit/fresh_causal_mechanics.json')['passed']
    if split == 'confirmation':
        assert not args.mechanics
        assert read_json(OUT / 'config/discovery_thresholds.json')['frozen']
    dest = OUT / 'raw' / args.run_id
    if (dest / 'signature.json').exists() and not args.resume:
        raise RuntimeError('Existing run requires --resume')
    dependencies = ['scripts/stage7a/run_events.py', 'scripts/stage7a/causal_variants.py',
                    'code/visual_reasoning/stage7a/assay.py', 'scripts/stage7a/common.py',
                    'code/visual_reasoning/stage4a/runtime.py', 'code/visual_reasoning/stage6b/text_interface.py',
                    'code/visual_reasoning/stage6a/runtime.py', 'code/visual_reasoning/stage3c9/streaming.py']
    signature = dict(manifest_sha256=sha(manifest), config_sha256=sha(OUT / 'config/stage7a_config.json'),
                     value_foil_policy_sha256=sha(OUT / 'config/value_foil_policy.json'),
                     image_budget_sha256=sha(OUT / 'config/image_preprocessing.json'), split=split,
                     mechanics=args.mechanics, passive_features_collected=False,
                     threshold_sha256=sha(OUT / 'config/discovery_thresholds.json') if split == 'confirmation' else None,
                     dependency_sha256={p: sha(ROOT / p) for p in dependencies})
    write_json(dest / 'signature.json', signature, freeze=True)
    for source in dependencies:
        target = dest / 'source_snapshot' / source
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists(): assert target.read_bytes() == (ROOT / source).read_bytes()
        else: target.write_bytes((ROOT / source).read_bytes())
    processor, model = load_runtime(Path(config['model_checkpoint']), device='cuda:0')
    configure_fresh_processor(processor)
    assert next(model.parameters()).dtype == torch.bfloat16
    write_json(dest / 'environment.json', dict(**runtime_environment(Path(config['model_checkpoint']), model, 40960),
               slurm_job_id=os.environ['SLURM_JOB_ID'], node=platform.node(), parameter_dtype='torch.bfloat16'))
    native_rows = {r['event_id']: r for r in read_jsonl(OUT / 'cohort/native_manifest.jsonl')}
    cohort_freeze = read_json(OUT / 'audit/cohort_freeze.json')
    assert sha(OUT / 'annotations/source_edit_review.json') == cohort_freeze['source_review_sha256']
    source_reviews = {r['base_id']: r for r in read_json(OUT / 'annotations/source_edit_review.json')}
    results = []
    for index, entry in enumerate(entries):
        result_path = dest / 'events' / (entry['id'] + '.json')
        if result_path.exists():
            existing = read_json(result_path)
            assert existing['complete'] and existing['manifest_sha256'] == signature['manifest_sha256']
            results.append({k: existing[k] for k in ('id', 'seconds', 'checks')})
            continue
        start = time.perf_counter()
        torch.cuda.reset_peak_memory_stats()
        row, event = entry['row'], entry['event']
        if row.get('image_path'): assert sha(row['image_path']) == row['image_sha256']
        review = read_json(entry['review_path'])
        assert sha(entry['review_path']) == entry['review_sha256']
        assert sha(entry['native_input_path']) == entry['native_input_sha256']
        assert sha(entry['native_generation_path']) == entry['native_generation_sha256']
        assert sha(entry['native_tokens_path']) == entry['native_tokens_sha256']
        if entry.get('binding_review_path'):
            assert sha(entry['binding_review_path']) == entry['binding_review_sha256']
        assert review['generation_sha256'] == sha(entry['native_generation_path'])
        assert review['tokens_sha256'] == sha(entry['native_tokens_path'])
        assert not review['causal_or_passive_scores_used']
        prepared, meta = prepare_condition(processor, row, 'cuda:0')
        native = read_json(entry['native_input_path'])
        assert all(meta[k] == native[k] for k in (
            'prompt_token_ids', 'visual_token_indices', 'image_grid_thw', 'decoded_image_sha256'))
        groups = remap_groups(entry, meta)
        assert groups == entry['source_groups']
        prefill, prefill_audit = prefill_condition(model, prepared, row.get('no_image', False))
        del prepared
        if args.mechanics and row.get('no_image'):
            prefill_audit['text_replay'] = validate_text_replay(model, prefill, event)
        root = make_event_root(model, prefill, event)
        arms = {}
        distributions = {}
        arms['N'], distributions['N'] = score_bundle(model, root, event, groups, validate=args.mechanics)
        checks = {'native_input_exact': True, 'all_finite': arms['N']['finite']}
        settings = {'source_groups': groups, 'irrelevant_controls_validated': False}
        if args.mechanics:
            canonical = score_event_arm(model, root, settings, event, validate=True)
            unhooked, _ = score_bundle(model, root, event, groups, hooked=False)
            checks['canonical_native_exact'] = score_equal(arms['N'], canonical)
            checks['unhooked_exact'] = score_equal(arms['N'], unhooked)
        for window, sources in [(2, entry['w2_sources']), (8, entry['w8_sources'])]:
            for source in sources:
                key = f'{source}_W{window}'
                arms[key], _ = score_bundle(model, root, event, groups, source=source, window=window, validate=args.mechanics)
                if args.mechanics:
                    canonical = score_event_arm(model, root, settings, event, roi=source, window=window, validate=True)
                    checks[key + '_canonical_exact'] = score_equal(arms[key], canonical)
        if args.mechanics and entry['w2_sources']:
            source = entry['w2_sources'][0]
            noop, _ = score_bundle(model, root, event, groups, source=source, window=8, gain=1., validate=True)
            repeated, _ = score_bundle(model, root, event, groups, source=source, validate=True)
            checks['noop_exact'] = score_equal(arms['N'], noop)
            checks['suppression_repeat_exact'] = repeated == arms[source + '_W2']
        del root, prefill
        release()
        controls = {}
        control_audits = {}
        variants = []
        if not args.mechanics:
            for source in entry['cf_physical_sources']:
                for kind in ('sham', 'semantic'):
                    reviewed_sha = source_reviews[row['base_id']]['image_sha256'][f'condition__{source}_{kind}.png']
                    variant, audit = semantic_variant(row, source, kind, reviewed_sha)
                    role = 'T' if source == entry['physical_demanded_source'] else 'X'
                    # Same-content shams calibrate distribution-similarity
                    # tolerances using discovery only, before confirmation.
                    variants.append((f'{role}_{kind}', variant, audit, kind == 'sham'))
            fixed_variants, unavailable = fixed_prefix_variants(entry, native_rows)
            control_audits.update(unavailable)
            for condition, variant in fixed_variants:
                assert variant['prompt'] == row['prompt']
                variants.append(('fixed_' + condition, variant,
                                 {'scope': 'Same native reasoning prefix, different image input; not a fresh-acquisition measurement'}, True))
        # Fresh text-interface mechanics use the same reviewed discovery prefix;
        # this is a replay audit, not a selected no-image native claim.
        elif not row.get('no_image'):
            variant = {**row, 'no_image': True, 'image_path': None}
            variants.append(('text_interface_mechanics', variant, {'role': 'mechanical fixed-prefix text replay'}, True))
        for name, variant, audit, retain_distribution in variants:
            if variant.get('image_path'): assert sha(variant['image_path']) == variant['image_sha256']
            prepared, variant_meta = prepare_condition(processor, variant, 'cuda:0')
            if name.endswith(('_sham', '_semantic')):
                assert all(variant_meta[k] == meta[k] for k in ('prompt_token_ids', 'visual_token_indices', 'image_grid_thw'))
            prefill, replay_audit = prefill_condition(model, prepared, variant.get('no_image', False))
            del prepared
            if args.mechanics and variant.get('no_image'):
                replay_audit['text_replay'] = validate_text_replay(model, prefill, event)
            root = make_event_root(model, prefill, event)
            variant_groups = remap_groups(entry, variant_meta)
            controls[name], distribution = score_bundle(model, root, event, variant_groups)
            if retain_distribution: distributions[name] = distribution
            if args.mechanics:
                canonical = score_event_arm(model, root, {'source_groups': variant_groups}, event)
                checks[name + '_canonical_exact'] = score_equal(controls[name], canonical)
            control_audits[name] = dict(**audit, input=variant_meta, replay=replay_audit)
            del root, prefill
            release()
        checks['all_finite'] = all(a['finite'] for a in [*arms.values(), *controls.values()])
        result = dict(id=entry['id'], event_id=entry['event_id'], base_id=entry['base_id'], split=split,
                      manifest_sha256=signature['manifest_sha256'], checks=checks, arms=arms, controls=controls,
                      control_audits=control_audits, prefill_audit=prefill_audit,
                      seconds=time.perf_counter()-start, peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
                      peak_host_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      passive_features_collected=False, complete=all(checks.values()))
        result_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(result_path.with_suffix('.npz'), **distributions)
        write_json(result_path, result)
        assert result['complete'], checks
        results.append({k: result[k] for k in ('id', 'seconds', 'checks')})
        print(f'{index+1}/{len(entries)} {entry["id"]} seconds={result["seconds"]:.1f} checks={checks}', flush=True)
    write_json(dest / 'run_summary.json', dict(completed=True, mechanics=args.mechanics, split=split, results=results))
    if args.mechanics:
        write_json(OUT / 'audit/fresh_causal_mechanics.json', dict(passed=True, evidence=str(dest), results=results), freeze=True)


if __name__ == '__main__':
    main()
