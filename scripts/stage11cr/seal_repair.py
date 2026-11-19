"""Select the highest-priority historical protocol after completion-only review."""
import pandas as pd
from scripts.stage11cr.common import ROOT,load,save,sha,now


def main():
    review=load(ROOT/'annotations/known_good_technical_review.json')
    diagnostic=load(ROOT/'audit/diagnostic_completion_review.json')
    assert review['frozen'] and review['gate']['pass_gate']
    assert len(review['rows'])==12 and all(r['exact_token_identity'] for r in review['rows'])
    assert not review['accuracy_used'] and not diagnostic['accuracy_used']
    path=ROOT/'stage11cr_known_good_reproduction.parquet';assert not path.exists()
    flat=[]
    for r in review['rows']:
        flat.append({k:r[k] for k in ['task_id','arm','tokens','cap','normal_eos','at_length_cap',
            'committed_final','pathological_repetition','exact_token_identity','first_divergence_token',
            'length_ratio','historical_tokens','batch_seconds','generation_sha256','input_sha256']})
    pd.DataFrame(flat).to_parquet(path,index=False)
    matrix=load(ROOT/'audit/discrepancy_matrix_v2_unknown_aware.json')
    for r in matrix['rows']:
        r['status']='AUDITED'
        if r['dimension']=='generation_kwargs':
            r.update(completion_improvement='Fixed SDPA2-case contrast: greedy0/2 EOS, historical sampling2/2 EOS.',
                exact_replay_improvement='Sampled eager historical recipe12/12 exact; sampled SDPA differs on both diagnostic cases.',
                new_divergence='SDPA sampled versus eager historical token divergence recorded in diagnostic review.')
        elif r['dimension']=='backend':
            r.update(completion_improvement='Not independently necessary for EOS in the2-case sampling contrast.',
                exact_replay_improvement='Restored eager historical bundle12/12 exact; sampled SDPA2/2 differs.',
                new_divergence='Backend changes stochastic traces; no accuracy consequence assessed.')
        elif r['dimension'] in ['chat_template','image']:
            r.update(completion_improvement='No discrepancy to restore: all12 input tensors/chat/pixels exactly match.',
                exact_replay_improvement='Input identities verified on CPU and replay.',new_divergence=False)
        elif r['dimension']=='length_semantics':
            r.update(completion_improvement='Historical common40960 restored;8/12 selected historical completions exceed8192. Length alone was not tested as a loop repair.',
                exact_replay_improvement='Same max_new_tokens semantics; prior caps differed.',new_divergence=False)
        elif r['dimension']=='cache':
            r.update(completion_improvement='UNKNOWN independent contribution; recovered library recomputes fresh-call vision position IDs.',
                exact_replay_improvement='Historical per-call seed/rope reset retained; cache implementation not explicitly recorded historically.',
                new_divergence='No observed divergence under complete historical recipe.')
        else:
            r.update(completion_improvement='No GPU alteration needed beyond restored historical recipe.',
                exact_replay_improvement='Historical recipe12/12 exact.',new_divergence=False)
    save(ROOT/'stage11cr_discrepancy_audit.json',dict(at=now(),rows=matrix['rows'],accuracy_used=False,
        diagnostic_review_sha256=sha(ROOT/'audit/diagnostic_completion_review.json'),
        input_equivalence_sha256=sha(ROOT/'audit/cpu_input_equivalence.json'),
        supported_diagnosis='Greedy decoding produces severe repetitive noncompletion in both fixed diagnostic cases; restoring historical sampling resolves EOS/final completion there. Exact historical recipe reproduces12/12 saved outputs.',
        limits='This does not establish a single cause for every original Stage11C failure or guarantee completion of the frozen technical/primary cohort.'))
    save(ROOT/'stage11cr_repaired_protocol.json',dict(at=now(),frozen=True,**{'pass':True},
        worker_protocol='historical',selection_priority=1,selection='Exact recovered Stage9A historical protocol',
        batch_size=1,dtype='bfloat16',tf32=False,attention=dict(text='eager',vision='sdpa'),
        generation=dict(do_sample=True,temperature=1.,top_p=.95,top_k=20,repetition_penalty=1.,
            max_new_tokens=40960,use_cache=True),seed='Reuse original item seed for each arm/condition',
        native_preprocessing='Unchanged Stage9A prepared_input; identical Stage11C input tensors',
        eos_ids=[151645,151643],reset_rope_per_call=True,fresh_kv_cache=True,
        model_revisions=load(ROOT/'config.json')['models'],
        known_good_gate=review['gate'],known_good_review_sha256=sha(ROOT/'annotations/known_good_technical_review.json'),
        cap_protocol_correction_sha256=sha(ROOT/'audit/cap_protocol_correction.json'),
        accuracy_used=False,primary_scientific_inputs_unchanged=True,
        next_authorized_action='Only original12 nonprimary cases ×2 arms; no primary until its gate passes.'))
    print('HISTORICAL_REPAIR_GATE_PASS:12/12 exact; R3 still required')


if __name__=='__main__':main()
