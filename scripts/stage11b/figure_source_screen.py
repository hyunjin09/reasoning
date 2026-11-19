"""Source-only discovery panel, frozen independently of native outcomes."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage11b.common import ROOT, load

data = load(ROOT/'audit/source_only_necessary_gate.json')['strata']
labels = ['Levels 3–5, all', 'Levels 4–5, all', 'Levels 3–4, all',
          'Levels 3–5, geometry', 'Levels 3–5, other', 'Levels 4–5, geometry']
fig, ax = plt.subplots(figsize=(10, 5.2))
values = [100*r['eligibility_rate'] for r in data]
colors = ['#2a7f62' if r['possible'] else '#9ba8b8' for r in data]
ax.barh(labels, values, color=colors, height=.62)
for i, (r, value) in enumerate(zip(data, values)):
    ax.text(value+.55, i, f"{r['eligible']}/{r['n']} ({value:.1f}%)", va='center', fontsize=10)
ax.axvline(40, ls='--', color='#963c37', lw=1.4, label='Required eligibility ≥40%')
ax.set_xlim(0, 55)
ax.invert_yaxis()
ax.set_xlabel('Families with sufficient, minimal, nonleaking visual evidence (%)')
ax.set_title('Stage11B discovery: source eligibility across six frozen strata', loc='left', pad=14)
ax.spines[['top', 'right']].set_visible(False)
ax.legend(loc='lower right', frameon=False)
fig.text(.02, .015,
    '128 independent families; two semantic reviews plus one bounded repair pass.\n'
    'Green indicates source feasibility only. Native accuracy and discordance gates remain required.', fontsize=9)
fig.tight_layout(rect=[0, .09, 1, 1])
for suffix in ['png', 'pdf']:
    p = ROOT/'figures'/f'figure2a_source_eligibility.{suffix}'
    assert not p.exists()
    fig.savefig(p, dpi=180, bbox_inches='tight')
plt.close(fig)
