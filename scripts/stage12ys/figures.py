"""Five standalone figure pairs, with absent/unknown assays explicit."""
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path('runs/stage12ys/v1/cache/matplotlib').resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scripts.stage12ys.execution import ROOT,load

def make():
    out=ROOT/'figures';out.mkdir(exist_ok=True)
    d=load(ROOT/'stage12ys_primary_inference.json');a=d['phaseA'];b=d['phaseB'];c=d['phaseC']
    def save(fig,name):
        fig.tight_layout()
        for ext in ['png','pdf']:fig.savefig(out/f'{name}.{ext}',dpi=180,bbox_inches='tight')
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,3));ax.axis('off')
    for x,text in zip([.1,.36,.65,.9],['IMAGE','Task-critical\nevidence E*','Derived\nreasoning state','ANSWER']):
        ax.text(x,.6,text,ha='center',va='center',bbox=dict(boxstyle='round,pad=.55',fc='#e7f1f6',ec='#234b66'))
    for x,y,label in [(.17,.29,'A: evidence recovery'),(.45,.57,'B/C: equal-evidence\nreasoning/state construction'),(.74,.84,'Downstream use')]:
        ax.annotate('',xy=(y,.6),xytext=(x,.6),arrowprops=dict(arrowstyle='->'));ax.text((x+y)/2,.22,label,ha='center',va='center',fontsize=9)
    ax.set_title('Stage12Y-S: prospective functional decomposition');save(fig,'Y1_role_decomposition')
    fig,axes=plt.subplots(1,2,figsize=(9,3.7))
    for k,(name,label) in enumerate([('G_img','Native image'),('G_E','Equal evidence')]):
        r=a[name];est=r['estimate'];ci=r['bootstrap95']
        if est is not None:axes[0].bar(k,est,color=['#39729a','#d98a31'][k]);axes[0].errorbar(k,est,yerr=[[est-ci[0]],[ci[1]-est]],fmt='none',color='black',capsize=4)
        axes[0].text(k,(est or 0)+.03,f'n={r["n"]}',ha='center')
    axes[0].set_xticks([0,1],['Native image','Equal evidence']);axes[0].axhline(0,color='gray',lw=1);axes[0].set_ylabel('Thinking − Instruct accuracy');axes[0].set_title('Paired screen gaps (95% family bootstrap)')
    r=a['G_access'];vals=[r['I_correct']/r['n'],r['T_correct']/r['n']] if r['n'] else [0,0]
    axes[1].bar(['E_I','E_T'],vals,color=['#39729a','#d98a31']);axes[1].set_ylim(0,1);axes[1].set_title(f'All-atom evidence recovery; common n={r["n"]}');axes[1].set_ylabel('Fraction correct')
    fig.suptitle('Descriptive single-run screen; fresh confirmation required',fontsize=10);save(fig,'Y2_native_equal_evidence_gap')
    fig,ax=plt.subplots(figsize=(7,4));keys=['A_COLLAPSE','B_PERSIST','C_BOTH_FAIL','D_UNRESOLVED'];counts=[a['native_thinking_only_transitions'].get(k,0) for k in keys]
    bars=ax.bar(['Collapses with E*','Persists with E*','Both fail with E*','Unresolved'],counts,color=['#5d9c78','#d98a31','#798ba0','#b0b0b0']);ax.bar_label(bars);ax.set_ylabel('Independent families');ax.set_title('Native Instruct− / Thinking+ screen decomposition');save(fig,'Y3_native_thinking_only')
    fig,ax=plt.subplots(figsize=(9,max(3,len(b['families'])*.24)))
    arms=['E_I','E_T','I_img','T_img','I_E','T_E']
    if b['families']:
        matrix=np.array([[r['counts'][x]['success']/3 if r['counts'][x]['n'] else np.nan for x in arms] for r in b['families']]);im=ax.imshow(matrix,vmin=0,vmax=1,cmap='Blues',aspect='auto')
        for y,r in enumerate(b['families']):
            for x,arm in enumerate(arms):
                v=r['counts'][arm];text=f'{v["success"]}/3'+(f'\n{v["missing"]} NA' if v['missing'] else '') if v['n'] else 'not run';ax.text(x,y,text,ha='center',va='center',fontsize=7)
        ax.set_yticks(range(len(b['families'])),[r['item_id'] for r in b['families']]);ax.set_xticks(range(6),arms);fig.colorbar(im,ax=ax,label='Correct/frozen replicates')
    else:ax.text(.5,.5,'No Phase B candidates',ha='center');ax.axis('off')
    ax.set_title('Fresh-seed confirmation signatures (all candidates; NA retained)');save(fig,'Y4_confirmed_role_signatures')
    fig,ax=plt.subplots(figsize=(9,max(3,len(c['families'])*.4)))
    if c['families']:
        arms=['I_E','T_E','Q_I','RT_T','RT_I','SH_I'];by={r['item_id']:r for r in b['families']};matrix=[];labels=[]
        for r in c['families']:
            prior=by[r['item_id']];values=[prior['counts'][x]['success']/3 for x in arms[:2]]+[r['panels'][x].count(True)/5 for x in arms[2:]];matrix.append(values);labels.append(r['item_id'])
        im=ax.imshow(matrix,vmin=0,vmax=1,cmap='Blues',aspect='auto');ax.set_yticks(range(len(labels)),labels);ax.set_xticks(range(len(arms)),['B: I_E','B: T_E','C: fresh I_E','R_T → T','R_T → I','Shuffle → I']);fig.colorbar(im,ax=ax,label='Correct/frozen replicates')
        for y,row in enumerate(matrix):
            for x,value in enumerate(row):
                family=c['families'][y]
                missing=by[family['item_id']]['counts'][arms[x]]['missing'] if x<2 else family['panels'][arms[x]].count(None)
                text=f'{round(value*(3 if x<2 else 5))}/{3 if x<2 else 5}'+(f'\n{missing} NA' if missing else '')
                ax.text(x,y,text,ha='center',va='center')
    else:ax.text(.5,.5,'Phase C not run: '+c['status'],ha='center',wrap=True);ax.axis('off')
    ax.set_title('Equal-evidence state construction; all replay inputs image-free');save(fig,'Y5_state_construction')
