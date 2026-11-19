"""Plot completed native reports, retaining each reviewed denominator.

Figures6–8 and the screening-candidate component of Figure9. Actual faithful
controls require the separate causal results. Inputs are explicitly hash-bound
completed reports; no incomplete live progress or automatic ranking is used.
"""
import argparse
from copy import deepcopy
import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.stage7a.common import ROOT, read_json, sha, write_json
from scripts.stage7a_bench.native_report_v2 import identity, verify_hashes

OUT = ROOT / 'outputs/stage7a_bench_v2'


def rate_label(metric):
    if metric['value'] is None:
        return f"Unknown; {metric['unknown']} unadjudicated"
    return f"{metric['numerator']}/{metric['denominator']}; {metric['unknown']} unadjudicated"


def report_rows(report):
    if (report.get('status') != 'COMPLETED_BENCHMARK_NATIVE_REPORT_ONLY' or
            report.get('causal_states_assigned') is not False or
            report.get('primary_benchmark_selected') is not False or not report.get('conditions')):
        raise ValueError('Only completed native reports without causal labels or selection may be plotted')
    rows = []
    for condition, record in sorted(report['conditions'].items()):
        native = record['native']
        counts = ('frozen', 'generated', 'unavailable', 'reviewed', 'pending_generation', 'pending_review')
        if (any(type(native.get(k)) is not int or native[k] < 0 for k in counts) or
                native['frozen'] != native['generated']+native['unavailable'] or
                native['generated'] != native['reviewed'] or
                native['pending_generation'] or native['pending_review'] or
                native.get('screen_complete') is not True or
                native.get('benchmark') != report['benchmark'] or native.get('condition') != condition):
            raise ValueError('Incomplete or mismatched report condition')
        metrics = {key:deepcopy(native[field]) for key, field in (
            ('final', 'final_accuracy'), ('local_error', 'local_visual_error_rate'),
            ('unsupported', 'unsupported_claim_rate'), ('f0_candidate', 'faithful_control_candidate_rate'))}
        metrics['binding_error'] = deepcopy(record['dimensions']['binding_error_among_adjudicated_bindings'])
        for metric in metrics.values():
            if (any(type(metric.get(k)) is not int or metric[k] < 0 for k in ('numerator', 'denominator', 'unknown')) or
                    metric['numerator'] > metric['denominator'] or
                    metric['denominator']+metric['unknown'] != native['reviewed']):
                raise ValueError('Invalid reviewed rate counts')
            value = metric.get('value')
            if metric['denominator'] == 0:
                if value is not None:
                    raise ValueError('An unknown rate is not zero')
            elif (type(value) not in (int, float) or not math.isfinite(value) or
                    not math.isclose(value, metric['numerator']/metric['denominator'], abs_tol=1e-12)):
                raise ValueError('Rate disagrees with its denominator')
        rows.append(dict(benchmark=report['benchmark'], condition=condition,
            frozen=native['frozen'], generated=native['generated'], unavailable=native['unavailable'], metrics=metrics))
    return rows


