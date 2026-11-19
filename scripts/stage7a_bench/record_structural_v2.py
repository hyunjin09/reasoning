"""Normalize completed manual image audits without reading model outputs."""
import argparse
from collections import Counter
from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json, write_jsonl

OUT = ROOT / 'outputs/stage7a_bench_v2'


def record(name):
    folder = OUT / 'structural_audit'
    notes_path = folder / f'{name}_manual_notes.json'
    notes = read_json(notes_path)
    manifest = OUT / 'cohort/benchmark_manifests' / f'{name}_structural.jsonl'
    rows = read_jsonl(manifest)
    frozen = read_json(OUT / 'cohort/sample_freeze.json')['structural'][name]
    assert sha(manifest) == frozen['sha256']
    assert len(notes) == len(rows) == 64
    assert [n[0] for n in notes] == list(range(64))
    sources, readouts, demands, qualities = [], [], [], []
    for row, note in zip(rows, notes):
        if name == 'mathvision_wild':
            index, official_id, source, readout, target, alternatives, reason, stratum, pair = note
            assert official_id == row['example_id']
            demand = 'visual_ocr' if stratum == 'printed_question' else 'visual'
            quality = 'manual_pair_review_with_notes'
            modes = ['photo', 'screenshot']
        elif name == 'mathsight':
            index, source, readout, target, alternatives, reason, demand, quality, pair = note
            stratum = demand
            modes = ['original', 'silent_no_image', 'explicit_guess']
        elif name == 'charxiv':
            index, source, readout, target, alternatives, reason, demand, quality = note
            pair, stratum, modes = False, 'scientific_chart', ['image_present']
        elif name == 'mmlongbench_doc':
            index, source, readout, target, alternatives, reason, demand, quality = note
            pair, stratum, modes = False, row['subject'], ['image_present']
        elif name in {'mmmu_pro', 'microvqa', 'medxpertqa_mm'}:
            index, source, readout, target, alternatives, reason, demand, quality = note
            pair, stratum = False, row.get('subject', row.get('family_id', 'multidiscipline'))
            modes = ['image_present', 'silent_no_image', 'explicit_guess']
        else:
            raise ValueError(name)
        source = 'S' + str(source) if isinstance(source, int) else source
        readout = 'R' + str(readout) if isinstance(readout, int) else readout
        assert source in {'S0', 'S1', 'S2', 'S3', 'S4'}
        assert readout in {'R0', 'R1', 'R2', 'R3', 'R4'}
        common = dict(benchmark=name, example_id=row['example_id'], structural_index=index,
            model_outputs_read=False, review='Manual visual review of frozen question/image/reference sheets',
            manual_notes_sha256=sha(notes_path), structural_manifest_sha256=sha(manifest),
            question=row.get('question'), task_quality=quality)
        sources.append(dict(**common, source_score=source, target=target, alternatives=alternatives,
            reason=reason, independent_semantic_edit=source == 'S4',
            edit_status='Feasibility only; no semantic edit or token-level ROI verified yet', stratum=stratum))
        qualified = any(word in quality for word in ['invalid', 'suspect', 'ambiguous', 'leak', 'missing'])
        readouts.append(dict(**common, readout_score=readout, reason=reason,
            error_oriented_ground_truth_available=readout == 'R4' and not qualified,
            error_orientation_status='Must verify local token/value/binding for each pilot; structural score is feasibility'))
        demands.append(dict(**common, visual_demand=demand,
            reliable_visual_demand=demand.startswith('visual'),
            explicit_source_absence=demand == 'explicit_no_image_text_task',
            paired_modes=modes, image_present_pair_available=True,
            clean_stress_equivalence_review=pair,
            causal_certification_available=False,
            notes=reason + ' Causal certification requires a later valid frozen pilot.'))
        qualities.append(dict(**common, stratum=stratum, notes=reason))
    for filename, records in [('source_identifiability', sources), ('readout_feasibility', readouts),
                              ('visual_demand_feasibility', demands), ('task_quality', qualities)]:
        path = folder / (filename + '.jsonl')
        prior = read_jsonl(path) if path.exists() else []
        own = [r for r in prior if r['benchmark'] == name]
        if own:
            assert own == records, 'Completed audit is immutable: ' + name
        else:
            write_jsonl(path, prior + records)
    s_count = sum(r['source_score'] in {'S3', 'S4'} for r in sources)
    r_count = sum(r['readout_score'] in {'R3', 'R4'} for r in readouts)
    summary = dict(count=64, S3_S4=s_count, R3_R4=r_count,
        source_distribution=dict(Counter(r['source_score'] for r in sources)),
        readout_distribution=dict(Counter(r['readout_score'] for r in readouts)),
        quality_distribution=dict(Counter(r['task_quality'] for r in qualities)),
        reliable_visual_demand=sum(r['reliable_visual_demand'] for r in demands),
        eligible_track_a=name in {'mathvision_wild', 'mathsight', 'charxiv', 'mmlongbench_doc'} and not(s_count / 64 < .2 and r_count / 64 < .2),
        eligible_track_b=name in {'mathsight', 'mmmu_pro', 'microvqa', 'medxpertqa_mm'}, model_outputs_read=False,
        eligibility_scope='Raw S/R feasibility gate only; invalid or ambiguous references do not establish model errors.',
        native_sampling='Frozen prospective order; no replacement after native output.',
        manual_notes_sha256=sha(notes_path))
    path = folder / 'benchmark_structural_summary.json'
    all_summaries = read_json(path)
    if name in all_summaries:
        assert all_summaries[name] == summary
    else:
        all_summaries[name] = summary
        write_json(path, all_summaries)
    print(name, summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('benchmark', choices=['mathvision_wild', 'mathsight', 'charxiv', 'mmmu_pro', 'microvqa', 'medxpertqa_mm', 'mmlongbench_doc'])
    record(parser.parse_args().benchmark)
