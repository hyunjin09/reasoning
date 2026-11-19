"""Illustrate completed certified states without selecting scientific events.

The first native-index event in each requested state is displayed. Pilot
membership, thresholds, assays and state labels are read-only inputs.
"""
import argparse
from pathlib import Path
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.native_report_v2 import identity, verify_hashes
from visual_reasoning.stage7a.reporting import certified

OUT = ROOT / 'outputs/stage7a_bench_v2'


def render(request_path):
    request_path = (ROOT / request_path).resolve()
    if not request_path.is_relative_to(OUT / 'analysis/example_figure_requests'):
        raise ValueError('Use an active example-figure request')
    request = read_json(request_path)
    name = identity(request['figure_batch_id'])
    hashes = {str(request_path.relative_to(ROOT)): sha(request_path)}

    def reference(ref, *, lines=False):
        path = (ROOT / ref['path']).resolve()
        if not path.is_relative_to(OUT) or sha(path) != ref['sha256']:
            raise ValueError('Changed or external example evidence')
        hashes[str(path.relative_to(ROOT))] = ref['sha256']
        return read_jsonl(path) if lines else read_json(path)

    compilation = reference(request['compilation'])
    result = reference(request['pilot_yield'])
    if (compilation.get('status') != 'COMPLETED_FROZEN_PILOT_COMPILED' or
            result.get('status') != 'COMPLETED_PILOT_YIELD_ONLY' or
            result['run_id'] != compilation['run_id'] or
            result['benchmark'] != compilation['benchmark'] or
            result.get('thresholds_retuned') is not False or
            result.get('primary_benchmark_selected') is not False):
        raise ValueError('Verified complete pilot and unchanged yield report required')
    for key, value in result['source_sha256'].items():
        if key in hashes and hashes[key] != value:
            raise ValueError('Conflicting completed-report provenance')
        hashes[key] = value
    verify_hashes(hashes)
    pilot = reference(compilation['pilot'])
    entries = {e['id']: e for e in pilot['selected_entries']}
    states = reference(compilation['outputs']['states'], lines=True)
    metrics = reference(compilation['outputs']['metrics'], lines=True)
    if (len(states) != len(entries) or len(metrics) != len(entries) or
            {r['id'] for r in states} != entries.keys() or
            {r['id'] for r in metrics} != entries.keys()):
        raise ValueError('Every illustrated state must belong to the complete frozen pilot')
    metrics = {r['id']: r for r in metrics}
    selected = []
    for state in ('FAITHFUL_READ', 'WRONG_SOURCE_READ'):
        candidates = [s for s in states if s['state'] == state and certified(s)]
        if not candidates:
            raise ValueError('This paired example figure requires both certified states')
        label = min(candidates, key=lambda s: (s['native_index'], s['id']))
        entry = entries[label['id']]
        footprint = entry['source_annotation']['footprint_figure']
        path = (ROOT / footprint['path']).resolve()
        if (not path.is_relative_to(OUT / 'causal_pilot/source_review_sheets') or
                sha(path) != footprint['sha256']):
            raise ValueError('Source footprint is missing, changed or external')
        hashes[str(path.relative_to(ROOT))] = footprint['sha256']
        selected.append(dict(label=label, entry=entry, metrics=metrics[label['id']],
                             footprint=footprint))
    dest = OUT / 'analysis/figures/example_batches' / name
    if dest.exists():
        raise FileExistsError('Preserve the existing example figure batch')
    fig, axes = plt.subplots(2, 2, figsize=(19, 15), gridspec_kw={'width_ratios': [1.2, 1]})
    fig.subplots_adjust(left=.025, right=.985, top=.93, bottom=.09, hspace=.24, wspace=.06)
    fig.suptitle(f"{result['benchmark']}: faithful and wrong-source read examples", fontsize=21)

    def number(value):
        return 'not measured' if value is None else f'{value:+.4f}'

    for (image_ax, text_ax), case in zip(axes, selected, strict=True):
        entry, label, m = case['entry'], case['label'], case['metrics']
        claim, values = entry['reviewed_claim'], entry['source_annotation']['candidates']
        image_ax.imshow(plt.imread(ROOT / case['footprint']['path']))
        image_ax.set_axis_off()
        image_ax.set_title(f"Native {entry['native_index']:03d} | {label['state']} | Tier {label['tier']}", fontsize=15)
        text_ax.set_axis_off()
        lines = [textwrap.fill('Native excerpt: ' + claim['quote'], 73), '',
                 f"Emitted readout: {claim['readout']} | Independent target: {claim['ground_truth']}",
                 textwrap.fill('T: ' + entry['physical_demanded_source'], 73),
                 textwrap.fill('X: ' + entry['physical_alternative_source'], 73), '',
                 'Source suppression (oriented log-probability effects):']
        for arm in ('T_W2', 'X_W2', 'T_W8', 'X_W8'):
            effect = m['source_effects'].get(arm)
            if effect is None:
                lines.append(arm + ': unavailable')
            elif claim['locally_correct']:
                lines.append(f"{arm}: correct-versus-foil contrast {number(effect['VSD'])}")
            else:
                lines.append(f"{arm}: wrong token {number(effect['EP_token'])}; wrong margin {number(effect['EP_margin'])}")
        lines += ['', 'Semantic controls: shift / matched sham / beyond sham']
        for role, original, edited in [('T', 'correct', 'target_semantic'),
                                       ('X', 'alternative_original', 'alternative_semantic')]:
            s = m['semantic_effects'].get(role)
            if s is None:
                lines.append(role + ': unavailable')
            else:
                lines.append(f"{role} {values[original]} -> {values[edited]}: " + ' / '.join(
                    number(s[k]) for k in ('semantic_shift', 'sham_shift', 'net_semantic_beyond_sham')))
        lines += ['', 'Positive semantic shift follows the edited source.',
                  'A preference shift need not reverse the emitted answer.',
                  'All scores use the fixed native evidence prefix.']
        text_ax.text(0, .98, '\n'.join(lines), transform=text_ax.transAxes,
                     va='top', fontsize=11, linespacing=1.3)
    fig.text(.025, .035, 'Display rule: first native-index event within each certified state; no change to scientific pilot selection.\n'
             'T (red outline) = demanded source; X (blue outline) = preselected alternative. Outlines are review annotations.\n'
             'Matched edits retain the source-review qualifications for typography, texture and context. These two examples do not estimate state prevalence.',
             fontsize=11, color='#42586b')
    verify_hashes(hashes)
    dest.mkdir(parents=True)
    files = {}
    for extension in ('png', 'pdf', 'svg'):
        path = dest / ('23_faithful_wrong_source_examples.' + extension)
        fig.savefig(path, dpi=140)
        files[extension] = dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
    plt.close(fig)
    write_json(dest / 'manifest.json', dict(status='RENDERED_PENDING_VISUAL_REVIEW',
        figure_batch_id=name, figure_number=23, files=files,
        selected_event_ids=[r['entry']['id'] for r in selected],
        selection_rule='Minimum native_index, then ID within each certified state; illustration only',
        source_sha256=hashes, renderer_sha256=sha(Path(__file__)),
        scientific_selection_changed=False, thresholds_retuned=False, primary_benchmark_selected=False))
    return dest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    print(render(parser.parse_args().request))
