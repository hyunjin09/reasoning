"""Publication artifacts for the plan's three conceptual figures; no result claims."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from scripts.stage7a.common import OUT, write_json, sha


COLORS = {'T': '#287d82', 'X': '#b74d43', 'P': '#8062a8', 'none': '#bd8a2f', 'unknown': '#687782'}


def box(ax, x, y, w, h, title, subtitle='', color='#287d82', size=11):
    ax.add_patch(FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle='round,pad=0.008,rounding_size=0.015',
                 facecolor='white', edgecolor=color, linewidth=1.5))
    ax.text(x, y+(h*.17 if subtitle else 0), title, ha='center', va='center', fontsize=size,
            color=color, fontweight='bold')
    if subtitle:
        ax.text(x, y-h*.18, subtitle, ha='center', va='center', fontsize=size-2, color='#27343e', linespacing=1.45)


def arrow(ax, start, end, label=None):
    ax.annotate('', xy=end, xytext=start, arrowprops=dict(arrowstyle='->', color='#687782', lw=1.2))
    if label:
        ax.text((start[0]+end[0])/2, (start[1]+end[1])/2+.025, label, ha='center', fontsize=9, color='#45535d',
                bbox=dict(facecolor='white', edgecolor='none', pad=2))


def canvas(title, size=(11, 6.8)):
    fig, ax = plt.subplots(figsize=size)
    fig.patch.set_facecolor('white')
    ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis('off')
    fig.suptitle(title, x=.06, y=.97, ha='left', fontsize=17, fontweight='bold', color='#20313b')
    fig.text(.06, .035, 'Stage7A study design · Schematic only; empirical support is reported separately.', fontsize=8, color='#63717b')
    fig.subplots_adjust(left=.04, right=.96, top=.89, bottom=.08)
    return fig, ax


def save(fig, stem):
    dest = OUT / 'analysis/figures'
    dest.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ('svg', 'pdf', 'png'):
        path = dest / (stem+'.'+ext)
        fig.savefig(path, dpi=180, facecolor='white')
        paths.append(path)
    plt.close(fig)
    return {str(p.relative_to(OUT)): sha(p) for p in paths}


def main():
    artifacts = {}
    fig, ax = canvas('Demand, source, and emitted evidence')
    box(ax, .5, .83, .43, .17, 'Reasoning demand D', 'Which visual field is required now?')
    box(ax, .23, .37, .36, .19, 'Causal source S', 'T: demanded  ·  X: alternative\nP: previous  ·  no identified source')
    box(ax, .77, .37, .36, .19, 'Emitted evidence E', 'Local value / entity binding\nCorrectness assessed independently')
    arrow(ax, (.42, .735), (.25, .48), 'Demand–source consistency')
    arrow(ax, (.58, .735), (.75, .48), 'Does E satisfy D?')
    arrow(ax, (.415, .37), (.585, .37))
    ax.text(.5, .14, 'Source evidence: W2 suppression + semantic edit + matched render sham\nKeep value, binding, wrong-token, and downstream readouts separate.', ha='center', va='center', fontsize=11, linespacing=1.7)
    artifacts.update(save(fig, '01_demand_source_evidence_triangle'))

    fig, ax = canvas('Six proposed causal grounding states', (12, 8))
    cards = [
        ('Faithful read', 'T supplies locally correct evidence.\nTarget edit controls the readout beyond sham.', 'T'),
        ('Prior fill / unsatisfied retrieval', 'Target unavailable; measured visual support weak.\nMatched availability controls converge.', 'none'),
        ('Wrong-source read', 'X promotes the actual wrong evidence.\nX semantic edit moves it in the expected direction.', 'X'),
        ('Stale-source read', 'After a reviewed demand switch, previous P persists.\nHarmful status requires error-oriented support.', 'P'),
        ('Source-coupled extraction error', 'T causally controls the evidence,\nbut the emitted local content is wrong.', 'T'),
        ('Downstream integration error', 'Correct local evidence is faithfully grounded.\nA separately reviewed later integration step fails.', 'X')]
    for index, (title, subtitle, key) in enumerate(cards):
        box(ax, .25+.5*(index % 2), .82-.30*(index//2), .455, .235, title, subtitle, COLORS[key], 12)
    ax.text(.5, .015, 'Unresolved cases remain unresolved. State labels require convergent causal evidence.', ha='center', fontsize=10, color=COLORS['unknown'])
    artifacts.update(save(fig, '02_six_state_taxonomy'))

    fig, ax = canvas('From reasoning demand to a causal grounding diagnosis', (13, 8))
    box(ax, .5, .89, .5, .13, 'Demanded source T → emitted claim E', 'Review the exact native claim and source identity first')
    box(ax, .5, .67, .58, .12, 'Which source causally supports this claim?', 'Suppression, semantic edits, and controls')
    arrow(ax, (.5, .817), (.5, .74))
    routes = [(.125, 'Demanded T', 'T'), (.375, 'Alternative X', 'X'), (.625, 'Previous P', 'P'), (.875, 'Visual support weak', 'none')]
    for x, title, key in routes:
        arrow(ax, (.5, .6), (x, .48))
        box(ax, x, .425, .23, .09, title, color=COLORS[key], size=11)
    box(ax, .125, .20, .23, .22, 'Local correctness', 'Correct → faithful read\nWrong → extraction error\nFaithful + later integration error', COLORS['T'], 10)
    box(ax, .375, .20, .23, .22, 'Wrong-source read', 'Actual error promoted\nby X + semantic\nfollowability', COLORS['X'], 10)
    box(ax, .625, .20, .23, .22, 'Stale-source read', 'Reviewed demand switch\nP-consistent evidence\nError orientation if harmful', COLORS['P'], 10)
    box(ax, .875, .20, .23, .22, 'Prior-fill candidate', 'Unavailable target\nMatched native and\nfixed-prefix convergence', COLORS['none'], 10)
    for x, _, _ in routes: arrow(ax, (x, .372), (x, .32))
    ax.text(.5, .025, 'Insufficient or contradictory evidence → UNRESOLVED', ha='center', fontsize=11, color=COLORS['unknown'])
    artifacts.update(save(fig, '22_causal_grounding_concept'))
    write_json(OUT / 'analysis/figures/schema_artifacts.json', dict(status='SCHEMATICS_ONLY', artifacts=artifacts))
    print('Three conceptual figure categories rendered as SVG, PDF and PNG; no empirical result claims.')


if __name__ == '__main__':
    main()