def render(request_path):
    request_path = (ROOT / request_path).resolve()
    if not request_path.is_relative_to(OUT / 'analysis/native_figure_requests'):
        raise ValueError('Use an active native figure request')
    request = read_json(request_path)
    name = identity(request['figure_batch_id'])
    hashes = {str(request_path.relative_to(ROOT)):sha(request_path)}
    rows, seen = [], set()
    for reference in request['reports']:
        path = (ROOT / reference['path']).resolve()
        if not path.is_relative_to(OUT / 'native_screen/reports') or path.name != 'report.json':
            raise ValueError('Use a completed native report in its report directory')
        if sha(path) != reference['sha256']:
            raise ValueError('Native report reference changed')
        report = read_json(path)
        if report['benchmark'] in seen:
            raise ValueError('Duplicate benchmark report')
        seen.add(report['benchmark'])
        verify_hashes(report['artifact_sha256'])
        rows += report_rows(report)
        hashes[str(path.relative_to(ROOT))] = reference['sha256']
        for key, value in report['artifact_sha256'].items():
            if key in hashes and hashes[key] != value:
                raise ValueError('Conflicting report provenance')
            hashes[key] = value
    if not rows:
        raise ValueError('At least one completed report is required')
    dest = (OUT / 'analysis/figures/native_batches' / name).resolve()
    if not dest.is_relative_to(OUT / 'analysis/figures/native_batches'):
        raise ValueError('Figure destination outside active directory')
    if dest.exists():
        raise FileExistsError('Preserve the previous figure batch')
    verify_hashes(hashes)
    dest.mkdir(parents=True)
    plt.rcParams.update({'font.family':'DejaVu Sans', 'svg.fonttype':'none', 'pdf.fonttype':42})
    definitions = [
        (6, 'native_accuracy', 'Final accuracy', [('final', 'Final correctness')]),
        (7, 'native_visual_source_errors', 'Local visual and source-binding errors',
            [('local_error', 'Wrong local claim'), ('binding_error', 'Wrong binding')]),
        (8, 'unsupported_visual_claims', 'Unsupported visual claims', [('unsupported', 'Unsupported claim')]),
        (9, 'native_faithful_candidates', 'Locally correct screening candidates', [('f0_candidate', 'F0 screening class')])]
    figures = []
    labels = [r['benchmark']+' / '+r['condition']+f"\n{r['generated']}/{r['frozen']} generated; {r['unavailable']} unavailable" for r in rows]
    for number, slug, title, series in definitions:
        fig, ax = plt.subplots(figsize=(13, max(3.7, 1.1+len(rows)*.8)))
        for column, (key, label) in enumerate(series):
            offset = (column-(len(series)-1)/2)*.3
            for index, row in enumerate(rows):
                metric = row['metrics'][key]
                y = index+offset
                color = ['#387ea3', '#af6945'][column]
                if metric['value'] is not None:
                    ax.scatter(100*metric['value'], y, color=color, s=45,
                               label=label if index == 0 else None)
                ax.text(105, y, label+': '+rate_label(metric), va='center', fontsize=8.5, color=color)
        ax.set(yticks=range(len(rows)), yticklabels=labels, xlim=(-2, 180),
               xticks=[0,25,50,75,100], xlabel='Percent among adjudicated responses (denominators at right)')
        ax.set_ylim(len(rows)-.55, -.55)
        ax.grid(axis='x', alpha=.18)
        ax.spines[['top','right','left']].set_visible(False)
        ax.spines['bottom'].set_bounds(0, 100)
        ax.tick_params(axis='y', length=0)
        ax.set_title(title, loc='left', pad=18, fontweight='bold')
        caption = 'Only the named completed reports are shown. Unknown judgments and unavailable inputs are retained. No causal labels or ranking.'
        if number == 7:
            caption += '\nLocal-error and binding-error rates have separately adjudicated denominators; they are not restricted to the F1/F2 class label.'
        if number == 9:
            caption += '\nF0 is a native screening candidate. This is only Figure9’s native component; certified faithful-control yield requires the causal pilot.'
        fig.text(.02, .025, caption, fontsize=8.5, color='#516473')
        fig.subplots_adjust(left=.32, right=.98, top=.80, bottom=.25)
        files = {}
        for extension in ('png','pdf','svg'):
            path = dest/f'{number:02d}_{slug}.{extension}'
            fig.savefig(path, dpi=160, bbox_inches='tight')
            files[extension] = dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
        plt.close(fig)
        figures.append(dict(figure_number=number, title=title, files=files, caption=caption,
            scope='Native component only; not causal faithful-control yield' if number == 9 else 'Named completed native reports only'))
    verify_hashes(hashes)
    payload = dict(status='RENDERED_PENDING_VISUAL_REVIEW', figure_batch_id=name, rows=rows, figures=figures,
        source_sha256=hashes, renderer_sha256=sha(ROOT/'scripts/stage7a_bench/render_native_v2.py'),
        complete_sweep_claimed=False, causal_scores_read=False, primary_benchmark_selected=False)
    write_json(dest/'manifest.json', payload)
    return dest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    print(render(parser.parse_args().request))
