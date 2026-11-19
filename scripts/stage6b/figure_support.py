"""Shared rendering for standalone research figures, with linked source evidence."""
import os
import re
from scripts.stage6b.common import OUT,write_json,read_json
os.environ['MPLCONFIGDIR']=str(OUT/'analysis/matplotlib_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

FIG=OUT/'analysis/figures';FIG.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
    'figure.dpi':110,'savefig.dpi':180,'pdf.fonttype':42})
BLUE='#2563a6';ORANGE='#d27628';GREEN='#23866c';GRAY='#89939e';RED='#b74b52'


def save(fig,number,name,title,caption,sources):
    caption=re.sub(r'(?<=\d)(?=[a-z])|(?<=[a-z])(?=\d)|(?<=%)(?=[A-Za-z])',' ',caption)
    stem=f'{number:02d}_{name}'
    fig.suptitle(title,fontsize=12)
    fig.tight_layout(rect=(0,.10,1,.94))
    fig.text(.01,.008,caption,fontsize=7,wrap=True,va='bottom')
    fig.savefig(FIG/(stem+'.png'));fig.savefig(FIG/(stem+'.pdf'));plt.close(fig)
    item={'number':number,'name':name,'title':title,'caption':caption,'png':stem+'.png','pdf':stem+'.pdf','evidence':sources}
    write_json(FIG/(stem+'.json'),item)


def strip(ax,series,labels,ylabel):
    ax.boxplot(series,positions=range(len(series)),widths=.45,showfliers=False)
    for i,values in enumerate(series):
        jitter=np.linspace(-.13,.13,len(values)) if len(values)>1 else [0]
        ax.scatter(i+np.asarray(jitter),values,s=10,alpha=.5,color=BLUE)
    ax.set_xticks(range(len(labels)),labels,rotation=15);ax.set_ylabel(ylabel.replace('_',' '));ax.axhline(0,color=GRAY,lw=.6)


def empty(ax,text):
    ax.axis('off');ax.text(.5,.5,text,ha='center',va='center',wrap=True,fontsize=11,transform=ax.transAxes)


def index():
    items=sorted([read_json(p) for p in FIG.glob('[0-9][0-9]_*.json')],key=lambda r:r['number'])
    lines=['# Stage6B figures','',
        'Standalone PNG and PDF artifacts. Example selection is illustrative after frozen labels; it does not alter any primary cohort or statistical contrast.','']
    for r in items:
        lines += [f"{r['number']}. [{r['title']}]({r['png']}) ([PDF]({r['pdf']})). {r['caption']}",'']
    (FIG/'index.md').write_text('\n'.join(lines)+'\n')
    return items
