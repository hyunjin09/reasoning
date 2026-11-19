"""Outcome-independent design panel for the approved Stage11C study."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from scripts.stage11c.common import ROOT


def main():
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set(xlim=(0, 11), ylim=(0, 5))
    ax.axis('off')

    def box(x, y, w, h, text, color):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.06',
                                   facecolor=color, edgecolor='#435466', linewidth=1.2))
        ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=11)

    def arrow(start, end):
        ax.annotate('', xy=end, xytext=start, arrowprops=dict(arrowstyle='->', color='#435466', lw=1.5))

    ax.text(.15, 4.75, 'Stage 11C: Thinking versus Instruct lifecycle localization', fontsize=16, weight='bold')
    box(.2, 3.05, 2.3, .95, 'Image + question', '#e8edf3')
    box(3.3, 3.05, 3.0, .95, 'Native Thinking\nNative Instruct Direct', '#dce9f6')
    box(7.0, 3.05, 3.5, .95, 'Native gap P1\nRequired gate before oracle', '#e9eef5')
    arrow((2.55, 3.53), (3.24, 3.53)); arrow((6.36, 3.53), (6.94, 3.53))
    box(.2, 1.3, 2.3, 1.05, 'Same correct E*\n+ original question\nNo image or cache', '#e1f0e6')
    box(3.3, 1.3, 3.0, 1.05, 'Oracle Thinking\nOracle Instruct Direct', '#e1f0e6')
    box(7.0, 1.3, 3.5, 1.05, 'Residual gap P2\nGap closure P3 = P1 − P2', '#e9eef5')
    arrow((2.55, 1.83), (3.24, 1.83)); arrow((6.36, 1.83), (6.94, 1.83))
    ax.text(.2, .75, 'Fresh source families • 1–4 visual facts, reviewed twice • batch size 1 • one calibrated generation cap', fontsize=10)
    ax.text(.2, .35, 'Secondary: 24-family neutral text; conditional 48-family Instruct CoT. Distinct checkpoints: operational localization.', fontsize=10)
    path = ROOT/'figures'
    path.mkdir(exist_ok=True)
    for suffix in ['pdf', 'png']:
        dest = path/f'figure1_design.{suffix}'
        fig.savefig(dest, bbox_inches='tight', dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
