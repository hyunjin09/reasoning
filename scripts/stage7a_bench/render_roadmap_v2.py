"""Export the approved workflow diagram; no experiment results are consumed."""
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from scripts.stage7a.common import ROOT, sha, write_json

OUT = ROOT / 'outputs/stage7a_bench_v2'
PLAN = ROOT / 'plan/stage7a_benchmark_failure_enrichment_plan_v2_mirage_track.md'


def main():
    if sha(PLAN) != '67b64e75d8c4f25426010e895bdfa966685f459d434ddbfddbd0f5e2ff6e1e75':
        raise ValueError('Review the roadmap against the modified approved plan')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none',
                         'pdf.fonttype': 42, 'font.size': 10})
    fig, ax = plt.subplots(figsize=(15, 5.8))
    fig.subplots_adjust(left=.02, right=.99, top=.98, bottom=.02)
    ax.set(xlim=(0, 145), ylim=(0, 56))
    ax.axis('off')
    ax.text(1, 52, 'From benchmark failures to causal grounding',
            fontsize=18, weight='bold', color='#243746')
    ax.text(1, 48, 'Stage 7A-Bench v2  |  Approved workflow; no empirical results shown',
            fontsize=11, color='#566774')

    def box(x, y, w, h, title, body, edge, fill, dashed=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
            boxstyle='round,pad=0.25,rounding_size=0.8', linewidth=1.3,
            edgecolor=edge, facecolor=fill, linestyle='--' if dashed else '-'))
        ax.text(x+w/2, y+h-2.4, title, ha='center', va='center',
                fontsize=12, weight='bold', color=edge)
        ax.text(x+w/2, y+(h-3.2)/2, body, ha='center', va='center',
                fontsize=10, linespacing=1.55, color='#243746')

    def arrow(start, end):
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle='-|>',
            mutation_scale=14, linewidth=1.4, color='#657887',
            connectionstyle='arc3,rad=0'))

    box(1, 27, 29, 15, 'Track A: source confusion',
        'Screen native visual reads\nLocalize target and alternatives\nKeep value and binding errors separate',
        '#417da3', '#edf4f8')
    box(1, 8, 29, 15, 'Track B: mirage / prior',
        'Establish visual demand\nCompare supported evidence conditions\nKeep behavioral claims separate',
        '#926d23', '#faf5e9')
    box(38, 18, 35, 23, 'Causal pilot',
        'Freeze eligible failures and controls\nW2: all layers and heads\nW8: target and primary alternative\nSemantic edits + matched shams, if feasible\nTest support for the wrong emitted claim',
        '#417da3', '#edf4f8')
    box(82, 18, 32, 23, 'Benchmark decision',
        'Rank the two tracks separately\nCompare causal yield, identifiability,\ncontrols, diversity and cost\nChoose one primary family\nand one recommendation',
        '#417da3', '#edf4f8')
    box(123, 18, 21, 23, 'Future work',
        'Model-scale study\nMonitor development\nIntervention testing',
        '#6a7078', '#f6f6f7', dashed=True)
    arrow((30.5, 34.5), (37.5, 33))
    arrow((30.5, 15.5), (37.5, 24))
    arrow((73.5, 29.5), (81.5, 29.5))
    arrow((114.5, 29.5), (122.5, 29.5))
    ax.plot([118.5, 118.5], [8, 43], color='#a14e57', linestyle='--', linewidth=1.2)
    ax.text(118.5, 44.3, 'Stage stops here', ha='center', fontsize=10,
            color='#a14e57', weight='bold')
    ax.text(133.5, 12, 'Requires a subsequent\napproved stage', ha='center',
            va='center', fontsize=10, color='#6a7078', linespacing=1.4)
    ax.text(38, 11.7, 'Primary-family target at feasible scale: ≥24 strong unfaithful events + ≥24 faithful controls.',
            fontsize=9.5, color='#243746')
    ax.text(38, 8.6, 'Preserve unavailable controls and unresolved states. Keep state definitions fixed.',
            fontsize=9.5, color='#566774')
    ax.text(1, 2.5, 'Image/no-image agreement alone is not a causal label. Monitoring and decoding interventions do not run in this stage.',
            fontsize=10, color='#566774')
    directory = OUT / 'analysis/figures'
    directory.mkdir(parents=True, exist_ok=True)
    files = {}
    for suffix in ('png', 'pdf', 'svg'):
        path = directory / ('25_roadmap_to_monitor_intervention.'+suffix)
        fig.savefig(path, dpi=160, facecolor='white')
        files[suffix] = dict(path=str(path.relative_to(ROOT)), sha256=sha(path))
    plt.close(fig)
    write_json(OUT / 'analysis/roadmap_figure.json', dict(
        status='RENDERED_PENDING_VISUAL_REVIEW', figure_number=25,
        figure='roadmap_to_monitor_intervention',
        source_plan=dict(path=str(PLAN.relative_to(ROOT)), sha256=sha(PLAN)),
        renderer=dict(path=str(__file__), sha256=sha(__file__)), files=files,
        scope='Approved stage architecture and subsequent-work boundary, not empirical findings, a selected benchmark or authorization to start future work.',
        native_outputs_read=False, causal_scores_read=False,
        primary_benchmark_selected=False, future_work_started=False))
    print('Rendered approved roadmap as PNG, PDF and SVG; visual review pending.')


if __name__ == '__main__':
    main()
