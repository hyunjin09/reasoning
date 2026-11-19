"""Open paired outcomes only after every included arm has closed its scoring/QC."""
from pathlib import Path
import pandas as pd
from scripts.stage13b.execution import ROOT,load,save,sha,now
from scripts.stage13b.review import tasks,technical,technical_path
from scripts.stage13b import reuse
from scripts.stage13b.inference import effects


def parquet(path,rows):
    assert not path.exists();pd.DataFrame(rows).to_parquet(path,index=False)


def response(t,reused=False):
    base=reuse.OLD if reused else ROOT;tid=t['task_id'];path=base/'generations'/tid/'generation.json';g=load(path)
    a=load(reuse.technical_path(tid)) if reused else technical(tid)
    p=reuse.score_path(tid) if reused else ROOT/'audit/score_adjudications'/f'{tid}.json'
    if not p.exists():p=ROOT/'audit/first_scores'/f'{tid}.json'
    s=load(p);mode=t['model_key'] if reused else t['mode'];before=False
    if mode=='T' and s['correct'] is not None and a['outcome']!='__NO_ANSWER__':
        if g['tokens']<32768:before=True
        else:
            timing=load(base/'audit/token_budget'/f'{tid}.json')
            assert timing['generation_sha256']==sha(path)
            before=timing['scoreable_before32k'];assert type(before) is bool
    return dict(task_id=tid,scale='4B' if reused else t['scale'],mode=mode,condition=t['arm'].split('_',1)[1],
        item_id=t['item_id'],family_id=t['family_id'],replicate=t['replicate'],seed=t['seed'],reused=reused,
        label=s['label'],correct=s['correct'],outcome=a['outcome'],**a['validity'],scoreable_before32k=before,
        tokens=g['tokens'],cap_hit=g['cap_hit'],finish_reason=g['finish_reason'],latency_seconds=g['request_latency_seconds'],
        generation_path=str(path),generation_sha256=sha(path),technical_path=str(reuse.technical_path(tid) if reused else technical_path(tid)),score_path=str(p))


def main(include_image=True):
    conditions=['EQ','img'] if include_image else ['EQ'];seals={}
    for scale in ['2B','4B','8B']:
        for c in conditions:
            for m in ['I','T']:
                p=ROOT/'audit/scoring_closed'/f'{scale}_{m}_{c}.json';seal=load(p)
                for f,h in seal['files'].items():assert sha(f)==h,f
                seals[str(p)]=sha(p)
    flat=[response(t) for t in tasks() if t['phase'] in (['equal','image'] if include_image else ['equal'])]
    flat += [response(t,True) for m in ['I','T'] for t in reuse.tasks(m)]
    assert len(flat)==(1728 if include_image else 864)
    families=[]
    for scale in ['2B','4B','8B']:
        for c in conditions:
            for src in load(ROOT/'stage13b_frozen48_manifest.json')['rows']:
                rr=[r for r in flat if r['scale']==scale and r['condition']==c and r['family_id']==src['family_id']]
                both={m:sorted([r for r in rr if r['mode']==m],key=lambda r:r['replicate']) for m in ['I','T']}
                assert all([r['replicate'] for r in both[m]]==[0,1,2] for m in ['I','T'])
                f=dict(family_id=src['family_id'],item_id=src['item_id'],scale=scale,condition=c,
                       I=[None if r['correct'] is None else int(r['correct']) for r in both['I']],
                       T=[None if r['correct'] is None else int(r['correct']) for r in both['T']],
                       T_before32k=[r['scoreable_before32k'] for r in both['T']])
                f['complete']=None not in f['I']+f['T']
                for m in ['I','T']:
                    values=[x for x in f[m] if x is not None];f[m+'_mean']=sum(values)/len(values) if values else None
                families.append(f)
    out=effects(families)
    for scale in ['2B','4B','8B']:
        for c in conditions:
            if scale=='4B' and c=='EQ':continue
            name='image' if c=='img' else 'equal_evidence'
            parquet(ROOT/f'stage13b_{scale.lower()}_{name}_results.parquet',[r for r in flat if r['scale']==scale and r['condition']==c])
    parquet(ROOT/'stage13b_family_level_results.parquet',families)
    save(ROOT/'stage13b_scale_effects.json',dict(at=now(),scales=out['scales'],absolute=out['absolute'],majority_transitions=out['majority_transitions']))
    save(ROOT/'stage13b_missingness_bounds.json',dict(at=now(),cells=out['missingness'],n_families=48,imputation=False))
    save(ROOT/'stage13b_32k_sensitivity.json',dict(at=now(),cells=out['sensitivity'],new_calls=0,decoding_matched=False))
    save(ROOT/'stage13b_scoring_audit.json',dict(at=now(),seals=seals,scope='Arm-separated same-agent QC, not independent-rater reliability',paired_outcomes_opened_at=now()))
    save(ROOT/'stage13b_primary_inference.json',dict(at=now(),**out,phase2_executed=include_image,independent_unit='conservative visual family',
        estimator='Family-equal complete three-replicate paired differences; 10000 paired bootstrap draws, integer signed count units'))
    save(ROOT/'audit/paired_inference_seal.json',dict(at=now(),files={str(p):sha(p) for p in ROOT.glob('stage13b_*') if p.is_file()},
        analysis_source_sha256={str(p):sha(p) for p in [Path(__file__),Path('scripts/stage13b/inference.py')]}))
    print('PRIMARY_SEALED',out['states'])


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--phase1-only',action='store_true');a=parser.parse_args();main(not a.phase1_only)
