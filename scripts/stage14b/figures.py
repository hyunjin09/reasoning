"""Five required Stage14B figures from sealed analyses only."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scripts.stage14b.common import *
from scripts.stage14b.protocol import VERSIONS


def main():
    for name in ('primary','secondary','confirmation'):assert (ROOT/'audit'/f'{name}_analysis_seal.json').exists()
    p=load(ROOT/'analysis/primary_results.json');c=load(ROOT/'analysis/confirmatory_results.json')
    dest=ROOT/'figures';dest.mkdir(exist_ok=True)
    def savefig(fig,name):
        fig.tight_layout();fig.savefig(dest/(name+'.png'),dpi=220);fig.savefig(dest/(name+'.pdf'));plt.close(fig)
    for key,name,title in [('P1_G_img','figure1_mathvision_native_gain','MATH-Vision: all 3,040 native problems'),('P3_G_post','figure3_post_evidence_gain','MATH-Vision: frozen E* 1,000')]:
        r=p[key];fig,axes=plt.subplots(1,2,figsize=(9,3.5))
        values=[r[m]['resolved_accuracy'] for m in 'IT'];axes[0].bar(['Instruct','Thinking'],[v*100 if v is not None else np.nan for v in values],color=['#457b9d','#e76f51'])
        for i,m in enumerate('IT'):
            ci_m=r['marginal_accuracy_clusters'][m]['ci95_pp']
            if ci_m:axes[0].plot([i,i],ci_m,color='black',lw=1.5)
        axes[0].set_ylabel('Resolved-answer accuracy (%)');axes[0].set_ylim(0,100)
        est=r['cluster']['estimate_pp'];ci=r['cluster']['ci95_pp']
        if est is not None:
            axes[1].plot(ci,[0,0],color='#333333');axes[1].plot([est],[0],'o',color='#333333')
        axes[1].axvline(0,color='gray',ls='--');axes[1].set_yticks([]);axes[1].set_xlabel('Paired Thinking − Instruct (pp)\n95% known-family cluster interval')
        fig.suptitle(title);savefig(fig,name)
    r=p['P2_R_I'];labels=['Stable correct','Regression','Rescue','Persistent wrong','Unresolved pair']
    tr=r['transitions'];vals=[tr['correct__correct'],tr['correct__wrong'],tr['wrong__correct'],tr['wrong__wrong'],sum(v for k,v in tr.items() if 'unresolved' in k)]
    fig,ax=plt.subplots(figsize=(8,3.6));ax.bar(labels,vals,color=['#457b9d','#e9c46a','#2a9d8f','#e76f51','#aaaaaa']);ax.set_ylabel('Frozen E* families');ax.set_title('Instruct: native image → equal evidence');ax.tick_params(axis='x',rotation=15);savefig(fig,'figure2_evidence_rescue')
    fig,ax=plt.subplots(figsize=(8,4));profile=p['P4_mathverse']['versions']
    for i,v in enumerate(VERSIONS):
        r=profile[v]['cluster'];est=r['estimate_pp'];ci=r['ci95_pp']
        if est is not None:ax.plot([i,i],ci,color='#264653');ax.plot([i],[est],'o',color='#264653')
    ax.set_xticks(range(6),['TD','TL','TO','VI','VD','VO']);ax.axhline(0,color='gray',ls='--');ax.set_ylabel('Thinking − Instruct (pp)');ax.set_title('MathVerse: 788 native families\nFamily-paired 95% intervals; source defects retained');savefig(fig,'figure4_mathverse_modality_profile')
    fig,ax=plt.subplots(figsize=(8,4))
    for name in ('G_img','G_post','MathVerse_profile'):
        ax.plot(range(3),c['stability'][name]['values_pp'],marker='o',label=name)
    ax.axhline(0,color='gray',ls='--');ax.set_xticks(range(3),['Main seed0','Seed1','Seed2']);ax.set_ylabel('Paired effect (pp)');ax.set_title('Frozen confirm-300 + 300: seed robustness');ax.legend();savefig(fig,'figure5_confirmatory_stability')
    save(ROOT/'audit/figure_manifest.json',dict(at=now(),files={str(p):sha(p) for p in dest.iterdir() if p.suffix in ('.png','.pdf')}))

if __name__=='__main__':main()
