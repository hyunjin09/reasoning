"""Outcome-independent, exportable causal-design figure."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage11b.common import ROOT

fig,ax=plt.subplots(figsize=(10,4.5));ax.set(xlim=(0,10),ylim=(0,4.5));ax.axis('off')
def box(x,y,text,color):
    ax.text(x,y,text,ha='center',va='center',fontsize=12,
        bbox=dict(boxstyle='round,pad=.65',fc=color,ec='#455468',lw=1.1))
def arrow(a,b,color='#455468'):
    ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',lw=1.7,color=color))
box(1.2,3.2,'Image + question','#e6edf7')
box(4.5,3.2,'Acquire / access\nvisual evidence','#e6edf7')
box(8.1,3.2,'Downstream reasoning\nThinking or CoT','#e6edf7')
arrow((2.45,3.2),(3.2,3.2));arrow((5.85,3.2),(6.5,3.2))
box(4.5,1.55,'Identical correct E*\n1–4 frozen visual facts','#e0f1e6')
box(8.1,1.55,'Same original question\nThinking or CoT','#e0f1e6')
arrow((5.85,1.55),(6.5,1.55),'#286348')
ax.text(1.1,1.55,'Oracle:\nimage removed',ha='center',va='center',fontsize=12,color='#286348')
ax.text(5,.25,'Primary localization: native Thinking–CoT gap minus oracle Thinking–CoT gap',
    ha='center',fontsize=11,color='#223145')
ax.set_title('Stage11B: equal evidence separates upstream access from downstream reasoning',fontsize=13,pad=16)
dest=ROOT/'figures';dest.mkdir(parents=True,exist_ok=True)
for suffix in ['png','pdf']:
    target=dest/f'figure1_causal_design.{suffix}'
    assert not target.exists()
    fig.savefig(target,dpi=180,bbox_inches='tight')
plt.close(fig)
