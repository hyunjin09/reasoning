"""Paired independent-trajectory inference and prospectively operationalized gates."""
from itertools import combinations
import numpy as np
from scripts.stage10c.common import SEED
from scripts.stage10c.protocol import contrasts

def effects(rows):return contrasts([r['y'] for r in rows],[r['nll'] for r in rows])

def summarize(rows):
 if not rows:return dict(n=0,primary=None)
 d=effects(rows);n=len(rows);indices=np.random.default_rng(SEED).integers(0,n,size=(4000,n));boot=d[indices].mean(1)
 ordinary=np.quantile(boot,[.025,.975],axis=0);adjusted=np.quantile(boot,[.00625,.99375],axis=0)
 return dict(n=n,ids=[r['trajectory_id'] for r in rows],primary={p:dict(point=float(d[:,j].mean()),ci95=ordinary[:,j].tolist(),familywise95_ci=adjusted[:,j].tolist(),
  positive=int((d[:,j]>0).sum()),negative=int((d[:,j]<0).sum()),tied=int((d[:,j]==0).sum())) for j,p in enumerate(['P1','P2','P3','P4'])},
  accuracy=dict(zip(['NATIVE','PRE_ALL_OFF','POST_ALL_OFF','POST_TARGET_OFF','POST_IRRELEVANT_OFF'],np.mean([r['y'] for r in rows],0).tolist())),
  mean_nll=dict(zip(['NATIVE','PRE_ALL_OFF','POST_ALL_OFF','POST_TARGET_OFF','POST_IRRELEVANT_OFF'],np.mean([r['nll'] for r in rows],0).tolist())))

def robustness(rows):
 d=effects(rows);n=len(rows);out=[]
 for k in (1,2):
  if n<=k:continue
  for gone in combinations(range(n),k):
   keep=[i for i in range(n) if i not in gone];out.append(dict(removed=[rows[i]['trajectory_id'] for i in gone],points=d[keep].mean(0).tolist()))
 minima=np.min([r['points'] for r in out],axis=0).tolist() if out else [None]*4
 return dict(leave_one_and_pair=out,minimum_points=minima,positive=[x is not None and x>0 for x in minima])

def gate(rows,result,technical):
 dsets={d:summarize([r for r in rows if r['dataset']==d]) for d in ['MathVision','MathVerse']}
 faithful=summarize([r for r in rows if r['historical_faithful']]);rob=robustness(rows)
 points=[result['primary'][k]['point'] for k in ['P1','P2','P3','P4']]
 datasets=all(s['n']>0 and all(s['primary'][k]['point']>0 for k in ['P1','P2']) for s in dsets.values())
 source_faithful=faithful['n']>0 and all(faithful['primary'][k]['point']>0 for k in ['P3','P4'])
 reopening=technical and min(points[:2])>0 and datasets and all(rob['positive'][:2])
 specificity=technical and min(points[2:])>0 and source_faithful and all(rob['positive'][2:])
 limited=any(v['familywise95_ci'][0]<=0<=v['familywise95_ci'][1] for v in result['primary'].values())
 return dict(main_gate_pass=bool(reopening and specificity),outcome='A' if reopening and specificity else 'B' if reopening else 'C' if specificity else 'D',
  reserve_gate_pass=bool(len(rows)==16 and technical and min(points)>0 and limited and datasets and all(rob['positive'])),
  reopening_pass=bool(reopening),specificity_pass=bool(specificity),gate_components=dict(all_four_positive=min(points)>0,both_dataset_reopening_positive=datasets,
   historical_faithful_specificity_positive=source_faithful,no_one_or_pair_dominance=all(rob['positive']),technical_pass=technical,precision_limited=limited),
  datasets=dsets,historical_faithful=faithful,robustness=rob)
