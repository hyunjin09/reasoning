"""Standalone publication-exportable causal local-assay figures."""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage10c.common import ROOT,load,save,sha,now

def store(fig,name):
 root=ROOT/'figures';root.mkdir(exist_ok=True)
 for suffix in ('png','pdf'):fig.savefig(root/f'{name}.{suffix}',dpi=180,bbox_inches='tight')
 plt.close(fig)

def paired(ax,rows,values,left,right,title,ylabel):
 for r in rows:
  y=values(r);color='#117a7a' if r['historical_faithful'] else '#ad6c37'
  ax.plot([0,1],y,color=color,alpha=.5,lw=1,marker='o',ms=4)
 mean=np.mean([values(r) for r in rows],0);ax.plot([0,1],mean,'kD-',lw=2,ms=7,label='Trajectory-equal mean')
 ax.set(xticks=[0,1],xticklabels=[left,right],title=title,ylabel=ylabel,xlim=(-.15,1.15));ax.legend(fontsize=8)

def main():
 assert os.environ.get('SLURM_JOB_ID');result=load(ROOT/'stage10c_primary_inference.json');rows=load(ROOT/'audit/final_scored.json')['pairs']
 fig,ax=plt.subplots(figsize=(10,3));ax.axhline(.5,color='#555',lw=2)
 ax.axvspan(-24,0,color='#117a7a',alpha=.2,label='PRE all-image mask');ax.axvspan(0,24,color='#ad6c37',alpha=.2,label='POST mask')
 ax.axvline(0,color='black',ls='--');ax.text(-34,.57,'A resolved → text reasoning',ha='center');ax.text(0,.73,'Frozen B demand',ha='center');ax.text(43,.57,'Normal access restored',ha='center')
 ax.annotate('',xy=(64,.27),xytext=(0,.27),arrowprops=dict(arrowstyle='<->'))
 ax.text(32,.34,'Local B outcome: first 64 tokens',ha='center')
 ax.set(xlim=(-50,68),ylim=(0,1),yticks=[],xlabel='Generated-token offset from frozen B onset',title='Stage10C: matched24-token causal windows, retained native prefix/cache');ax.legend(loc='lower left',fontsize=8)
 store(fig,'stage10c_figure1_windows')
 fig,ax=plt.subplots(figsize=(6,4));paired(ax,rows,lambda r:[r['y'][1],r['y'][2]],'PRE all off','POST all off','Behavioral reopening','Local B correctness')
 ax.set_yticks([0,.25,.5,.75,1]);fig.text(.5,.01,'Teal: historically faithful; brown: historical wrong/unresolved.',ha='center',fontsize=8);fig.tight_layout(rect=[0,.04,1,1]);store(fig,'stage10c_figure2_behavioral')
 fig,ax=plt.subplots(figsize=(6,4));paired(ax,rows,lambda r:[r['nll'][1]-r['nll'][0],r['nll'][2]-r['nll'][0]],'PRE all off','POST all off','Mechanistic reopening','Native B-span ΔNLL / token')
 ax.axhline(0,color='gray',ls='--',lw=1);fig.tight_layout();store(fig,'stage10c_figure3_mechanistic')
 fig,(a,b)=plt.subplots(1,2,figsize=(11,4));paired(a,rows,lambda r:[r['y'][4],r['y'][3]],'Irrelevant off','Target off','Behavioral source specificity','Local B correctness')
 paired(b,rows,lambda r:[r['nll'][4]-r['nll'][0],r['nll'][3]-r['nll'][0]],'Irrelevant off','Target off','Mechanistic source specificity','Native B-span ΔNLL / token')
 b.axhline(0,color='gray',ls='--',lw=1);fig.tight_layout();store(fig,'stage10c_figure4_specificity')
 if result['outcome']=='A':
  fig,ax=plt.subplots(figsize=(10,3));ax.axis('off')
  for x,text in [(.15,'Visual evidence A'),(.5,'Text reasoning'),(.85,'New visual evidence B')]:ax.text(x,.6,text,ha='center',va='center',bbox=dict(boxstyle='round',facecolor='#e9f3f3'),transform=ax.transAxes)
  for lo,hi in [(.28,.38),(.62,.72)]:ax.annotate('',xy=(hi,.6),xytext=(lo,.6),xycoords='axes fraction',arrowprops=dict(arrowstyle='->'))
  ax.text(.5,.25,'Natural sequential reopening under standard masking; universal repeated alternation remains untested.',ha='center',fontsize=10,transform=ax.transAxes)
  ax.text(.5,.05,'Stage10AR: controlled4B V→T evidence. Stage10C: natural2B PRE→POST contrast. Distinct cohorts.',ha='center',fontsize=9,transform=ax.transAxes)
  store(fig,'stage10c_figure5_framework')
 save(ROOT/'audit/figure_receipt.json',dict(at=now(),sha256={str(p):sha(p) for p in (ROOT/'figures').glob('*') if p.suffix in ('.png','.pdf')}))
if __name__=='__main__':main()
