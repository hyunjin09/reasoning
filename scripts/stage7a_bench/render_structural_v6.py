"""Export retained structural evidence without revising the historical audit."""
from collections import Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json

OUT = ROOT / 'outputs/stage7a_bench_v2'
ROLES = {'phantom_0': 'No valid source / prior fill',
         'mmmu_pro': 'No valid source / prior fill',
         'charxiv': 'Wrong source / source confusion',
         'mmlongbench_doc': 'Wrong source / source confusion',
         'mathvision_wild': 'Degraded source / extraction'}
COLORS = ['#dce2e8', '#becbd8', '#86abc6', '#417da3', '#164f77']


def main():
    paths = ['cohort/reduced_comparison_inventory_v6.json',
        'structural_audit/benchmark_structural_summary.json',
        'structural_audit/source_identifiability.jsonl',
        'structural_audit/readout_feasibility.jsonl',
        'config/track_a_candidates.json', 'config/track_b_candidates.json',
        'cohort/benchmark_manifests/mmlongbench_doc_image_present_native.jsonl']
    hashes = {str((OUT / p).relative_to(ROOT)): sha(OUT / p) for p in paths}
    amendment = ROOT / 'plan/stage7a_bench_v2_scope_amendment_20260913.md'
    hashes[str(amendment.relative_to(ROOT))] = sha(amendment)
    inventory_packet = read_json(OUT / paths[0])
    original = inventory_packet['original_inventory']
    assert sha(ROOT / original['path']) == original['sha256']
    hashes[original['path']] = original['sha256']
    inventory = {r['candidate_id']: r for r in inventory_packet['candidates']}
    assert set(inventory) == set(ROLES)
    order = list(ROLES)
    names = {n: inventory[n]['canonical_name'] for n in order}
    summary = read_json(OUT / paths[1])
    audited = [n for n in order if n != 'phantom_0']
    assert all(summary[n]['count'] == 64 and summary[n]['model_outputs_read'] is False
               for n in audited)
    distributions = {}
    for prefix, path, field in [('S', paths[2], 'source_score'), ('R', paths[3], 'readout_score')]:
        rows = [r for r in read_jsonl(OUT / path) if r['benchmark'] in audited]
        assert len(rows) == 256 and all(r['model_outputs_read'] is False for r in rows)
        assert len({(r['benchmark'], r['example_id']) for r in rows}) == len(rows)
        distributions[prefix] = {n: Counter(r[field] for r in rows if r['benchmark'] == n)
                                 for n in audited}
        for n, counts in distributions[prefix].items():
            assert sum(counts.values()) == 64 and set(counts) <= {prefix+str(i) for i in range(5)}
            assert counts[prefix+'3'] + counts[prefix+'4'] == summary[n][prefix+'3_'+prefix+'4']
    tracks = {t: read_json(OUT / f'config/track_{t.lower()}_candidates.json') for t in ('A', 'B')}
    docs = read_jsonl(OUT / paths[6])
    document_availability = Counter(r.get('preflight_status', 'ready') for r in docs)
    assert len(docs) == 200 and document_availability['ready'] == 195
    dest = OUT / 'analysis/reduced_structural_v6'
    if dest.exists():
        raise FileExistsError('Preserve existing reduced structural export')
    dest.mkdir(parents=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
        'axes.spines.top': False, 'axes.spines.right': False, 'savefig.facecolor': 'white',
        'svg.fonttype': 'none', 'pdf.fonttype': 42})
    figures = []

    def save(fig, stem, data, scope):
        files = {}
        for extension in ('png', 'pdf', 'svg'):
            p = dest / (stem+'.'+extension)
            fig.savefig(p, dpi=170, bbox_inches='tight')
            files[extension] = dict(path=str(p.relative_to(ROOT)), sha256=sha(p))
        plt.close(fig)
        figures.append(dict(figure=stem, data=data, scope=scope, files=files))

    fig, ax = plt.subplots(figsize=(11.6, 3.7))
    ax.axis('off')
    track_rows = [[names[n], ', '.join(t for t in tracks if n in tracks[t]), ROLES[n]] for n in order]
    table = ax.table(cellText=track_rows, colLabels=['Retained benchmark', 'Original track', 'Amended mechanistic role'],
                     cellLoc='left', colLoc='left', colWidths=[.28, .17, .55], loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.8)
    ax.set_title('Reduced sweep: three distinct failure axes', loc='left', fontweight='bold')
    fig.text(.125, .02, 'Assigned roles, not measured causal states. Original A/B membership and broad artifacts are preserved.', fontsize=9)
    save(fig, '01_retained_mechanistic_roles', dict(order=order, rows=track_rows), 'User-approved roles; no ranking or measured-state claim.')

    availability = []
    for n in order:
        r = inventory[n]
        detail = ('200 text-only questions; no image by design' if n == 'phantom_0' else
                  '1,091 questions / 134 PDFs; frozen screen 195 ready, 5 unavailable' if n == 'mmlongbench_doc' else
                  f"{r['local_row_count']:,} annotation rows; preserved acquisition snapshot")
        availability.append(dict(benchmark=n, display=detail, inventory_status=r['status']))
    fig, ax = plt.subplots(figsize=(11.2, 3.9))
    ax.set(xlim=(0, 1), ylim=(4.6, -.6), xticks=[], yticks=range(5), yticklabels=[names[n] for n in order])
    for i, row in enumerate(availability):
        ax.text(.02, i, row['display'], va='center')
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title('Retained dataset availability', loc='left', fontweight='bold', pad=15)
    fig.text(.125, -.02, 'Availability does not certify reference correctness, native success or source-causal identifiability.\nDocument exclusions retain their frozen preflight reasons in the figure manifest.', fontsize=9)
    save(fig, '02_retained_dataset_availability', dict(rows=availability, document_preflight=document_availability), 'Existing acquisition and frozen input readiness only.')

    keys = ('S3_S4', 'R3_R4', 'reliable_visual_demand')
    matrix = np.array([[summary[n][k] for k in keys] for n in audited])
    fig, ax = plt.subplots(figsize=(9, 4.8))
    plot = ax.imshow(matrix / 64, cmap='Blues', vmin=0, vmax=1, aspect='auto')
    ax.set(yticks=range(4), yticklabels=[names[n] for n in audited],
           xticks=range(3), xticklabels=['S3 / S4', 'R3 / R4', 'Visual demand'])
    ax.xaxis.tick_top()
    for (i, j), value in np.ndenumerate(matrix):
        ax.text(j, i, f'{value}/64', ha='center', va='center', color='white' if value > 42 else '#203648')
    fig.colorbar(plot, ax=ax, label='Fraction of frozen audit', shrink=.8)
    fig.suptitle('Structural feasibility before native generation', fontweight='bold')
    fig.text(.02, -.01, 'Phantom: N/A, no visual source. Prospective structural scores are not observed event eligibility or causal-state yield.', fontsize=9)
    save(fig, '03_retained_structural_feasibility', dict(order=audited, keys=keys, counts=matrix.tolist()), '64 pre-native audit examples per image benchmark.')

    labels = {'S': ['S0 none', 'S1 coarse', 'S2 target', 'S3 target + alternatives', 'S4 independently editable'],
              'R': ['R0 none', 'R1 final only', 'R2 value', 'R3 binding', 'R4 value + binding + error']}
    for number, prefix, title in [(4, 'S', 'Source identifiability'), (5, 'R', 'Readout feasibility')]:
        fig, ax = plt.subplots(figsize=(10.5, 4.4))
        left = np.zeros(4)
        for j in range(5):
            values = np.array([distributions[prefix][n][prefix+str(j)] for n in audited])
            ax.barh(range(4), values, left=left, color=COLORS[j], label=labels[prefix][j])
            for i, value in enumerate(values):
                if value >= 3:
                    ax.text(left[i]+value/2, i, str(value), ha='center', va='center', color='white' if j >= 3 else '#203648')
            left += values
        ax.set(xlim=(0, 64), xticks=[0, 16, 32, 48, 64], yticks=range(4),
               yticklabels=[names[n] for n in audited], xlabel='Frozen pre-native examples (64 each)')
        ax.invert_yaxis()
        ax.set_title(title+' in the retained benchmarks', loc='left', fontweight='bold')
        ax.legend(loc='upper center', bbox_to_anchor=(.5, -.17), ncol=3, frameon=False, fontsize=9)
        save(fig, f'{number:02d}_retained_{prefix}_distribution', dict(order=audited, counts=distributions[prefix]), 'Preserved prospective structural scores; Phantom N/A.')
    assert all(sha(ROOT / p) == digest for p, digest in hashes.items())
    write_json(dest / 'figures.json', dict(status='COMPLETE_RETAINED_STRUCTURAL_FIGURES_ONLY',
        renderer_sha256=sha(ROOT / 'scripts/stage7a_bench/render_structural_v6.py'),
        source_sha256=hashes, figures=figures, native_outputs_read=False, causal_scores_read=False,
        primary_benchmark_selected=False, historical_artifacts_rewritten=False), freeze=True)
    print('RETAINED_STRUCTURAL_FIGURES', len(figures), 'FORMATS', 3)


if __name__ == '__main__':
    main()
