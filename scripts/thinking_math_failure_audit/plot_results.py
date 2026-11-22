"""Render the published numeric tables without raw inference artifacts."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/thinking_math_failure_audit/v1'


def main():
    with (OUT/'question_type_failure_rates.csv').open() as f: rows=list(csv.DictReader(f))
    subjects=sorted([r for r in rows if r['dataset']=='MATH-Vision' and r['dimension']=='subject'],key=lambda r:float(r['wrong_rate']))
    with (OUT/'source_feature_failure_rates.csv').open() as f: features=list(csv.DictReader(f))
    sizes=[next(r for r in features if r['feature']=='structured_subfacts' and r['level']==label) for label in ['none','1-4','5-9','10-19','20+']]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,(ax,bx)=plt.subplots(1,2,figsize=(15,7),gridspec_kw={'width_ratios':[1.4,1]})
    for i,r in enumerate(subjects):
        rate=float(r['wrong_rate'])*100;low=float(r['ci_low'])*100;high=float(r['ci_high'])*100
        ax.errorbar(rate,i,xerr=np.array([[rate-low],[high-rate]]),fmt='o',color='#24627b',capsize=3)
        ax.text(100,i,f"{r['wrong']}/{r['scored']}",va='center',fontsize=9)
    ax.set_yticks(range(len(subjects)),[r['level'] for r in subjects]);ax.set_xlim(0,115)
    ax.set_xticks([0,20,40,60,80,100]);ax.set_xlabel('Native final-answer error (%)');ax.set_title('All MATH-Vision native items, Thinking r0')
    x=np.arange(len(sizes));rates=np.array([float(r['wrong_rate'])*100 for r in sizes])
    lo=rates-np.array([float(r['ci_low'])*100 for r in sizes]);hi=np.array([float(r['ci_high'])*100 for r in sizes])-rates
    bx.bar(x,rates,color=['#8c9c9e','#357b86','#357b86','#c17c3d','#c17c3d'],width=.7)
    bx.errorbar(x,rates,yerr=[lo,hi],fmt='none',color='#253e46',capsize=4)
    for i,r in enumerate(sizes):bx.text(i,rates[i]+hi[i]+2,f"{r['wrong']}/{r['scored']}",ha='center',fontsize=9)
    bx.set_xticks(x,['Scalar only','1–4','5–9','10–19','20+']);bx.set_ylim(0,90)
    bx.set_ylabel('Native final-answer error (%)');bx.set_xlabel('Recorded structured internal subfacts');bx.set_title('Source-eligible 1,000-family subset')
    fig.suptitle('Where Qwen3-VL-4B-Thinking fails on MATH-Vision',fontsize=16,y=.99)
    fig.text(.5,.012,'Unscorable finals excluded. 95% family-cluster bootstrap intervals. Retrospective associations; source-size units and subject composition differ.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.04,1,.95]);(OUT/'figures').mkdir(exist_ok=True)
    fig.savefig(OUT/'figures/question_types_and_structure.svg');plt.close(fig)


if __name__=='__main__':main()
