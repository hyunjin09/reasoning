"""Five descriptive source figures; no model performance inputs."""
import os
from pathlib import Path
os.environ['MPLCONFIGDIR']=str(Path('runs/stage14a/cache/matplotlib').resolve())
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.stage14a.common import *
s=load(ROOT/'stage14a_source_statistics.json');m=s['mathvision'];v=s['mathverse'];out=ROOT/'figures';out.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
paths=[]
def finish(fig,name):
 for ext in ['png','pdf']:
  p=out/f'{name}.{ext}';assert not p.exists();fig.savefig(p,dpi=180,bbox_inches='tight');paths.append(str(p))
 plt.close(fig)
fig,ax=plt.subplots(figsize=(11,5));ax.axis('off')
boxes=[(.13,.75,'3,040 native problems\n2,104 conservative families'),(.5,.75,'1,727 frozen-order\nrepresentatives screened'),(.87,.75,'1,000 final families\nall second reviewed'),(.5,.25,'725 source exclusions\n2 accepted-source aliases'),(.87,.25,'250 final-cohort rereads\n300 confirmation families')]
for x,y,t in boxes:ax.text(x,y,t,ha='center',va='center',bbox=dict(boxstyle='round,pad=.6',fc='#e7f0f9',ec='#416f99'),transform=ax.transAxes)
for a,b in [(boxes[0],boxes[1]),(boxes[1],boxes[2]),(boxes[1],boxes[3]),(boxes[2],boxes[4])]:ax.annotate('',xy=(b[0]-.1 if a[1]==b[1] else b[0],b[1]+.11 if a[1]!=b[1] else b[1]),xytext=(a[0]+.1 if a[1]==b[1] else a[0],a[1]-.11 if a[1]!=b[1] else a[1]),xycoords='axes fraction',arrowprops=dict(arrowstyle='->',color='#416f99'))
ax.set_title('14A-1 · MATH-Vision source screening',pad=20);ax.text(.5,-.03,'One complete-reread rejection replaced from the frozen order; original evidence retained.',ha='center',transform=ax.transAxes,fontsize=10);finish(fig,'figure14a_1_screening_flow')
fig,axs=plt.subplots(2,2,figsize=(13,11),gridspec_kw={'height_ratios':[2,1]})
for ax,(field,counts) in zip(axs.flat,m['distributions'].items()):
 items=sorted(counts.items(),key=lambda kv:kv[1],reverse=True) if field=='subject' else sorted(counts.items())
 labels,values=zip(*items);bars=ax.barh(labels,values,color='#416f99');ax.invert_yaxis();ax.bar_label(bars,padding=3);ax.set_xlim(0,max(values)*1.2);ax.set_title(field.replace('_',' '));ax.set_xlabel('Accepted families')
fig.suptitle('14A-2 · Final E* cohort composition (N = 1,000)');fig.tight_layout();finish(fig,'figure14a_2_cohort_composition')
fig,ax=plt.subplots(figsize=(10,4));items=list(m['evidence_types'].items());labels=[k.removeprefix('requires_').replace('_',' ') for k,_ in items];vals=[v for _,v in items];bars=ax.barh(labels,vals,color='#50866d');ax.invert_yaxis();ax.bar_label(bars,padding=4);ax.set_xlim(0,1000);ax.set_xlabel('Families (categories overlap)');ax.set_title('14A-3 · Required source evidence');finish(fig,'figure14a_3_evidence_types')
fig,ax=plt.subplots(figsize=(10,4));labels=['Text Dominant','Text Lite','Text Only','Vision Intensive','Vision Dominant','Vision Only'];bars=ax.barh(labels,[788]*6,color='#7963a2');ax.invert_yaxis();ax.bar_label(bars,padding=4);ax.set_xlim(0,900);ax.set_xlabel('Native families with version present');ax.set_title('14A-4 · MathVerse modality map: 788 complete six-version families');fig.text(.12,-.03,'Availability is not semantic sufficiency; 350 families pass all recorded source checks.',fontsize=10);finish(fig,'figure14a_4_mathverse_modality_map')
fig,ax=plt.subplots(figsize=(12,4));categories=['UNTOUCHED','SOURCE_ONLY','GENERATION_OR_TECHNICAL','OUTCOME_OR_TRACE_REVIEW','OTHER_EXPOSURE_UNCLASSIFIED'];colors=['#bbbbbb','#76b7b2','#edc948','#e15759','#9c755f'];y=['MATH-Vision (2,104 families)','MathVerse (788 native families)'];left=[0,0]
for cat,color in zip(categories,colors):
 vals=[s['historical_exposure'][ds].get(cat,0) for ds in ['mathvision','mathverse']];bars=ax.barh(y,vals,left=left,label=cat.replace('_',' ').lower(),color=color)
 for i,n in enumerate(vals):
  if n>=100:ax.text(left[i]+n/2,i,str(n),ha='center',va='center',fontsize=10)
 left=[a+b for a,b in zip(left,vals)]
ax.invert_yaxis();ax.set_xlabel('Conservative family count; mutually exclusive provenance groups');ax.set_title('14A-5 · Historical exposure (strictly untouched = 0 in both cohorts)');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.27),ncol=2,frameon=False);fig.text(.12,-.36,'Source catalogs count as exposure. Generation does not establish human inspection; unknown provenance stays separate.',fontsize=9);finish(fig,'figure14a_5_historical_exposure')
save(ROOT/'audit/source_figure_manifest.json',dict(at=now(),files={p:sha(p) for p in paths},source_statistics_sha256=sha(ROOT/'stage14a_source_statistics.json'),model_performance_inputs=False))
print('FIGURES',5,'FORMATS',len(paths))
