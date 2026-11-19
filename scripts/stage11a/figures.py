"""Export the four specified descriptive figures from the sealed census."""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage11a.common import ROOT,ARMS,load

LABELS=['Direct','Prompted CoT','Native Thinking']
COLORS=['#4c78a8','#f2a541','#54a27a','#b47bb0','#9a9a9a']

def finish(fig,name):
    directory=ROOT/'figures';directory.mkdir(exist_ok=True)
    fig.savefig(directory/(name+'.png'),dpi=180,bbox_inches='tight')
    fig.savefig(directory/(name+'.pdf'),bbox_inches='tight');plt.close(fig)

def main():
    assert os.environ.get('SLURM_JOB_ID')
    data=load(ROOT/'stage11a_primary_inference.json')
    modes=data['matched_probed_subset']['modes'];fine=data['agreement']['fine_proportions_promotable']
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(12,3));ax.axis('off')
    names=['Image','Explicit-probe\nrecoverable E*','Observable native\nevidence E*','Downstream\nreasoning','Answer']
    xs=np.linspace(.06,.94,5)
    for i,(x,name) in enumerate(zip(xs,names)):
        ax.text(x,.67,name,ha='center',va='center',bbox=dict(boxstyle='round,pad=.65',facecolor='#eef2f5',edgecolor='#65768a'),transform=ax.transAxes)
        if i<4:ax.annotate('',xy=(xs[i+1]-.07,.67),xytext=(x+.07,.67),xycoords='axes fraction',arrowprops={'arrowstyle':'->','lw':1.5})
    for x,label in zip([.28,.50,.72],['B1: recovery limitation','B2: native-access limitation','B3: utilization limitation']):
        ax.text(x,.28,label,ha='center',transform=ax.transAxes,color='#9c3d3d')
    ax.text(.5,.03,'Measurement framework; native text and explicit probes do not identify hidden-state encoding or causal mediation.',ha='center',transform=ax.transAxes,fontsize=9)
    finish(fig,'01_bottleneck_model')
    fig,ax=plt.subplots(figsize=(8,4.5));x=np.arange(3);width=.24
    for j,(key,label) in enumerate([('probe_accessible','Explicit probe: all E*'),('native_sufficient','Native text: sufficient E*'),('final_correct','Native final correct')]):
        vals=[modes[a][key]['point'] for a in ARMS]
        err=np.array([[v-modes[a][key]['ci95'][0],modes[a][key]['ci95'][1]-v] for a,v in zip(ARMS,vals)]).T
        ax.bar(x+(j-1)*width,vals,width,label=label,color=COLORS[j],yerr=err,capsize=3)
    ax.set(xticks=x,xticklabels=LABELS,ylim=(0,1.13),ylabel='Fraction of matched probed families',title=f"Evidence and answers on the same {modes['thinking']['n']} families")
    ax.legend(fontsize=8,loc='upper left',ncols=1);ax.text(.01,-.18,'Error bars: 95% family bootstrap intervals (4,000 draws). Exact Stage9A CoT protocol.',transform=ax.transAxes,fontsize=8)
    finish(fig,'02_evidence_by_mode')
    fig,ax=plt.subplots(figsize=(8,4.5));bottom=np.zeros(3)
    profiles=['P1','P2','P3','P4','P5'];names=['Recovery limitation','Native-access limitation','Downstream limitation','Sufficient-evidence success','Mixed / unresolved']
    for j,(p,label) in enumerate(zip(profiles,names)):
        vals=np.array([modes[a]['profiles'].get(p,0)/modes[a]['probe_n'] for a in ARMS]);ax.bar(x,vals,bottom=bottom,label=label,color=COLORS[j]);bottom+=vals
    ax.set(xticks=x,xticklabels=LABELS,ylim=(0,1),ylabel='Fraction of matched probed families',title='Descriptive pipeline profiles'+('' if fine else ' — agreement-limited'))
    ax.legend(bbox_to_anchor=(1.02,1),loc='upper left',fontsize=8)
    ax.text(.01,-.18,'P5 retains overlapping predicates, correct answers without sufficient text evidence, and N5.',transform=ax.transAxes,fontsize=8)
    finish(fig,'03_failure_profiles')
    fig,ax=plt.subplots(figsize=(8,4.6));e=data['E5'];cats=['A','B','C','D'];vals=[e['counts'].get(c,0) for c in cats]
    ax.bar(np.arange(4),vals,color=COLORS[:4]);ax.set(xticks=np.arange(4),xticklabels=['Availability\ngain','Native-access\ngain','Downstream\ngain','Mixed /\nunresolved'],ylabel='Independent families',title=f"Thinking correct / CoT failed: {e['n']} matched families")
    for i,v in enumerate(vals):ax.text(i,v+.15,str(v),ha='center')
    ax.set_ylim(0,max(vals+[1])*1.25+1)
    ax.text(.01,-.20,'Failure = wrong or no valid final; descriptive localization, not a causal explanation.',transform=ax.transAxes,fontsize=8)
    finish(fig,'04_discordant_localization')

if __name__=='__main__':main()
