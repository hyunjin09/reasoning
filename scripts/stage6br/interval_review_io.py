"""Save explicit human/agent decisions; this module does not infer semantics."""
import hashlib
import json

from scripts.stage6b.common import read_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows


def load_reviews():
    result = {}
    for path in sorted((OUT / 'annotation_repair/interval_reviews').glob('*.jsonl')):
        for row in rows(path):
            assert row['id'] not in result
            result[row['id']] = row
    path = OUT / 'annotation_repair/interval_review_corrections.jsonl'
    if path.exists():
        for correction in rows(path):
            previous = result[correction['id']]
            assert previous['verdict'] == correction['previous_verdict']
            result[correction['id']] = previous | correction | {'superseded_review': previous}
    return result


def potentially_eligible_hold(review):
    return review is None or review['verdict'] in {'ACCEPTED_T0', 'PENDING_CONTEXT_RECHECK'}


def save_decisions(batch_name, decisions):
    packet = OUT / 'review/interval_batches' / (batch_name + '.json')
    batch = read_json(packet)
    assert len(batch) == len(decisions)
    rows = []
    for item, (verdict, reason) in zip(batch, decisions):
        assert verdict in {'ACCEPTED_T0', 'ACCEPTED_T1', 'DEMAND_CHANGE', 'UNRESOLVED', 'READOUT_INSUFFICIENT'}
        assert reason
        rows.append({k:item[k] for k in ('id','pre_id','post_id','demand_before','demand_after')} | {
            'verdict':verdict, 'reason':reason,
            'endpoint_contexts_explicitly_reviewed':True,
            'entire_native_interval_reviewed':True,
            'native_interval_sha256':hashlib.sha256(item['native_interval_text'].encode()).hexdigest(),
            'review_packet':str(packet.relative_to(OUT)),
            'annotation_method':'Main-agent explicit interval plus parent-context review',
            'causal_values_used':False})
    write_jsonl(OUT / 'annotation_repair/interval_reviews' / (batch_name + '.jsonl'), rows, freeze=True)
    print(batch_name, len(rows), 'accepted', sum(r['verdict'].startswith('ACCEPTED') for r in rows))
