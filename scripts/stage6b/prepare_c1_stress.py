"""Freeze B1 text prefixes across the eleven existing image conditions."""
from collections import defaultdict, Counter
from scripts.stage6b.common import OUT, SOURCE, read_jsonl, sha, write_json, write_jsonl, verify_stage6a


def main():
    verify_stage6a()
    release=[r for r in read_jsonl(SOURCE/'cohort/primary_release_events.jsonl') if r['cohort']=='C1']
    native={r['event_id']:r for r in read_jsonl(SOURCE/'traces/controlled_native_index.jsonl') if r['cohort']=='C1'}
    readouts={r['base_id']:r for r in read_jsonl(SOURCE/'c1_diagram_stress/readouts.jsonl')}
    maps=defaultdict(dict)
    for r in read_jsonl(SOURCE/'regions/controlled_roi_maps.jsonl'):
        if r['cohort']=='C1':maps[r['event_id']][r['source_id']]=r
    rows=[];conditions=defaultdict(set)
    scored={'intact','mild','strong','mask','sham_mild','sham_strong','sham_mask'}
    for row in release:
        base=row['base_id'];eid=row['event_id'];condition=row['condition'];old=readouts[base]
        assert old['numeric_label_correctness']=='CORRECT'
        end=int(old['ed_generated_index'])
        event={k:old[k] for k in ['history_before_ed_token_ids','history_before_ed_text',
            'history_before_ed_sha256','original_divergent_suffix_ids','counterfactual_divergent_suffix_ids',
            'original_divergent_suffix_text','counterfactual_divergent_suffix_text']}
        event.update(candidate_start_token=end,current_query_zero_based=end-1,
            native_claim_suffix_ids=old['original_divergent_suffix_ids'],
            native_claim_suffix_text=old['original_divergent_suffix_text'],
            correct_semantic_value=old['target']['value'],foil_semantic_value=old['target']['counterfactual'],
            reviewed_claim={k:old[k] for k in ['claim_quote','char_start','char_end','local_visual_correctness','numeric_label_correctness']},
            readout_orientation='Dx=mean_logP(intact x)-mean_logP(counterfactual xprime), same direction in every condition; reverse interpretation for counterfactual')
        assert len(event['history_before_ed_token_ids'])==end and end>=8
        groups={}
        if condition!='no_image':
            footprint=maps[eid]['T']['absolute_token_indices']
            groups['placebo_T' if condition=='unrelated' else 'T']=footprint
        entry={'id':eid,'event_id':eid,'base_id':base,'cohort':'C1','dataset':row['dataset'],
            'split':row['split'],'group_id':row['group_id'],'condition':condition,'phase':'b',
            'row':row,'event':event,'source_groups':groups,
            'roles':{'focal':'T' if condition not in ['no_image','unrelated'] else None,
                     'demanded':'T','semantic_source_valid':condition not in ['no_image','unrelated']},
            'native_input_path':native[eid]['input_metadata_artifact'],
            'native_generation_path':native[eid]['generation_artifact'],
            'intact_prefix_native_generation_path':old['full_prior_history_artifact'],
            'prefix_history_sha256':old['history_before_ed_sha256'],
            'prefix_literal_target_occurrences':event['history_before_ed_text'].count(str(old['target']['value'])),
            'prefix_occurrence_caveat':'Literal string counts are descriptive; geometric binding and earlier causal use remain separate.',
            'w2_sources':['T'] if condition in scored else [],
            'w8_sources':['T'] if row['split']=='confirmation' and condition in ['intact','strong','mask'] else [],
            'final_correctness_reference':'Native-condition final labels remain separate from fixed-prefix output preferences.',
            'analysis_mode':'B1_fixed_intact_text_prefix',
            'no_image_comparison':'Distribution comparison only; no visual VSD or cross-interface KV identity.'}
        rows.append(entry);conditions[base].add(condition)
    expected={'intact','counterfactual','mild','strong','mask','sham_mild','sham_strong',
              'sham_mask','counterfactual_render_sham','unrelated','no_image'}
    assert len(rows)==1199 and len(conditions)==109 and all(c==expected for c in conditions.values())
    assert all(len({r['prefix_history_sha256'] for r in rows if r['base_id']==base})==1 for base in conditions)
    write_jsonl(OUT/'c1_mirage/fixed_prefix_manifest.jsonl',rows,freeze=True)
    write_json(OUT/'config/c1_stress_rules.json',{'conditions':sorted(expected),
        'primary_vsd_conditions':sorted(scored),'w8_confirmation_conditions':['intact','strong','mask'],
        'prefix_selection':'Reuse Stage6A independently reviewed intact local numeric source readout, without changing its native text history.',
        'primary_candidates':'intact x versus counterfactual xprime; preserve both token and sequence log-probabilities',
        'counterfactual_gate':'Positive source-semantic followability beyond render sham is necessary for strict semantic mirage; thresholds frozen using discovery only.',
        'native_condition_features':'Separate B2 extraction; never pool with B1 fixed-prefix contrasts.',
        'target_removal':'Only saved Stage6A matched manipulations; no-image has no target ROI and unrelated footprint is descriptive placebo only.',
        'attention_or_causal_selection':False},freeze=True)
    write_json(OUT/'audit/c1_fixed_prefix_freeze.json',{'status':'PASS','bases':109,'events':1199,
        'conditions_per_base':11,'events_by_split':dict(Counter(r['split'] for r in rows)),
        'manifest_sha256':sha(OUT/'c1_mirage/fixed_prefix_manifest.jsonl'),
        'identical_textual_prefixes_per_base':True,'GPU_replay_audit_pending':True},freeze=True)
    print('C1 B1 manifest frozen: 109 bases, 1199 fixed-prefix conditions; no GPU scores used.')


if __name__=='__main__':main()
