"""Binding alternatives at the same reviewed assertions, before causal scores."""
from collections import Counter, defaultdict
from itertools import product

from scripts.stage6b.common import read_json, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.matching import match_graph, match_priority
from scripts.stage6br.interval_review_io import load_reviews, potentially_eligible_hold


def main():
    values = {r['id']:r for r in rows(OUT / 'annotation_repair/value_readouts.jsonl')}
    binding = defaultdict(list)
    for name in ('binding_readouts', 'ordinary_binding_readouts'):
        for r in rows(OUT / ('annotation_repair/' + name + '.jsonl')):
            key = (r['event_id'], r['assertion_start'], r['assertion_end'], tuple(r['demand_sources']))
            binding[key].append(r)
    intervals = list(rows(OUT / 'review/interval_packets.jsonl'))
    variants = defaultdict(list)
    for r in intervals:
        if not r['structural_primary_candidate']:
            continue
        anchors = [values[r[k]] for k in ('pre_id','post_id')]
        choices = []
        for a in anchors:
            key = (a['event_id'], a['assertion_start'], a['assertion_end'], tuple(a['demand_sources']))
            choices.append([('V',a)] + [('B',b) for b in binding[key]])
        for (ka,a),(kb,b) in product(*choices):
            gap = b['event']['current_query_zero_based'] - a['event']['current_query_zero_based']
            if gap <= 0:
                continue
            if ('B' in (ka,kb) and a['assertion_start'] == b['assertion_start']
                    and a['assertion_end'] == b['assertion_end']):
                continue  # Do not create a hold by changing score start within one assertion.
            variant = {k:r[k] for k in ('id','base_id','dataset','condition','split','evidence_class','demand_after','endpoint_transition_type')}
            variant.update({'pre_id':a['id'],'post_id':b['id'],
                            'readout_type': ka + '/' + kb,
                            'token_gap':gap,'normalized_progress':b['normalized_token_progress']})
            variants[r['id']].append(variant)
    flat = [v for group in variants.values() for v in group]
    write_jsonl(OUT / 'annotation_repair/interval_readout_variants.jsonl', flat, freeze=True)
    rules = read_json(OUT / 'config/hold_matching_rules.json')
    transitions = {key:v for key,v in variants.items() if v[0]['endpoint_transition_type']=='T1'}
    holds = {key:v for key,v in variants.items() if v[0]['endpoint_transition_type']=='T0'}
    graph, witnesses = {}, []
    for tid, ts in transitions.items():
        choices = []
        for hid, hs in holds.items():
            viable = [(score,t,h) for t,h in product(ts,hs) if (score:=match_priority(t,h,rules)) is not None]
            if viable:
                score,t,h = min(viable, key=lambda item:(item[0],item[1]['pre_id'],item[2]['pre_id']))
                choices.append((score,hid))
                witnesses.append({'transition_id':tid,'hold_id':hid,'transition_variant':t,'hold_variant':h})
        graph[tid] = [hid for _,hid in sorted(choices)]
    compatible = set(hid for choices in graph.values() for hid in choices)
    reviews = load_reviews()
    possible_graph = {tid:[hid for hid in choices if potentially_eligible_hold(reviews.get(hid))] for tid,choices in graph.items()}
    accepted_graph = {tid:[hid for hid in choices if hid in reviews and reviews[hid]['verdict']=='ACCEPTED_T0'] for tid,choices in graph.items()}
    audit = {'status':'JOINT_READOUT_STRUCTURAL_UPPER_BOUND_NOT_PANEL_GATE',
             'variants':len(flat),'type_signatures':Counter(r['readout_type'] for r in flat),
             'compatible_hold_ids':sorted(compatible),
             'maximum_structural_pairs':len(match_graph(graph)),
             'upper_bound_after_review':len(match_graph(possible_graph)),
             'accepted_hold_matching_upper_bound':len(match_graph(accepted_graph)),
             'unreviewed_compatible_holds':len(compatible-set(reviews)),
             'transition_validity_assumed_for_upper_bound':True,
             'binding_endpoint_context_validity_assumed_for_upper_bound':True,
             'each_interval_can_be_used_once':True,
             'mixed_endpoint_types_must_match_identical_signature':True,
             'causal_values_used':False}
    write_json(OUT / 'audit/joint_readout_matching_upper_bound.json', audit)
    write_jsonl(OUT / 'review/interval_match_witnesses.jsonl', witnesses, freeze=True)
    print({k:v for k,v in audit.items() if k!='compatible_hold_ids'})


if __name__=='__main__':
    main()
