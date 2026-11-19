"""Reveal native passive values only after the semantic adjudication seal."""
import os
from pathlib import Path
import numpy as np
from scripts.stage10b.common import ROOT,load,save,sha,now
from scripts.stage10b.routing import roi_indices,reaccess


def main():
    assert os.environ.get('SLURM_JOB_ID')
    sp=ROOT/'audit/semantic_adjudication_frozen.json';semantic=load(sp)
    assert semantic['sealed'] and not semantic['routing_opened']
    independent=load(ROOT/'audit/semantic_independent_passes_frozen.json')
    for p,d in independent['annotation_source_sha256'].items():assert sha(p)==d,p
    assert semantic['independent_passes_sha256']==sha(ROOT/'audit/semantic_independent_passes_frozen.json')
    freeze_path=ROOT/'audit/pre_signal_analysis_freeze_v3.json';frozen=load(freeze_path)
    for p,d in frozen['source_sha256'].items():assert sha(p)==d,p
    corpus=load(ROOT/'stage10b_corpus_manifest.json');by={r['trajectory_id']:r for r in corpus['rows']}
    rulepath=Path('outputs/stage8a/analysis/discovery_freeze_v1/freeze.json');rule=load(rulepath)['retrieval'];tau=rule['tau_R']
    cfg=load('outputs/stage9a/v1/stage9a_generation_config.json')
    assert cfg['detector_freeze_sha256']==sha(rulepath) and cfg['threshold']==tau
    assert sha(rule['models'])==rule['models_sha256']
    grouped={}
    for event in semantic['events']:grouped.setdefault(event['trajectory_id'],[]).append(event)
    rows=[];sources={}
    for tid,events in grouped.items():
        row=by[tid];native=Path(row['native_directory']);meta=load(native/'input.json');grid=meta['visual_mapping']['merged_grid_shape']
        passive=row['passive_path'];data=None;focus=scores=None
        if passive:
            receipt=load(native/'result.json');assert sha(passive)==receipt['provenance_sha256'][passive]
            data=np.load(passive,allow_pickle=False);sources[passive]=sha(passive)
            focus=data['visual_focus'];scores=data['retrieval_score']
            assert focus.shape==(row['generated_tokens'],int(np.prod(grid)))
            assert scores.shape==(row['generated_tokens'],)
            assert data['visual_positions'].tolist()==meta['visual_token_indices']
            assert row['model_revision']==cfg['models']['thinking']['revision']
            assert data['feature_keys'].tolist()==['visual_mass','qk_visual_nonvisual','qk_visual_reasoning','visual_top4_mass','visual_max','visual_entropy','visual_effective_count','sink_mass']
        for event in events:
            base=dict(event_id=event['event_id'],trajectory_id=tid,dataset=row['dataset'],onset=event['onset'],semantic_clean=event['semantic_clean'])
            target=roi_indices(event.get('target_roi_normalized'),grid)
            control=roi_indices(event.get('irrelevant_roi_normalized'),grid)
            if event.get('irrelevant_roi_normalized') is None:control=sorted(set(range(int(np.prod(grid))))-set(target))
            control=sorted(set(control)-set(target))
            if not passive:
                rows.append(dict(base,C5=False,lag=None,evidence_channel=None,
                    classification='ROUTING_DATA_MISSING' if target and control else 'TARGET_AMBIGUOUS',
                    coverage_complete=False,measured_tokens=0,rows=[],target_positions=target,irrelevant_positions=control,
                    threshold=tau,source_grid=grid,
                    detector_compatibility='Historical event summaries lack full B-specific patch routing for arbitrary frozen windows.',
                    missing_reason='No full per-patch native routing array. Historical causal scores are not used.'));continue
            b=event['onset'];end=min(row['generated_tokens'],b+32)
            result=reaccess(focus[b:end],scores[b:end],list(range(end-b)),
                target=target,irrelevant=control,tau=tau,observation_offset=event.get('observation_offset'))
            rows.append(dict(base,**result,detector_compatibility='compatible_frozen_Stage8A_detector_native2B_Thinking',
                passive_path=passive,passive_sha256=sources[passive],query_alignment='row i predicts generated token i; its query processed token i-1, row0 multimodal prefill.',
                source_grid=grid,threshold=tau))
        if data is not None:data.close()
        del focus,scores,data
    save(ROOT/'audit/reaccess_historical.json',dict(at=now(),rows=rows,semantic_sha256=sha(sp),passive_source_sha256=sources,
        detector_freeze_sha256=sha(rulepath),analysis_freeze_sha256=sha(freeze_path),
        new_gpu_hours=0,causal_outcomes_used=False))
    print('HISTORICAL PASSIVE EXTRACT',len(rows),'events',sum(r['C5'] for r in rows),'positive events;not independent yield',flush=True)


if __name__=='__main__':main()
