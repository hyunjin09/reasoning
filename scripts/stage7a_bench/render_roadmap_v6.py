"""Render the user-amended workflow without reading experimental results."""
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from scripts.stage7a.common import ROOT, sha, write_json

OUT = ROOT / 'outputs/stage7a_bench_v2'
SOURCES = {
    'plan/stage7a_benchmark_failure_enrichment_plan_v2_mirage_track.md':
        '67b64e75d8c4f25426010e895bdfa966685f459d434ddbfddbd0f5e2ff6e1e75',
    'plan/stage7a_bench_v2_scope_amendment_20260913.md':
        'deea82ef0b6868e4b4918c0c43978800a8ba9a13eed65cf9c6cd626f600a534d',
}


def main():
    for name, digest in SOURCES.items():
        if sha(ROOT / name) != digest:
            raise ValueError('Review the roadmap against its amended authority: '+name)
    dest = OUT / 'analysis/reduced_roadmap_v6'
    if dest.exists():
        raise FileExistsError('Preserve the previous roadmap export')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none',
                         'pdf.fonttype': 42, 'font.size': 10})
    fig, ax = plt.subplots(figsize=(20, 7.5))
    fig.subplots_adjust(left=.01, right=.99, top=.98, bottom=.02)
    ax.set(xlim=(0, 240), ylim=(0, 86))
    ax.axis('off')
    ax.text(1, 81, 'Reduced benchmark sweep: failure → causal diagnosis → user review',
            fontsize=19, weight='bold', color='#243746')
    ax.text(1, 76, 'User-approved scope amendment | Intended benchmark roles, not measured causal states',
            fontsize=11, color='#566774')

    def box(x, y, w, h, title, body, edge='#417da3', fill='#edf4f8', dashed=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
            boxstyle='round,pad=0.3,rounding_size=1', linewidth=1.3,
            edgecolor=edge, facecolor=fill, linestyle='--' if dashed else '-'))
        ax.text(x+w/2, y+h-3.4, title, ha='center', va='center', fontsize=11,
                weight='bold', color=edge)
        ax.text(x+w/2, y+(h-5)/2, body, ha='center', va='center', fontsize=10,
                linespacing=1.6, color='#243746')

    def arrow(start, end):
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>',
            mutation_scale=15, linewidth=1.3, color='#657887'))

    box(1, 55, 42, 17, 'No valid source / prior fill',
        'Phantom-0 + MMMU-Pro', '#926d23', '#faf5e9')
    box(1, 33, 42, 17, 'Wrong source / confusion',
        'CharXiv + MMLongBench-Doc')
    box(1, 11, 42, 17, 'Degraded source / extraction',
        'MathWild', '#597958', '#eef4ed')
    box(53, 23, 40, 37, 'Remaining native sequence',
        'MathWild: fixed 96-review gate\nComplete frozen sample if passed\n↓\nMMMU-Pro → MMLongBench-Doc\nPreserve all negative evidence')
    box(102, 23, 39, 37, 'Eligible causal pilots',
        'Freeze failures + faithful controls\nLocalize demanded / alternate source\nUse oriented error readouts\nSource suppression + semantic edits\nMatched shams where feasible\nKeep strict state definitions')
    box(150, 23, 39, 37, 'Reduced comparison',
        'Failure yield × identifiability\n× readout validity\n× intervention relevance\nRetain faithful controls\nExactly one recommendation\nReturn results to the user')
    box(203, 23, 35, 37, 'Possible future work',
        'Online grounding monitor\n↓\nGrounding-aware decoding\nor rollback\n\nUser selects the next action',
        '#6a7078', '#f6f6f7', dashed=True)
    for y in (63.5, 41.5, 19.5):
        arrow((43.8, y), (52.2, 41.5))
    arrow((93.8, 41.5), (101.2, 41.5))
    arrow((141.8, 41.5), (149.2, 41.5))
    ax.plot([197, 197], [14, 68], color='#a14e57', linestyle='--', linewidth=1.6)
    ax.text(197, 70, 'STOP', ha='center', fontsize=12, color='#a14e57', weight='bold')
    ax.text(197, 10, 'No automatic next experiment', ha='center', fontsize=10, color='#a14e57')
    ax.text(53, 16, 'Phantom and CharXiv remain completed and preserved; neither is rerun.',
            fontsize=10, color='#566774')
    ax.text(1, 4, 'Deferred: MathSight, MicroVQA, MedXpertQA-MM. No additional benchmark, model scale, monitor or decoding experiment in this action.',
            fontsize=10, color='#566774')
    dest.mkdir(parents=True)
    files = {}
    for suffix in ('png', 'pdf', 'svg'):
        path = dest / ('25_reduced_roadmap.'+suffix)
        fig.savefig(path, dpi=160, facecolor='white')
        files[suffix] = dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
    plt.close(fig)
    for name, digest in SOURCES.items():
        if sha(ROOT / name) != digest:
            raise ValueError('Roadmap authority changed during export')
    write_json(dest / 'manifest.json', dict(status='RENDERED_PENDING_VISUAL_REVIEW',
        figure_number=25, files=files, source_sha256=SOURCES,
        renderer=dict(path=str(__file__), sha256=sha(__file__)),
        native_outputs_read=False, causal_scores_read=False,
        primary_benchmark_selected=False, future_work_started=False,
        scope='Amended workflow and stop boundary only; no empirical state or recommendation.'))
    print(dest)


if __name__ == '__main__':
    main()
