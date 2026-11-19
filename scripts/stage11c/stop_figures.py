"""Honest display of unavailable primary endpoints after an early technical stop."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage11c.common import ROOT


def make_figures(gate, split):
    fig,ax=plt.subplots(figsize=(8,4.8))
    arms=['Thinking','Instruct Direct']
    counts=[gate['cap_hits']['thinking'],gate['cap_hits']['instruct_direct']]
    bars=ax.bar(arms, counts, color=['#476c9b','#b27352'],width=.55)
    ax.axhline(4.5,ls='--',color='#8b3030',label='STOP at 5 or more cap hits')
    ax.bar_label(bars,labels=[f'{v}/16' for v in counts],padding=3)
    ax.set(ylim=(0,18),ylabel='Cap hits in 16 matched families',
           title='Figure 2 — Native completion gate failed')
    ax.legend(loc='upper center',bbox_to_anchor=(.5,-.09),frameon=False)
    fig.text(.5,.02,f'32/{2*split["primary_n"]} planned native calls executed; full-cohort performance NOT ESTIMATED.',ha='center',fontsize=10)
    fig.subplots_adjust(bottom=.22)
    _save(fig,'figure2_native_completion_stop')
    for name,title,lines in [
        ('figure3_oracle_not_run','Figure 3 — Equal-Evidence Oracle',
         'NOT RUN\n\nThe prescribed native completion gate failed.\nNo oracle or neutral-control accuracy is available.'),
        ('figure4_localization_not_estimated','Figure 4 — Gap localization',
         'P1 native gap: NOT ESTIMATED\nP2 oracle residual: NOT ESTIMATED\nP3 gap closure: NOT ESTIMATED\n\nNo upstream, downstream or mixed localization claim.')]:
        fig,ax=plt.subplots(figsize=(8,4.5));ax.axis('off')
        ax.set_title(title,fontsize=16,pad=20)
        ax.text(.5,.53,lines,ha='center',va='center',fontsize=14,linespacing=1.65)
        ax.text(.5,.05,'Unexecuted conditions are unknown, never zero.',ha='center',fontsize=10,color='#555555')
        _save(fig,name)


def _save(fig,name):
    for ext in ['png','pdf']:
        path=ROOT/'figures'/f'{name}.{ext}'
        assert not path.exists()
        fig.savefig(path,bbox_inches='tight',dpi=180)
    plt.close(fig)
