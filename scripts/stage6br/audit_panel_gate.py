"""Optimistic matching capacity: unfinished annotation can only lower the bound."""
from collections import Counter, defaultdict
from itertools import product

from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching

from scripts.stage6b.common import read_json, sha, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.matching import match_graph, match_priority
from scripts.stage6br.interval_review_io import load_reviews, potentially_eligible_hold


def independently_check(graph):
    left = sorted(graph)
    right = sorted({v for vs in graph.values() for v in vs})
    lookup = {v:i for i,v in enumerate(right)}
    rr,cc = [],[]
    for i,key in enumerate(left):
        for value in graph[key]:
            rr.append(i); cc.append(lookup[value])
    matrix = csr_matrix(([1]*len(rr),(rr,cc)),shape=(len(left),len(right)))
    reference = int((maximum_bipartite_matching(matrix,perm_type='column') >= 0).sum())
    pairs = match_graph(graph)
    assert reference == len(pairs)
    return pairs


def cover_certificate(graph, pairs):
    """Konig certificate: a vertex cover as small as the matching."""
    matched_left = dict(pairs)
    matched_right = {right:left for left,right in pairs}
    reached_left = set(graph) - set(matched_left)
    reached_right = set()
    pending = list(reached_left)
    while pending:
        left = pending.pop()
        for right in graph[left]:
            if matched_left.get(left) == right or right in reached_right:
                continue
            reached_right.add(right)
            if right in matched_right and matched_right[right] not in reached_left:
                reached_left.add(matched_right[right]); pending.append(matched_right[right])
    cover_left = set(graph) - reached_left
    assert all(left in cover_left or right in reached_right for left,vs in graph.items() for right in vs)
    assert len(cover_left) + len(reached_right) == len(pairs)
    return {'left':sorted(cover_left),'right':sorted(reached_right),'size':len(pairs),'all_edges_covered':True}


def main():
    inputs = ['annotation_repair/interval_readout_variants.jsonl',
              'review/role_interval_packets.jsonl','config/hold_matching_rules.json',
              'annotation_repair/interval_review_corrections.jsonl']
    inputs += [str(p.relative_to(OUT)) for p in sorted((OUT/'annotation_repair/interval_reviews').glob('*.jsonl'))]
    variants = defaultdict(list)
    for name in inputs[:2]:
        for r in rows(OUT/name):
            if r.get('structural_primary_candidate',True):
                variants[r['id']].append(r)
    reviews = load_reviews()
    rules = read_json(OUT/'config/hold_matching_rules.json')
    transitions = {k:v for k,v in variants.items() if v[0]['endpoint_transition_type']=='T1'}
    holds = {k:v for k,v in variants.items() if v[0]['endpoint_transition_type']=='T0' and potentially_eligible_hold(reviews.get(k))}
    graph,base_graph,witnesses = {},defaultdict(set),[]
    for tid,ts in transitions.items():
        choices=[]
        for hid,hs in holds.items():
            viable=[(score,a,b) for a,b in product(ts,hs) if (score:=match_priority(a,b,rules)) is not None]
            if not viable:
                continue
            score,a,b = min(viable,key=lambda x:(x[0],x[1]['pre_id'],x[2]['pre_id']))
            choices.append((score,hid));base_graph[a['base_id']].add(hid)
            keys=('base_id','pre_id','post_id','readout_type','token_gap','normalized_progress')
            witnesses.append({'transition_id':tid,'hold_id':hid,
                              'transition_variant':{k:a[k] for k in keys},
                              'hold_variant':{k:b[k] for k in keys}})
        graph[tid]=[hid for _,hid in sorted(choices)]
    base_graph={k:sorted(v) for k,v in base_graph.items()}
    pairs=independently_check(graph)
    base_pairs=independently_check(base_graph)
    certificate=cover_certificate(graph,pairs)
    compatible={x for vs in graph.values() for x in vs}
    report={
        'status':'STOP_REPAIR_INSUFFICIENT' if len(pairs)<64 else 'ANNOTATION_MUST_CONTINUE',
        'decisive_gate':'minimum64 matched T0 holds',
        'minimum_matched_holds':64,'maximum_possible_matched_holds':len(pairs),
        'maximum_distinct_matched_transition_bases':len(base_pairs),
        'matched_base_count_used_as_stop_rule':False,
        'review_decisions':Counter(r['verdict'] for r in reviews.values()),
        'compatible_hold_intervals':len(compatible),
        'unreviewed_or_reopened_compatible_holds':sum(k not in reviews or reviews[k]['verdict']=='PENDING_CONTEXT_RECHECK' for k in compatible),
        'optimistic_assumptions':['Every unfinished transition endpoint is valid',
            'Every unreviewed or reopened hold is valid',
            'Every binding variant has valid full context',
            'New role-interval ROI overlaps are eligible'],
        'independent_scipy_matching_agrees':True,
        'vertex_cover_certificate':'audit/panel_gate_vertex_cover.json',
        'candidate_readout_families':['V','full_claim_B','native_role_confirmation_B'],
        'one_hold_use_per_underlying_interval':True,
        'scope_of_bound':'Frozen constructed readout/interval pool and matching rules; not all possible readouts in C1.',
        'full_section12_reannotation_complete':False,
        'no_causal_scores_or_state_prevalence_measured':True,
        'input_hashes':{name:sha(OUT/name) for name in inputs}}
    write_json(OUT/'audit/panel_gate.json',report,freeze=True)
    write_json(OUT/'audit/panel_gate_vertex_cover.json',certificate,freeze=True)
    write_json(OUT/'audit/panel_gate_graph.json',graph,freeze=True)
    write_jsonl(OUT/'audit/panel_gate_match_witnesses.jsonl',witnesses,freeze=True)
    print({k:v for k,v in report.items() if k!='input_hashes'})


if __name__=='__main__':
    main()
