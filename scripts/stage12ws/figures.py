"""Five standalone figure pairs with explicit missing and gated panels."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage12ws.common import ROOT,load
OUT=Path('reports/stage12ws/v1/figures')

def bars(ax,conditions,names):
    names=[n for n in names if n in conditions]
    if not names:ax.text(.5,.5,'NOT RUN — phase gate',ha='center',va='center',transform=ax.transAxes);return
    vals=[conditions[n]['correct']/7 for n in names];upper=[conditions[n]['missing']/7 for n in names]
    ax.bar(range(len(names)),vals,color='#347d9e')
    ax.errorbar(range(len(names)),vals,yerr=[[0]*len(names),upper],fmt='none',color='#ad5b34',capsize=3)
    ax.set_xticks(range(len(names)),names,rotation=55,ha='right',fontsize=8);ax.set_ylim(0,1.16);ax.set_ylabel('Correct / 7')
    for i,n in enumerate(names):
        r=conditions[n];ax.text(i,vals[i]+.03,f"{r['correct']}/7"+(f" +{r['missing']}?" if r['missing'] else ''),ha='center',fontsize=8)

def finish(fig,name):
    fig.tight_layout();fig.savefig(OUT/(name+'.png'),dpi=170);fig.savefig(OUT/(name+'.pdf'));plt.close(fig)

def main():
    OUT.mkdir(parents=True,exist_ok=True);d=load(ROOT/'stage12ws_primary_inference.json')
    for name,title,select in [
       ('W1_portability','Full-state and single-block deletion landscape',lambda r:['FULL','Q']+list(r['block_effects'])),
       ('W2_derived','Raw evidence and derived-state constructions',lambda r:['ESTAR','ESTAR_D','FULL','MINUS_D']),
       ('W5_order','One frozen block-order perturbation',lambda r:['FULL','ORDER'])]:
        fig,axs=plt.subplots(2,2,figsize=(12,8));fig.suptitle(title)
        for ax,r in zip(axs.flat,d['families']):
            bars(ax,r['conditions'],select(r));ax.set_title(f"Family {r['item_id']} — "+('A eligible' if r['eligible'] else 'A ineligible/unresolved'))
        finish(fig,name)
    fig,axs=plt.subplots(2,2,figsize=(12,8));fig.suptitle('Single-block paired effects and candidate retained sets')
    for ax,r in zip(axs.flat,d['families']):
        e=r['block_effects'];ax.set_title('Family '+r['item_id'])
        if not e:ax.text(.5,.5,'NOT RUN — family gate',ha='center',transform=ax.transAxes);continue
        names=list(e);lo=[e[n]['net_bounds'][0]/7 for n in names];hi=[e[n]['net_bounds'][1]/7 for n in names]
        mid=[(a+b)/2 for a,b in zip(lo,hi)]
        ax.bar(range(len(names)),mid,color='#347d9e');ax.errorbar(range(len(names)),mid,yerr=[[m-a for m,a in zip(mid,lo)],[b-m for b,m in zip(hi,mid)]],fmt='none',color='black',capsize=3)
        ax.axhline(0,color='gray');ax.axhline(4/7,color='#ad5b34',ls='--',lw=1);ax.set_ylim(-1,1)
        ax.set_xticks(range(len(names)),names,rotation=45,ha='right',fontsize=8);ax.set_ylabel('FULL minus deletion')
        g=r.get('greedy',{});ax.set_xlabel('D: '+g.get('status','not run')+'; retained '+str(g.get('candidate_retained','—')))
    finish(fig,'W3_distributed')
    fig,ax=plt.subplots(figsize=(11,5));n=d['interference_repair'];ax.set_title('Family750: paired prefix interference / repair')
    if n:
        c={**{k:n[k] for k in ['Pa','Pb','Pc']},**{k:n[v] for k,v in n['aliases'].items()}}
        bars(ax,c,['Pa','Pb','Pc','F1','F2','F3','F4']);ax.set_xlabel('Pa299, Pb448, Pc598; F1=Pa, F2=F4=Pb, F3=Pc. Three unique inputs.')
    else:ax.text(.5,.5,'NOT RUN — phase gate',ha='center',transform=ax.transAxes)
    finish(fig,'W4_interference_repair')

if __name__=='__main__':main()
