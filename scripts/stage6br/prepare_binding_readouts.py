"""Exact full-claim B/E readouts for image-confirmed binding mistakes.

These are readout candidates, not a selected failure panel. Selection of the
separate case-control panel must wait until the primary panel is frozen.
"""
import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import re
from collections import Counter, defaultdict

from transformers import AutoTokenizer

from scripts.stage6b.common import read_json, sha, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from visual_reasoning.stage6b.protocol import candidate_event


def binding_repair(base, start, native):
    """Return adjudicated correct assertion, support sources and optional V pair."""
    if base == 'mathverse_645' and start in {1497, 4161}:
        return native.replace('radius', 'diameter'), ['A'], native.replace('3 cm', '1.5 cm'), ['A']
    if base == 'mathverse_664' and start == 1690:
        return native.replace('diameter d', 'radius r'), ['T'], native.replace('11 cm', '22 cm'), ['T']
    if base == 'mathverse_673' and start == 240:
        return native.replace('diameter', 'radius'), ['A'], native.replace('10.5', '21'), ['A']
    if base == 'mathverse_745' and start == 116:
        return native.replace('diameter', 'radius'), ['A'], native.replace('3 cm', '6 cm'), ['A']
    if base == 'mathverse_771' and start in {512, 1231}:
        return native.replace('AB', 'AO').replace('diameter', 'radius'), ['T'], native.replace('7', '14'), ['T']
    if base == 'mathverse_786' and start in {281, 1344}:
        correct = ('the radius of the larger circle is 4 units.' if start == 281
                   else 'So the radius of the larger circle = 4.')
        return correct, ['T'], native.replace('4', '2'), ['T']
    if base == 'mathvision_2427' and start in {2076, 4246, 4792}:
        return native.replace('horizontal', 'vertical').replace('to the right', 'upward'), ['A'], None, None
    if base == 'mathvision_2427' and start == 4683:
        return native.replace('total height', 'left vertical side length'), ['T'], native.replace('8', '10'), ['A', 'T']
    if base == 'mathvista_238' and start in {527, 1308, 2131, 3345, 4047}:
        return native.replace('RQ', 'RS').replace('R to Q', 'R to S'), ['A'], native.replace('10', '15'), ['A', 'B']
    if base == 'mathvista_408' and start == 5474:
        return native.replace('the hypotenuse', 'the right hypotenuse subsegment'), ['T'], native.replace('12', '15'), ['A', 'T']
    if base == 'mathvista_757':
        if start == 873:
            return native.replace('external part', 'internal part of the lower secant'), ['A'], None, None
        if start == 2935:
            return 'the internal part of the lower secant which is 12', ['A'], None, None
        if 'tangent' in native and start != 8718:
            return native.replace('tangent', 'external lower-secant'), ['B'], None, None
    if base == 'mathvista_781' and start == 2720:
        return native.replace('FH', 'FK'), ['A'], None, None
    return None


