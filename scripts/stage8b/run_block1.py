"""Two independent Slurm GPUs analyze frozen item tables, with shared bootstrap seeds."""
import json
import os
import socket
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from visual_reasoning.stage8b.block1_data import (ROOT,PRIMARY,SECONDARY,FAMILIES,PHASE_METRICS,
    digest,save,b0_path,load_frame,nuisance,episode_metrics)
from visual_reasoning.stage8b.block1_statistics import ItemBootstrap,paired_summary,BOOTSTRAPS,SEED


class Analysis:
    def __init__(self,frame,freeze,device):
        self.frame=frame;self.freeze=freeze;self.device=device;self.engines={}
        self.pairs=json.loads((ROOT/'audit'/'matching_freeze.json').read_text())['pairs']

    def engine(self,frame,completion=False):
        key=(tuple(frame.item_id),completion)
        if key not in self.engines:
            group=(frame.completion=='capped').to_numpy(dtype=int) if completion else (frame.benchmark_label=='wrong').to_numpy(dtype=int)
            self.engines[key]=ItemBootstrap(group,device=self.device)
        return self.engines[key]

    def compare(self,frame,metric,full=True):
        sub=frame.loc[frame.benchmark_label.isin(['correct','wrong'])]
        engine=self.engine(sub);y=sub[metric].to_numpy(dtype=float)
        raw,raw_samples=engine.raw(y);data=dict(metric=metric,raw=raw,adjusted={});samples={'raw':raw_samples}
        modes=['length','joint','full'] if full else ['full']
        for mode in modes:
            d,names=nuisance(sub,mode,self.freeze)
            value,replicates=engine.adjusted(y,d);value['covariates']=names
            data['adjusted'][mode]=value;samples[mode]=replicates
        if full:
            normal=sub.loc[sub.completion=='normal completed'];normal_engine=self.engine(normal)
            ny=normal[metric].to_numpy(dtype=float)
            data['normal_raw'],samples['normal_raw']=normal_engine.raw(ny)
            d,names=nuisance(normal,'full',self.freeze)
            data['adjusted']['normal_full'],samples['normal_full']=normal_engine.adjusted(ny,d)
            data['adjusted']['normal_full']['covariates']=names
            by_id=frame.set_index('item_id')
            diffs=[by_id.loc[p['wrong_id'],metric]-by_id.loc[p['correct_id'],metric] for p in self.pairs
                   if p['wrong_id'] in by_id.index and p['correct_id'] in by_id.index]
            data['matched']=paired_summary(diffs,device=self.device)
        return data,samples

    def completion(self,metric):
        sub=self.frame.loc[self.frame.completion.isin(['normal completed','capped'])]
        engine=self.engine(sub,completion=True);y=sub[metric].to_numpy(dtype=float)
        raw,_=engine.raw(y);d,names=nuisance(sub,'completion_full',self.freeze)
        adjusted,_=engine.adjusted(y,d)
        adjusted['covariates']=names
        return dict(direction='capped minus normal; all outcomes including unresolved',raw=raw,adjusted=adjusted)

    def curves(self,events):
        frame=self.frame.loc[self.frame.benchmark_label.isin(['correct','wrong'])]
        grid=np.linspace(0,1,21);densities=[];cumulative=[]
        for row in frame.itertuples():
            starts=events.loc[events.item_id==row.item_id,'normalized_start'].to_numpy()
            counts=np.histogram(starts,bins=grid)[0]
            token_bins=np.searchsorted(grid,np.arange(row.reasoning_tokens)/row.reasoning_tokens,side='right')-1
            exposure=np.bincount(np.minimum(token_bins,19),minlength=20)
            densities.append(np.divide(1000*counts,exposure,out=np.full(20,np.nan),where=exposure>0))
            cumulative.append(np.sum(starts[:,None]<=grid[None,:],axis=0))
        engine=self.engine(frame);result={}
        for name,values,positions in [('density',np.array(densities),(grid[:-1]+grid[1:])/2),('cumulative',np.array(cumulative),grid)]:
            rows=[]
            for p,y in zip(positions,values.T):
                raw,_=engine.raw(y);rows.append(dict(position=float(p),**raw))
            result[name]=rows
        return result


