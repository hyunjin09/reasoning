"""Render the five completed structural figures from auditable, frozen counts.

This report reads no native outputs or causal scores and makes no winner claim.
"""
from collections import Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json

OUT = ROOT / 'outputs/stage7a_bench_v2'
FIG = OUT / 'analysis/figures'
ORDER = ['mathvision_wild', 'mmlongbench_doc', 'charxiv', 'mathsight',
         'mmmu_pro', 'mmmu_pro_bclean', 'phantom_0', 'microvqa',
         'medxpertqa_mm', 'vqa_rad', 'rexvqa']
COLORS = ['#dce2e8', '#becbd8', '#86abc6', '#417da3', '#164f77']


def main():
    sources = ['cohort/dataset_inventory.json', 'structural_audit/benchmark_structural_summary.json',
        'structural_audit/source_identifiability.jsonl', 'structural_audit/readout_feasibility.jsonl',
        'config/track_a_candidates.json', 'config/track_b_candidates.json']
    inventory = {r['candidate_id']: r for r in read_json(OUT / sources[0])['candidates']}
    summary = read_json(OUT / sources[1])
    audited = [name for name in ORDER if name in summary]
    assert len(audited) == 8 and all(summary[n]['count'] == 64 and not summary[n]['model_outputs_read'] for n in audited)
    names = {k: v['canonical_name'].replace(' B-Clean-style subset', ' B-Clean subset') for k, v in inventory.items()}
    distributions = {}
    for prefix, path, field in [('S', sources[2], 'source_score'), ('R', sources[3], 'readout_score')]:
        rows = read_jsonl(OUT / path)
        assert len(rows) == 512 and all(not r['model_outputs_read'] for r in rows)
        assert len({(r['benchmark'], r['example_id']) for r in rows}) == len(rows)
        distributions[prefix] = {n: Counter(str(r[field]) for r in rows if r['benchmark'] == n) for n in audited}
        for name, counts in distributions[prefix].items():
            assert sum(counts.values()) == 64 and set(counts) <= {prefix+str(i) for i in range(5)}
            assert counts[prefix+'3'] + counts[prefix+'4'] == summary[name][prefix+'3_'+prefix+'4']
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
        'axes.spines.top': False, 'axes.spines.right': False,
        'savefig.facecolor': 'white', 'svg.fonttype': 'none', 'pdf.fonttype': 42})
    records = []

    def save(fig, stem, data, scope):
        paths = {}
        for extension in ('png', 'pdf', 'svg'):
            path = FIG / (stem + '.' + extension)
            fig.savefig(path, dpi=170, bbox_inches='tight')
            paths[extension] = dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
        plt.close(fig)
        records.append(dict(figure=stem, data=data, scope=scope, files=paths))

    tracks = {t: read_json(OUT / f'config/track_{t.lower()}_candidates.json') for t in ('A', 'B')}
    values = np.array([[int(n in tracks[t]) for t in ('A', 'B')] for n in ORDER])
    fig, ax = plt.subplots(figsize=(7.8, 5.7))
    ax.imshow(values, cmap=matplotlib.colors.ListedColormap(['#f0f3f6', '#417da3']), vmin=0, vmax=1, aspect='auto')
    ax.set(yticks=range(len(ORDER)), yticklabels=[names[n] for n in ORDER],
           xticks=[0, 1], xticklabels=['A: source confusion', 'B: mirage / prior'])
    ax.xaxis.tick_top()
    for i in range(len(ORDER)):
        for j in range(2):
            ax.text(j, i, 'Included' if values[i, j] else '—', ha='center', va='center',
                    color='white' if values[i, j] else '#617181')
    fig.suptitle('Approved benchmark tracks', y=1.02, fontweight='bold')
    fig.text(.02, -.035, 'B-Clean is a protocol-derived subset of MMMU-Pro, not an additional base dataset.', fontsize=9)
    save(fig, '01_benchmark_track_map', dict(order=ORDER, tracks=tracks), 'Approved candidate roles; no performance ranking.')

    availability = []
    for n in ORDER:
        row = inventory[n]
        if n == 'mmmu_pro_bclean': status, color = 'Protocol available; labels require local derivation', '#c99432'
        elif row['status'] == 'ACCESS_GATED': status, color = 'Anonymous access gated', '#a14e57'
        elif row['status'] == 'TRANSFER_BLOCKED_HTTP_404_429': status, color = 'Transfer blocked: HTTP 404 / 429', '#a14e57'
        elif row['status'] == 'PARTIAL_ONE_QUARANTINED_PDF': status, color = 'Partial: 134 valid PDFs; one quarantined', '#c99432'
        elif n == 'phantom_0': status, color = '200 text-only questions; no images by design', '#417da3'
        else: status, color = f"Available: {row['local_row_count']:,} annotation rows", '#417da3'
        availability.append(dict(benchmark=n, display=status, status=row['status'], color=color))
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.set(xlim=(0, 1), ylim=(len(ORDER)-.5, -.5), xticks=[], yticks=range(len(ORDER)), yticklabels=[names[n] for n in ORDER])
    for i, r in enumerate(availability):
        ax.scatter(.025, i, s=90, color=r['color'])
        ax.text(.065, i, r['display'], va='center')
    ax.set_title('Dataset availability on this server', loc='left', pad=16, fontweight='bold')
    for spine in ax.spines.values(): spine.set_visible(False)
    fig.text(.02, -.02, 'Availability records are distinct from task/reference validity. Existing immutable acquisition snapshot retained.', fontsize=9)
    save(fig, '02_server_dataset_availability', availability, 'Local acquisition status; raw rows are not all valid tasks.')

    matrix = np.array([[summary[n][k] / 64 for k in ('S3_S4', 'R3_R4', 'reliable_visual_demand')] for n in audited])
    fig, ax = plt.subplots(figsize=(8.8, 5.3))
    plot = ax.imshow(matrix, cmap='Blues', vmin=0, vmax=1, aspect='auto')
    ax.set(yticks=range(len(audited)), yticklabels=[names[n] for n in audited],
           xticks=range(3), xticklabels=['S3 / S4', 'R3 / R4', 'Visual demand'])
    ax.xaxis.tick_top()
    for i in range(len(audited)):
        for j in range(3):
            ax.text(j, i, f'{round(matrix[i,j]*64)}/64\n{matrix[i,j]:.0%}', ha='center', va='center', color='white' if matrix[i,j] > .65 else '#203648')
    fig.colorbar(plot, ax=ax, label='Fraction of frozen audit', shrink=.8)
    fig.suptitle('Structural feasibility before model generation', y=1.02, fontweight='bold')
    fig.text(.015, -.035, 'S3/S4: target + alternatives localizable/editable. R3/R4: binding readout feasible.\nRaw feasibility does not certify source edits, reference correctness, or a causal state.', fontsize=9)
    save(fig, '03_structural_identifiability_matrix', dict(order=audited, counts={n:{k:summary[n][k] for k in ('S3_S4','R3_R4','reliable_visual_demand')} for n in audited}), '64 output-blind examples per accessible base dataset; feasibility only.')

    definitions = {
        'S': ['S0: none', 'S1: coarse', 'S2: target', 'S3: target + alternatives', 'S4: independently editable'],
        'R': ['R0: none', 'R1: final only', 'R2: value', 'R3: binding', 'R4: value + binding + error']}
    for number, prefix, title in [(4, 'S', 'Source-identifiability distribution'), (5, 'R', 'Readout-feasibility distribution')]:
        fig, ax = plt.subplots(figsize=(10.5, 5.5))
        left = np.zeros(len(audited))
        for j in range(5):
            count = np.array([distributions[prefix][n][prefix+str(j)] for n in audited])
            ax.barh(range(len(audited)), count, left=left, height=.65, color=COLORS[j], label=definitions[prefix][j])
            for i, value in enumerate(count):
                if value >= 3: ax.text(left[i]+value/2, i, str(value), ha='center', va='center', color='white' if j >= 3 else '#203648', fontsize=9)
            left += count
        ax.set(xlim=(0,64), xticks=[0,16,32,48,64], yticks=range(len(audited)), yticklabels=[names[n] for n in audited], xlabel='Examples in frozen structural audit (n = 64 each)')
        ax.invert_yaxis()
        ax.set_title(title, loc='left', pad=15, fontweight='bold')
        ax.legend(loc='upper center', bbox_to_anchor=(.5,-.16), ncol=3, frameon=False, fontsize=9)
        save(fig, f'{number:02d}_{"source_identifiability" if prefix == "S" else "readout_feasibility"}_distribution',
             dict(order=audited, counts=distributions[prefix]), 'Prospective structural feasibility; not observed causal-state yield.')
    write_json(OUT / 'analysis/structural_figures.json', dict(status='COMPLETE_STRUCTURAL_FIGURES_ONLY',
        renderer_sha256=sha(ROOT / 'scripts/stage7a_bench/render_structural_v2.py'),
        source_sha256={p:sha(OUT/p) for p in sources}, figures=records, native_outputs_read=False,
        causal_scores_read=False, primary_benchmark_selected=False))
    print('STRUCTURAL_FIGURES', len(records), 'formats', 3, 'audited', len(audited)*64)


if __name__ == '__main__':
    main()