def main():
    config = read_json(OUT / 'config/stage6br_config.json')
    tokenizer = AutoTokenizer.from_pretrained(config['model_checkpoint'], local_files_only=True)
    index = {r['event_id']: r for r in rows(OUT / 'inputs/c1_index.jsonl')}
    cases = defaultdict(dict)
    for split in ('discovery', 'confirmation'):
        for r in rows(OUT / f'review/{split}_quote_readouts.jsonl'):
            repair = binding_repair(r['base_id'], r['quote_char_start'], r['quote'])
            if repair is not None:
                cases[r['event_id']][r['quote_char_start']] = (r, repair)
    readouts, pairs, exclusions = [], [], []
    number = re.compile(r'(?<![\d.])-?\d+(?:\.\d+)?')
    for eid, event_cases in sorted(cases.items()):
        meta = index[eid]
        tokens = list(rows(meta['tokens_artifact']))
        raw = ''.join(t['decoded_token'] for t in tokens)
        packet = read_json(OUT / 'review/packets' / (eid + '.json'))
        sources = {s['source_id']: s for s in packet['sources']}
        for start, (r, (correct_binding, support, correct_value, value_support)) in sorted(event_cases.items()):
            native = r['quote']
            assert raw[start:start+len(native)] == native
            assert number.findall(correct_binding) == number.findall(native), (eid, start, 'Binding must keep literal values fixed')
            pair_ids = []
            for kind, correct, demand in [('B', correct_binding, support), ('V', correct_value, value_support)]:
                if correct is None:
                    continue
                assert correct != native
                try:
                    event = candidate_event(tokens, start, start+len(native), correct, native, tokenizer)
                except (ValueError, RuntimeError) as error:
                    exclusions.append({'event_id':eid,'char_start':start,'readout_type':kind,'reason':str(error)})
                    continue
                assert event['native_claim_suffix_ids'] == event['counterfactual_divergent_suffix_ids']
                rid = eid + '__claim_' + str(start) + '_' + kind
                pair_ids.append(rid)
                readouts.append({'id':rid, **{k:meta[k] for k in ('event_id','base_id','dataset','condition','split','group_id')},
                    'source_id':r['associated_source_id'], 'demand_sources':demand,
                    'span_id':r['span_id'], 'char_start':start, 'char_end':start+len(native),
                    'assertion_start':start,'assertion_end':start+len(native),'assertion':native,
                    'native_claim':native, 'correct_claim':correct, 'wrong_claim':native,
                    'event':event, 'readout_types':[kind,'E'], 'readout_validity':'MULTI_VALID',
                    'ground_truth_direction':'correct_minus_native_wrong', 'wrong_direction':'native_wrong_minus_correct',
                    'observed_wrong_claim':True, 'values_held_fixed':kind=='B',
                    'full_claim_context_scored':True,
                    'reason_for_validity':'Main-agent exact-quote and source-image review confirmed the wrong binding; the explicit corrected role/quantity is image-grounded. No causal promotion is inferred.',
                    'source_identity_mapped':all(sources[s]['current_image_source_identity_mapped'] for s in demand),
                    'normalized_token_progress':event['current_query_zero_based']/len(tokens),
                    'primary_interval_review_status':'NOT_INCLUDED_BY_THIS_READOUT_EXPORT',
                    'new_visual_acquisition_required':'UNRESOLVED',
                    'frozen_before_new_causal_scores':True})
            if len(pair_ids)==2:
                first, second = readouts[-2:]
                assert first['event']['history_before_ed_token_ids']==second['event']['history_before_ed_token_ids']
                pairs.append({'id':eid+'__readout_pair_'+str(start),'B_id':pair_ids[0],'V_id':pair_ids[1],
                    'same_native_prefix':True,'same_observed_wrong_claim':True,'demand_sets_may_differ':True,
                    'purpose':'Readout separation at the identical native prefix; no timing difference between V and B.'})
    write_jsonl(OUT / 'annotation_repair/binding_readouts.jsonl', [r for r in readouts if 'B' in r['readout_types']], freeze=True)
    write_jsonl(OUT / 'annotation_repair/claim_value_readouts.jsonl', [r for r in readouts if 'V' in r['readout_types']], freeze=True)
    write_jsonl(OUT / 'annotation_repair/value_binding_pairs.jsonl', pairs, freeze=True)
    write_jsonl(OUT / 'annotation_repair/binding_readout_exclusions.jsonl', exclusions, freeze=True)
    audit = {'status':'FULL_CLAIM_READOUTS_FROZEN_FAILURE_PANEL_NOT_SELECTED',
        'binding_error_readouts':sum('B' in r['readout_types'] for r in readouts),
        'same_prefix_value_binding_pairs':len(pairs),'bases':len({r['base_id'] for r in readouts}),
        'excluded':len(exclusions),'all_binding_values_fixed':True,'all_native_wrong_tokens_exact':True,
        'causal_error_promotion_tested':False,'gpu_computation':False,
        'binding_manifest_sha256':sha(OUT / 'annotation_repair/binding_readouts.jsonl')}
    write_json(OUT / 'audit/binding_readout_freeze.json',audit,freeze=True)
    print(audit)


if __name__ == '__main__':
    main()