def main():
    rank=int(os.environ['SLURM_PROCID']);assert int(os.environ['SLURM_NTASKS'])==2
    assert socket.gethostname().split('.')[0]=='node06' and torch.cuda.device_count()==1
    torch.cuda.set_device(0)
    freeze=json.loads((ROOT/'audit'/'analysis_definition_freeze.json').read_text())
    execution=json.loads((ROOT/'audit'/'execution_freeze.json').read_text())
    for path,sha in execution['source_sha256'].items():assert digest(path)==sha,path
    for path,sha in execution['input_sha256'].items():assert digest(path)==sha,path
    base=json.loads(b0_path('freeze.json').read_text())
    for path,sha in base['artifacts_sha256'].items():assert digest(path)==sha,path
    frame=load_frame();device='cuda:0';analysis=Analysis(frame,freeze,device)
    environment=dict(rank=rank,host=socket.gethostname(),slurm_job_id=os.environ['SLURM_JOB_ID'],
        gpu=str(torch.cuda.get_device_properties(0)),gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),
        torch=torch.__version__,numpy=np.__version__,pandas=pd.__version__,resamples=BOOTSTRAPS,seed=SEED,dtype='float64')
    save(ROOT/'workers'/f'rank{rank}'/'environment.json',environment)
    # Validate actual-device bootstrap/OLS mechanics against a CPU reference.
    sub=frame.loc[frame.benchmark_label.isin(['correct','wrong'])]
    group=(sub.benchmark_label=='wrong').to_numpy(dtype=int);y=sub.retrieval_density.to_numpy()
    d,_=nuisance(sub,'full',freeze)
    cpu=ItemBootstrap(group,resamples=32);gpu=ItemBootstrap(group,resamples=32,device=device)
    c,cr=cpu.adjusted(y,d);g,gr=gpu.adjusted(y,d)
    np.testing.assert_allclose(cr,gr,atol=1e-9,rtol=1e-9,equal_nan=True)
    np.testing.assert_allclose(c['coefficient'],g['coefficient'],atol=1e-9,rtol=1e-9)
    a,ar=cpu.raw(y);b,br=gpu.raw(y);np.testing.assert_allclose(ar,br,atol=1e-12,rtol=1e-12)
    save(ROOT/'workers'/f'rank{rank}'/'gpu_parity.json',dict(passed=True,technical_resamples=32,scientific_resamples=4000,
        max_OLS_bootstrap_difference=float(np.nanmax(np.abs(cr-gr))),raw_bootstrap_max_difference=float(np.nanmax(np.abs(ar-br)))))
    print(json.dumps(dict(event='gpu_parity_pass',**environment)),flush=True)
    tasks=[('primary',m) for m in PRIMARY]+[('secondary',m) for m in SECONDARY]
    episode_primary=[m for m in PRIMARY if m!='active_token_fraction' and not m.startswith('standardized_')]
    for gap in [0,8]:tasks += [(f'gap{gap}',m) for m in episode_primary]
    tasks += [('low_displacement','standardized_tortuosity')]
    phases=pd.read_parquet(b0_path('phase_metrics.parquet'))
    for p in range(1,5):
        for metric in PHASE_METRICS:
            key=f'phase{p}_{metric}';values=phases.loc[phases.phase==p].set_index('item_id')[metric]
            frame[key]=frame.item_id.map(values);tasks.append(('phase',key))
    for metric in PHASE_METRICS:
        key='late_minus_early_'+metric;frame[key]=frame['phase4_'+metric]-frame['phase1_'+metric]
        tasks.append(('phase',key))
    tasks.append(('curves','curves'))
    gap_frames={gap:episode_metrics(frame,pd.read_parquet(b0_path(f'retrieval_episode_gap{gap}_sensitivity.parquet'))) for gap in [0,8]}
    started=time.monotonic();mine=list(enumerate(tasks))[rank::2]
    for k,(task_index,(kind,metric)) in enumerate(mine):
        clock=time.monotonic();samples={}
        if kind=='curves':
            events=pd.read_parquet(b0_path('retrieval_episode_table.parquet'),columns=['item_id','normalized_start'])
            result=analysis.curves(events)
        else:
            data=gap_frames[int(kind[3:])] if kind.startswith('gap') else frame
            if kind=='low_displacement':data=frame.loc[frame.standardized_net_displacement>freeze['small_displacement_cutoff']]
            result,samples=analysis.compare(data,metric,full=kind!='phase')
            if kind=='primary':result['completion']=analysis.completion(metric)
            result.update(kind=kind,primary=kind=='primary')
        name=f'{task_index:03d}_{kind}_{metric}'
        save(ROOT/'tasks'/(name+'.json'),result)
        if samples:np.savez_compressed(ROOT/'tasks'/(name+'_bootstrap.npz'),**samples)
        progress=dict(event='task_complete',rank=rank,task=name,completed=k+1,target=len(mine),
            elapsed_seconds=time.monotonic()-started,task_seconds=time.monotonic()-clock,
            peak_gpu_bytes=torch.cuda.max_memory_allocated())
        with (ROOT/'workers'/f'rank{rank}'/'progress.jsonl').open('a') as stream:stream.write(json.dumps(progress)+'\n')
        print(json.dumps(progress),flush=True)
    save(ROOT/'workers'/f'rank{rank}'/'complete.json',dict(completed=True,tasks=[i for i,_ in mine],
        all_tasks=[dict(index=i,kind=k,metric=m) for i,(k,m) in enumerate(tasks)],elapsed_seconds=time.monotonic()-started))


if __name__=='__main__':main()
