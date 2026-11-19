"""Real native role confirmations with an explicit numeric antecedent."""
import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

from collections import defaultdict

from transformers import AutoTokenizer

from scripts.stage6b.common import read_json, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from visual_reasoning.stage6b.protocol import candidate_event


def main():
    tokenizer = AutoTokenizer.from_pretrained(read_json(OUT / 'config/stage6br_config.json')['model_checkpoint'], local_files_only=True)
    values = {r['id']:r for r in rows(OUT / 'annotation_repair/value_readouts.jsonl')}
    index = {r['event_id']:r for r in rows(OUT / 'inputs/c1_index.jsonl')}
    groups = defaultdict(list)
    exclusions = []
    for i, r in enumerate(rows(OUT / 'review/role_confirmation_local_candidates.jsonl')):
        if i in {14,16}:
            exclusions.append({'proposal_index':r['proposal_index'], 'reason':'The intervening3 value is the actual antecedent of slant height; the preceding mapped5 readout is not the antecedent.'})
            continue
        groups[r['event_id']].append(r)
    result = []
    for eid, candidates in sorted(groups.items()):
        tokens = list(rows(index[eid]['tokens_artifact']))
        raw = ''.join(t['decoded_token'] for t in tokens)
        for r in candidates:
            native = r['phrase']
            assert raw[r['char_start']:r['char_end']] == native
            replacement = {'radius':'diameter', 'diameter':'radius', 'height':'horizontal width'}[r['role']]
            foil = native.replace(r['role'],replacement)
            event = candidate_event(tokens, r['char_start'], r['char_end'], native, foil, tokenizer)
            assert event['original_divergent_suffix_ids'] == event['native_claim_suffix_ids']
            a = values[r['value_readout_id']]
            row = {k:a[k] for k in ('event_id','base_id','dataset','condition','split','group_id','demand_sources','source_id','evidence_class','source_identity_mapped')}
            row.update({'id':eid+'__role_confirmation_'+str(r['char_start']),
                        'span_id':r['span_id'],'char_start':r['char_start'],'char_end':r['char_end'],
                        'assertion_start':r['char_start'],'assertion_end':r['char_end'],'assertion':native,
                        'event':event,'readout_types':['B'],'native_claim':native,'correct_claim':native,'foil_claim':foil,
                        'readout_validity':'BINDING_CANDIDATE_CONTEXT_REVIEW_REQUIRED',
                        'values_held_fixed_in_native_prefix':True,'antecedent_value':r['native_value'],
                        'antecedent_readout_id':a['id'],'observed_wrong_claim':False,
                        'source_content_already_explicit_in_prior_reasoning':True,
                        'ground_truth_direction':'correct_minus_foil','wrong_direction':None,
                        'normalized_token_progress':event['current_query_zero_based']/len(tokens),
                        'new_visual_acquisition_required':'UNRESOLVED',
                        'native_parent_prefix_through_assertion':r['context'][:r['char_end']-r['span_char_start']],
                        'reason_for_validity':'Main-agent read all32 local candidate contexts and excluded two incorrect antecedent associations. A native role confirmation preserves the explicit antecedent value. Full interval review determines whether identifying the role is a new visual subgoal.',
                        'frozen_before_new_causal_scores':True})
            result.append(row)
    write_jsonl(OUT / 'annotation_repair/role_confirmation_readouts.jsonl', result, freeze=True)
    write_jsonl(OUT / 'annotation_repair/role_confirmation_exclusions.jsonl', exclusions, freeze=True)
    audit = {'status':'ROLE_CONFIRMATION_CANDIDATES_NOT_ACCEPTED_INTERVALS','readouts':len(result),
             'bases':len({r['base_id'] for r in result}),'antecedent_exclusions':len(exclusions),
             'all_native_prefixes_exact':True,'causal_values_used':False,'gpu_computation':False}
    write_json(OUT / 'audit/role_confirmation_readouts.json', audit, freeze=True)
    print(audit)


if __name__=='__main__':
    main()
