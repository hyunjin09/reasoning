"""Verify retained complete conditions across original runs and worker shards.

Original bundles stay in place. The only interrupted-run exception is the
explicitly protected MathWild prefix; every other science run and wrapper must
finish. This reader neither releases a benchmark nor admits a causal pilot.
"""
from pathlib import Path

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha
from scripts.stage7a_bench.causal_provenance_v2 import verified_families
from scripts.stage7a_bench.native_migration_v3 import pending_rows
from scripts.stage7a_bench.native_yield_v2 import indexed, summarize_condition
from scripts.stage7a_bench.reviewed_units_v5 import ordered_owners, verify_unit

OUT = ROOT / 'outputs/stage7a_bench_v2'
RETAINED = {'mathvision_wild', 'mmmu_pro', 'mmlongbench_doc'}


def load_completed_screen(benchmark, bindings):
    if benchmark not in RETAINED:
        raise ValueError('Only the three retained remaining benchmarks use this adapter')
    hashes = {}

    def path(name, directory):
        p = (ROOT / name).resolve()
        if not p.is_relative_to(OUT / directory):
            raise ValueError('Evidence outside its active-stage directory')
        return p

    def read(p, lines=False):
        hashes[str(p.relative_to(ROOT))] = sha(p)
        return read_jsonl(p) if lines else read_json(p)

    freeze = read(OUT / 'cohort/sample_freeze.json')['native_screen']
    specs = {key[len(benchmark)+1:]: spec for key, spec in freeze.items()
             if key.startswith(benchmark+'_')}
    if not specs or set(bindings) != set(specs):
        raise ValueError('All frozen retained conditions require an explicit binding')
    certificate = read(OUT / 'audit/native_source_family_integrity.json')
    screen, review_groups, provenance, generated, families = {}, {}, [], [], None
    for condition, spec in specs.items():
        binding = bindings[condition]
        manifest = path(spec['manifest'], 'cohort/benchmark_manifests')
        if path(binding['manifest'], 'cohort/benchmark_manifests') != manifest:
            raise ValueError('Binding differs from the frozen condition manifest')
        rows = read(manifest, True)
        digest = sha(manifest)
        if (digest != spec['sha256'] or len(rows) != spec['count'] or not rows or
                any(r['benchmark'] != benchmark or r['condition'] != condition for r in rows)):
            raise ValueError('Frozen native condition changed')
        runs = indexed(binding['runs'], 'native_run_id')
        owners = ordered_owners([r['event_id'] for r in rows],
                                {run: info['event_ids'] for run, info in runs.items()})
        results_by_run, labels_by_run, bases = {}, {}, {}
        for run, info in runs.items():
            if not isinstance(run, str) or Path(run).name != run or run in ('.', '..'):
                raise ValueError('Unsafe native run identity')
            base = bases[run] = path(OUT / 'native_screen/generations' / run,
                                     'native_screen/generations')
            signature = read(base / 'signature.json')
            if signature['manifests'].get(str(manifest.relative_to(ROOT))) != digest:
                raise ValueError('Worker signature lacks the exact frozen manifest')
            if info.get('preserved_prefix'):
                reference = info['preserved_prefix']
                packet_path = path(reference['path'], 'config')
                if sha(packet_path) != reference['sha256']:
                    raise ValueError('Preserved-prefix receipt changed')
                packet = read(packet_path)
                if (benchmark != 'mathvision_wild' or condition != 'photo' or
                        packet['predecessor_run_id'] != run or
                        packet['completed_event_ids'] != info['event_ids'] or
                        signature['event_ids'] != packet['all_event_ids']):
                    raise ValueError('Only the protected original MathWild prefix may be interrupted')
                pending_rows(ROOT, rows, packet, packet['continuation_run_id'])
                hashes.update(packet['protected_files'])
                results_by_run[run] = None
            else:
                summary = read(base / 'run_summary.json')
                wrapper = read(path(OUT / 'raw' / run / 'run_summary.json', 'raw'))
                results_by_run[run] = indexed(summary['results'])
                if (summary.get('completed') is not True or wrapper.get('completed') is not True or
                        type(wrapper.get('exit_code')) is not int or wrapper['exit_code'] != 0 or
                        signature['event_ids'] != info['event_ids'] or
                        set(results_by_run[run]) != set(info['event_ids'])):
                    raise ValueError('Shard and registered wrapper must complete exactly their owned units')
            review_path = path(info['review_path'], 'native_screen/manual_reviews')
            labels_by_run[run] = indexed(read(review_path, True))
            if not set(labels_by_run[run]) <= set(info['event_ids']):
                raise ValueError('Review outside its worker ownership')
        results, reviews = [], []
        for index, (event_id, run) in enumerate(owners):
            if Path(event_id).name != event_id or event_id in ('.', '..'):
                raise ValueError('Unsafe event identity')
            row, directory = rows[index], bases[run] / 'examples' / event_id
            if read(directory / 'manifest_row.json') != row:
                raise ValueError('Native source/prompt row changed')
            result = read(directory / 'result.json')
            if (any(result.get(k) != row[k] for k in ('event_id', 'base_id', 'benchmark', 'condition')) or
                    results_by_run[run] is not None and result != results_by_run[run][event_id]):
                raise ValueError('Individual result differs from its owned completed unit')
            results.append(result)
            if result.get('unavailable'):
                if (row.get('preflight_status', 'ready') == 'ready' or
                        result.get('unavailable_reason') != row['preflight_status'] or
                        event_id in labels_by_run[run]):
                    raise ValueError('Unavailable input must preserve its frozen reason without a review')
                continue
            if event_id not in labels_by_run[run]:
                raise ValueError('Generated response lacks a full semantic review')
            review = labels_by_run[run][event_id]
            meta, generation = read(directory / 'input.json'), read(directory / 'generation.json')
            tokens = read(directory / 'tokens.jsonl', True)
            if (row.get('image_path') and meta.get('image_path') != row['image_path'] or
                    (meta.get('image_assets') or []) != (row.get('image_assets') or []) or
                    row['no_image'] and (meta.get('visual_token_indices') or meta.get('image_grid_thw') is not None)):
                raise ValueError('Native image identity or no-image input differs')
            if row.get('document_path') and (
                    any(meta.get(k) != row[k] for k in
                        ('document_path', 'document_sha256', 'renderer_version', 'render_scale')) or
                    [p.get('physical_page') for p in meta.get('visual_images', [])] != list(range(1, row['page_count']+1))):
                raise ValueError('Native document identity or complete physical page order differs')
            verify_unit(row=row, index=index, manifest_sha256=digest, result=result, review=review,
                meta=meta, generation=generation, tokens=tokens,
                generation_sha256=sha(directory / 'generation.json'), tokens_sha256=sha(directory / 'tokens.jsonl'))
            reviews.append(review)
            generated.append(event_id)
            provenance.append(dict(event_id=event_id, native_run_id=run,
                                   review_path=runs[run]['review_path']))
        screen[condition] = summarize_condition(rows, results, reviews)
        review_groups[condition] = reviews
        if not screen[condition]['screen_complete']:
            raise ValueError('Retained condition coverage is incomplete')
        current = verified_families(certificate, str(manifest.relative_to(ROOT)), digest, benchmark)
        if families is not None and current != families:
            raise ValueError('Paired source-family certificates differ')
        families = current
    return dict(screen=screen, frozen_counts={k: v['count'] for k, v in specs.items()},
        family_map=families, generated_event_ids=generated, reviews=review_groups,
        unit_provenance=provenance, artifact_sha256=hashes,
        scope='Complete retained native coverage from original bundles; no gate release, pilot admission or causal scores')
